"""Tầng LLM (Qwen MaaS, OpenAI-compatible) — luồng 2 lượt.

Lượt 1: intent router  → JSON {intent, params}  → code dispatch.
Lượt 2: diễn giải số đã tính → câu trả lời.

Thiếu key MaaS → fallback rule-based (router từ khóa + render template) để
chạy/test local không cần MaaS.

Trục thời gian: 'month' (mặc định — dự phóng cuối tháng vs tháng trước) | 'week' (WoW).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

VALID_INTENTS = {
    "overview", "decline", "growth", "uptrend", "voucher",
    "churn", "at_risk", "decompose", "forecast", "payment", "merchant",
    "month", "freeform", "unknown",
}

_client = None
_MODEL = os.getenv("LLM_MODEL", "")
# Model NHANH cho freeform (không "thinking"): Qwen3 trên MaaS không tắt được reasoning
# (~20s/câu), nên freeform dùng Gemma 4 (~2-5s, không sinh reasoning token).
_FREEFORM_MODEL = (os.getenv("FREEFORM_MODEL") or "google/gemma-4-31b-it")

# Qwen3 "thinking" -> tắt để content không rỗng.
_THINK_OFF = {"chat_template_kwargs": {"enable_thinking": False}}


def _get_client():
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
{"intent": "...", "params": {"category": null, "top_n": 10, "merchant_name": null, "period": "month"}}

intent ∈ [overview, decline, growth, uptrend, voucher, churn, at_risk, decompose, forecast, freeform, unknown]
- overview: tổng quan TOÀN DANH MỤC / "tình hình thế nào" (KHÔNG dùng khi hỏi về 1 merchant cụ thể)
- decline: merchant nào giảm
- growth: top tăng trưởng / xếp hạng tăng
- uptrend: merchant tăng ĐỀU/liên tục nhiều tuần
- voucher: nên chạy voucher / khuyến mãi cho ai
- churn: ai sắp rời bỏ / cảnh báo churn
- at_risk: merchant quan trọng đang lung lay / đáng cứu
- decompose: vì sao [merchant] tăng/giảm
- forecast: dự phóng/ước lượng cuối tháng, "cao hơn tháng trước không", so với tháng trước
- freeform: câu so sánh/tổng hợp/lọc nhiều chiều/không khớp rõ; HOẶC hỏi về MỘT merchant cụ thể (vd "Tiệm Bánh Mì 36 doanh số thế nào", "tình hình của X") khi KHÔNG hỏi "vì sao" → trả lời dựa trên TOÀN BỘ số liệu đã tính (set merchant_name)
- unknown: hoàn toàn ngoài chủ đề dữ liệu merchant
params.category: ngành (Sub-cate) nếu nêu (vd "Fashion", "Electronics", "Coffee & Tea"), không thì null.
params.merchant_name: tên merchant nếu hỏi 1 merchant cụ thể.
params.top_n: số nếu nêu (vd "top 5" -> 5), mặc định 10.
params.period: "week" nếu câu hỏi nói về TUẦN/WoW; còn lại để "month" (mặc định, theo tháng & dự phóng).

QUY TẮC QUAN TRỌNG: 8 nhóm cấu trúc (overview, decline, growth, uptrend, voucher, churn, at_risk, decompose) và forecast CHỈ chọn khi câu hỏi RÕ RÀNG thuộc đúng nhóm đó. MỌI câu hỏi khác — câu mở, câu suy luận, so sánh, lọc, hỏi về 1 merchant/ngành cụ thể, hay câu chưa từng thấy — PHẢI chọn "freeform" để agent TỰ SUY NGHĨ trên dữ liệu đã tính. Hạn chế tối đa "unknown": chỉ khi câu hoàn toàn KHÔNG liên quan dữ liệu merchant (vd hỏi thời tiết). Khi phân vân giữa một nhóm cấu trúc và freeform → CHỌN freeform."""

