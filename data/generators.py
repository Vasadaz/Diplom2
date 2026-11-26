"""Генерация тестовых данных и константы для Stellar Burgers API Tests."""
import time

from faker import Faker

fake = Faker()

# Заведомо несуществующий ObjectId: 24 нуля проходят формат, но не найдутся в БД
INVALID_INGREDIENT_HASH = "000000000000000000000000"

# Строка, которая не является валидным ObjectId вообще
MALFORMED_INGREDIENT_HASH = "not-a-valid-hash"


def generate_user() -> dict[str, str]:
    """
    Сгенерировать уникальные данные пользователя.

    Timestamp в локальной части email защищает от коллизий между прогонами:
    fake.unique гарантирует уникальность только внутри одного процесса.

    Returns:
        dict: ключи email, password, name.
    """
    stamp = int(time.time() * 1000)
    return {
        "email": f"qa_{stamp}_{fake.user_name()}@example.com",
        "password": fake.password(length=10),
        "name": fake.first_name(),
    }


def generate_login(user: dict) -> dict[str, str]:
    """
    Выделить из данных пользователя только поля для логина.

    Args:
        user: словарь с email и password (может содержать лишние поля).

    Returns:
        dict: ключи email, password.
    """
    return {"email": user["email"], "password": user["password"]}
