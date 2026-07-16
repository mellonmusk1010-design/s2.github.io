"""쿠팡 실습용 생필품 카탈로그 (실습 가격 · 로컬 이미지)."""

# 이미지는 coupang/static/img 실습용 카드 (항상 로드됨)
def _img(name: str) -> str:
    return f"/static/coupang/img/{name}.svg"


PRODUCTS = {
    "categories": [
        {"slug": "tissue", "name": "휴지·티슈"},
        {"slug": "clean", "name": "세제·청소"},
        {"slug": "body", "name": "세면·구강"},
        {"slug": "kitchen", "name": "주방·식품"},
    ],
    "products": [
        {"id": "c01", "name": "3겹 화장지 30롤", "price": 18900, "categorySlug": "tissue", "badge": "로켓배송", "image": _img("c01")},
        {"id": "c02", "name": "물티슈 100매 10팩", "price": 12900, "categorySlug": "tissue", "badge": "로켓배송", "image": _img("c02")},
        {"id": "c03", "name": "키친타월 12롤", "price": 9900, "categorySlug": "tissue", "badge": "로켓배송", "image": _img("c03")},
        {"id": "c04", "name": "미용티슈 3박스", "price": 7900, "categorySlug": "tissue", "badge": "무료배송", "image": _img("c04")},
        {"id": "c05", "name": "액체 세탁세제 3L", "price": 15900, "categorySlug": "clean", "badge": "로켓배송", "image": _img("c05")},
        {"id": "c06", "name": "섬유유연제 2.6L", "price": 11900, "categorySlug": "clean", "badge": "로켓배송", "image": _img("c06")},
        {"id": "c07", "name": "주방세제 1.2L", "price": 4900, "categorySlug": "clean", "badge": "로켓배송", "image": _img("c07")},
        {"id": "c08", "name": "다목적 세정제 스프레이", "price": 6900, "categorySlug": "clean", "badge": "무료배송", "image": _img("c08")},
        {"id": "c09", "name": "고무장갑 중형 5켤레", "price": 5900, "categorySlug": "clean", "badge": "로켓배송", "image": _img("c09")},
        {"id": "c10", "name": "쓰레기봉투 50L 100매", "price": 8900, "categorySlug": "clean", "badge": "로켓배송", "image": _img("c10")},
        {"id": "c11", "name": "샴푸 680ml", "price": 12900, "categorySlug": "body", "badge": "로켓배송", "image": _img("c11")},
        {"id": "c12", "name": "바디워시 1L", "price": 9900, "categorySlug": "body", "badge": "로켓배송", "image": _img("c12")},
        {"id": "c13", "name": "치약 160g 3개", "price": 8900, "categorySlug": "body", "badge": "로켓배송", "image": _img("c13")},
        {"id": "c14", "name": "칫솔 4개입", "price": 6900, "categorySlug": "body", "badge": "무료배송", "image": _img("c14")},
        {"id": "c15", "name": "핸드워시 500ml", "price": 5900, "categorySlug": "body", "badge": "로켓배송", "image": _img("c15")},
        {"id": "c16", "name": "생수 2L 12병", "price": 7900, "categorySlug": "kitchen", "badge": "로켓배송", "image": _img("c16")},
        {"id": "c17", "name": "즉석밥 210g 12개", "price": 14900, "categorySlug": "kitchen", "badge": "로켓배송", "image": _img("c17")},
        {"id": "c18", "name": "라면 5봉 묶음", "price": 4500, "categorySlug": "kitchen", "badge": "로켓배송", "image": _img("c18")},
        {"id": "c19", "name": "종이컵 1000개", "price": 9900, "categorySlug": "kitchen", "badge": "무료배송", "image": _img("c19")},
        {"id": "c20", "name": "랩·호일 세트", "price": 8900, "categorySlug": "kitchen", "badge": "로켓배송", "image": _img("c20")},
    ],
    "note": "실습용 예시 상품·가격입니다. 실제 쿠팡 판매 상품과 다를 수 있습니다.",
}


def get_catalog():
    return PRODUCTS
