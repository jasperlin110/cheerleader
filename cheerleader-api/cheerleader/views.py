from django.http import HttpRequest, HttpResponse


def csrf(_: HttpRequest) -> HttpResponse:
    return HttpResponse('CSRF token set.')
