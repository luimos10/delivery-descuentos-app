from scraper.picodi import get_picodi
from scraper.chocale import get_chocale_delivery_discounts
from scraper.banks import get_bank_delivery_discounts
from bot.telegram_bot import send_coupons
from database.db import init_db, save_coupon


def _collect_coupons():
    all_coupons = []
    sources = [
        ("Banks", get_bank_delivery_discounts),
        ("Picodi", get_picodi),
        ("Chocale", get_chocale_delivery_discounts),
    ]
    for source_name, loader in sources:
        try:
            items = loader()
            all_coupons.extend(items)
            print(f"[main] {source_name}: {len(items)} ofertas leidas.")
        except Exception as e:
            print(f"[main] {source_name} fallo: {e}")
    return all_coupons


def run():
    init_db()

    coupons = _collect_coupons()
    new_coupons = []

    for c in coupons:
        if save_coupon(c):
            new_coupons.append(c)

    sent_count = send_coupons(new_coupons)
    return sent_count


if __name__ == "__main__":

    run()