_ROUTER_FEWSHOT = [
    ("Tổng quan tháng này thế nào?", {"intent": "overview", "params": {"category": None, "top_n": 10, "merchant_name": None, "period": "month"}}),
    ("Merchant nào giảm mạnh nhất tuần này?", {"intent": "decline", "params": {"category": None, "top_n": 10, "merchant_name": None, "period": "week"}}),
    ("Top 5 tăng trưởng", {"intent": "growth", "params": {"category": None, "top_n": 5, "merchant_name": None, "period": "month"}}),
    ("Dự phóng cuối tháng có cao hơn tháng trước không?", {"intent": "forecast", "params": {"category": None, "top_n": 10, "merchant_name": None, "period": "month"}}),
    ("Vì sao Cafe Workspace giảm?", {"intent": "decompose", "params": {"category": None, "top_n": 10, "merchant_name": "Cafe Workspace", "period": "month"}}),
    ("Ai quan trọng đang lung lay?", {"intent": "at_risk", "params": {"category": None, "top_n": 10, "merchant_name": None, "period": "month"}}),
    ("Tiệm Bánh Mì 36 doanh số thế nào?", {"intent": "freeform", "params": {"category": None, "top_n": 10, "merchant_name": "Tiệm Bánh Mì 36", "period": "month"}}),
]


def route_intent(question: str) -> dict[str, Any]:
    client = _get_client()
    if client:
        try:
            msgs = [{"role": "system", "content": _ROUTER_SYSTEM}]
            for q, a in _ROUTER_FEWSHOT:
                msgs.append({"role": "user", "content": q})
                msgs.append({"role": "assistant", "content": json.dumps(a, ensure_ascii=False)})
            msgs.append({"role": "user", "content": question})
            resp = client.chat.completions.create(
                model=_MODEL, messages=msgs, temperature=0, max_tokens=300,
                extra_body=_THINK_OFF,
            )
            parsed = _extract_json(resp.choices[0].message.content)
            if parsed and parsed.get("intent") in VALID_INTENTS:
                parsed.setdefault("params", {})
                parsed["params"].setdefault("period", _detect_period(question))
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
    ("payment", ["cơ cấu thanh toán", "cơ cấu kênh", "kênh thanh toán",
                 "phương thức thanh toán", "theo từng kênh", "tỷ trọng kênh",
                 "cơ cấu sof", "thanh toán theo loại"]),
    ("overview", ["tổng quan", "tình hình", "bức tranh", "danh mục thế nào"]),
    ("forecast", ["dự phóng", "dự báo", "ước lượng", "cuối tháng", "cao hơn tháng trước",
                  "so với tháng trước", "hết tháng", "est", "forecast"]),
    ("at_risk", ["lung lay", "đáng cứu", "quan trọng", "ưu tiên cứu", "đáng tiền"]),
    ("decompose", ["vì sao", "tại sao", "lý do", "bóc tách", "nguyên nhân"]),
    ("voucher", ["voucher", "khuyến mãi", "giảm giá", "ưu đãi", "chạy chương trình"]),
    ("churn", ["churn", "rời bỏ", "sắp rời", "bỏ đi", "rủi ro", "chăm sóc gấp", "sắp mất"]),
    ("uptrend", ["tăng đều", "tăng liên tục", "tăng mỗi tuần", "liên tục tăng",
                 "tuần nào cũng tăng", "đều đặn", "ổn định tăng", "xu hướng tăng", "tăng bền"]),
    ("growth", ["tăng trưởng", "tăng", "phát triển", "xếp hạng"]),
    ("decline", ["giảm", "sụt", "tụt", "đi xuống"]),
]

_CATS = ["Bakery & Dessert", "Coffee & Tea", "Restaurant", "Fashion", "Electronics",
         "Grocery", "Books & Stationery", "Beauty & Cosmetics", "Others"]


def _detect_period(q: str) -> str:
    low = q.lower()
    if any(k in low for k in ["tuần", "wow", "theo tuần", "tuần này", "tuần trước"]):
        return "week"
    return "month"


