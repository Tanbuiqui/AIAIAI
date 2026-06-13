"""Tầng LLM (Qwen MaaS, OpenAI-compatible) — luồng 2 lượt.

Lượt 1: intent router  → JSON {intent, params}  → code dispatch (KHÔNG dùng
          native tool-calling; chỉ ép model trả JSON).
Lượt 2: diễn giải số đã tính → câu trả lời 4 phần.

Không cấu hình được LLM (thiếu key) → fallback rule-based: router bằng từ khóa,
diễn giải bằng template. Nhờ vậy chạy/test local không cần MaaS.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

VALID_INTENTS = {
    "overview", "decline", "growth", "uptrend", "voucher",
    "churn", "at_risk", "decompose", "freeform", "unknown",
}

_client = None
_MODEL = os.getenv("LLM_MODEL", "")


def _get_client():
    """Khởi tạo OpenAI-compatible client nếu có cấu hình; lỗi/thiếu -> None."""
    global _client
    if _client is not None:
        return _client
    base = os.getenv("LLM_BASE_URL") or os.getenv("GREENNODE_MAAS_BASE_URL")
    key = os.getenv("LLM_API_KEY") or os.getenv("GREENNODE_MAAS_API_KEY")
    if not (base and key and _MODEL):
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(base_url=base, api_key=key)
        return _client
    except Exception:
        return None


def llm_available() -> bool:
    return _get_client() is not None


# ============================ LƯỢT 1: INTENT ============================

_ROUTER_SYSTEM = """Bạn là bộ định tuyến ý định cho trợ lý phân tích merchant.
Đọc câu hỏi tiếng Việt của Account Manager và trả về DUY NHẤT một JSON hợp lệ,
KHÔNG kèm giải thích, theo schema:
{"intent": "...", "params": {"region": null, "category": null, "top_n": 10, "merchant_name": null}}

