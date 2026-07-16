"""Main site routes — 홈 · 실습 허브 · QR 결제 세션."""

import secrets
import socket
import time
from threading import Lock

from flask import Blueprint, jsonify, render_template, request

main_bp = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/main",
)

# QR 결제 세션 (실습용 · 메모리)
_pay_sessions: dict[str, dict] = {}
_pay_lock = Lock()
_PAY_TTL_SEC = 60 * 30  # 30분


def _purge_old_sessions() -> None:
    now = time.time()
    dead = [k for k, v in _pay_sessions.items() if now - v.get("ts", 0) > _PAY_TTL_SEC]
    for k in dead:
        _pay_sessions.pop(k, None)


def _lan_ip() -> str:
    """폰 스캔용: 이 PC의 LAN IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.3)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/practice")
def practice():
    return render_template("practice.html")


@main_bp.route("/words")
def words():
    """실습 전 모를 만한 단어 학습."""
    return render_template("words.html")


@main_bp.route("/api/pay/base")
def pay_base():
    """QR에 넣을 베이스 URL (localhost면 LAN IP)."""
    host = (request.host or "").split(":")[0]
    port = request.environ.get("SERVER_PORT") or "5000"
    # Host 헤더에 포트 포함될 수 있음
    if ":" in (request.host or ""):
        port = (request.host or "").split(":")[-1]
    if host in ("127.0.0.1", "localhost", "::1", "[::1]", ""):
        base = f"http://{_lan_ip()}:{port}"
    else:
        scheme = request.headers.get("X-Forwarded-Proto") or request.scheme or "http"
        base = f"{scheme}://{request.host}"
    return jsonify({"ok": True, "base": base, "lan": _lan_ip()})


@main_bp.route("/api/pay/session", methods=["POST"])
def pay_create_session():
    """키오스크가 QR 결제 세션을 만들 때."""
    with _pay_lock:
        _purge_old_sessions()
        # URL에 안전한 짧은 hex id
        sid = secrets.token_hex(8)
        _pay_sessions[sid] = {"paid": False, "ts": time.time()}
    return jsonify({"id": sid, "ok": True})


@main_bp.route("/api/pay/status/<sid>")
def pay_status(sid: str):
    """키오스크가 스캔 완료 여부를 폴링."""
    with _pay_lock:
        s = _pay_sessions.get(sid)
        if not s:
            return jsonify({"ok": False, "paid": False})
        return jsonify({"ok": True, "paid": bool(s.get("paid"))})


@main_bp.route("/api/pay/confirm/<sid>", methods=["POST", "GET"])
def pay_confirm(sid: str):
    """연습 버튼 또는 스캔 페이지에서 결제 확정."""
    with _pay_lock:
        s = _pay_sessions.get(sid)
        if s is None:
            return jsonify({"ok": False, "paid": False}), 404
        s["paid"] = True
        s["ts"] = time.time()
    return jsonify({"ok": True, "paid": True})


@main_bp.route("/pay/scan/<sid>")
def pay_scan(sid: str):
    """폰에서 QR 스캔 시 — 결제 완료 표시 + 세션 paid."""
    found = False
    with _pay_lock:
        s = _pay_sessions.get(sid)
        if s is not None:
            s["paid"] = True
            s["ts"] = time.time()
            found = True

    title = "결제 완료" if found else "만료된 QR"
    msg = (
        "키오스크 화면이 곧 주문 완료로 바뀝니다.<br/>이 창을 닫아도 됩니다."
        if found
        else "QR이 만료되었거나 잘못된 주소입니다.<br/>키오스크에서 다시 시도해 주세요."
    )
    color = "#059669" if found else "#b91c1c"
    # localStorage로 같은 PC 다른 탭 폴링도 지원
    ls_js = (
        f"try{{localStorage.setItem('ieum_pay_done_{sid}','1');}}catch(e){{}}"
        if found
        else ""
    )
    return (
        f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} — 이음</title>
<style>
body{{font-family:system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;
background:#f4f7fc;color:#0f172a;text-align:center;padding:28px}}
.box{{background:#fff;border-radius:20px;padding:36px 28px;max-width:380px;box-shadow:0 12px 40px rgba(15,23,42,.12)}}
.icon{{font-size:3rem;margin-bottom:12px}}
h1{{font-size:1.75rem;margin:0 0 12px;color:{color}}}
p{{font-size:1.15rem;line-height:1.55;color:#475569;margin:0}}
</style>
</head>
<body>
<div class="box">
  <div class="icon">{"✓" if found else "!"}</div>
  <h1>{title}</h1>
  <p>{msg}</p>
</div>
<script>{ls_js}</script>
</body>
</html>""",
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )
