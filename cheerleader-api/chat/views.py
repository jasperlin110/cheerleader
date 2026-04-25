import json
import uuid
from datetime import datetime, timezone
from json import JSONDecodeError

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate
from langchain_core.messages import HumanMessage, messages_from_dict, messages_to_dict

from chat import utils

REQUEST_BODY_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {
            "type": "string",
            "const": "user",
        },
        "time": {
            "type": "string",
        },
        "message": {
            "type": "string",
        },
    },
    "required": [
        "role",
        "time",
        "message",
    ],
    "additionalProperties": False,
}


@require_POST
def bot_response(request: HttpRequest) -> HttpResponse:
    try:
        request_body = json.loads(request.body)
        validate(request_body, REQUEST_BODY_SCHEMA)
    except (JSONDecodeError, ValidationError) as e:
        return HttpResponseBadRequest(e)

    user_message = request_body.get("message")

    message_count = request.session.get("message_count", 0)
    request.session["message_count"] = message_count + 1
    if request.session["message_count"] > settings.MAX_USER_MESSAGE_COUNT:
        bot_message = f"You've reached your message limit! You can contact Jasper at {settings.EMAIL_ADDRESS} or " \
                      f"{settings.PHONE_NUMBER}."
    else:
        messages_data = request.session.get("chat_messages")
        prior_messages = messages_from_dict(messages_data) if messages_data else []

        app = utils.generate_bot()
        thread_id = request.session.get("thread_id") or str(uuid.uuid4())
        request.session["thread_id"] = thread_id
        config = {"configurable": {"thread_id": thread_id}}

        result = app.invoke(
            {"messages": prior_messages + [HumanMessage(content=user_message)]},
            config=config,
        )
        bot_message = result["messages"][-1].content
        request.session["chat_messages"] = messages_to_dict(result["messages"])

    return JsonResponse({
        "role": "bot",
        "time": datetime.now(timezone.utc),
        "message": bot_message,
    })
