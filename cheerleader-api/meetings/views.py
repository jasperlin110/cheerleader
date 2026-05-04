import json
import re

import requests

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from chat.models import ChatSession
from users.models import User


def _build_invitee_re() -> re.Pattern:
    base = re.escape(settings.CALENDLY_API_BASE_URL.rstrip("/"))
    return re.compile(
        rf"^{base}(?:/api/v2)?/scheduled_events/([A-Za-z0-9_-]+)/invitees/([A-Za-z0-9_-]+)$"
    )


_INVITEE_RE = _build_invitee_re()


@require_POST
def handle_meeting_creation(request: HttpRequest) -> JsonResponse:
    body = json.loads(request.body) if request.body else {}
    invitee_uri = body.get("invitee_uri")

    user = None
    if invitee_uri and settings.CALENDLY_API_KEY:
        m = _INVITEE_RE.match(invitee_uri)
        if not m:
            return JsonResponse({"error": "invalid invitee_uri"}, status=400)
        safe_uri = f"{settings.CALENDLY_API_BASE_URL.rstrip('/')}/scheduled_events/{m.group(1)}/invitees/{m.group(2)}"
        resp = requests.get(
            safe_uri,
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
            user, _ = User.objects.update_or_create(
                email=resource["email"],
                defaults={
                    "name": resource.get("name", ""),
                    "phone_number": [qa["answer"] for qa in resource["questions_and_answers"] if qa["position"] == 1].pop(),
                    "timezone": resource.get("timezone", ""),
                },
            )

    ChatSession.objects.filter(session_key=request.session.session_key).update(
        meeting_scheduled=True,
        **({"user": user} if user else {}),
    )
    return JsonResponse({"ok": True})
