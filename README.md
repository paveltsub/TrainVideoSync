# TrainVideoSync

**Реализовано**:

1. **Синхронное воспроизведение 4-х видео** в одном GUI с регулировкой скорости (папка `video_player`).
2. **Клиент-серверная архитектура**: сервер синхронизирует и отсылает кадры, клиент отображает, включая метки на старый кадр (папка `server_client`).
3. **Отправка видео через чат-бот Telegram** по запросу `/get_video` (папка `bot`).

Видео и аннотации находятся в папке `data`.

---

## Установка

1. **Склонируйте** репозиторий или скачайте архив:
   ```bash
   git clone https://github.com/paveltsub/TrainVideoSync
   ```
   Перейдите в папку проекта

2. **Создайте виртуальное окружение/активируйте виртуальное окружение:**
   ```bash
   python -m venv venv
   ```
   ```
   .\venv\Scripts\activate - Windows
   ```
   ```
   source venv/bin/activate - Linux/Mac
   ```

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
---

## Запуск

1. **Запуск видеоплеера (синхронное воспроизведение):**
   Перейдите в папку video_player:
   ```bash
   cd video_player
   python video_player.py
   ```
2. **Запуск клиент-серверной архитектуры:**
   ```bash
   cd server_client
   ```
   Терминал 1 (сервер):
   ```bash
   python server.py
   ```
   
   Терминал 2 (клиент):
   ```bash
   python client.py
   ```
3. **Запуск телеграм-бота:**
   Перейдите в папку bot:
   ```bash
   cd bot
   ```
   
   В файле telegram_bot.py замените переменную bot_token на токен бота.
   Запустите:
   ```bash
   python telegram_bot.py
   ```

   Проверьте работу бота в Telegram, перейдя к @TrainVideos_bot.
