"""Утилиты сборки тел запросов и разбора ответов API Stellar Burgers."""


def build_order_payload(ingredient_ids: list[str]) -> dict:
    """
    Собрать тело запроса создания заказа.

    Args:
        ingredient_ids: список хешей ингредиентов.

    Returns:
        dict: словарь с ключом ingredients.
    """
    return {"ingredients": ingredient_ids}


def ingredient_ids_from_order(order: dict) -> list[str]:
    """
    Достать хеши ингредиентов из объекта заказа в ответе.

    Сервер отдаёт ingredients двумя разными способами: в ответе на создание
    заказа с авторизацией это заполненные объекты с полем _id, а в поле
    ingredients запроса — просто строки. Функция приводит оба варианта
    к списку хешей.

    Args:
        order: объект order из тела ответа.

    Returns:
        list[str]: хеши ингредиентов в порядке ответа сервера.
    """
    ids: list[str] = []
    for item in order.get("ingredients", []):
        ids.append(item["_id"] if isinstance(item, dict) else item)
    return ids
