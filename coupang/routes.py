"""쿠팡 구매 실습 라우트."""

from flask import Blueprint, jsonify, render_template

from coupang.products import get_catalog

coupang_bp = Blueprint(
    "coupang",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/coupang",
)


@coupang_bp.route("/practice/coupang")
def practice_coupang():
    return render_template("coupang.html")


@coupang_bp.route("/api/coupang/products")
def api_coupang_products():
    return jsonify(get_catalog())
