"""
Базовый HTTP-клиент: хранит сессию, базовый URL и общие заголовки.

Транспортные методы намеренно названы с префиксом подчёркивания
(`_get`, `_post`, `_patch`, `_delete`), чтобы доменные методы наследников
(`delete_user`, `create_order`) не могли случайно перекрыть транспорт
и вызвать бесконечную рекурсию.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://stellarburgers.education-services.ru"
DEFAULT_TIMEOUT = 15


class BaseClient:
    """Обёртка над requests.Session с базовым URL из окружения."""

    BASE_URL: str = os.getenv("BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", DEFAULT_TIMEOUT))

    def __init__(self) -> None:
        """Создать сессию и выставить Content-Type по умолчанию."""
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def close(self) -> None:
        """Закрыть сессию и освободить TCP-соединения."""
        self._session.close()

    @staticmethod
    def bearer(access_token: str) -> dict[str, str]:
        """
        Собрать заголовок авторизации из токена.

        API Stellar Burgers возвращает accessToken уже с префиксом "Bearer ",
        поэтому префикс добавляется только если его нет.

        Args:
            access_token: токен из ответа register/login.

        Returns:
            dict: заголовок Authorization.
        """
        token = (
            access_token
            if access_token.startswith("Bearer ")
            else f"Bearer {access_token}"
        )
        return {"Authorization": token}

    def _url(self, path: str) -> str:
        """
        Склеить базовый URL и относительный путь эндпоинта.

        Args:
            path: путь вида "/api/auth/login".

        Returns:
            str: абсолютный URL.
        """
        return f"{self.BASE_URL}{path}"

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Выполнить HTTP-запрос. Единственная точка выхода в сеть.

        Args:
            method: HTTP-метод ("GET", "POST", ...).
            path: относительный путь эндпоинта.
            **kwargs: любые параметры requests (json, headers, params).

        Returns:
            requests.Response: ответ без проверки статуса.
        """
        kwargs.setdefault("timeout", self.TIMEOUT)
        return self._session.request(method, self._url(path), **kwargs)

    def _get(self, path: str, **kwargs) -> requests.Response:
        """HTTP GET по относительному пути."""
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, json: dict | None = None, **kwargs) -> requests.Response:
        """HTTP POST с JSON-телом."""
        return self._request("POST", path, json=json, **kwargs)

    def _patch(self, path: str, json: dict | None = None, **kwargs) -> requests.Response:
        """HTTP PATCH с JSON-телом."""
        return self._request("PATCH", path, json=json, **kwargs)

    def _delete(self, path: str, **kwargs) -> requests.Response:
        """HTTP DELETE по относительному пути."""
        return self._request("DELETE", path, **kwargs)
