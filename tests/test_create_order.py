"""
Тесты создания заказа: POST /api/orders.

Покрывают авторизацию, её отсутствие, наличие и отсутствие ингредиентов,
а также неверный хеш ингредиента.

Ожидания взяты из документации API: 200 на успех, 401 без авторизации,
400 без ингредиентов, 500 при невалидном хеше ингредиента.
"""
import allure
import pytest

from api.orders_client import OrdersClient
from data.generators import INVALID_INGREDIENT_HASH, MALFORMED_INGREDIENT_HASH
from data.messages import INGREDIENTS_REQUIRED, UNAUTHORIZED
from helpers.allure_attach import attach_response
from helpers.helpers import build_order_payload, ingredient_ids_from_order

FEATURE = "Создание заказа"


@allure.feature(FEATURE)
class TestCreateOrder:
    """Сценарии создания заказа."""

    pytestmark = pytest.mark.regression

    @allure.story("Заказ с авторизацией")
    @allure.title("Заказ с авторизацией и валидными ингредиентами создаётся")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_create_order_with_auth_and_ingredients(
        self,
        orders_client: OrdersClient,
        new_user: dict,
        valid_ingredient_ids: list[str],
    ) -> None:
        """Заказ с токеном и валидными ингредиентами создаётся и получает номер."""
        payload = build_order_payload(valid_ingredient_ids)

        with allure.step("POST /api/orders с токеном и тремя ингредиентами"):
            response = orders_client.create_order(
                payload, access_token=new_user["accessToken"]
            )
            attach_response(response)

        with allure.step("Проверить код ответа 200 и success=True"):
            assert response.status_code == 200, response.text
            body = response.json()
            assert body.get("success") is True

        with allure.step("Проверить номер заказа"):
            number = body["order"].get("number")
            assert isinstance(number, int), f"number не является числом: {number!r}"
            assert number > 0

        with allure.step("Проверить, что вернулись отправленные ингредиенты"):
            actual = ingredient_ids_from_order(body["order"])
            assert set(actual) == set(valid_ingredient_ids), (
                f"Состав заказа не совпал: отправлено {valid_ingredient_ids}, "
                f"получено {actual}"
            )

    @allure.story("Заказ с авторизацией")
    @allure.title("Заказ из одного ингредиента принимается сервером")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_order_with_single_ingredient(
        self,
        orders_client: OrdersClient,
        new_user: dict,
        valid_ingredient_ids: list[str],
    ) -> None:
        """Заказ из одного ингредиента принимается сервером."""
        with allure.step("POST /api/orders с одним ингредиентом"):
            response = orders_client.create_order(
                build_order_payload(valid_ingredient_ids[:1]),
                access_token=new_user["accessToken"],
            )
            attach_response(response)

        with allure.step("Проверить 200 и success=True"):
            assert response.status_code == 200, response.text
            assert response.json().get("success") is True

    @allure.story("Заказ без авторизации")
    @allure.title("Заказ без авторизации отклоняется с 401")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_create_order_without_auth_returns_401(
        self,
        orders_client: OrdersClient,
        valid_ingredient_ids: list[str],
    ) -> None:
        """
        Заказ без токена отклоняется: 401 и требование авторизации.

        Документация: делать заказы могут только авторизованные пользователи,
        без авторизации возвращается 401 Unauthorized с сообщением
        "You should be authorised".
        """
        payload = build_order_payload(valid_ingredient_ids)

        with allure.step("POST /api/orders без заголовка Authorization"):
            response = orders_client.create_order(payload)
            attach_response(response)

        with allure.step("Проверить 401, success=False и текст ошибки"):
            assert response.status_code == 401, (
                f"Ожидался 401, получен {response.status_code}: {response.text}"
            )
            body = response.json()
            assert body.get("success") is False
            assert body.get("message") == UNAUTHORIZED

    @allure.story("Заказ без ингредиентов")
    @allure.title("Заказ с пустым списком ингредиентов возвращает 400")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_order_without_ingredients_returns_400(
        self,
        orders_client: OrdersClient,
        new_user: dict,
    ) -> None:
        """Заказ с пустым списком ингредиентов возвращает 400."""
        with allure.step("POST /api/orders с ingredients=[]"):
            response = orders_client.create_order(
                build_order_payload([]),
                access_token=new_user["accessToken"],
            )
            attach_response(response)

        with allure.step("Проверить 400 и текст 'Ingredient ids must be provided'"):
            assert response.status_code == 400, response.text
            body = response.json()
            assert body.get("success") is False
            assert body.get("message") == INGREDIENTS_REQUIRED

    @allure.story("Заказ без ингредиентов")
    @allure.title("Заказ без поля ingredients возвращает 400")
    @allure.severity(allure.severity_level.MINOR)
    def test_create_order_without_ingredients_field_returns_400(
        self,
        orders_client: OrdersClient,
        new_user: dict,
    ) -> None:
        """Заказ без поля ingredients возвращает 400."""
        with allure.step("POST /api/orders с пустым телом запроса"):
            response = orders_client.create_order(
                {}, access_token=new_user["accessToken"]
            )
            attach_response(response)

        with allure.step("Проверить 400 и success=False"):
            assert response.status_code == 400, response.text
            assert response.json().get("success") is False

    @allure.story("Заказ с неверным хешем ингредиента")
    @allure.title("Заказ с невалидным хешем ингредиента возвращает 500")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "bad_hash",
        [INVALID_INGREDIENT_HASH, MALFORMED_INGREDIENT_HASH],
        ids=["nonexistent_object_id", "malformed_string"],
    )
    def test_create_order_with_invalid_ingredient_hash_returns_500(
        self,
        orders_client: OrdersClient,
        new_user: dict,
        bad_hash: str,
    ) -> None:
        """
        Заказ с неверным хешем ингредиента возвращает 500.

        Документация: если в запросе передан невалидный хеш ингредиента,
        вернётся 500 Internal Server Error.
        """
        with allure.step(f"POST /api/orders с хешем {bad_hash}"):
            response = orders_client.create_order(
                build_order_payload([bad_hash]),
                access_token=new_user["accessToken"],
            )
            attach_response(response)

        with allure.step("Проверить код ответа 500"):
            assert response.status_code == 500, (
                f"Ожидался 500, получен {response.status_code}: {response.text}"
            )

    @allure.story("Заказ с неверным хешем ингредиента")
    @allure.title("Битый хеш среди валидных ингредиентов возвращает 500")
    @allure.severity(allure.severity_level.MINOR)
    def test_create_order_with_mixed_valid_and_invalid_hash_returns_500(
        self,
        orders_client: OrdersClient,
        new_user: dict,
        valid_ingredient_ids: list[str],
    ) -> None:
        """Заказ с одним битым хешем среди валидных возвращает 500."""
        payload = build_order_payload(
            [valid_ingredient_ids[0], INVALID_INGREDIENT_HASH]
        )

        with allure.step("POST /api/orders: валидный хеш + несуществующий"):
            response = orders_client.create_order(
                payload, access_token=new_user["accessToken"]
            )
            attach_response(response)

        with allure.step("Проверить код ответа 500"):
            assert response.status_code == 500, (
                f"Ожидался 500, получен {response.status_code}: {response.text}"
            )
