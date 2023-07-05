import json
from datetime import datetime, timezone
from json import JSONDecodeError

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate
from langchain.schema import messages_to_dict, messages_from_dict

from chat.bots import utils

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
        messages = request.session.get("chat_messages")
        if messages:
            messages = messages_from_dict(messages)

        bot = utils.generate_bot(messages)
        bot_message = bot.predict(
            user_message=user_message
        )
        request.session["chat_messages"] = messages_to_dict(bot.memory.chat_memory.messages)

    return JsonResponse({
        "role": "bot",
        "time": datetime.now(timezone.utc),
        "message": bot_message,
    })
