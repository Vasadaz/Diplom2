# Stellar Burgers — API-тесты

Проект автотестов API сервиса Stellar Burgers: pytest + requests + allure-pytest.

Покрыты три группы эндпоинтов: создание пользователя, логин, создание заказа.

## Стек

| Инструмент | Назначение |
|---|---|
| pytest | запуск и параметризация тестов |
| requests | HTTP-клиент и сессии |
| allure-pytest | отчётность |
| Faker | генерация тестовых данных |
| python-dotenv | конфигурация через `.env` |

## Структура

```
.
├── api/
│   ├── base_client.py      # сессия, базовый URL, таймаут, транспорт (_get/_post/...)
│   ├── auth_client.py      # register, login, get_user, logout, delete_user
│   └── orders_client.py    # create_order, get_orders, get_ingredients
├── data/
│   ├── generators.py       # генерация пользователя, невалидные хеши ингредиентов
│   └── messages.py         # тексты ответов API из документации
├── helpers/
│   ├── helpers.py          # сборка тела заказа
│   └── allure_attach.py    # прикрепление request/response к отчёту
├── tests/
│   ├── test_create_user.py
│   ├── test_login_user.py
│   └── test_create_order.py
├── conftest.py             # клиенты, фабрика регистрации, уборка пользователей
├── pytest.ini
├── requirements.txt
├── .env.example
└── .gitignore
```

## Установка

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # при необходимости поправьте BASE_URL
```

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `BASE_URL` | `https://stellarburgers.education-services.ru` | адрес стенда |
| `REQUEST_TIMEOUT` | `15` | таймаут запроса, секунды |

`.env` в репозиторий не коммитится (см. `.gitignore`), в репозитории лежит `.env.example`.

## Запуск тестов

```bash
pytest                                  # весь набор, результаты Allure — в allure-results/
pytest -m smoke                         # только критичные проверки
pytest -m regression                    # полный регрессионный набор
pytest tests/test_create_order.py -v    # один модуль
```

`--alluredir=allure-results` уже прописан в `pytest.ini`, поэтому отдельно его указывать не нужно.

## Отчёт Allure

```bash
pytest --alluredir=allure-results --clean-alluredir
allure serve allure-results      # локальный просмотр
# или
allure generate allure-results -o allure-report --clean
allure open allure-report
```

Allure CLI ставится отдельно от pip — инструкция: https://allurereport.org/docs/install/

В отчёте тесты сгруппированы по `feature` (создание пользователя, логин, создание заказа), у каждого есть `story`, заголовок на русском, severity и шаги. К запросам прикреплён HTTP-обмен: метод, URL, тело запроса, код и тело ответа.

## Покрытие требований

| Требование | Тест |
|---|---|
| Создать уникального пользователя | `test_create_unique_user_success` |
| Создать уже зарегистрированного | `test_create_duplicate_user_returns_403` |
| Создать без обязательного поля | `test_create_user_without_required_field_returns_403` (email / password / name) |
| Создать с пустым обязательным полем | `test_create_user_with_empty_required_field_returns_403` (email / password / name) |
| Логин под существующим пользователем | `test_login_existing_user_success` |
| Вход с неверным логином и паролем | `test_login_with_wrong_password_returns_401`, `test_login_with_wrong_email_returns_401`, `test_login_invalid_credentials_returns_401` |
| Создание заказа с авторизацией | `test_create_order_with_auth_and_ingredients`, `test_create_order_with_single_ingredient` |
| Создание заказа без авторизации | `test_create_order_without_auth_returns_401` |
| Заказ с ингредиентами | `test_create_order_with_auth_and_ingredients` (3 ингредиента, 1 ингредиент) |
| Заказ без ингредиентов | `test_create_order_without_ingredients_returns_400`, `test_create_order_without_ingredients_field_returns_400` |
| Заказ с неверным хешем ингредиента | `test_create_order_with_invalid_ingredient_hash_returns_500` (несуществующий ObjectId, строка не по формату), `test_create_order_with_mixed_valid_and_invalid_hash_returns_500` |

Ожидаемые коды и тексты ответов взяты из документации API: 200 на успех, 403 на дубль email и на отсутствие обязательного поля, 401 на неверные учётные данные и на запрос без авторизации, 400 на отсутствие ингредиентов, 500 на невалидный хеш ингредиента.

## Особенности реализации

- Клиенты живут всю сессию, поэтому TCP-соединения переиспользуются.
- Пользователь создаётся на каждый тест, требующий авторизации, и удаляется в teardown фикстуры `created_users` — даже если проверки упали.
- Уникальность email обеспечивается timestamp в локальной части адреса: `fake.unique` гарантирует уникальность только внутри одного процесса.
- Справочник ингредиентов читается один раз за сессию (`valid_ingredient_ids`).
- Токен из ответа приходит уже с префиксом `Bearer `, поэтому заголовок собирается в `BaseClient.bearer()` без дублирования префикса.

## Ожидания и расхождения со стендом

При прогоне на `stellarburgers.education-services.ru` от документации расходятся три сценария:

| Что проверяется | Документация | Ответ стенда на 24.11.2026 | Тест |
|---|---|---|---|
| Заказ без авторизации | 401 `You should be authorised` | 200, заказ создан без владельца | `test_create_order_without_auth_returns_401` |
| Несуществующий, но корректный по формату ObjectId (`000000000000000000000000`) | 500 Internal Server Error | 400 `One or more ids provided are incorrect` | `test_create_order_with_invalid_ingredient_hash_returns_500[nonexistent_object_id]` |
| Валидный ингредиент + несуществующий | 500 Internal Server Error | 200, заказ создан только из валидного ингредиента, неизвестный отброшен молча | `test_create_order_with_mixed_valid_and_invalid_hash_returns_500` |

Строка не по формату ObjectId (`not-a-valid-hash`) даёт 500 — здесь стенд документации соответствует.

Эти три падения — находки, а не ошибки автотестов: их место в отчёте о дефектах. Когда бэкенд приведут к документации, тесты станут зелёными без правок.

## Примечание про формат ответа

В теле запроса `ingredients` — список строк-хешей, а в ответе сервер может вернуть его списком объектов ингредиентов (`_id`, `name`, `price`, ...). Поэтому сравнение состава идёт через `ingredient_ids_from_order()` из `helpers/helpers.py`, которая поддерживает оба варианта и не зависит от формата ответа.
