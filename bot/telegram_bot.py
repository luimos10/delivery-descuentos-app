import asyncio
import re
from telegram import Bot
from config import TELEGRAM_TOKEN, CHAT_ID

MAX_MESSAGE_LEN = 3500


def _extract_weekday(text):
    lowered = text.lower()
    patterns = [
        ("lunes", r"\blunes\b"),
        ("martes", r"\bmartes\b"),
        ("miercoles", r"\bmi[eé]rcoles\b"),
        ("jueves", r"\bjueves\b"),
        ("viernes", r"\bviernes\b"),
        ("sabado", r"\bs[aá]bado\b"),
        ("domingo", r"\bdomingo\b"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, lowered):
            return label
    if "todos los dias" in lowered or "todos los días" in lowered:
        return "todos los dias"
    return "no especificado"


def _build_benefit(c):
    parts = []
    discount = int(c.get("discount", 0) or 0)
    raw_code = c.get("code", "")
    is_real_code = bool(raw_code) and not raw_code.startswith("SRC-") and not raw_code.startswith("BANK-")
    if discount > 0:
        parts.append(f"{discount}%")
    if is_real_code:
        parts.append(f"cupon {raw_code}")
    if not parts:
        return "sin porcentaje/cupon"
    return " + ".join(parts)


def _coupon_line(c):
    app = c.get("app", "Delivery")
    benefit = _build_benefit(c)
    issuer = c.get("issuer", "")
    issuer_label = issuer if issuer else "sin banco"
    weekday = _extract_weekday(c.get("title", ""))
    return f"- {app} | {benefit} | {issuer_label} | {weekday}"


def _build_messages(coupons):

    header = "🚨 NUEVOS CUPONES\n\n"
    messages = []
    current = header

    for coupon in coupons:
        line = _coupon_line(coupon) + "\n"
        if len(current) + len(line) > MAX_MESSAGE_LEN:
            messages.append(current.rstrip())
            current = header + line
        else:
            current += line

    if current.strip():
        messages.append(current.rstrip())

    return messages


async def _send_messages_async(messages):
    async with Bot(token=TELEGRAM_TOKEN) as bot:
        for message in messages:
            await bot.send_message(chat_id=CHAT_ID, text=message)


def send_coupon(c):

    send_coupons([c])


def send_coupons(coupons):

    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[telegram] TELEGRAM_TOKEN/CHAT_ID no configurados. No se enviaron mensajes.")
        return 0

    if not coupons:
        print("[telegram] No hay cupones nuevos para enviar.")
        return 0

    messages = _build_messages(coupons)
    asyncio.run(_send_messages_async(messages))
    return len(coupons)
