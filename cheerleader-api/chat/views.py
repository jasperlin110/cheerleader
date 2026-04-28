import json
import uuid
from datetime import datetime, timezone
from json import JSONDecodeError

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, StreamingHttpResponse
from django.views.decorators.http import require_GET, require_POST
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate
from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict, messages_to_dict

from chat import utils

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
def history(request: HttpRequest) -> HttpResponse:
    from django.http import JsonResponse
    raw = request.session.get("chat_messages") or []
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
def bot_response(request: HttpRequest) -> HttpResponse:
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
        prior_messages = messages_from_dict(request.session.get("chat_messages") or [])
        thread_id = request.session.get("thread_id") or str(uuid.uuid4())
        request.session["thread_id"] = thread_id

        def stream():
            full = ""
            for token in utils.stream_response(prior_messages, user_message, thread_id):
                full += token
                yield _sse({"token": token})
            bot_time = datetime.now(timezone.utc).isoformat()
            request.session["chat_messages"] = messages_to_dict(
                prior_messages + [
                    HumanMessage(content=user_message, additional_kwargs={"time": user_time}),
                    AIMessage(content=full, additional_kwargs={"time": bot_time}),
                ]
            )
            request.session.save()
            yield _sse({"done": True, "time": bot_time})

    response = StreamingHttpResponse(stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