def _keyword_route(q: str) -> dict[str, Any]:
    low = q.lower()
    intent = "freeform"
    for name, kws in _KW:
        if any(k in low for k in kws):
            intent = name
            break
    category = next((c for c in _CATS if c.lower() in low), None)
    mtop = re.search(r"top\s*(\d+)", low)
    top_n = int(mtop.group(1)) if mtop else 10
    return {"intent": intent,
            "params": {"category": category, "top_n": top_n,
                       "merchant_name": None, "period": _detect_period(q)}}


# Định tuyến tức thì bằng từ khóa (không gọi LLM) — dùng cho nhóm preset.
def keyword_route(question: str) -> dict[str, Any]:
    return _keyword_route(question)


# ============================ LƯỢT 2: DIỄN GIẢI ============================

_INTERP_SYSTEM = """Bạn là chuyên gia tư vấn tăng trưởng merchant, nói tiếng Việt,
súc tích, giọng cố vấn. Bạn nhận KẾT QUẢ SỐ ĐÃ ĐƯỢC TÍNH SẴN (JSON) và viết lại
thành câu trả lời. TUYỆT ĐỐI không bịa hay đổi số — chỉ dùng đúng số trong JSON.
Bối cảnh: dữ liệu theo ngày, tháng hiện tại CHƯA HẾT nên số tháng này là DỰ PHÓNG cuối
tháng (run-rate) so với tháng trước (đủ); "period":"week" nghĩa là so theo tuần (WoW).
Cấu trúc 4 phần:
1. **Kết luận ngắn** (1 câu, số liệu in đậm).
2. **Số liệu chi tiết** — dùng bảng markdown nếu là danh sách/xếp hạng.
3. **Nguyên nhân** — gạch đầu dòng định lượng.
4. **Đề xuất hành động** — cụ thể, làm được ngay.
Mức churn: Cao 🔴, Trung bình 🟡, Thấp 🟢.
QUAN TRỌNG: mọi số THAY ĐỔI tăng/giảm phải ghi rõ dấu +/− ngay trước số (tăng → "+1.8%",
giảm → "−45%") để hệ thống tô màu xanh/đỏ. Số tuyệt đối (doanh số) để nguyên."""

_FREEFORM_SYSTEM = """Bạn là chuyên gia phân tích merchant, nói tiếng Việt, súc tích, giọng cố vấn.
Bạn nhận BẢNG SỐ LIỆU đã được hệ thống tính sẵn cho từng merchant (JSON). Trả lời câu hỏi
CHỈ dựa trên bảng này. TUYỆT ĐỐI không bịa/đổi số; được phép lọc, so sánh, xếp hạng, cộng/đếm.
Giải thích cột: revenue_prev_month=doanh số tháng trước (đủ); revenue_mtd=doanh số tháng này
ĐÃ ĐẠT (đến hiện tại); revenue_proj_month_end=DỰ PHÓNG cuối tháng (run-rate);
monthly_revenue={"YYYY-MM": doanh số TPV} cho MỌI tháng có trong dữ liệu (vd "2026-02") — DÙNG cái này khi hỏi về 1 tháng cụ thể (tháng gần nhất có thể là số chưa đủ tháng);
mom_pct=%dự phóng tháng này vs tháng trước; wow_pct=%thay đổi tuần gần nhất;
txn_now_week=số giao dịch tuần gần nhất; aov_now=giá trị đơn TB;
churn_risk=Cao/Trung bình/Thấp; weeks_declining_streak/weeks_increasing_streak=số tuần
giảm/tăng liên tiếp; payment_mix_pct=tỷ trọng doanh số theo kênh (Payment Gateway/VietQR/Wallet);
wallet_paylater_pct=tỷ trọng Paylater trong Wallet;
tpv_by_type=doanh số TUYỆT ĐỐI theo từng kênh (toàn kỳ); tpv_by_sof=doanh số TUYỆT ĐỐI theo từng SOF (Paylater/Others, toàn kỳ).
QUAN TRỌNG khi tính TỔNG theo kênh/SOF cho nhiều merchant: phải CỘNG các giá trị tuyệt đối tpv_by_type/tpv_by_sof rồi mới chia ra %; TUYỆT ĐỐI không cộng hay bình quân các con số % per-merchant.
Trình bày: kết luận ngắn (số in đậm) → bảng/gạch đầu dòng → đề xuất.
QUAN TRỌNG: mọi số THAY ĐỔI tăng/giảm ghi rõ dấu +/− (tăng → "+1.8%", giảm → "−45%") để tô màu.
Số tuyệt đối để nguyên. Nếu bảng KHÔNG có trường/dữ liệu cần thiết, nói thẳng "dữ liệu không có trong bảng" — TUYỆT ĐỐI KHÔNG bịa số, không tự nghĩ ra con số không có trong bảng.
TRẢ LỜI CỰC NGẮN (tối đa ~70 từ, 2–4 câu): 1 câu kết luận + số liệu chính + 1 đề xuất; KHÔNG lan man, KHÔNG lặp lại đề bài, KHÔNG kẻ bảng dài."""


