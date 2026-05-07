import hmac
from functools import wraps

from django.conf import settings
from django.http import HttpRequest, JsonResponse


def get_client_ip(request: HttpRequest) -> str | None:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        ip = xff.split(",")[0].strip()
        if ip:
            return ip
    return request.META.get("REMOTE_ADDR") or None


def admin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        secret = settings.ADMIN_SECRET_KEY
        if not secret or not hmac.compare_digest(request.headers.get("x-api-key", ""), secret):
            return JsonResponse({"error": "unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper
