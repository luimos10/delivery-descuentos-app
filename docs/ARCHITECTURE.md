# Arquitectura y Flujo

## Estructura principal

```text
delivery-coupons-pro/
  scraper/
    picodi.py        # Ofertas/cupones desde Picodi (PedidosYa/Rappi/Uber Eats)
    chocale.py       # Guía mensual de descuentos delivery (Chile)
    banks.py         # Sitios bancarios/tarjetas + fallback por emisor
  database/
    db.py            # SQLite: crear tabla, guardar deduplicado, listar cupones
  bot/
    telegram_bot.py  # Formatea y envía mensajes a Telegram
  dashboard/
    dashboard.py     # UI Streamlit con filtros y exportación
  main.py            # Orquestador (scrapers -> DB -> Telegram)
  scheduler.py       # Ejecuta main.run() al iniciar y cada 24 horas
  config.py          # Lee TELEGRAM_TOKEN, CHAT_ID y DATABASE desde entorno/.env
```

## Flujo de datos

`main.run()`:

1. `database.init_db()`
2. `scraper.banks.get_bank_delivery_discounts()`
3. `scraper.picodi.get_picodi()`
4. `scraper.chocale.get_chocale_delivery_discounts()`
5. Merge de ofertas
6. `save_coupon()` con `INSERT OR IGNORE` por `code`
7. `bot.send_coupons(new_coupons)`

## Flujo de ejecución

Manual:

```powershell
.\venv\Scripts\python.exe main.py
```

Automático:

```powershell
.\venv\Scripts\python.exe -u scheduler.py
```

Dashboard:

```powershell
.\venv\Scripts\python.exe -m streamlit run dashboard\dashboard.py
```
