import hashlib
import re

import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://chocale.cl/?s=descuentos+delivery+rappi+uber+eats"
APP_KEYWORDS = ("rappi", "uber eats", "pedidosya", "justo")
BANK_KEYWORDS = {
    "BancoEstado": ("bancoestado",),
    "Banco de Chile": ("banco de chile", "edwards"),
    "Banco Falabella": ("banco falabella",),
    "Tenpo": ("tenpo",),
    "MACH": ("mach", "machbank"),
    "Banco Ripley": ("banco ripley", "ripley"),
    "Tarjeta Lider Bci": ("lider bci", "líder bci", "banco bci", "tarjeta bci"),
    "Tarjeta Cencosud": ("cencosud", "cencosud scotiabank"),
}


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


def _detect_app(text):
    lowered = text.lower()
    if "uber eats" in lowered:
        return "Uber Eats"
    if "rappi" in lowered:
        return "Rappi"
    if "pedidosya" in lowered:
        return "PedidosYa"
    if "justo" in lowered:
        return "Justo"
    return "Delivery"


def _build_code(url, text):
    found = _extract_code(text)
    if found:
        return found
    digest = hashlib.sha1(f"{url}|{text}".encode("utf-8")).hexdigest()[:10].upper()
    return f"SRC-{digest}"


def _detect_issuer(text):
    lowered = text.lower()
    for issuer, keywords in BANK_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return issuer
    return ""


def _get_latest_guide_url():
    response = requests.get(SEARCH_URL, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not href.startswith("https://chocale.cl/20"):
            continue
        lowered = href.lower()
        if "delivery" in lowered and ("rappi" in lowered or "uber-eats" in lowered):
            candidates.append(href)

    if not candidates:
        return None

    def score(url):
        match = re.search(r"/(20\d{2})/(0[1-9]|1[0-2])/", url)
        if not match:
            return (0, 0)
        return (int(match.group(1)), int(match.group(2)))

    return max(candidates, key=score)


def get_chocale_delivery_discounts():
    guide_url = _get_latest_guide_url()
    if not guide_url:
        return []

    response = requests.get(guide_url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.select_one(".entry-content")
    if not content:
        return []

    coupons = []
    seen = set()
    for element in content.find_all(["p", "li"]):
        text = _clean_text(element.get_text(" ", strip=True))
        if len(text) < 25:
            continue

        lowered = text.lower()
        if not any(keyword in lowered for keyword in APP_KEYWORDS):
            continue
        if not any(signal in lowered for signal in ("descuento", "off", "beneficio", "%", "banco", "tarjeta")):
            continue

        key = text.lower()
        if key in seen:
            continue
        seen.add(key)

        coupons.append(
            {
                "title": text[:220],
                "code": _build_code(guide_url, text),
                "app": _detect_app(text),
                "discount": _extract_discount(text),
                "issuer": _detect_issuer(text),
                "source": "Chocale",
                "url": guide_url,
            }
        )

    return coupons
