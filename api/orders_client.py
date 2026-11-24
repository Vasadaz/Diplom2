"""Клиент для эндпоинтов заказов и справочника ингредиентов."""
import requests

from api.base_client import BaseClient


class OrdersClient(BaseClient):
    """Методы создания заказов и получения списка ингредиентов."""

    ORDERS = "/api/orders"
    INGREDIENTS = "/api/ingredients"

    def create_order(
        self,
        payload: dict,
        access_token: str | None = None,
    ) -> requests.Response:
        """
        Создать заказ.

        Args:
            payload: словарь с ключом ingredients (список хешей).
            access_token: токен авторизации; None — запрос без авторизации.

        Returns:
            requests.Response: 200 при успехе, 400 без ингредиентов,
            401 без авторизации, 500 при неверном хеше.
        """
        headers = self.bearer(access_token) if access_token else {}
        return self._post(self.ORDERS, json=payload, headers=headers)

    def get_orders(self, access_token: str) -> requests.Response:
        """
        Получить заказы текущего пользователя.

        Args:
            access_token: токен авторизации.

        Returns:
            requests.Response: 200 и список orders, 401 без авторизации.
        """
        return self._get(self.ORDERS, headers=self.bearer(access_token))

    def get_ingredients(self) -> requests.Response:
        """
        Получить справочник всех ингредиентов.

        Returns:
            requests.Response: 200 и список в поле data.
        """
        return self._get(self.INGREDIENTS)
