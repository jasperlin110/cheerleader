import json
import uuid
from datetime import datetime, timedelta, timezone
from json import JSONDecodeError

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse, StreamingHttpResponse
from django.utils import timezone as django_timezone
from django.views.decorators.http import require_GET, require_POST
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate
from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict, messages_to_dict

from chat import utils
from chat.models import ChatSession
from cheerleader.utils import admin_only


REQUEST_BODY_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string", "const": "user"},
        "time": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["role", "time", "message"],
    "additionalProperties": False,
}


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@require_GET
def get_history(request: HttpRequest) -> HttpResponse:
    try:
        raw = ChatSession.objects.get(session_key=request.session.session_key).messages
    except ChatSession.DoesNotExist:
        raw = []
    messages_lc = messages_from_dict(raw)
    result = []
    for msg in messages_lc:
        if isinstance(msg, HumanMessage):
            result.append({
                "role": "user",
                "time": msg.additional_kwargs.get("time", ""),
                "message": msg.content,
            })
        elif isinstance(msg, AIMessage):
            result.append({
                "role": "bot",
                "time": msg.additional_kwargs.get("time", ""),
                "message": msg.content,
            })
    return JsonResponse({"messages": result})


@require_POST
def post_bot_response(request: HttpRequest) -> HttpResponse:
    try:
        request_body = json.loads(request.body)
        validate(request_body, REQUEST_BODY_SCHEMA)
    except (JSONDecodeError, ValidationError) as e:
        return HttpResponseBadRequest(e)

    user_message = request_body["message"]
    user_time = datetime.now(timezone.utc).isoformat()
    message_count = request.session.get("message_count", 0)
    request.session["message_count"] = message_count + 1

    if request.session["message_count"] > settings.MAX_USER_MESSAGE_COUNT:
        limit_msg = (
            f"You've reached your message limit! You can contact Jasper at "
            f"{settings.EMAIL_ADDRESS} or {settings.PHONE_NUMBER}."
        )

        def stream():
            yield _sse({"token": limit_msg})
            yield _sse({"done": True, "time": datetime.now(timezone.utc).isoformat()})
            request.session.save()

    else:
        try:
            chat_session = ChatSession.objects.get(session_key=request.session.session_key)
            prior_messages = messages_from_dict(chat_session.messages)
        except ChatSession.DoesNotExist:
            prior_messages = []
        thread_id = request.session.get("thread_id") or str(uuid.uuid4())
        request.session["thread_id"] = thread_id

        def stream():
            full = ""
            for token in utils.stream_response(prior_messages, user_message, thread_id):
                full += token
                yield _sse({"token": token})
            bot_time = datetime.now(timezone.utc).isoformat()
            updated_messages = messages_to_dict(
                prior_messages + [
                    HumanMessage(content=user_message, additional_kwargs={"time": user_time}),
                    AIMessage(content=full, additional_kwargs={"time": bot_time}),
                ]
            )
            ip = (request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                  or request.META.get("REMOTE_ADDR"))
            ChatSession.objects.update_or_create(
                session_key=request.session.session_key,
                defaults={"messages": updated_messages, "ip_address": ip or None},
            )
            request.session.save()
            yield _sse({"done": True, "time": bot_time})

    response = StreamingHttpResponse(stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@require_POST
@admin_only
def send_chat_dump(request: HttpRequest) -> JsonResponse:
    """POST /chat/dump/ — requires x-api-key: <ADMIN_SECRET_KEY>.

    Reads ChatSession rows updated in the last 24h and emails a plain-text
    dump to EMAIL_ADDRESS via iCloud SMTP. Intended to be triggered daily
    by a GitHub Actions cron job.
    """
    now = django_timezone.now()
    recent = ChatSession.objects.select_related("user").filter(updated_at__gte=now - timedelta(hours=24))

    if not recent:
        body = "No chat sessions today."
    else:
        lines = []
        for i, s in enumerate(recent, 1):
            lines.append(f"Session {i} (key: {s.session_key[:8]}...)\n" + "-" * 40)
            for msg in messages_from_dict(s.messages):
                role = "User" if isinstance(msg, HumanMessage) else "Cheerleader"
                lines.append(f"{role}: {msg.content}")
            lines.append(f"IP: {s.ip_address or 'unknown'}")
            lines.append(f"Meeting booked: {'yes' if s.meeting_scheduled else 'no'}")
            if s.user:
                lines.append(f"User: {s.user.name} <{s.user.email}>")
            lines.append("")
        body = "\n".join(lines)

    today = now.strftime("%Y-%m-%d")
    send_mail(
        subject=f"Cheerleader Chat Dump — {today}",
        message=body,
        from_email=None,
        recipient_list=[settings.EMAIL_ADDRESS],
    )
    return JsonResponse({"ok": True, "sessions": recent.count()})