intent ∈ [overview, decline, growth, uptrend, voucher, churn, at_risk, decompose, freeform, unknown]
- overview: tổng quan danh mục / "tuần này thế nào"
- decline: merchant nào giảm
- growth: top tăng trưởng / xếp hạng tăng (so tuần này vs tuần trước)
- uptrend: merchant tăng ĐỀU/liên tục nhiều tuần ("tăng đều mỗi tuần", "tăng liên tục", "xu hướng tăng")
- voucher: nên chạy voucher / khuyến mãi cho ai
- churn: ai sắp rời bỏ / cảnh báo churn
- at_risk: merchant quan trọng đang lung lay / đáng cứu
- decompose: vì sao [merchant] tăng/giảm
- freeform: câu so sánh / tổng hợp / lọc nhiều chiều / không khớp rõ 1 nhóm trên → sẽ được trả lời dựa trên TOÀN BỘ số liệu đã tính (ưu tiên dùng cho mọi câu "lạ")
- unknown: hoàn toàn ngoài chủ đề dữ liệu merchant
params.region/category: trích nếu nêu (vd "TP.HCM", "F&B"), không thì null.
params.merchant_name: tên merchant nếu hỏi về 1 merchant cụ thể.
params.top_n: số nếu nêu (vd "top 5" -> 5), mặc định 10."""

_ROUTER_FEWSHOT = [
    ("Tổng quan tuần này thế nào?", {"intent": "overview", "params": {"region": None, "category": None, "top_n": 10, "merchant_name": None}}),
    ("Merchant nào ở TP.HCM giảm mạnh nhất?", {"intent": "decline", "params": {"region": "TP.HCM", "category": None, "top_n": 10, "merchant_name": None}}),
    ("Top 5 tăng trưởng", {"intent": "growth", "params": {"region": None, "category": None, "top_n": 5, "merchant_name": None}}),
    ("Vì sao Cafe Workspace giảm?", {"intent": "decompose", "params": {"region": None, "category": None, "top_n": 10, "merchant_name": "Cafe Workspace"}}),
    ("Ai quan trọng đang lung lay?", {"intent": "at_risk", "params": {"region": None, "category": None, "top_n": 10, "merchant_name": None}}),
]


def route_intent(question: str) -> dict[str, Any]:
    """Trả {intent, params}. Ưu tiên LLM; fallback từ khóa. Luôn an toàn."""
    client = _get_client()
    if client:
        try:
            msgs = [{"role": "system", "content": _ROUTER_SYSTEM}]
            for q, a in _ROUTER_FEWSHOT:
                msgs.append({"role": "user", "content": q})
                msgs.append({"role": "assistant", "content": json.dumps(a, ensure_ascii=False)})
            msgs.append({"role": "user", "content": question})
            resp = client.chat.completions.create(
                model=_MODEL, messages=msgs, temperature=0, max_tokens=200,
            )
            parsed = _extract_json(resp.choices[0].message.content)
            if parsed and parsed.get("intent") in VALID_INTENTS:
                parsed.setdefault("params", {})
                return parsed
        except Exception:
            pass
    return _keyword_route(question)


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


_KW = [
    ("overview", ["tổng quan", "tuần này thế nào", "bức tranh", "danh mục thế nào", "tình hình"]),
    ("at_risk", ["lung lay", "đáng cứu", "quan trọng", "giá trị", "ưu tiên cứu", "đáng tiền"]),
    ("decompose", ["vì sao", "tại sao", "lý do", "bóc tách", "nguyên nhân"]),
    ("voucher", ["voucher", "khuyến mãi", "giảm giá", "ưu đãi", "chạy chương trình"]),
    ("churn", ["churn", "rời bỏ", "sắp rời", "bỏ đi", "rủi ro", "chăm sóc gấp", "sắp mất"]),
    ("uptrend", ["tăng đều", "tăng liên tục", "tăng mỗi tuần", "liên tục tăng",
                 "tuần nào cũng tăng", "đều đặn", "ổn định tăng", "xu hướng tăng", "tăng bền"]),
    ("growth", ["tăng trưởng", "tăng", "phát triển", "xếp hạng"]),
    ("decline", ["giảm", "sụt", "tụt", "đi xuống"]),
]

_REGIONS = ["TP.HCM", "Hà Nội", "Đà Nẵng"]
_CATS = ["F&B", "Thời trang", "Điện tử", "Tạp hóa", "Sách", "Làm đẹp", "Khác"]


def _keyword_route(q: str) -> dict[str, Any]:
    low = q.lower()
    intent = "freeform"
    for name, kws in _KW:
        if any(k in low for k in kws):
            intent = name
            break
    region = next((r for r in _REGIONS if r.lower() in low), None)
    category = next((c for c in _CATS if c.lower() in low), None)
    mtop = re.search(r"top\s*(\d+)", low)
    top_n = int(mtop.group(1)) if mtop else 10
    return {"intent": intent,
            "params": {"region": region, "category": category,
                       "top_n": top_n, "merchant_name": None}}


# ============================ LƯỢT 2: DIỄN GIẢI ============================

_INTERP_SYSTEM = """Bạn là chuyên gia tư vấn tăng trưởng merchant, nói tiếng Việt,
súc tích, giọng cố vấn. Bạn nhận KẾT QUẢ SỐ ĐÃ ĐƯỢC TÍNH SẴN (JSON) và viết lại
thành câu trả lời. TUYỆT ĐỐI không bịa hay đổi số — chỉ dùng đúng số trong JSON.
Cấu trúc 4 phần:
1. **Kết luận ngắn** (1 câu, số liệu in đậm).
2. **Số liệu chi tiết** — dùng bảng markdown nếu là danh sách/xếp hạng.
3. **Nguyên nhân** — gạch đầu dòng định lượng.
4. **Đề xuất hành động** — cụ thể, làm được ngay.
Mức churn: Cao 🔴, Trung bình 🟡, Thấp 🟢."""


_FREEFORM_SYSTEM = """Bạn là chuyên gia phân tích merchant, nói tiếng Việt, súc tích, giọng cố vấn.
Bạn nhận BẢNG SỐ LIỆU đã được hệ thống tính sẵn cho từng merchant (JSON). Hãy trả lời câu hỏi
của Account Manager CHỈ dựa trên bảng này. TUYỆT ĐỐI không bịa hoặc đổi số — chỉ dùng đúng số trong bảng;
được phép lọc, so sánh, xếp hạng, cộng/đếm, tính trung bình từ các số đã cho.
Giải thích cột: revenue_now/revenue_prev=doanh thu tuần này/trước; wow_pct=%thay đổi tuần;
gross_profit_now / gross_profit_last4w=lợi nhuận gộp tuần này / tổng 4 tuần; margin_pct=biên lợi nhuận;
return_rate_pct=tỷ lệ khách quay lại; churn_risk=Cao/Trung bình/Thấp;
weeks_declining_streak=số tuần giảm liên tiếp; weeks_increasing_streak=số tuần tăng liên tiếp.
Trình bày: kết luận ngắn (số in đậm) → bảng/gạch đầu dòng số liệu → đề xuất hành động.
Nếu bảng không đủ dữ kiện để trả lời, nói rõ thay vì suy đoán."""


def interpret_freeform(question: str, digest: list[dict], meta: dict[str, Any]) -> str | None:
    """Trả lời câu hỏi tự do dựa trên bảng số liệu đã tính. None nếu không có LLM."""
    client = _get_client()
    if not client:
        return None
    try:
        payload = json.dumps({"meta": meta, "merchants": digest}, ensure_ascii=False)
        resp = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _FREEFORM_SYSTEM},
                {"role": "user", "content":
                    f"Câu hỏi: {question}\n\nBảng số liệu đã tính (JSON — mọi con số CHÍNH XÁC):\n{payload}\n\n"
                    "Trả lời câu hỏi chỉ dựa trên bảng trên, bằng tiếng Việt."},
            ],
            temperature=0.2, max_tokens=1000,
        )
        txt = (resp.choices[0].message.content or "").strip()
        return txt or None
    except Exception:
        return None


def interpret(question: str, result: dict[str, Any], meta: dict[str, Any]) -> str:
    """Diễn giải kết quả số -> markdown. LLM nếu có, fallback template."""
    client = _get_client()
    if client:
        try:
            payload = json.dumps({"question": question, "meta": meta, "result": result},
                                 ensure_ascii=False)
            resp = client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": _INTERP_SYSTEM},
                    {"role": "user", "content":
                        f"Câu hỏi: {question}\nDữ liệu đã tính (JSON):\n{payload}\n"
                        "Viết câu trả lời 4 phần bằng tiếng Việt."},
                ],
                temperature=0.3, max_tokens=900,
            )
            txt = resp.choices[0].message.content
            if txt and txt.strip():
                return txt.strip()
        except Exception:
            pass
    return render_fallback(result, meta)


# --------- fallback render (markdown thuần, không cần LLM) ---------

def render_fallback(r: dict[str, Any], meta: dict[str, Any]) -> str:
    intent = r.get("intent", "unknown")
    fn = _RENDERERS.get(intent)
    if fn:
        return fn(r, meta)
    return ("Mình chưa rõ câu hỏi. Thử các gợi ý: **Tổng quan tuần này**, "
            "**Merchant nào giảm tuần này?**, **Top 10 tăng trưởng**, "
            "**Ai sắp churn?**, **Ai quan trọng đang lung lay?**, "
            "**Nên chạy voucher cho ai?**")


def _scope_txt(r):
    s = r.get("scope", {})
    bits = [x for x in (s.get("category"), s.get("region")) if x]
    return f" ({' · '.join(bits)})" if bits else ""


def _r_overview(r, meta):
    sign = "tăng" if r["revenue_wow_pct"] >= 0 else "giảm"
    lines = [
        f"**Tuần {meta['current_week']}** — danh mục{_scope_txt(r)}: tổng doanh thu "
        f"**{_v(r['total_revenue'])}** ({sign} **{r['revenue_wow_pct']:+}%** WoW), "
        f"lợi nhuận gộp **{_v(r['total_gross_profit'])}**.",
        "",
        f"- 🟢 Tăng: **{r['n_up']}** merchant — 🔴 Giảm: **{r['n_down']}** — "
        f"⚠️ Churn Cao: **{r['n_churn_high']}**",
        "",
        "**Tăng mạnh nhất:**",
    ]
    lines += [f"- {m['name']} ({m['wow_pct']:+}%, {m['revenue_fmt']})" for m in r["top_up"]]
    lines.append("**Giảm mạnh nhất:**")
    lines += [f"- {m['name']} ({m['wow_pct']:+}%, {m['revenue_fmt']})" for m in r["top_down"]]
    lines.append("\n**Đề xuất:** ưu tiên xem nhóm churn Cao và merchant giảm mạnh trước.")
    return "\n".join(lines)


def _r_decline(r, meta):
    if not r["items"]:
        return f"Không có merchant nào giảm doanh thu tuần này{_scope_txt(r)}. 🎉"
    head = (f"**{r['count']}** merchant giảm doanh thu tuần này{_scope_txt(r)}. "
            "Sắp theo mức giảm:")
    tbl = ["", "| Merchant | Ngành | WoW | Giao dịch | Khách quay lại | Churn |",
           "|---|---|---|---|---|---|"]
    for m in r["items"]:
        tbl.append(f"| {m['name']} | {m['category']} | **{m['wow_pct']}%** | "
                   f"{m['txn_wow']:+}% | {m['rr_wow']:+}% | {_badge(m['churn'])} |")
    tip = ("\n**Đề xuất:** merchant giảm do ít giao dịch → kéo traffic; "
           "do khách quay lại giảm → loyalty/win-back.")
    return head + "\n" + "\n".join(tbl) + tip


def _r_growth(r, meta):
    if not r["items"]:
        return f"Chưa có merchant tăng trưởng dương{_scope_txt(r)}."
    head = f"**Top {len(r['items'])} tăng trưởng** tuần này{_scope_txt(r)}:"
    tbl = ["", "| # | Merchant | Ngành | Doanh thu | % tăng |", "|---|---|---|---|---|"]
    for i, m in enumerate(r["items"], 1):
        tbl.append(f"| {i} | {m['name']} | {m['category']} | {m['revenue_fmt']} | "
                   f"**{m['wow_pct']:+}%** |")
    return head + "\n" + "\n".join(tbl)


def _r_uptrend(r, meta):
    if not r["items"]:
        return "Không có merchant nào tăng đều qua các tuần."
    head = f"**{r['count']}** merchant tăng đều (xếp theo số tuần tăng liên tiếp & mức tăng cả kỳ):"
    tbl = ["", "| # | Merchant | Ngành | Tăng liên tiếp | Tăng cả kỳ | Doanh thu |",
           "|---|---|---|---|---|---|"]
    for i, m in enumerate(r["items"], 1):
        mono = " 🟢" if m["monotonic"] else ""
        tbl.append(f"| {i} | {m['name']} | {m['category']} | {m['streak']}/{m['total_steps']} tuần{mono} | "
                   f"**+{m['growth_total_pct']}%** | {m['revenue_first_fmt']} → {m['revenue_fmt']} |")
    tip = ("\n🟢 = tăng liên tục tất cả các tuần. **Đề xuất:** nhân rộng chiến lược đang chạy; "
           "cân nhắc tăng hạn mức/ưu đãi để giữ đà.")
    return head + "\n" + "\n".join(tbl) + tip


def _r_voucher(r, meta):
    if not r["items"]:
        return "Hiện chưa có merchant nào khớp tiêu chí voucher (giảm + khách quay lại giảm)."
    head = (f"**{len(r['items'])}** merchant nên chạy chương trình giữ chân "
            "(ưu tiên theo lợi nhuận gộp):")
    out = [head, ""]
    for m in r["items"]:
        warn = " ⚠️ biên mỏng" if m["thin_margin"] else ""
        out.append(f"- **{m['name']}** ({m['category']}, lợi nhuận {m['gross_profit_fmt']}, "
                   f"biên {m['margin_pct']}%{warn}) — WoW {m['wow_pct']}%, khách quay lại "
                   f"{m['rr_wow']:+}%\n  → {m['recommendation']}")
    return "\n".join(out)


def _r_churn(r, meta):
    if not r["items"]:
        return "Không có merchant churn risk Cao. 🎉"
    head = (f"Cảnh báo churn: **{r['n_high']}** Cao 🔴, **{r['n_medium']}** Trung bình 🟡. "
            "Danh sách ưu tiên:")
    out = [head, ""]
    for m in r["items"]:
        out.append(f"- {_badge(m['churn'])} **{m['name']}** ({m['category']}) — "
                   f"WoW {m['wow_pct']}%; {m['reason']}.")
    out.append("\n**Đề xuất:** liên hệ nhóm Cao trong 48h; gói giữ chân theo nguyên nhân.")
    return "\n".join(out)


def _r_at_risk(r, meta):
    if not r["items"]:
        return "Không có merchant giá trị cao đang ở mức rủi ro."
    head = ("**Merchant quan trọng đang lung lay** — ưu tiên cứu theo *giá trị có nguy cơ mất* "
            "(lợi nhuận gộp 4 tuần × trọng số rủi ro):")
    tbl = ["", "| # | Merchant | Lợi nhuận 4 tuần | Churn | Giá trị nguy cơ | Lý do |",
           "|---|---|---|---|---|---|"]
    for i, m in enumerate(r["items"], 1):
        tbl.append(f"| {i} | {m['name']} | {m['gross_profit_last4_fmt']} | "
                   f"{_badge(m['churn'])} | **{m['value_at_risk_fmt']}** | {m['reason']} |")
    tip = ("\n**Đề xuất:** dồn nguồn lực cho top đầu — lợi nhuận lớn + rủi ro cao = "
           "mất nhiều nhất nếu rời bỏ.")
    return head + "\n" + "\n".join(tbl) + tip


def _r_decompose(r, meta):
    if not r.get("found"):
        return "Không tìm thấy merchant phù hợp để bóc tách. Nêu rõ tên merchant giúp mình nhé."
    sign = "tăng" if r["wow_pct"] >= 0 else "giảm"
    head = (f"**{r['name']}** {sign} **{r['wow_pct']}%** doanh thu WoW. Bóc tách 3 động lực:")
    out = [head, "",
           f"- **Số lượng giao dịch:** {r['txn_wow']:+}% → đóng góp ~{r['qty_effect_pct']:+}% doanh thu",
           f"- **Giá trị đơn (AOV):** {r['aov_wow']:+}% → đóng góp ~{r['aov_effect_pct']:+}%",
           f"- **Tỷ lệ khách quay lại:** {r['rr_wow']:+}%",
           f"- *Phần dư (khách/nhiễu):* ~{r['residual_pct']:+}%",
           "", "**Đề xuất hành động:**"]
    out += [f"- {a}" for a in r["actions"]]
    return "\n".join(out)


_RENDERERS = {
    "overview": _r_overview, "decline": _r_decline, "growth": _r_growth,
    "uptrend": _r_uptrend, "voucher": _r_voucher, "churn": _r_churn,
    "at_risk": _r_at_risk, "decompose": _r_decompose,
}


def _badge(level: str) -> str:
    return {"Cao": "🔴 Cao", "Trung bình": "🟡 Trung bình", "Thấp": "🟢 Thấp"}.get(level, level)


def _v(x) -> str:
    return f"{round(x):,} đ".replace(",", ".")
