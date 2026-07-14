# Деплой бота на Railway (безкоштовно, працює 24/7)

Загальна схема: код → GitHub → Railway → додаєш токени → бот працює.

## Крок 1. Акаунт GitHub
1. Зайди на https://github.com → Sign up (якщо акаунта ще немає).
2. Підтверди пошту.

## Крок 2. Створити репозиторій на GitHub
1. https://github.com/new
2. Repository name: `telegram-design-bot` (будь-яка назва).
3. Обери **Private** (щоб код був прихований).
4. НЕ додавай README/gitignore (вони вже є). Натисни **Create repository**.
5. Скопіюй адресу виду `https://github.com/ТВІЙ_ЛОГІН/telegram-design-bot.git`.

## Крок 3. Залити код (виконати в терміналі в папці проєкту)
```bash
git init
git add .
git commit -m "Telegram design bot"
git branch -M main
git remote add origin https://github.com/ТВІЙ_ЛОГІН/telegram-design-bot.git
git push -u origin main
```
> Файл `.env` НЕ заллється (він у .gitignore) — це правильно, токен має лишатись секретом.

## Крок 4. Railway
1. https://railway.app → Login → **Login with GitHub**.
2. **New Project** → **Deploy from GitHub repo** → обери свій репозиторій.
3. Railway сам знайде Python і почне збірку.

## Крок 5. Додати секрети (замість файлу .env)
1. У проєкті Railway відкрий вкладку **Variables**.
2. Додай дві змінні:
   - `BOT_TOKEN` = твій токен від BotFather
   - `OWNER_CHAT_ID` = твій chat_id
3. Railway автоматично перезапустить бота.

## Крок 6. Перевірка
1. Вкладка **Deployments** → **View Logs** → маєш побачити «Бот запущено».
2. Напиши боту `/start` у Telegram — навіть із вимкненим ПК він відповідає.

## Оновлення бота в майбутньому
Змінив код локально — залий зміни, Railway задеплоїть сам:
```bash
git add .
git commit -m "опис змін"
git push
```
