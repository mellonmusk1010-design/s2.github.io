"""메가MGC커피 공식 사이트 메뉴 수집 (menu.php)."""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MENU_CACHE = Path(__file__).resolve().parent / "static" / "data" / "mega_menu.json"
BASE = "https://www.mega-mgccoffee.com/menu/menu.php"
IMG_HOST = "https://img.79plus.co.kr"
CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.mega-mgccoffee.com/menu/?menu_category1=1&menu_category2=1",
    "X-Requested-With": "XMLHttpRequest",
}

# 음료 / 푸드
CATEGORIES = [
    {"id": 1, "slug": "drink", "name": "음료", "c1": "1", "c2": "1"},
    {"id": 2, "slug": "food", "name": "푸드", "c1": "2", "c2": "2"},
]

PRICE_HINTS = {"음료": 3000, "푸드": 3500}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30, context=CTX) as res:
        return res.read().decode("utf-8", "replace")


def _fetch_category(c1: str, c2: str, page: int = 1) -> str:
    params = {
        "page": str(page),
        "menu_category1": c1,
        "menu_category2": c2,
        "category": "",
        "list_checkbox_all": "1",
    }
    return _get(BASE + "?" + urllib.parse.urlencode(params))


def _parse_items(html: str, category: dict) -> list[dict]:
    items = []
    # each <li> block
    blocks = re.split(r"<li>", html)
    seen = set()
    for block in blocks:
        imgs = re.findall(
            r'src="(https://img\.79plus\.co\.kr/megahp/manager/upload/menu/[^"]+)"',
            block,
        )
        names = re.findall(
            r'cont_text_title">\s*<div class="text text1">\s*<b>([^<]+)</b>',
            block,
        )
        if not names:
            names = re.findall(r"<b>([^<]{2,50})</b>", block)
        if not imgs or not names:
            continue
        name = names[0].strip()
        if name in seen or len(name) < 2:
            continue
        seen.add(name)
        image = imgs[0]
        label = ""
        lm = re.search(
            r'cont_gallery_list_label[^"]*"[^>]*>\s*([^<]+)',
            block,
        )
        if lm:
            label = lm.group(1).strip()
        eng = ""
        em = re.search(
            r'cont_text_info">\s*<div class="text text1">\s*([^<]+)',
            block,
        )
        if em:
            eng = em.group(1).strip()
        kcal = ""
        km = re.search(r"([\d.]+)\s*kcal", block, re.I)
        if km:
            kcal = km.group(1)
        price = PRICE_HINTS.get(category["name"], 3000)
        if "라떼" in name or "프라페" in name or "스무디" in name:
            price += 500
        if "세트" in name:
            price += 1000
        pid = abs(hash(name + image)) % 10_000_000
        items.append(
            {
                "id": pid,
                "categoryId": category["id"],
                "categorySlug": category["slug"],
                "categoryName": category["name"],
                "name": name,
                "engName": eng,
                "label": label,
                "calorie": kcal,
                "image": image,
                "price": price,
                "hasSet": False,
                "hasSingle": True,
                "source": "https://www.mega-mgccoffee.com/menu/",
            }
        )
    return items


def fetch_live_menu() -> dict:
    categories = []
    products: list[dict] = []
    for cat in CATEGORIES:
        categories.append(
            {"id": cat["id"], "slug": cat["slug"], "name": cat["name"]}
        )
        try:
            html = _fetch_category(cat["c1"], cat["c2"], 1)
            products.extend(_parse_items(html, cat))
            # page 2 if available
            html2 = _fetch_category(cat["c1"], cat["c2"], 2)
            if len(html2) > 500:
                products.extend(_parse_items(html2, cat))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            continue

    # de-dupe by name
    by_name = {}
    for p in products:
        by_name[p["name"]] = p
    products = list(by_name.values())

    return {
        "source": "https://www.mega-mgccoffee.com/menu/",
        "brand": "mega",
        "note": "메뉴명·이미지는 메가MGC커피 공식 사이트 기준. 가격은 실습용 예시.",
        "categories": categories,
        "products": products,
        "setDefaults": {"setExtra": 0},
        "sides": [],
        "drinks": [],
    }


def load_cached_menu() -> dict:
    if MENU_CACHE.exists():
        return json.loads(MENU_CACHE.read_text(encoding="utf-8"))
    raise FileNotFoundError("mega menu cache missing")


def get_menu() -> dict:
    try:
        data = fetch_live_menu()
        if data.get("products"):
            try:
                MENU_CACHE.parent.mkdir(parents=True, exist_ok=True)
                MENU_CACHE.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except OSError:
                pass
            return data
        return load_cached_menu()
    except Exception as e:
        try:
            data = load_cached_menu()
            data["fallback"] = True
            data["error"] = str(e)
            return data
        except Exception as cache_err:
            return {"error": str(e), "cache_error": str(cache_err), "products": [], "categories": []}
