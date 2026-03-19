# Security Policy

## Variables sensibles

Nunca subas secretos al repositorio:

- `TELEGRAM_TOKEN`
- `CHAT_ID`
- Cualquier API key/token de terceros

Usa `.env` local (ya ignorado por `.gitignore`) y comparte solo `.env.example`.

## Archivos locales que no deben versionarse

- `*.db`, `*.sqlite`, `*.sqlite3`
- `venv/`, `.venv/`
- `__pycache__/`, `*.pyc`
- logs y archivos de lock

## Si un secreto se filtró

1. Revoca/rota el secreto inmediatamente (por ejemplo, regenerar token de bot).
2. Elimina el secreto del código y del historial de git.
3. Fuerza nuevos valores en `.env` local.
4. Revisa commits recientes antes del siguiente push.

## Recomendaciones operativas

- Mantén dependencias actualizadas.
- Revisa cambios de scraping porque fuentes externas cambian frecuentemente.
- Usa Pull Requests con validación CI para cambios de producción.
