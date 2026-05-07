import json
import logging
import re
from json import JSONDecodeError

import requests

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from chat.models import ChatSession
from users.models import User


logger = logging.getLogger(__name__)


def _build_invitee_re() -> re.Pattern:
    base = re.escape(settings.CALENDLY_API_BASE_URL.rstrip("/"))
    return re.compile(
        rf"^{base}(?:/api/v2)?/scheduled_events/([A-Za-z0-9_-]+)/invitees/([A-Za-z0-9_-]+)$"
    )

_INVITEE_RE = _build_invitee_re()

REQUEST_BODY_SCHEMA = {
    "type": "object",
    "properties": {
        "invitee_uri": {"type": "string", "pattern": _INVITEE_RE.pattern},
    },
    "required": ["invitee_uri"],
    "additionalProperties": False,
}


@require_POST
def handle_meeting_creation(request: HttpRequest) -> JsonResponse:
    try:
        body = json.loads(request.body) if request.body else {}
        validate(body, REQUEST_BODY_SCHEMA)
    except (JSONDecodeError, ValidationError):
        return JsonResponse({"error": "invalid request"}, status=400)
    invitee_uri = body["invitee_uri"]

    user = None
    if not settings.CALENDLY_API_KEY:
        logger.error("Missing CALENDLY_API_KEY")
    else:
        resp = requests.get(
            invitee_uri,
            headers={"Authorization": f"Bearer {settings.CALENDLY_API_KEY}"},
            timeout=5,
        )
        if resp.ok:
            resource = resp.json().get("resource", {})
            # Example Calendly response
            # {
            #   "resource": {
            #     "email": "email@example.com",
            #     "name": "John Doe",
            #     "timezone": "America/New_York",
            #     "questions_and_answers": [
            #       {
            #         "answer": "radio button answer",
            #         "position": 0,
            #         "question": "Question with Radio Buttons answer type"
            #       },
            #       {
            #         "answer": "Multiple line\nAnswer",
            #         "position": 1,
            #         "question": "Question with Multiple Lines answer type"
            #       },
            #       {
            #         "answer": "Answer 1\nAnswer 2\nAnswer 3",
            #         "position": 2,
            #         "question": "Question with Checkboxes answer type"
            #       }
            #     ]
            #   }
            # }
            email = resource.get("email")
            if not email:
                logger.error("Calendly invitee resource missing email: %s", resource)
            else:
                phone_number = next(
                    (qa["answer"] for qa in resource.get("questions_and_answers", []) if qa.get("position") == 1),
                    "",
                )
                user, _ = User.objects.update_or_create(
                    email=email,
                    defaults={
                        "name": resource.get("name", ""),
                        "phone_number": phone_number,
                        "timezone": resource.get("timezone", ""),
                    },
                )

    ChatSession.objects.filter(session_key=request.session.session_key).update(
        meeting_scheduled=True,
        **({"user": user} if user else {}),
    )
    return JsonResponse({"ok": True})
