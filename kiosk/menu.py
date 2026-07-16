"""McDonald's Korea official menu fetch for kiosk practice."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MENU_CACHE = Path(__file__).resolve().parent / "static" / "data" / "mcdonalds_menu.json"
MCD_API = "https://www.mcdonalds.co.kr/api/v1"
MCD_IMG = "https://www.mcdonalds.co.kr"
API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.mcdonalds.co.kr/kor/menu/burger",
}

# 카테고리 기본 단품가 (이름 매칭 실패 시 fallback). 실습용 예시 가격.
PRICE_HINTS = {
    "버거": 5500,
    "사이드&디저트": 2800,
    "맥카페&음료": 2800,
    "맥모닝": 4000,
    "맥런치": 5900,
    "해피밀": 4500,
    "해피 스낵": 2000,
}

# 이름 키워드 → 단품 실습가 (긴 키워드 우선 매칭). 실제 매장가와 다를 수 있음.
# hasSet 메뉴는 키오스크에서 setExtra(기본 +2800원)를 더해 세트가를 계산한다.
NAME_PRICE_HINTS: list[tuple[str, int]] = [
    # 버거 (프리미엄 → 베이직)
    ("더블 쿼터파운더", 7800),
    ("더블 맥스파이시", 7000),
    ("더블 불고기", 5500),
    ("더블 치즈버거", 4500),
    ("더블 그릴드", 5800),
    ("트리플 치즈버거", 6000),
    ("쿼터파운더", 6100),
    # 사이드 키워드를 버거 '맥스파이시'보다 먼저 (치킨 텐더 오매칭 방지)
    ("맥스파이시® 치킨 텐더", 3200),
    ("맥스파이시 치킨 텐더", 3200),
    ("치킨 텐더", 3200),
    ("맥스파이시", 5500),
    ("맥크리스피™ 치킨 디럭스", 6800),
    ("맥크리스피 치킨 디럭스", 6800),
    ("맥크리스피™ 치킨 클래식", 5900),
    ("맥크리스피 치킨 클래식", 5900),
    ("맥크리스피", 5900),
    ("베이컨 토마토 디럭스", 6400),
    ("베이컨 토마토 에그", 4500),
    ("토마토 치즈 비프", 5900),
    ("충주 찰옥수수 치즈 크로켓 버거", 5900),
    ("충주 찰옥수수 치즈 크로켓 머핀", 4500),
    ("충주 찰옥수수", 5900),
    ("1955", 6400),
    ("슈비", 6400),
    ("슈슈", 5300),
    ("빅맥", 5500),
    ("불고기 버거", 4000),
    ("맥치킨® 모짜렐라", 5500),
    ("맥치킨 모짜렐라", 5500),
    ("맥치킨", 4000),
    ("치즈버거", 3000),
    ("햄버거", 2700),
    # 모닝
    ("디럭스 브렉퍼스트", 5500),
    ("그릴드 치킨 모닝", 4800),
    ("베이컨 에그 맥머핀", 4000),
    ("소시지 에그 맥머핀", 4000),
    ("치킨 치즈 머핀", 4200),
    ("에그 맥머핀", 3500),
    ("핫케익 3", 4200),
    ("핫케익 2", 3200),
    ("핫케익", 3200),
    # 사이드
    ("후렌치 후라이 Large", 3200),
    ("후렌치 후라이 Medium", 2700),
    ("후렌치 후라이 Small", 2000),
    ("후렌치 후라이", 2700),
    ("맥너겟® 10", 6500),
    ("맥너겟 10", 6500),
    ("맥너겟® 6", 4500),
    ("맥너겟 6", 4500),
    ("맥너겟® 4", 3400),
    ("맥너겟 4", 3400),
    ("맥너겟", 3400),
    ("골든 모짜렐라 치즈스틱 4", 4500),
    ("골든 모짜렐라 치즈스틱 2", 2800),
    ("치즈스틱 4", 4500),
    ("치즈스틱 2", 2800),
    ("치즈스틱", 2800),
    ("해쉬 브라운", 1800),
    ("해시 브라운", 1800),
    ("코울슬로", 2200),
    ("맥윙™ 8", 9900),
    ("맥윙 8", 9900),
    ("맥윙™ 4", 5900),
    ("맥윙 4", 5900),
    ("맥윙™ 2", 3400),
    ("맥윙 2", 3400),
    ("맥윙", 3400),
    ("상하이 치킨 스낵랩", 3500),
    ("게살 크림 크로켓 스낵랩", 3500),
    ("스낵랩", 3500),
    ("맥플러리", 3500),
    ("선데이", 2500),
    ("스트로베리콘", 1500),
    ("아이스크림콘", 1500),
    # 음료
    ("코카-콜라 제로 Large", 2400),
    ("코카-콜라 제로 Medium", 2000),
    ("코카-콜라 Large", 2400),
    ("코카-콜라 Medium", 2000),
    ("코카-콜라", 2000),
    ("스프라이트 제로 Large", 2400),
    ("스프라이트 제로 Medium", 2000),
    ("스프라이트 Large", 2400),
    ("스프라이트 Medium", 2000),
    ("스프라이트", 2000),
    ("환타 Large", 2400),
    ("환타 Medium", 2000),
    ("환타", 2000),
    ("그리머스 쉐이크", 3500),
    ("딸기 쉐이크", 3500),
    ("바닐라 쉐이크", 3500),
    ("초코 쉐이크", 3500),
    ("쉐이크", 3500),
    ("오렌지 주스", 2800),
    ("생수", 1500),
    ("아이스 바닐라 라떼 Large", 4300),
    ("아이스 바닐라 라떼 Medium", 3800),
    ("바닐라 라떼 Large", 4300),
    ("바닐라 라떼 Medium", 3800),
    ("바닐라 라떼", 3800),
    ("아이스 카페라떼 Large", 4300),
    ("아이스 카페라떼 Medium", 3800),
    ("카페라떼 Large", 4300),
    ("카페라떼 Medium", 3800),
    ("카페라떼", 3800),
    ("카푸치노 Large", 4300),
    ("카푸치노 Medium", 3800),
    ("카푸치노", 3800),
    ("아이스 아메리카노 Large", 3300),
    ("아이스 아메리카노 Medium", 2800),
    ("아메리카노 Large", 3300),
    ("아메리카노 Medium", 2800),
    ("아메리카노", 2800),
    ("아이스 드립 커피 Large", 3000),
    ("아이스 드립 커피 Medium", 2500),
    ("드립 커피 Large", 3000),
    ("드립 커피 Medium", 2500),
    ("드립 커피", 2500),
    ("망고 맥피즈 Large", 3500),
    ("망고 맥피즈 Medium", 3000),
    ("망고 맥피즈", 3000),
    ("망고 피치 아이스티 Large", 3500),
    ("망고 피치 아이스티 Medium", 3000),
    ("피치 아이스티 Large", 3500),
    ("피치 아이스티 Medium", 3000),
    ("아이스티", 3000),
]

SIDE_PRIORITY = [
    "후렌치 후라이 Medium",
    "후렌치 후라이 Large",
    "후렌치 후라이 Small",
    "맥너겟",
    "해쉬 브라운",
    "해시 브라운",
    "치즈스틱",
    "치킨 텐더",
    "코울슬로",
]
DRINK_PRIORITY = [
    "코카-콜라 Medium",
    "코카-콜라 Large",
    "코카-콜라 제로 Medium",
    "스프라이트 Medium",
    "스프라이트 Large",
    "환타 Medium",
    "환타 Large",
    "스프라이트 제로",
    "코카-콜라",
    "스프라이트",
    "환타",
    "사이다",
    "쉐이크",
    "오렌지 주스",
    "아메리카노 Medium",
    "아이스 아메리카노 Medium",
    "드립 커피 Medium",
]
BURGER_PRIORITY = [
    "빅맥",
    "상하이",
    "1955",
    "쿼터파운더",
    "불고기",
    "맥치킨",
    "치즈버거",
    "햄버거",
]


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _img_url(path: str) -> str:
    if not path:
        return ""
    if path.startswith("http"):
        return path
    parts = path.split("/")
    encoded = "/".join(urllib.parse.quote(p) for p in parts)
    return MCD_IMG + encoded


def _estimate_price(name: str, category: str) -> int:
    """단품 실습 가격. 세트 여부는 키오스크 UI에서 setExtra로 가산한다."""
    raw = name or ""
    # 표시/매칭용: 끝의 '세트'·'콤보' 제거 후 키워드 조회
    bare = re.sub(r"\s*(세트|콤보)\s*$", "", raw).strip() or raw
    n = bare.lower()

    price = None
    for kw, p in NAME_PRICE_HINTS:
        if kw.lower() in bare.lower() or kw in bare:
            price = p
            break

    if price is None:
        base = PRICE_HINTS.get(category, 4000)
        if "더블" in bare:
            price = base + 1500
        elif "라지" in bare or "large" in n:
            price = base + 500
        elif "small" in n or "스몰" in bare:
            price = max(1500, base - 800)
        else:
            price = base

    # 모닝/사이드 '콤보'는 단품보다 구성이 많아 가산
    if re.search(r"콤보\s*$", raw) and "세트" not in raw:
        price += 2000

    # 해피 스낵 카테고리는 프로모션 할인가 느낌으로 소폭 인하
    if category == "해피 스낵":
        price = max(1500, price - 500)

    # 맥런치: 점심 세트 구성가 (단품 대비 소폭 할인된 세트 느낌)
    if category == "맥런치":
        price = max(4500, price + 1500)

    return int(price)


def _priority_score(name: str, keywords: list[str]) -> int:
    for i, kw in enumerate(keywords):
        if kw in name:
            return i
    score = 1000
    if "디카페인" in name:
        score += 200
    if "Large" in name:
        score += 5
    return score


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=API_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode("utf-8"))


def _fetch_category_items(main_category: int) -> list[dict]:
    """Fetch products from all subcategories (e.g. 맥카페 + 음료)."""
    base_params = {"page": 1, "view_rows": 100, "mainCategory": main_category}
    first = _get_json(
        f"{MCD_API}/kor/product/product/list?" + urllib.parse.urlencode(base_params)
    )["resultObject"]

    by_id: dict[int, dict] = {}
    for it in first.get("list") or []:
        by_id[it["seq"]] = it

    for sub in first.get("subCategory") or []:
        sub_seq = sub.get("seq")
        if not sub_seq:
            continue
        params = {
            "page": 1,
            "view_rows": 100,
            "mainCategory": main_category,
            "subCategory": sub_seq,
        }
        try:
            data = _get_json(
                f"{MCD_API}/kor/product/product/list?"
                + urllib.parse.urlencode(params)
            )["resultObject"]
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
        ):
            continue
        for it in data.get("list") or []:
            by_id[it["seq"]] = it

    return list(by_id.values())


def _normalize_product(it: dict, category: dict) -> dict | None:
    if it.get("status") != "Y":
        return None
    image = (
        it.get("pcListImageUrl")
        or it.get("pcImageUrl")
        or it.get("moListImageUrl")
        or it.get("moImageUrl")
        or ""
    )
    raw_name = _strip_html(it.get("korName") or "")
    if not raw_name:
        return None
    menu_status = it.get("menuStatus") or ""
    has_set = "세트" in menu_status or "세트" in raw_name
    has_single = "단품" in menu_status or "세트" not in raw_name
    # 표시명: "빅맥 세트" → "빅맥" (사진은 원본 유지)
    name = re.sub(r"\s*세트\s*$", "", raw_name).strip() or raw_name
    eng = _strip_html(it.get("engName") or "")
    eng = re.sub(r"\s*Meal\s*$", "", eng, flags=re.I).strip() or eng
    return {
        "id": it.get("seq"),
        "categoryId": category["seq"],
        "categorySlug": category["slug"],
        "categoryName": category["korName"],
        "name": name,
        "engName": eng,
        "desc": _strip_html(
            (it.get("korContent") or "")
            .replace("<br>", " ")
            .replace("<br/>", " ")
            .replace("<br />", " ")
        ),
        "calorie": it.get("calorie") or "",
        "image": _img_url(image),
        # 단품 실습가 (세트는 키오스크에서 setExtra 가산)
        "price": _estimate_price(raw_name, category["korName"]),
        "hasSet": has_set,
        "hasSingle": has_single or not has_set,
        "menuStatus": menu_status,
        "subCategorySeq": it.get("subCategorySeq"),
        "source": "https://www.mcdonalds.co.kr",
    }


def _sort_products(products: list[dict], slug: str) -> list[dict]:
    if slug == "sides":
        keywords = SIDE_PRIORITY
    elif slug == "mc-cafe":
        keywords = DRINK_PRIORITY
    elif slug == "burger":
        keywords = BURGER_PRIORITY
    else:
        keywords = []

    def key(p: dict):
        return (
            _priority_score(p["name"], keywords),
            0 if p.get("image") else 1,
            p["name"],
        )

    return sorted(products, key=key)


def _pick_set_sides(products: list[dict]) -> list[dict]:
    sides = [p for p in products if p["categorySlug"] == "sides" and p.get("image")]
    dessert_kw = ["맥플러리", "선데이", "파이", "콘파이", "디저트", "아이스크림"]
    mains = [p for p in sides if not any(k in p["name"] for k in dessert_kw)]
    mains = _sort_products(mains, "sides")
    picked = []
    seen_family = set()
    for p in mains:
        family = p["name"]
        for size in (" Small", " Medium", " Large", " 스몰", " 미디엄", " 라지"):
            family = family.replace(size, "")
        if "후렌치 후라이" in p["name"]:
            key = f"후렌치 후라이 {p['name'].split()[-1]}"
            if key in seen_family:
                continue
            seen_family.add(key)
            picked.append(p)
            continue
        if family in seen_family:
            continue
        seen_family.add(family)
        picked.append(p)
        if len(picked) >= 10:
            break
    return [
        {"id": s["id"], "name": s["name"], "image": s["image"], "price": 0}
        for s in picked
    ]


def _pick_set_drinks(products: list[dict]) -> list[dict]:
    drinks = [p for p in products if p["categorySlug"] == "mc-cafe" and p.get("image")]
    drinks = _sort_products(drinks, "mc-cafe")
    soft = []
    coffee = []
    for p in drinks:
        if any(k in p["name"] for k in ("코카-콜라", "스프라이트", "환타", "사이다")):
            soft.append(p)
        elif "디카페인" in p["name"]:
            continue
        else:
            coffee.append(p)

    def prefer_medium(items):
        med = [p for p in items if "Medium" in p["name"]]
        large = [p for p in items if "Large" in p["name"]]
        other = [p for p in items if p not in med and p not in large]
        return med + large + other

    ordered = prefer_medium(soft) + prefer_medium(coffee)
    picked = []
    seen = set()
    for p in ordered:
        if p["name"] in seen:
            continue
        seen.add(p["name"])
        picked.append(p)
        if len(picked) >= 12:
            break
    return [
        {"id": d["id"], "name": d["name"], "image": d["image"], "price": 0}
        for d in picked
    ]


def fetch_live_menu() -> dict:
    """Fetch latest menu from McDonald's Korea official API (all subcategories)."""
    cats_raw = _get_json(f"{MCD_API}/kor/category/list")["resultObject"]["list"]
    order = ["burger", "sides", "mc-cafe", "mc-morning", "mc-lunch", "happy-snack"]
    cats_map = {c["slug"]: c for c in cats_raw}
    categories = []
    products: list[dict] = []

    for slug in order:
        c = cats_map.get(slug)
        if not c:
            continue
        categories.append({"id": c["seq"], "slug": c["slug"], "name": c["korName"]})
        items = _fetch_category_items(c["seq"])
        cat_products = []
        for it in items:
            p = _normalize_product(it, c)
            if p:
                cat_products.append(p)
        products.extend(_sort_products(cat_products, slug))

    return {
        "source": "https://www.mcdonalds.co.kr/api/v1",
        "note": "메뉴명·이미지는 맥도날드 코리아 공식 사이트 기준. 가격은 실습용 예시입니다.",
        "categories": categories,
        "products": products,
        "setDefaults": {"setExtra": 2800},
        "sides": _pick_set_sides(products),
        "drinks": _pick_set_drinks(products),
    }


def _clean_display_names(data: dict) -> dict:
    """Ensure product names drop trailing '세트' even from older cache files."""
    for p in data.get("products") or []:
        raw = p.get("name") or ""
        if "세트" in raw:
            p["hasSet"] = True
        cleaned = re.sub(r"\s*세트\s*$", "", raw).strip()
        if cleaned:
            p["name"] = cleaned
    return data


def load_cached_menu() -> dict:
    if MENU_CACHE.exists():
        return _clean_display_names(
            json.loads(MENU_CACHE.read_text(encoding="utf-8"))
        )
    raise FileNotFoundError("menu cache missing")


def get_menu() -> dict:
    """Live menu with local cache fallback; refreshes cache on success."""
    try:
        data = fetch_live_menu()
        data = _clean_display_names(data)
        try:
            MENU_CACHE.parent.mkdir(parents=True, exist_ok=True)
            MENU_CACHE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass
        return data
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        KeyError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as e:
        data = load_cached_menu()
        data["fallback"] = True
        data["error"] = str(e)
        return data
