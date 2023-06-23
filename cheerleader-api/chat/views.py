import json
from datetime import datetime, timezone
from json import JSONDecodeError

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

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


def bot_response(request: HttpRequest) -> HttpResponse:
    try:
        request_body = json.loads(request.body)
        validate(request_body, REQUEST_BODY_SCHEMA)
    except (JSONDecodeError, ValidationError) as e:
        return HttpResponseBadRequest(e)

    user_message = request_body.get("message")

    request.session.setdefault("message_count", 0)
    request.session["message_count"] += 1
    if request.session["message_count"] > settings.MAX_USER_MESSAGE_COUNT:
        bot_message = f"You've reached your message limit! You can contact Jasper at {settings.EMAIL_ADDRESS} or " \
                      f"{settings.PHONE_NUMBER}."
    else:
        bot = utils.generate_bot()
        bot_message = bot.predict(
            user_message=user_message
        )

    return JsonResponse({
        "role": "bot",
        "time": datetime.now(timezone.utc),
        "message": bot_message,
    })