def interpret_freeform(question: str, digest: list[dict], meta: dict[str, Any]) -> str | None:
    client = _get_client()
    if not client:
        return None
    payload = json.dumps({"meta": meta, "merchants": digest}, ensure_ascii=False)
    msgs = [
        {"role": "system", "content": _FREEFORM_SYSTEM},
        {"role": "user", "content":
            f"Câu hỏi: {question}\n\nBảng số liệu đã tính (JSON — số CHÍNH XÁC):\n{payload}\n\n"
            "Trả lời câu hỏi chỉ dựa trên bảng trên, bằng tiếng Việt."},
    ]
    # Gemma (nhanh, không thinking) trước; lỗi -> fallback Qwen (chậm nhưng chắc).
    candidates = [m for m in (_FREEFORM_MODEL, _MODEL) if m]
    for i, model in enumerate(dict.fromkeys(candidates)):
        try:
            kwargs = dict(model=model, messages=msgs, temperature=0.2, max_tokens=320)
            if model == _MODEL:
                kwargs["extra_body"] = _THINK_OFF
            resp = client.chat.completions.create(**kwargs)
            txt = (resp.choices[0].message.content or "").strip()
            if txt:
                return txt
        except Exception as e:  # log để chẩn đoán (hiện trong runtime logs)
            print(f"[freeform] model={model} lỗi: {e!r}", flush=True)
    return None


def interpret(question: str, result: dict[str, Any], meta: dict[str, Any]) -> str:
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
                temperature=0.3, max_tokens=900, extra_body=_THINK_OFF,
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
    return ("Mình chưa rõ câu hỏi. Thử: **Tổng quan tháng này**, "
            "**Merchant nào giảm?**, **Top 10 tăng trưởng**, **Ai sắp churn?**, "
            "**Ai quan trọng đang lung lay?**, **Nên chạy voucher cho ai?**, "
            "**Dự phóng cuối tháng có cao hơn tháng trước?**")


def _scope_txt(r):
    c = r.get("scope", {}).get("category")
    return f" ({c})" if c else ""


def _per(r):
    """nhãn 'tháng' / 'tuần' theo period."""
    return "tuần" if r.get("period") == "week" else "tháng"


def _vs(r):
    return "vs tuần trước" if r.get("period") == "week" else "vs tháng trước (dự phóng)"


