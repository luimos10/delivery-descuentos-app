import hashlib
import re

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

BANK_SOURCES = [
    {
        "issuer": "Banco de Chile",
        "source": "Banco de Chile",
        "url": "https://sitiospublicos.bancochile.cl/personas/beneficios/detalle/rappi-dto",
    },
    {
        "issuer": "Banco Falabella",
        "source": "Banco Falabella",
        "url": "https://www.bancofalabella.cl/descuentos/detalle/rappi-pro-2",
    },
    {
        "issuer": "BancoEstado",
        "source": "BancoEstado",
        "url": "https://www.bancoestado.cl/content/bancoestado-public/cl/es/home/home/todosuma---bancoestado-personas/todos-beneficios/rappi---beneficios-bancoestado.html",
    },
    {
        "issuer": "Tenpo",
        "source": "Tenpo",
        "url": "https://www.tenpo.cl/beneficios/rappi-marzo",
    },
    {
        "issuer": "MACH",
        "source": "MACH",
        "url": "https://www.machbank.cl/beneficios",
    },
    {
        "issuer": "Tarjeta Lider Bci",
        "source": "Lider Bci",
        "url": "https://www.liderbci.cl/descuentos/rappi",
    },
    {
        "issuer": "Tarjeta Cencosud",
        "source": "Cencosud",
        "url": "https://www.tarjetacencosud.cl/publico/home",
    },
    {
        "issuer": "Banco Ripley",
        "source": "Banco Ripley",
        "url": "https://www.bancoripley.cl/tarjeta-ripley",
    },
]

CHCALE_SEARCH_BASE = "https://chocale.cl/?s="
ISSUER_FALLBACK = {
    "BancoEstado": ("bancoestado", "banco estado"),
    "Banco Falabella": ("banco falabella", "cmr"),
    "Banco Ripley": ("banco ripley", "ripley"),
    "Tarjeta Cencosud": ("cencosud", "cencosud scotiabank"),
    "MACH": ("mach", "machbank"),
}

APP_KEYWORDS = {
    "Uber Eats": ("uber eats",),
    "Rappi": ("rappi",),
    "PedidosYa": ("pedidosya", "pedidos ya"),
}

DELIVERY_SIGNALS = (
    "delivery",
    "descuento",
    "dcto",
    "off",
    "promo",
    "cashback",
    "%",
    "tope",
    "código",
    "codigo",
    "envío",
    "envio",
)


def _clean_text(value):
    return " ".join(value.split())


def _extract_discount(text):
    match = re.search(r"(\d{1,3})\s*%", text)
    if match:
        return int(match.group(1))
    return 0


def _detect_app(text):
    lowered = text.lower()
    for app, keywords in APP_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return app
    return "Delivery"


def _is_candidate(text):
    lowered = text.lower()
    app_hit = any(keyword in lowered for keywords in APP_KEYWORDS.values()
                  for keyword in keywords)
    signal_hit = any(signal in lowered for signal in DELIVERY_SIGNALS)
    if not app_hit or not signal_hit:
        return False
    if len(text) > 280 and "%" not in text and "descuento" not in lowered and "cashback" not in lowered:
        return False
    if "${" in text or "beneficios relacionados" in lowered:
        return False
    return True


def _build_code(url, title):
    digest = hashlib.sha1(f"{url}|{title}".encode(
        "utf-8")).hexdigest()[:12].upper()
    return f"BANK-{digest}"


def _sort_urls_by_recency(urls):
    def score(url):
        match = re.search(r"/(20\d{2})/(0[1-9]|1[0-2])/", url)
        if not match:
            return (0, 0)
        return (int(match.group(1)), int(match.group(2)))

    return sorted(urls, key=score, reverse=True)


def _extract_text_blocks(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.extract()

    blocks = []
    for element in soup.find_all(["h1", "h2", "h3", "p", "li", "a"]):
        text = _clean_text(element.get_text(" ", strip=True))
        if len(text) >= 20:
            blocks.append(text)
    return blocks


def _collect_from_source(source):
    response = requests.get(source["url"], headers=HEADERS, timeout=25)
    response.raise_for_status()
    blocks = _extract_text_blocks(response.text)

    coupons = []
    seen = set()
    for text in blocks:
        if not _is_candidate(text):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)

        coupons.append(
            {
                "title": text[:220],
                "code": _build_code(source["url"], text),
                "app": _detect_app(text),
                "discount": _extract_discount(text),
                "issuer": source["issuer"],
                "source": source["source"],
                "url": source["url"],
            }
        )
        if len(coupons) >= 15:
            break

    return coupons


def _collect_from_chocale_fallback(issuer):
    keywords = ISSUER_FALLBACK.get(issuer)
    if not keywords:
        return []

    query = f"{issuer} descuentos delivery rappi uber eats pedidosya"
    search_url = CHCALE_SEARCH_BASE + query.replace(" ", "+")
    response = requests.get(search_url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    candidate_urls = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        lowered = href.lower()
        if not href.startswith("https://chocale.cl/20"):
            continue
        if "delivery" not in lowered:
            continue
        if not any(app_kw in lowered for app_kw in ("rappi", "uber-eats", "pedidosya")):
            continue
        if href not in candidate_urls:
            candidate_urls.append(href)

    coupons = []
    seen = set()
    for article_url in _sort_urls_by_recency(candidate_urls)[:6]:
        try:
            article = requests.get(article_url, headers=HEADERS, timeout=25)
            article.raise_for_status()
        except Exception:
            continue

        article_soup = BeautifulSoup(article.text, "html.parser")
        content = article_soup.select_one(".entry-content")
        if not content:
            continue

        for element in content.find_all(["p", "li"]):
            text = _clean_text(element.get_text(" ", strip=True))
            lowered = text.lower()
            if len(text) < 25:
                continue
            if not any(keyword in lowered for keyword in keywords):
                continue
            if not _is_candidate(text):
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            coupons.append(
                {
                    "title": text[:220],
                    "code": _build_code(article_url, text),
                    "app": _detect_app(text),
                    "discount": _extract_discount(text),
                    "issuer": issuer,
                    "source": "Chocale (fallback)",
                    "url": article_url,
                }
            )
            if len(coupons) >= 5:
                break
        if coupons:
            break
    return coupons


def get_bank_delivery_discounts():
    coupons = []
    issuer_counts = {}
    for source in BANK_SOURCES:
        try:
            found = _collect_from_source(source)
            coupons.extend(found)
            issuer_counts[source["issuer"]] = issuer_counts.get(
                source["issuer"], 0) + len(found)
        except Exception:
            continue

    for issuer in ISSUER_FALLBACK:
        if issuer_counts.get(issuer, 0) > 0:
            continue
        try:
            coupons.extend(_collect_from_chocale_fallback(issuer))
        except Exception:
            continue
    return coupons
