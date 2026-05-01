from functools import wraps

from django.conf import settings
from django.http import JsonResponse


def admin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        secret = settings.ADMIN_SECRET_KEY
        if not secret or request.headers.get("x-api-key") != secret:
            return JsonResponse({"error": "unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper
