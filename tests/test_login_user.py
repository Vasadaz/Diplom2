"""
Тесты логина: POST /api/auth/login.

Покрывают вход существующего пользователя и неверные учётные данные.
"""
import allure
import pytest

from api.auth_client import AuthClient
from data.generators import generate_login
from data.messages import WRONG_CREDENTIALS
from helpers.allure_attach import attach_response

FEATURE = "Логин пользователя"


@allure.feature(FEATURE)
class TestLoginUser:
    """Сценарии входа пользователя."""

    pytestmark = pytest.mark.regression

    @allure.story("Успешный вход")
    @allure.title("Вход зарегистрированного пользователя возвращает 200 и токены")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_login_existing_user_success(
        self,
        auth_client: AuthClient,
        new_user: dict,
    ) -> None:
        """Логин зарегистрированного пользователя возвращает 200 и токены."""
        payload = generate_login(new_user)

        with allure.step(f"POST /api/auth/login для {payload['email']}"):
            response = auth_client.login(payload)
            attach_response(response)

        with allure.step("Проверить 200, success=True и оба токена"):
            assert response.status_code == 200, response.text
            body = response.json()
            assert body.get("success") is True
            assert body.get("accessToken"), "accessToken отсутствует"
            assert body.get("refreshToken"), "refreshToken отсутствует"

        with allure.step("Проверить, что вернулся тот же пользователь"):
            assert body["user"]["email"] == new_user["email"].lower()

    @allure.story("Неверные учётные данные")
    @allure.title("Существующий email с неверным паролем возвращает 401")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_with_wrong_password_returns_401(
        self,
        auth_client: AuthClient,
        new_user: dict,
    ) -> None:
        """Существующий email с неверным паролем возвращает 401."""
        payload = {"email": new_user["email"], "password": "definitely-wrong-pass"}

        with allure.step("POST /api/auth/login с неверным паролем"):
            response = auth_client.login(payload)
            attach_response(response)

        with allure.step("Проверить 401 и текст 'email or password are incorrect'"):
            assert response.status_code == 401, response.text
            body = response.json()
            assert body.get("success") is False
            assert body.get("message") == WRONG_CREDENTIALS

    @allure.story("Неверные учётные данные")
    @allure.title("Несуществующий email с верным паролем возвращает 401")
    @allure.severity(allure.severity_level.NORMAL)
    def test_login_with_wrong_email_returns_401(
        self,
        auth_client: AuthClient,
        new_user: dict,
    ) -> None:
        """Неверный email с верным паролем возвращает 401."""
        payload = {
            "email": "not-registered-user@example.com",
            "password": new_user["password"],
        }

        with allure.step("POST /api/auth/login с незарегистрированным email"):
            response = auth_client.login(payload)
            attach_response(response)

        with allure.step("Проверить 401 и success=False"):
            assert response.status_code == 401, response.text
            assert response.json().get("success") is False

    @allure.story("Неверные учётные данные")
    @allure.title("Пустые или неверные email и пароль возвращают 401")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize(
        ("email", "password"),
        [
            ("wrong@example.com", "wrongpassword"),
            ("", "somepassword"),
            ("valid@example.com", ""),
            ("", ""),
        ],
        ids=["both_wrong", "empty_email", "empty_password", "both_empty"],
    )
    def test_login_invalid_credentials_returns_401(
        self,
        auth_client: AuthClient,
        email: str,
        password: str,
    ) -> None:
        """Неверные или пустые учётные данные возвращают 401."""
        with allure.step(f"POST /api/auth/login: email='{email}', password='{password}'"):
            response = auth_client.login({"email": email, "password": password})
            attach_response(response)

        with allure.step("Проверить 401 и текст 'email or password are incorrect'"):
            assert response.status_code == 401, response.text
            body = response.json()
            assert body.get("success") is False
            assert body.get("message") == WRONG_CREDENTIALS
