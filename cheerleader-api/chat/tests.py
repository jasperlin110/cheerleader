import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase
from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict, messages_to_dict


class SSEHelperTest(TestCase):
    def test_token_event_format(self):
        from chat.views import _sse
        self.assertEqual(_sse({"token": "hi"}), 'data: {"token": "hi"}\n\n')

    def test_done_event_roundtrips(self):
        from chat.views import _sse
        result = _sse({"done": True, "time": "2024-01-01T00:00:00Z"})
        self.assertTrue(result.startswith("data: "))
        self.assertTrue(result.endswith("\n\n"))
        parsed = json.loads(result[len("data: "):].strip())
        self.assertTrue(parsed["done"])
        self.assertEqual(parsed["time"], "2024-01-01T00:00:00Z")


class HistoryViewTest(TestCase):
    def test_empty_session_returns_empty_list(self):
        response = self.client.get("/chat/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["messages"], [])

    def test_rejects_post(self):
        self.assertEqual(self.client.post("/chat/history/").status_code, 405)

    def test_deserializes_human_and_ai_messages(self):
        session = self.client.session
        session["chat_messages"] = messages_to_dict([
            HumanMessage(content="Hello", additional_kwargs={"time": "2024-01-01T00:00:00+00:00"}),
            AIMessage(content="Hi there", additional_kwargs={"time": "2024-01-01T00:00:01+00:00"}),
        ])
        session.save()

        msgs = self.client.get("/chat/history/").json()["messages"]
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0], {"role": "user", "time": "2024-01-01T00:00:00+00:00", "message": "Hello"})
        self.assertEqual(msgs[1], {"role": "bot", "time": "2024-01-01T00:00:01+00:00", "message": "Hi there"})

    def test_missing_time_defaults_to_empty_string(self):
        session = self.client.session
        session["chat_messages"] = messages_to_dict([HumanMessage(content="No time")])
        session.save()

        msgs = self.client.get("/chat/history/").json()["messages"]
        self.assertEqual(msgs[0]["time"], "")


