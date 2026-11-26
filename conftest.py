"""
Корневые фикстуры pytest для Stellar Burgers API Tests.

Клиенты живут на всю сессию (переиспользование TCP-соединений),
пользователь создаётся на каждый тест и удаляется в teardown,
справочник ингредиентов читается один раз.
"""
from typing import Callable, Iterator

import allure
import pytest

from api.auth_client import AuthClient
from api.orders_client import OrdersClient
from data.generators import generate_user


@pytest.fixture(scope="session")
def auth_client() -> Iterator[AuthClient]:
    """Вернуть AuthClient на всю сессию и закрыть сессию после прогона."""
    client = AuthClient()
    yield client
    client.close()


@pytest.fixture(scope="session")
def orders_client() -> Iterator[OrdersClient]:
    """Вернуть OrdersClient на всю сессию и закрыть сессию после прогона."""
    client = OrdersClient()
    yield client
    client.close()


@pytest.fixture
def created_users(auth_client: AuthClient) -> Iterator[list[str]]:
    """
    Реестр токенов созданных пользователей для гарантированной уборки.

    Тест или фикстура добавляет accessToken в список; после теста
    все пользователи удаляются, даже если проверки упали.

    Yields:
        list[str]: изменяемый список accessToken.
    """
    tokens: list[str] = []
    yield tokens

    with allure.step("Teardown: удалить созданных тестовых пользователей"):
        for token in tokens:
            try:
                auth_client.delete_user(token)
            except Exception as error:  # noqa: BLE001 - teardown не должен ломать прогон
                print(f"Не удалось удалить пользователя: {error}")


@pytest.fixture
def register_user(
    auth_client: AuthClient,
    created_users: list[str],
) -> Callable[..., dict]:
    """
    Вернуть фабрику регистрации пользователей с автоматическим удалением.

    Returns:
        Callable: функция, принимающая опциональный payload и возвращающая
        словарь с данными пользователя, accessToken и refreshToken.
    """

    def factory(payload: dict | None = None) -> dict:
        """Зарегистрировать пользователя и поставить его в очередь на удаление."""
        user_data = payload or generate_user()
        with allure.step(
            f"Подготовка: зарегистрировать пользователя {user_data['email']}"
        ):
            response = auth_client.register(user_data)
            assert response.status_code == 200, (
                f"Не удалось создать тестового пользователя: "
                f"{response.status_code} {response.text}"
            )
            body = response.json()

            token = body.get("accessToken", "")
            if token:
                created_users.append(token)

        return {
            **user_data,
            "accessToken": token,
            "refreshToken": body.get("refreshToken", ""),
        }

    return factory


@pytest.fixture
def new_user(register_user: Callable[..., dict]) -> dict:
    """
    Зарегистрировать одного уникального пользователя для теста.

    Returns:
        dict: email, password, name, accessToken, refreshToken.
        Удаление выполняется фикстурой created_users.
    """
    return register_user()


@pytest.fixture(scope="session")
def valid_ingredient_ids(orders_client: OrdersClient) -> list[str]:
    """
    Получить хеши ингредиентов из базы один раз за сессию.

    Returns:
        list[str]: _id первых трёх ингредиентов справочника.
    """
    with allure.step("Подготовка: получить справочник ингредиентов"):
        response = orders_client.get_ingredients()
        assert response.status_code == 200, (
            f"Не удалось получить список ингредиентов: "
            f"{response.status_code} {response.text}"
        )
        data = response.json().get("data", [])
        assert data, "База ингредиентов пуста — тесты заказов невозможны"
    return [item["_id"] for item in data[:3]]
