# Delivery Coupons Pro

Proyecto para scrapear cupones, guardarlos en SQLite, enviarlos por Telegram y verlos en un dashboard de Streamlit.
Fuentes actuales: páginas oficiales de bancos/tarjetas en Chile + Picodi (PedidosYa/Rappi/Uber Eats) + Chócale (guía mensual de delivery y descuentos bancarios).

## Requisitos

- Windows + PowerShell
- Python 3.14 (o compatible con tu entorno virtual)

## Instalacion

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuracion

Revisa `config.py`:

- `TELEGRAM_TOKEN`
- `CHAT_ID`
- `DATABASE`

## Ejecutar una corrida manual

```powershell
.\venv\Scripts\python.exe main.py
```

## Ejecutar scheduler (inmediato + cada 24 horas)

```powershell
.\venv\Scripts\python.exe -u scheduler.py
```

## Ejecutar dashboard

```powershell
.\venv\Scripts\python.exe -m streamlit run dashboard\dashboard.py
```

## Comportamiento actual

- Solo envía cupones nuevos (evita duplicados con SQLite).
- Agrupa cupones en mensajes para evitar rafagas de muchos mensajes.
- El scheduler ejecuta una corrida al iniciar y luego cada 24 horas.
- Incluye ofertas de Uber Eats y Rappi, además de beneficios bancarios de: BancoEstado, Banco de Chile, Banco Falabella, Tenpo, MACH, Banco Ripley, Tarjeta Lider Bci y Tarjeta Cencosud (según promociones publicadas vigentes en sus sitios/fuentes).
