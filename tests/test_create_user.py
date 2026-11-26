"""
Тесты создания пользователя: POST /api/auth/register.

Покрывают уникального пользователя, повторную регистрацию и отсутствие
(или пустое значение) каждого из обязательных полей.
"""
import allure
import pytest

from api.auth_client import AuthClient
from data.generators import generate_user
from data.messages import REQUIRED_FIELDS, USER_ALREADY_EXISTS
from helpers.allure_attach import attach_response

FEATURE = "Создание пользователя"


@allure.feature(FEATURE)
class TestCreateUser:
    """Сценарии регистрации пользователя."""

    pytestmark = pytest.mark.regression

    @allure.story("Регистрация уникального пользователя")
    @allure.title("Уникальный пользователь регистрируется и получает токены")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_create_unique_user_success(
        self,
        auth_client: AuthClient,
        created_users: list[str],
    ) -> None:
        """Регистрация нового пользователя возвращает 200, токены и данные user."""
        user_data = generate_user()

        with allure.step("POST /api/auth/register с уникальными данными"):
            response = auth_client.register(user_data)
            attach_response(response)
            # токен регистрируется на удаление до проверок, иначе при падении
            # ассерта пользователь останется на стенде
            if response.status_code == 200:
                token = response.json().get("accessToken", "")
                if token:
                    created_users.append(token)

        with allure.step("Проверить код ответа 200 и success=True"):
            assert response.status_code == 200, response.text
            body = response.json()
            assert body.get("success") is True

        with allure.step("Проверить, что вернулись оба токена"):
            assert body.get("accessToken", "").startswith("Bearer ")
            assert body.get("refreshToken"), "refreshToken отсутствует"

        with allure.step("Проверить данные пользователя в ответе"):
            assert body["user"]["email"] == user_data["email"].lower()
            assert body["user"]["name"] == user_data["name"]
            assert "password" not in body["user"], "Пароль не должен возвращаться"

    @allure.story("Повторная регистрация")
    @allure.title("Регистрация существующего email возвращает 403")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_duplicate_user_returns_403(
        self,
        auth_client: AuthClient,
        new_user: dict,
    ) -> None:
        """Повторная регистрация того же email возвращает 403."""
        payload = {
            "email": new_user["email"],
            "password": new_user["password"],
            "name": new_user["name"],
        }

        with allure.step(f"POST /api/auth/register повторно для {payload['email']}"):
            response = auth_client.register(payload)
            attach_response(response)

        with allure.step("Проверить 403 и текст 'User already exists'"):
            assert response.status_code == 403, response.text
            body = response.json()
            assert body.get("success") is False
            assert body.get("message") == USER_ALREADY_EXISTS

    @allure.story("Незаполненное обязательное поле")
    @allure.title("Регистрация без поля {missing_field} возвращает 403")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "missing_field",
        ["email", "password", "name"],
        ids=["no_email", "no_password", "no_name"],
    )
    def test_create_user_without_required_field_returns_403(
        self,
        auth_client: AuthClient,
        missing_field: str,
    ) -> None:
        """Регистрация без обязательного поля возвращает 403 с текстом ошибки."""
        user_data = generate_user()
        del user_data[missing_field]

        with allure.step(f"POST /api/auth/register без поля {missing_field}"):
            response = auth_client.register(user_data)
            attach_response(response)

        with allure.step("Проверить 403 и текст про обязательные поля"):
            assert response.status_code == 403, response.text
            body = response.json()
            assert body.get("success") is False
            assert body.get("message") == REQUIRED_FIELDS

    @allure.story("Незаполненное обязательное поле")
    @allure.title("Регистрация с пустым полем {empty_field} возвращает 403")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize(
        "empty_field",
        ["email", "password", "name"],
        ids=["empty_email", "empty_password", "empty_name"],
    )
    def test_create_user_with_empty_required_field_returns_403(
        self,
        auth_client: AuthClient,
        empty_field: str,
    ) -> None:
        """Регистрация с пустой строкой в обязательном поле возвращает 403."""
        user_data = generate_user()
        user_data[empty_field] = ""

        with allure.step(f"POST /api/auth/register с пустым полем {empty_field}"):
            response = auth_client.register(user_data)
            attach_response(response)

        with allure.step("Проверить 403 и success=False"):
            assert response.status_code == 403, response.text
            assert response.json().get("success") is False
