# Delivery Coupons Pro

Scraper de cupones de delivery en Chile con persistencia en SQLite, notificaciones por Telegram y dashboard en Streamlit.

## Qué hace

- Lee promociones desde fuentes bancarias + Picodi + Chócale.
- Guarda solo registros nuevos en SQLite (sin duplicados por `code`).
- Envía solo cupones nuevos al canal/chat de Telegram.
- Permite filtrar, exportar y revisar cobertura en dashboard.

## Estructura

```text
delivery-coupons-pro/
  bot/                 # Envío de mensajes Telegram
  dashboard/           # UI Streamlit
  database/            # Acceso SQLite
  docs/                # Documentación de arquitectura y seguridad
  scraper/             # Recolección de fuentes externas
  config.py            # Variables de entorno y defaults
  main.py              # Flujo manual (scrape -> DB -> Telegram)
  scheduler.py         # Ejecución automática cada 24h
```

Más detalle técnico: `docs/ARCHITECTURE.md`.

## Requisitos

- Windows + PowerShell
- Python 3.11+ (recomendado)

## Instalación

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuración

```powershell
Copy-Item .env.example .env
```

Variables necesarias en `.env`:

- `TELEGRAM_TOKEN`
- `CHAT_ID`
- `DATABASE` (por defecto: `cupones.db`)

## Ejecución

Corrida manual:

```powershell
.\venv\Scripts\python.exe main.py
```

Scheduler (inmediato + cada 24h):

```powershell
.\venv\Scripts\python.exe -u scheduler.py
```

Dashboard:

```powershell
.\venv\Scripts\python.exe -m streamlit run dashboard\dashboard.py
```

## Checklist antes de subir a GitHub

1. Verificar que `.env` no esté trackeado.
2. Verificar que `*.db`, `__pycache__/` y `venv/` no estén trackeados.
3. Ejecutar validación rápida:
   ```powershell
   python -m py_compile main.py scheduler.py config.py bot\telegram_bot.py database\db.py scraper\*.py dashboard\dashboard.py
   ```
4. Confirmar que no haya secretos en commits/historial.
