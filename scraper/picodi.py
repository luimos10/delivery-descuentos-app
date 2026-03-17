import hashlib
import re

import requests
from bs4 import BeautifulSoup

PICODI_SOURCES = [
    {"app": "PedidosYa", "url": "https://www.picodi.com/cl/pedidosya"},
    {"app": "Rappi", "url": "https://www.picodi.com/cl/rappi"},
    {"app": "Uber Eats", "url": "https://www.picodi.com/cl/ubereats"},
]


def _clean_text(value):

    return " ".join(value.split())


def _extract_discount(text):
    match = re.search(r"(\d{1,3})\s*%", text)
    if match:
        return int(match.group(1))
    return 0


def _extract_code(text):
    match = re.search(r"(?:codigo|c[oó]digo|cup[oó]n)\s*[:#-]?\s*([A-Z0-9-]{4,})", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def _is_promo_text(text):
    lowered = text.lower()
    if any(noise in lowered for noise in ("valoracion", "valoración", "más sobre", "faq", "preguntas")):
        return False
    return any(keyword in lowered for keyword in ("descuento", "off", "entrega", "envio", "envío", "promo", "%"))


def _build_code(url, text):
    found = _extract_code(text)
    if found:
        return found
    digest = hashlib.sha1(f"{url}|{text}".encode("utf-8")).hexdigest()[:10].upper()
    return f"SRC-{digest}"


def _parse_picodi_source(app_name, url):

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    coupons = []
    seen_titles = set()

    for item in soup.find_all("h3"):
        title = _clean_text(item.get_text(" ", strip=True))
        if not title or title in seen_titles:
            continue
        if not _is_promo_text(title):
            continue

        seen_titles.add(title)

        coupons.append({
            "title": title,
            "code": _build_code(url, title),
            "app": app_name,
            "discount": _extract_discount(title),
            "issuer": "",
            "source": "Picodi",
            "url": url,
        })
        if len(coupons) >= 20:
            break

    return coupons


def get_picodi():
    all_coupons = []
    for source in PICODI_SOURCES:
        all_coupons.extend(_parse_picodi_source(source["app"], source["url"]))
    return all_coupons
