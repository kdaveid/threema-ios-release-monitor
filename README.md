# Threema iOS Release Monitor

Meldet neue Tags von [threema-ch/threema-ios](https://github.com/threema-ch/threema-ios/tags) per Telegram.

- Prüft werktags um 08:00 und 14:00 (Europe/Zurich), verschickt nur Mo–Fr 08:00–17:30.
- Der zuletzt gemeldete Build steht in `state/last_build.txt`.
- Benötigte Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- Test: Actions → „Threema iOS Check“ → „Run workflow“ mit „Bürozeiten ignorieren“.
