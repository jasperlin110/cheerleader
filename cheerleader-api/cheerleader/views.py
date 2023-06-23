from django.http import JsonResponse, HttpRequest, HttpResponse
from django.middleware.csrf import get_token


def csrf(request: HttpRequest) -> HttpResponse:
    return JsonResponse({'csrfToken': get_token(request)})
