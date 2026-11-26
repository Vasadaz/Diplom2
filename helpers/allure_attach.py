"""Прикрепление HTTP-обмена к Allure-отчёту."""
import allure
import requests


def attach_response(response: requests.Response) -> None:
    """
    Прикрепить запрос и ответ к текущему шагу Allure.

    Без вложения разобрать причину падения в отчёте невозможно: видно только
    код ответа, но не отправленное тело и текст ошибки сервера.

    Args:
        response: ответ requests, полученный от стенда.
    """
    request = response.request
    request_body = request.body
    if isinstance(request_body, bytes):
        request_body = request_body.decode("utf-8", errors="replace")

    allure.attach(
        f"{request.method} {request.url}\n"
        f"request body: {request_body}\n\n"
        f"status: {response.status_code}\n"
        f"response body: {response.text}",
        name=f"{request.method} {response.status_code} {request.path_url}",
        attachment_type=allure.attachment_type.TEXT,
    )
