"""Kiosk routes — McDonald's / Mega Coffee (번갈아 출현)."""

import random

from flask import Blueprint, jsonify, render_template, session

from kiosk import mega_menu
from kiosk.menu import get_menu as get_mcd_menu

kiosk_bp = Blueprint(
    "kiosk",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/kiosk",
)


@kiosk_bp.route("/practice/kiosk")
def practice_kiosk():
    """맥도날드 ↔ 메가커피 번갈아 또는 첫 방문 시 랜덤."""
    last = session.get("kiosk_brand")
    if last == "mcdonalds":
        brand = "mega"
    elif last == "mega":
        brand = "mcdonalds"
    else:
        brand = random.choice(["mcdonalds", "mega"])
    session["kiosk_brand"] = brand

    if brand == "mega":
        return render_template("mega.html", brand=brand)
    return render_template("kiosk.html", brand=brand)


@kiosk_bp.route("/api/kiosk/menu")
def api_kiosk_menu():
    """맥도날드 메뉴."""
    try:
        return jsonify(get_mcd_menu())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@kiosk_bp.route("/api/kiosk/menu/mega")
def api_kiosk_menu_mega():
    """메가MGC커피 공식 사이트 메뉴."""
    try:
        return jsonify(mega_menu.get_menu())
    except Exception as e:
        return jsonify({"error": str(e)}), 502
