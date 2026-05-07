from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from cheerleader.utils import admin_only, get_client_ip


class GetClientIpTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_remote_addr_when_no_xff(self):
        request = self.factory.get("/", REMOTE_ADDR="1.2.3.4")
        self.assertEqual(get_client_ip(request), "1.2.3.4")

    def test_returns_first_xff_hop(self):
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="5.6.7.8, 9.10.11.12")
        self.assertEqual(get_client_ip(request), "5.6.7.8")

    def test_returns_none_when_no_addr(self):
        request = self.factory.get("/", REMOTE_ADDR="")
        self.assertIsNone(get_client_ip(request))

    def test_xff_strips_whitespace(self):
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="  5.6.7.8  , 9.10.11.12")
        self.assertEqual(get_client_ip(request), "5.6.7.8")


class AdminOnlyTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        @admin_only
        def dummy_view(request):
            return JsonResponse({"ok": True})

        self.view = dummy_view

    @override_settings(ADMIN_SECRET_KEY="secret")
    def test_correct_key_calls_view(self):
        request = self.factory.post("/", HTTP_X_API_KEY="secret")
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(ADMIN_SECRET_KEY="secret")
    def test_wrong_key_returns_401(self):
        request = self.factory.post("/", HTTP_X_API_KEY="wrong")
        self.assertEqual(self.view(request).status_code, 401)

    @override_settings(ADMIN_SECRET_KEY="secret")
    def test_missing_key_returns_401(self):
        request = self.factory.post("/")
        self.assertEqual(self.view(request).status_code, 401)

    @override_settings(ADMIN_SECRET_KEY=None)
    def test_no_secret_configured_returns_401(self):
        request = self.factory.post("/", HTTP_X_API_KEY="anything")
        self.assertEqual(self.view(request).status_code, 401)
