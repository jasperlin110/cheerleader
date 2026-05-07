import json
from unittest.mock import MagicMock, patch

from jsonschema.validators import validate

from django.test import TestCase, override_settings

from chat.models import ChatSession
from meetings.views import REQUEST_BODY_SCHEMA

VALID_URI = "https://api.calendly.com/scheduled_events/ABC123/invitees/XYZ456"
VALID_URI_V2 = "https://api.calendly.com/api/v2/scheduled_events/ABC123/invitees/XYZ456"


class HandleMeetingCreationTests(TestCase):
    def setUp(self):
        # GET /chat/history/ initializes the session and creates a ChatSession row
        self.client.get("/chat/history/")
        self.chat_session = ChatSession.objects.get(
            session_key=self.client.session.session_key
        )

    def post(self, body):
        return self.client.post(
            "/meeting/", data=body, content_type="application/json"
        )

    # --- Method guard ---

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get("/meeting/").status_code, 405)

    # --- Input validation ---

    def test_invalid_json_returns_400(self):
        self.assertEqual(self.post("not-json").status_code, 400)

    def test_missing_invitee_uri_returns_400(self):
        self.assertEqual(self.post(json.dumps({})).status_code, 400)

    def test_invitee_uri_wrong_domain_returns_400(self):
        body = json.dumps({"invitee_uri": "https://evil.com/scheduled_events/A/invitees/B"})
        self.assertEqual(self.post(body).status_code, 400)

    def test_invitee_uri_not_a_string_returns_400(self):
        self.assertEqual(self.post(json.dumps({"invitee_uri": 123})).status_code, 400)

    def test_extra_fields_returns_400(self):
        body = json.dumps({"invitee_uri": VALID_URI, "extra": "field"})
        self.assertEqual(self.post(body).status_code, 400)

    def test_v1_uri_passes_schema_validation(self):
        validate({"invitee_uri": VALID_URI}, REQUEST_BODY_SCHEMA)

    def test_v2_uri_passes_schema_validation(self):
        validate({"invitee_uri": VALID_URI_V2}, REQUEST_BODY_SCHEMA)

    # --- meeting_scheduled always set ---

    def test_no_calendly_key_still_marks_meeting_scheduled(self):
        with override_settings(CALENDLY_API_KEY=None), self.assertLogs("meetings.views", level="ERROR") as logs:
            response = self.post(json.dumps({"invitee_uri": VALID_URI}))
        self.assertEqual(response.status_code, 200)
        self.chat_session.refresh_from_db()
        self.assertTrue(self.chat_session.meeting_scheduled)
        self.assertIsNone(self.chat_session.user)
        self.assertTrue(any("Missing CALENDLY_API_KEY" in msg for msg in logs.output))

    @patch("meetings.views.requests.get")
    def test_calendly_api_error_still_marks_meeting_scheduled(self, mock_get):
        mock_get.return_value = MagicMock(ok=False)
        with override_settings(CALENDLY_API_KEY="test-key"):
            response = self.post(json.dumps({"invitee_uri": VALID_URI}))
        self.assertEqual(response.status_code, 200)
        self.chat_session.refresh_from_db()
        self.assertTrue(self.chat_session.meeting_scheduled)
        self.assertIsNone(self.chat_session.user)

    # --- Calendly response parsing edge cases ---

    @patch("meetings.views.requests.get")
    def test_missing_email_does_not_create_user(self, mock_get):
        mock_get.return_value = MagicMock(ok=True)
        mock_get.return_value.json.return_value = {"resource": {"name": "John"}}
        with override_settings(CALENDLY_API_KEY="test-key"), self.assertLogs("meetings.views", level="ERROR") as logs:
            response = self.post(json.dumps({"invitee_uri": VALID_URI}))
        self.assertEqual(response.status_code, 200)
        self.chat_session.refresh_from_db()
        self.assertTrue(self.chat_session.meeting_scheduled)
        self.assertIsNone(self.chat_session.user)
        self.assertTrue(any("Calendly invitee resource missing email:" in msg for msg in logs.output))

    @patch("meetings.views.requests.get")
    def test_missing_phone_question_uses_empty_string(self, mock_get):
        mock_get.return_value = MagicMock(ok=True)
        mock_get.return_value.json.return_value = {
            "resource": {
                "email": "test@example.com",
                "name": "John",
                "timezone": "UTC",
                "questions_and_answers": [],
            }
        }
        with override_settings(CALENDLY_API_KEY="test-key"):
            response = self.post(json.dumps({"invitee_uri": VALID_URI}))
        self.assertEqual(response.status_code, 200)
        self.chat_session.refresh_from_db()
        self.assertTrue(self.chat_session.meeting_scheduled)
        self.assertIsNotNone(self.chat_session.user)
        self.assertEqual(self.chat_session.user.phone_number, "")

    @patch("meetings.views.requests.get")
    def test_full_response_creates_user_with_correct_fields(self, mock_get):
        mock_get.return_value = MagicMock(ok=True)
        mock_get.return_value.json.return_value = {
            "resource": {
                "email": "test@example.com",
                "name": "John Doe",
                "timezone": "America/New_York",
                "questions_and_answers": [
                    {"answer": "some answer", "position": 0, "question": "Q0"},
                    {"answer": "555-1234", "position": 1, "question": "Phone"},
                ],
            }
        }
        with override_settings(CALENDLY_API_KEY="test-key"):
            response = self.post(json.dumps({"invitee_uri": VALID_URI}))
        self.assertEqual(response.status_code, 200)
        self.chat_session.refresh_from_db()
        self.assertTrue(self.chat_session.meeting_scheduled)
        user = self.chat_session.user
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.phone_number, "555-1234")
        self.assertEqual(user.timezone, "America/New_York")
