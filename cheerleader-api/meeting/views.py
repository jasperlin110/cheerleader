import json

import requests

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from chat.models import ChatSession, User


@require_POST
def handle_meeting_creation(request: HttpRequest) -> JsonResponse:
    body = json.loads(request.body) if request.body else {}
    invitee_uri = body.get("invitee_uri")

    user = None
    if invitee_uri and settings.CALENDLY_API_KEY:
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
            user, _ = User.objects.update_or_create(
                email=resource["email"],
                defaults={
                    "name": resource.get("name", ""),
                    "phone_number": [qa["answer"] for qa in resource["questions_and_answers"] if qa["position"] == 0].pop(),
                    "timezone": resource.get("timezone", ""),
                },
            )

    ChatSession.objects.filter(session_key=request.session.session_key).update(
        meeting_scheduled=True,
        **({"user": user} if user else {}),
    )
    return JsonResponse({"ok": True})