class BotResponseViewTest(TestCase):
    URL = "/chat/bot-response/"
    VALID_BODY = {"role": "user", "time": "2024-01-01T00:00:00Z", "message": "Hi"}

    def _post(self, body):
        return self.client.post(self.URL, data=json.dumps(body), content_type="application/json")

    def _consume(self, response) -> str:
        return b"".join(response.streaming_content).decode()

    def test_rejects_get(self):
        self.assertEqual(self.client.get(self.URL).status_code, 405)

    def test_invalid_json_returns_400(self):
        response = self.client.post(self.URL, data="not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_missing_message_field_returns_400(self):
        self.assertEqual(self._post({"role": "user", "time": "now"}).status_code, 400)

    def test_wrong_role_returns_400(self):
        self.assertEqual(self._post({"role": "bot", "time": "now", "message": "hi"}).status_code, 400)

    def test_additional_properties_returns_400(self):
        self.assertEqual(self._post({**self.VALID_BODY, "extra": "field"}).status_code, 400)

    @patch("chat.views.utils.stream_response")
    def test_valid_request_returns_sse_stream(self, mock_stream):
        mock_stream.return_value = iter(["Hello", " world"])
        response = self._post(self.VALID_BODY)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        content = self._consume(response)
        self.assertIn('"token": "Hello"', content)
        self.assertIn('"token": " world"', content)
        self.assertIn('"done": true', content)

    @patch("chat.views.utils.stream_response")
    def test_no_cache_headers_set(self, mock_stream):
        mock_stream.return_value = iter([])
        response = self._post(self.VALID_BODY)
        self.assertEqual(response["Cache-Control"], "no-cache")
        self.assertEqual(response["X-Accel-Buffering"], "no")
        self._consume(response)

    @patch("chat.views.utils.stream_response")
    def test_increments_message_count(self, mock_stream):
        mock_stream.return_value = iter(["Hi"])
        self._consume(self._post(self.VALID_BODY))
        self.assertEqual(self.client.session["message_count"], 1)

    @patch("chat.views.utils.stream_response")
    def test_message_count_accumulates_across_requests(self, mock_stream):
        for _ in range(3):
            mock_stream.return_value = iter(["Hi"])
            self._consume(self._post(self.VALID_BODY))
        self.assertEqual(self.client.session["message_count"], 3)

    @patch("chat.views.utils.stream_response")
    def test_saves_user_and_bot_messages_to_session(self, mock_stream):
        mock_stream.return_value = iter(["Hello back"])
        self._consume(self._post(self.VALID_BODY))

        msgs = messages_from_dict(self.client.session["chat_messages"])
        self.assertEqual(len(msgs), 2)
        self.assertIsInstance(msgs[0], HumanMessage)
        self.assertEqual(msgs[0].content, "Hi")
        self.assertIsInstance(msgs[1], AIMessage)
        self.assertEqual(msgs[1].content, "Hello back")

    @patch("chat.views.utils.stream_response")
    def test_thread_id_created_and_reused(self, mock_stream):
        mock_stream.return_value = iter(["Hi"])
        self._consume(self._post(self.VALID_BODY))
        thread_id = self.client.session["thread_id"]
        self.assertIsNotNone(thread_id)

        mock_stream.return_value = iter(["Hi again"])
        self._consume(self._post(self.VALID_BODY))
        self.assertEqual(self.client.session["thread_id"], thread_id)

    def test_rate_limit_returns_contact_info(self):
        session = self.client.session
        session["message_count"] = settings.MAX_USER_MESSAGE_COUNT
        session.save()

        content = self._consume(self._post(self.VALID_BODY))
        self.assertIn("message limit", content)
        self.assertIn(settings.EMAIL_ADDRESS, content)
        self.assertIn(settings.PHONE_NUMBER, content)

    def test_rate_limit_does_not_call_stream_response(self):
        session = self.client.session
        session["message_count"] = settings.MAX_USER_MESSAGE_COUNT
        session.save()

        with patch("chat.views.utils.stream_response") as mock_stream:
            self._consume(self._post(self.VALID_BODY))
            mock_stream.assert_not_called()


class StreamResponseTest(TestCase):
    @patch("chat.utils._create_app")
    def test_yields_ai_message_chunks(self, mock_create_app):
        from langchain_core.messages import AIMessageChunk
        mock_app = MagicMock()
        mock_app.stream.return_value = [
            (AIMessageChunk(content="Hello"), {}),
            (AIMessageChunk(content=" world"), {}),
        ]
        mock_create_app.return_value = mock_app

        from chat.utils import stream_response
        self.assertEqual(list(stream_response([], "test", "thread-1")), ["Hello", " world"])

    @patch("chat.utils._create_app")
    def test_skips_empty_content_chunks(self, mock_create_app):
        from langchain_core.messages import AIMessageChunk
        mock_app = MagicMock()
        mock_app.stream.return_value = [
            (AIMessageChunk(content=""), {}),
            (AIMessageChunk(content="Hi"), {}),
        ]
        mock_create_app.return_value = mock_app

        from chat.utils import stream_response
        self.assertEqual(list(stream_response([], "test", "thread-1")), ["Hi"])

    @patch("chat.utils._create_app")
    def test_skips_non_ai_message_chunks(self, mock_create_app):
        from langchain_core.messages import AIMessageChunk
        mock_app = MagicMock()
        mock_app.stream.return_value = [
            (HumanMessage(content="not AI"), {}),
            (AIMessageChunk(content="AI response"), {}),
        ]
        mock_create_app.return_value = mock_app

        from chat.utils import stream_response
        self.assertEqual(list(stream_response([], "test", "thread-1")), ["AI response"])

    @patch("chat.utils._create_app")
    def test_includes_prior_messages_in_stream_input(self, mock_create_app):
        mock_app = MagicMock()
        mock_app.stream.return_value = []
        mock_create_app.return_value = mock_app

        from chat.utils import stream_response
        prior = [HumanMessage(content="prior")]
        list(stream_response(prior, "new message", "thread-abc"))

        input_msgs = mock_app.stream.call_args[0][0]["messages"]
        self.assertEqual(len(input_msgs), 2)
        self.assertEqual(input_msgs[0].content, "prior")
        self.assertEqual(input_msgs[1].content, "new message")

    @patch("chat.utils._create_app")
    def test_passes_thread_id_in_config(self, mock_create_app):
        mock_app = MagicMock()
        mock_app.stream.return_value = []
        mock_create_app.return_value = mock_app

        from chat.utils import stream_response
        list(stream_response([], "test", "my-thread-id"))

        config = mock_app.stream.call_args[1]["config"]
        self.assertEqual(config["configurable"]["thread_id"], "my-thread-id")