def _r_overview(r, meta):
    p = _per(r)
    head = "tuần gần nhất" if p == "tuần" else f"tháng {meta.get('current_month','')} (dự phóng cuối tháng)"
    sign = "tăng" if r["change_pct"] >= 0 else "giảm"
    lines = [
        f"**{head.capitalize()}**{_scope_txt(r)}: tổng doanh số **{_v(r['total_now'])}** "
        f"({sign} **{r['change_pct']:+}%** {_vs(r)}).",
    ]
    if p == "tháng":
        lines.append(f"- Đã đạt đến nay: **{_v(r['total_mtd'])}** "
                     f"({meta.get('days_elapsed','?')}/{meta.get('days_in_month','?')} ngày).")
    lines += [
        f"- 🟢 Tăng: **{r['n_up']}** merchant — 🔴 Giảm: **{r['n_down']}** — "
        f"⚠️ Churn Cao: **{r['n_churn_high']}**",
        "", "**Tăng mạnh nhất:**",
    ]
    lines += [f"- {m['name']} ({m['change_pct']:+}%, {m['revenue_fmt']})" for m in r["top_up"]]
    lines.append("**Giảm mạnh nhất:**")
    lines += [f"- {m['name']} ({m['change_pct']:+}%, {m['revenue_fmt']})" for m in r["top_down"]]
    lines.append("\n**Đề xuất:** ưu tiên nhóm churn Cao và merchant giảm mạnh trước.")
    return "\n".join(lines)


def _r_decline(r, meta):
    if not r["items"]:
        return f"Không có merchant nào giảm doanh số ({_per(r)}){_scope_txt(r)}. 🎉"
    head = f"**{r['count']}** merchant giảm doanh số ({_per(r)}){_scope_txt(r)}. Sắp theo mức giảm:"
    tbl = ["", "| Merchant | Ngành | Thay đổi | Giao dịch | Giá trị đơn | Churn |",
           "|---|---|---|---|---|---|"]
    for m in r["items"]:
        tbl.append(f"| {m['name']} | {m['category']} | **{m['change_pct']:+}%** | "
                   f"{m['txn_chg']:+}% | {m['aov_chg']:+}% | {_badge(m['churn'])} |")
    tip = ("\n**Đề xuất:** giảm do ít giao dịch → kéo traffic; do giá trị đơn giảm → upsell/combo.")
    return head + "\n" + "\n".join(tbl) + tip


def _r_growth(r, meta):
    if not r["items"]:
        return f"Chưa có merchant tăng trưởng dương ({_per(r)}){_scope_txt(r)}."
    head = f"**Top {len(r['items'])} tăng trưởng** ({_per(r)}){_scope_txt(r)}:"
    tbl = ["", "| # | Merchant | Ngành | Doanh số | % tăng |", "|---|---|---|---|---|"]
    for i, m in enumerate(r["items"], 1):
        tbl.append(f"| {i} | {m['name']} | {m['category']} | {m['revenue_fmt']} | "
                   f"**{m['change_pct']:+}%** |")
    return head + "\n" + "\n".join(tbl)


def _r_uptrend(r, meta):
    if not r["items"]:
        return "Không có merchant nào tăng đều qua các tuần."
    head = f"**{r['count']}** merchant tăng đều (xếp theo số tuần tăng liên tiếp & mức tăng cả kỳ):"
    tbl = ["", "| # | Merchant | Ngành | Tăng liên tiếp | Tăng cả kỳ | Doanh số tuần |",
           "|---|---|---|---|---|---|"]
    for i, m in enumerate(r["items"], 1):
        mono = " 🟢" if m["monotonic"] else ""
        tbl.append(f"| {i} | {m['name']} | {m['category']} | {m['streak']}/{m['total_steps']} tuần{mono} | "
                   f"**+{m['growth_total_pct']}%** | {m['revenue_first_fmt']} → {m['revenue_fmt']} |")
    tip = "\n🟢 = tăng liên tục mọi tuần. **Đề xuất:** nhân rộng chiến lược; tăng hạn mức/ưu đãi giữ đà."
    return head + "\n" + "\n".join(tbl) + tip


def _r_voucher(r, meta):
    if not r["items"]:
        return "Hiện chưa có merchant nào khớp tiêu chí voucher (doanh số đang giảm)."
    head = f"**{len(r['items'])}** merchant nên chạy chương trình giữ chân (ưu tiên theo doanh số):"
    out = [head, ""]
    for m in r["items"]:
        out.append(f"- **{m['name']}** ({m['category']}, doanh số {m['revenue_fmt']}) — "
                   f"thay đổi {m['change_pct']:+}%, churn {_badge(m['churn'])}\n  → {m['recommendation']}")
    return "\n".join(out)


