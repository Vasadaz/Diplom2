"""
Клиент для эндпоинтов аутентификации Stellar Burgers.

Доменные методы (`register`, `login`, `delete_user`) опираются на
транспортные `_post` / `_get` / `_delete` из BaseClient. Имена не совпадают
с транспортными, поэтому рекурсия невозможна.
"""
import requests

from api.base_client import BaseClient


class AuthClient(BaseClient):
    """Методы работы с пользователями: регистрация, логин, профиль, удаление."""

    REGISTER = "/api/auth/register"
    LOGIN = "/api/auth/login"
    LOGOUT = "/api/auth/logout"
    USER = "/api/auth/user"

    def register(self, payload: dict) -> requests.Response:
        """
        Зарегистрировать нового пользователя.

        Args:
            payload: словарь с ключами email, password, name.

        Returns:
            requests.Response: 200 и токены при успехе, 403 при дубле
            или отсутствии обязательного поля.
        """
        return self._post(self.REGISTER, json=payload)

    def login(self, payload: dict) -> requests.Response:
        """
        Выполнить вход существующего пользователя.

        Args:
            payload: словарь с ключами email, password.

        Returns:
            requests.Response: 200 и токены при успехе, 401 при неверных данных.
        """
        return self._post(self.LOGIN, json=payload)

    def get_user(self, access_token: str) -> requests.Response:
        """
        Получить данные текущего пользователя.

        Args:
            access_token: значение заголовка Authorization.

        Returns:
            requests.Response: 200 и объект user, 401 без валидного токена.
        """
        return self._get(self.USER, headers=self.bearer(access_token))

    def delete_user(self, access_token: str) -> requests.Response:
        """
        Удалить пользователя по токену. Используется в teardown фикстуры.

        Args:
            access_token: значение заголовка Authorization.

        Returns:
            requests.Response: 202 при успешном удалении.
        """
        return self._delete(self.USER, headers=self.bearer(access_token))

    def logout(self, refresh_token: str) -> requests.Response:
        """
        Завершить сессию пользователя.

        Args:
            refresh_token: refreshToken из ответа register/login.

        Returns:
            requests.Response: 200 при успехе.
        """
        return self._post(self.LOGOUT, json={"token": refresh_token})
