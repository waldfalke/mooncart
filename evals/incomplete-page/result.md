# Неполный capture — 2026-10-09

## Проверяемое утверждение

Барьер до наблюдения товара не заставляет модель выбирать между потерей состояния и выдуманным товаром. Сохраняется частичный `captured` JSON; более поздние статусы остаются строгими.

## RED / GREEN исполняемого контракта

До изменения схемы новые проверки отвергли `merchant.name: null` и `items: []`: оба прогона завершились с кодом 1. Наблюдённые ошибки схемы: `None is not of type 'string'` и `[] should be non-empty`.

После изменения nullable name/title и пустые items допустимы только в `captured`. Validator требует issues для null-полей и именно blocker на `/items` при отсутствии строк. Тесты также отвергают отсутствие issues, warning вместо этого blocker, пустые строки name/title и неполные `validated` данные. Fixture `evals/schema/blocked-order-draft.json` — синтетический пример внутреннего формата, не модель поведения магазина или СДЭК. Текущие результаты устанавливаются прогоном `evals/schema/validate.py` и `evals/validator/validate_semantics.py`.

## Независимый архивный replay

Агент со свежим контекстом получил скилл, URL и архивный snapshot страницы с барьером. Это replay, не текущий живой браузерный запуск. Воспроизводимые локальные проверки используют синтетическую fixture `evals/schema/blocked-order-draft.json`.

В сохранённом `order-draft.json`: безопасный URL и evidence; имя/валюта — null, товары — пустой массив. Отдельные blockers: `human_verification` на `/items`, `merchant_name_unobserved` и `merchant_currency_unobserved`. Артефакт помечен issue `archive_replay`. Товар не восстановлен из URL; служебные идентификаторы challenge не перенесены.

Validator агента завершился с кодом 0. Автор независимо повторил validator и проверил фактические `status == captured`, `items == []`, null name/currency. Оба шага успешны. Проверка подтверждает сохранение раннего барьера и применение инструкции к архивному входу, но не доказывает прохождение нового CAPTCHA или текущую доступность магазина.