def _r_churn(r, meta):
    if not r["items"]:
        return "Không có merchant churn risk Cao. 🎉"
    head = (f"Cảnh báo churn: **{r['n_high']}** Cao 🔴, **{r['n_medium']}** Trung bình 🟡. "
            "Danh sách ưu tiên:")
    out = [head, ""]
    for m in r["items"]:
        out.append(f"- {_badge(m['churn'])} **{m['name']}** ({m['category']}) — "
                   f"WoW {m['wow_pct']:+}%; {m['reason']}.")
    out.append("\n**Đề xuất:** liên hệ nhóm Cao trong 48h; gói giữ chân theo nguyên nhân.")
    return "\n".join(out)


def _r_at_risk(r, meta):
    if not r["items"]:
        return "Không có merchant giá trị cao đang ở mức rủi ro."
    head = ("**Merchant quan trọng đang lung lay** — ưu tiên cứu theo *giá trị có nguy cơ mất* "
            "(doanh số dự phóng tháng × trọng số rủi ro):")
    tbl = ["", "| # | Merchant | Doanh số dự phóng | Churn | Giá trị nguy cơ | Lý do |",
           "|---|---|---|---|---|---|"]
    for i, m in enumerate(r["items"], 1):
        tbl.append(f"| {i} | {m['name']} | {m['revenue_proj_fmt']} | "
                   f"{_badge(m['churn'])} | **{m['value_at_risk_fmt']}** | {m['reason']} |")
    tip = "\n**Đề xuất:** dồn nguồn lực cho top đầu — doanh số lớn + rủi ro cao = mất nhiều nhất."
    return head + "\n" + "\n".join(tbl) + tip


def _r_decompose(r, meta):
    if not r.get("found"):
        return "Không tìm thấy merchant phù hợp để bóc tách. Nêu rõ tên merchant giúp mình nhé."
    sign = "tăng" if r["change_pct"] >= 0 else "giảm"
    head = f"**{r['name']}** {sign} **{r['change_pct']:+}%** doanh số ({_per(r)}). Bóc tách động lực:"
    out = [head, "",
           f"- **Số lượng giao dịch:** {r['txn_chg']:+}% → đóng góp ~{r['qty_effect_pct']:+}% doanh số",
           f"- **Giá trị đơn (AOV):** {r['aov_chg']:+}% → đóng góp ~{r['aov_effect_pct']:+}%",
           f"- *Phần dư (cơ cấu/nhiễu):* ~{r['residual_pct']:+}%",
           "", "**Đề xuất hành động:**"]
    out += [f"- {a}" for a in r["actions"]]
    return "\n".join(out)


def _r_forecast(r, meta):
    verdict = "CAO HƠN ✅" if r["is_higher"] else "THẤP HƠN ⚠️"
    head = (f"Dự phóng cuối tháng {meta.get('current_month','')}{_scope_txt(r)}: tổng doanh số "
            f"**{_v(r['total_proj_month_end'])}** — **{verdict}** tháng trước "
            f"(**{_v(r['total_prev_month'])}**), thay đổi **{r['change_pct']:+}%**.")
    body = [head, "",
            f"- Đã đạt {r['days_elapsed']}/{r['days_in_month']} ngày: **{_v(r['total_mtd'])}**.",
            f"- 🟢 **{r['n_higher']}** merchant dự phóng cao hơn — 🔴 **{r['n_lower']}** thấp hơn.",
            "", "**Dự phóng tăng mạnh nhất:**"]
    body += [f"- {m['name']} ({m['change_pct']:+}%, {m['revenue_proj_fmt']})" for m in r["top_higher"][:5]]
    if r["top_lower"]:
        body.append("**Dự phóng giảm nhiều nhất:**")
        body += [f"- {m['name']} ({m['change_pct']:+}%, {m['revenue_proj_fmt']})" for m in r["top_lower"][:5]]
    body.append("\n**Đề xuất:** đẩy nhóm đang giảm nửa cuối tháng để cứu chỉ tiêu tháng.")
    return "\n".join(body)


