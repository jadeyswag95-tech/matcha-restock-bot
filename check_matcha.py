"""
監控丸久小山園（Marukyu Koyamaen）抹茶商品頁面：
偵測新品上架 / 補貨 / 降價，並透過 LINE 推播通知。

每次執行流程：
1. 抓取商品頁面，解析每個商品的 id / 名稱 / 價格 / 是否有庫存 / 連結
2. 跟上一次的快照（state.json）比對
3. 有變化就組訊息，用 LINE Messaging API 廣播出去
4. 把最新狀態寫回 state.json
"""

import json
import os
import sys
from pathlib import Path

import cloudscraper
import requests
from bs4 import BeautifulSoup

CATALOG_URL = "https://www.marukyu-koyamaen.co.jp/english/shop/products/catalog/matcha"
STATE_FILE = Path(__file__).parent / "state.json"

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"

# 官網有 Cloudflare 防護，一般 requests 會被 403 擋下，改用 cloudscraper 繞過
_scraper = cloudscraper.create_scraper()


def fetch_products():
    resp = _scraper.get(CATALOG_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    products = {}
    for li in soup.select("li.product"):
        item_id = li.get("id", "")
        if not item_id.startswith("item-"):
            continue
        product_id = item_id.replace("item-", "")

        link_tag = li.select_one("a.woocommerce-loop-product__link")
        name_tag = li.select_one(".product-name h4")
        price_tag = li.select_one(".product-price .woocommerce-Price-amount")

        if not (link_tag and name_tag and price_tag):
            continue

        # 價格文字類似 "¥12,600"，取數字部分
        price_text = price_tag.get_text(strip=True)
        price_digits = "".join(ch for ch in price_text if ch.isdigit())
        price = int(price_digits) if price_digits else None

        in_stock = "outofstock" not in li.get("class", [])

        products[product_id] = {
            "name": name_tag.get_text(strip=True),
            "price": price,
            "in_stock": in_stock,
            "link": link_tag.get("href", ""),
        }

    return products


def load_previous_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(products):
    STATE_FILE.write_text(
        json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def diff_products(previous, current):
    events = []

    for product_id, curr in current.items():
        prev = previous.get(product_id)

        if prev is None:
            events.append(("新品上架", curr))
            continue

        if not prev.get("in_stock") and curr.get("in_stock"):
            events.append(("補貨", curr))

        if (
            prev.get("price") is not None
            and curr.get("price") is not None
            and curr["price"] < prev["price"]
        ):
            events.append(("降價", curr, prev["price"]))

    return events


def format_message(events):
    lines = ["🍵 丸久小山園抹茶更新通知"]
    for event in events:
        kind = event[0]
        product = event[1]
        line = f"\n【{kind}】{product['name']}"
        if kind == "降價":
            old_price = event[2]
            line += f"\n¥{old_price:,} → ¥{product['price']:,}"
        elif product.get("price") is not None:
            line += f"\n¥{product['price']:,}"
        line += f"\n{product['link']}"
        lines.append(line)
    return "\n".join(lines)


def send_line_broadcast(message):
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("未設定 LINE_CHANNEL_ACCESS_TOKEN，略過推播（僅本地測試模式）")
        return

    # LINE 單則文字訊息上限 5000 字，超過就截斷避免推播失敗
    if len(message) > 4900:
        message = message[:4900] + "\n...(訊息過長，已截斷)"

    resp = requests.post(
        LINE_BROADCAST_URL,
        headers={
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"messages": [{"type": "text", "text": message}]},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"LINE 推播失敗: {resp.status_code} {resp.text}", file=sys.stderr)
        resp.raise_for_status()


def main():
    previous = load_previous_state()
    current = fetch_products()

    if not current:
        print("警告：這次沒有抓到任何商品，可能是網站結構變了，先不更新狀態", file=sys.stderr)
        sys.exit(1)

    is_first_run = not previous
    events = [] if is_first_run else diff_products(previous, current)

    if is_first_run:
        print(f"第一次執行，記錄 {len(current)} 個商品為基準，不發通知")
    elif events:
        message = format_message(events)
        print(message)
        send_line_broadcast(message)
    else:
        print("沒有變化")

    save_state(current)


if __name__ == "__main__":
    main()