def _r_payment(r, meta):
    head = (f"**Cơ cấu thanh toán**{_scope_txt(r)} — tổng TPV **{_v(r['total_tpv'])}** "
            "(toàn kỳ dữ liệu):")
    tbl = ["", "| Kênh | TPV | Giao dịch | % tổng |", "|---|---|---|---|"]
    for t in r["types"]:
        txn = f"{t['txn']:,}".replace(",", ".")
        tbl.append(f"| {t['name']} | {t['tpv_fmt']} | {txn} | **{t['pct']}%** |")
    out = [head] + tbl
    if r["sof"]:
        out += ["", f"**SOF trong Wallet** (tổng Wallet {_v(r['wallet_tpv'])}):",
                "", "| SOF | TPV | Giao dịch | % Wallet | % tổng |", "|---|---|---|---|---|"]
        for s in r["sof"]:
            txn = f"{s['txn']:,}".replace(",", ".")
            out.append(f"| {s['name']} | {s['tpv_fmt']} | {txn} | {s['pct_wallet']}% | {s['pct_total']}% |")
    return "\n".join(out)


def _r_merchant(r, meta):
    if not r.get("found"):
        return "Không tìm thấy merchant đó. Nêu đúng tên giúp mình nhé."
    mix = " · ".join(f"{k} {v}%" for k, v in r["payment_mix"].items())
    return "\n".join([
        f"**{r['name']}** ({r['category']}) — tình hình:",
        "",
        f"- 💰 Dự phóng cuối tháng: **{r['revenue_proj_fmt']}** ({r['mom_pct']:+}% vs tháng trước)",
        f"- Đã đạt tháng này: {r['revenue_mtd_fmt']} · tháng trước: {r['revenue_prev_fmt']}",
        f"- 📅 Tuần gần nhất: WoW **{r['wow_pct']:+}%** · {r['txn_week']} giao dịch/tuần · AOV {r['aov_fmt']}",
        f"- ⚠️ Churn: {_badge(r['churn'])} (giảm liên tiếp {r['consec']} tuần / tăng {r['up_streak']} tuần)",
        f"- 💳 Kênh thanh toán: {mix} — Paylater {r['wallet_paylater_pct']}% của Wallet",
        "- 📆 Doanh số theo tháng: " + " · ".join(f"{k}: {v}" for k, v in r.get("monthly", {}).items()),
    ])


def _r_month(r, meta):
    if not r.get("found"):
        return (f"Không có dữ liệu cho tháng **{r['month']}**. "
                f"Các tháng có sẵn: {', '.join(r['available_months'])}.")
    head = f"**Top {len(r['items'])} merchant theo TPV — tháng {r['month']}** (tổng {_v(r['total_tpv'])}, {r['n']} merchant):"
    tbl = ["", "| # | Merchant | Ngành | TPV |", "|---|---|---|---|"]
    for i, m in enumerate(r["items"], 1):
        tbl.append(f"| {i} | {m['name']} | {m['category']} | {m['tpv_fmt']} |")
    return head + "\n" + "\n".join(tbl)


_RENDERERS = {
    "overview": _r_overview, "decline": _r_decline, "growth": _r_growth,
    "uptrend": _r_uptrend, "voucher": _r_voucher, "churn": _r_churn,
    "at_risk": _r_at_risk, "decompose": _r_decompose, "forecast": _r_forecast,
    "payment": _r_payment, "merchant": _r_merchant, "month": _r_month,
}


def _badge(level: str) -> str:
    return {"Cao": "🔴 Cao", "Trung bình": "🟡 Trung bình", "Thấp": "🟢 Thấp"}.get(level, level)


def _v(x) -> str:
    return f"{round(x):,} đ".replace(",", ".")
