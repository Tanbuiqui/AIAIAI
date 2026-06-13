"""Merchant Growth Agent — lõi phân tích (mọi con số tính BẰNG CODE).

Đọc CSV/Excel giao dịch merchant theo tuần, tính chỉ số phái sinh và 7 nhóm
phân tích ở spec mục 4. LLM chỉ diễn giải kết quả đã tính — không tự tính.

Logic churn/decline/growth tái hiện đúng `verify_sample_data.py`.
"""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

REQUIRED_COLS = [
    "merchant_id", "merchant_name", "category", "region", "week_start",
    "transaction_count", "revenue_vnd", "gross_profit_vnd",
    "unique_customers", "returning_customers", "avg_order_value_vnd",
]

NUMERIC_COLS = [
    "transaction_count", "revenue_vnd", "gross_profit_vnd",
    "unique_customers", "returning_customers", "avg_order_value_vnd",
]

# biên lợi nhuận mỏng -> cảnh báo khi đề xuất giảm giá (spec 4.3)
THIN_MARGIN = 0.25


class SchemaError(ValueError):
    """File thiếu cột bắt buộc."""


def load_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    """Đọc CSV/Excel từ bytes, tự nhận diện schema. Thiếu cột -> báo rõ."""
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(content))
    else:
        # CSV: thử UTF-8 (có BOM) trước, fallback latin-1
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1")

    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise SchemaError(
            "File thiếu cột bắt buộc: " + ", ".join(missing)
            + ". Cần đủ: " + ", ".join(REQUIRED_COLS)
        )

    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["merchant_id", "week_start"] + NUMERIC_COLS)
    df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce")
    df = df.dropna(subset=["week_start"]).sort_values(["merchant_id", "week_start"])
    return df.reset_index(drop=True)


def _fmt_vnd(x: float) -> str:
    return f"{round(x):,} đ".replace(",", ".")


def _ret_rate(returning: float, unique: float) -> float:
    return returning / unique if unique else 0.0


class MerchantAnalyzer:
    """Giữ 1 DataFrame đã nạp và expose 7 nhóm phân tích."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.weeks = sorted(df["week_start"].unique())
        self.current_week = self.weeks[-1]
        self.prev_week = self.weeks[-2] if len(self.weeks) > 1 else None
        # per-merchant: chuỗi tuần đã sort
        self._by_m: dict[str, pd.DataFrame] = {
            mid: g.sort_values("week_start").reset_index(drop=True)
            for mid, g in df.groupby("merchant_id")
        }
        self._metrics = {mid: self._compute_metrics(g) for mid, g in self._by_m.items()}

    # ---------- metrics cho 1 merchant ----------
    def _compute_metrics(self, g: pd.DataFrame) -> dict[str, Any]:
        rev = g["revenue_vnd"].tolist()
        txn = g["transaction_count"].tolist()
        aov = g["avg_order_value_vnd"].tolist()
        gp = g["gross_profit_vnd"].tolist()
        uniq = g["unique_customers"].tolist()
        retn = g["returning_customers"].tolist()
        rr = [_ret_rate(retn[i], uniq[i]) for i in range(len(g))]

        n = len(rev)
        wow = (rev[-1] - rev[-2]) / rev[-2] * 100 if n > 1 and rev[-2] else 0.0

        consec = 0
        for i in range(n - 1, 0, -1):
            if rev[i] < rev[i - 1]:
                consec += 1
            else:
                break

        avg_prev4 = sum(rev[-5:-1]) / len(rev[-5:-1]) if n > 1 else rev[-1]
        crash = rev[-1] < 0.7 * avg_prev4 if avg_prev4 else False
        low_ret = (rr[-1] < 0.25 and n >= 4 and rr[-1] < rr[-4])

        if consec >= 3 or crash or low_ret:
            churn = "Cao"
        elif consec == 2 or (n > 1 and rr[-1] < rr[-2] * 0.9):
            churn = "Trung bình"
        else:
            churn = "Thấp"

        # WoW các động lực
        txn_wow = (txn[-1] - txn[-2]) / txn[-2] * 100 if n > 1 and txn[-2] else 0.0
        aov_wow = (aov[-1] - aov[-2]) / aov[-2] * 100 if n > 1 and aov[-2] else 0.0
        rr_wow = (rr[-1] - rr[-2]) / rr[-2] * 100 if n > 1 and rr[-2] else 0.0

        margin = gp[-1] / rev[-1] if rev[-1] else 0.0
        gp_last4 = sum(gp[-4:])

        return dict(
            merchant_id=g["merchant_id"].iloc[0],
            name=g["merchant_name"].iloc[0],
            category=g["category"].iloc[0],
            region=g["region"].iloc[0],
            rev_now=rev[-1], rev_prev=rev[-2] if n > 1 else rev[-1],
            gp_now=gp[-1], gp_last4=gp_last4,
            wow=wow, consec=consec, crash=crash, low_ret=low_ret,
            churn=churn, margin=margin,
            txn_now=txn[-1], aov_now=aov[-1], rr_now=rr[-1],
            txn_wow=txn_wow, aov_wow=aov_wow, rr_wow=rr_wow,
            txn_prev=txn[-2] if n > 1 else txn[-1],
            aov_prev=aov[-2] if n > 1 else aov[-1],
        )

    def _filter(self, region: str | None, category: str | None) -> list[dict]:
        out = list(self._metrics.values())
        if region:
            out = [m for m in out if str(m["region"]).lower() == region.lower()]
        if category:
            out = [m for m in out if str(m["category"]).lower() == category.lower()]
        return out

    # ---------- chuỗi theo tuần (cho line chart) ----------
    def series_all(self) -> dict[str, Any]:
        weeks = [pd.Timestamp(w).date().isoformat() for w in self.weeks]
        merchants = []
        for mid, g in self._by_m.items():
            merchants.append({
                "id": mid,
                "name": g["merchant_name"].iloc[0],
                "category": g["category"].iloc[0],
                "region": g["region"].iloc[0],
                "revenue": [int(x) for x in g["revenue_vnd"].tolist()],
            })
        return {"weeks": weeks, "merchants": merchants}

    # ---------- digest: toàn bộ chỉ số đã tính (cho freeform Q&A) ----------
    def digest(self) -> list[dict[str, Any]]:
        rows = []
        for m in self._metrics.values():
            rev = self._by_m[m["merchant_id"]]["revenue_vnd"].tolist()
            steps = [rev[i] > rev[i - 1] for i in range(1, len(rev))]
            up_streak = 0
            for u in reversed(steps):
                if u:
                    up_streak += 1
                else:
                    break
            rows.append({
                "name": m["name"], "category": m["category"], "region": m["region"],
                "revenue_now": round(m["rev_now"]), "revenue_prev": round(m["rev_prev"]),
                "wow_pct": round(m["wow"], 1),
                "gross_profit_now": round(m["gp_now"]), "gross_profit_last4w": round(m["gp_last4"]),
                "margin_pct": round(m["margin"] * 100, 1),
                "return_rate_pct": round(m["rr_now"] * 100, 1),
                "churn_risk": m["churn"],
                "weeks_declining_streak": m["consec"], "weeks_increasing_streak": up_streak,
                "txn_now": m["txn_now"], "aov_now": m["aov_now"],
            })
        return rows

    # ---------- meta ----------
    def meta(self) -> dict[str, Any]:
        return {
            "n_merchants": len(self._by_m),
            "n_weeks": len(self.weeks),
            "current_week": pd.Timestamp(self.current_week).date().isoformat(),
            "week_first": pd.Timestamp(self.weeks[0]).date().isoformat(),
            "categories": sorted(self.df["category"].dropna().unique().tolist()),
            "regions": sorted(self.df["region"].dropna().unique().tolist()),
        }

    # ---------- 4.5 Tổng quan ----------
    def overview(self, region=None, category=None, **_) -> dict[str, Any]:
        ms = self._filter(region, category)
        total_rev = sum(m["rev_now"] for m in ms)
        total_rev_prev = sum(m["rev_prev"] for m in ms)
        total_gp = sum(m["gp_now"] for m in ms)
        rev_wow = (total_rev - total_rev_prev) / total_rev_prev * 100 if total_rev_prev else 0.0
        up = [m for m in ms if m["wow"] > 0]
        down = [m for m in ms if m["wow"] < 0]
        high = [m for m in ms if m["churn"] == "Cao"]
        movers_up = sorted(ms, key=lambda m: -m["wow"])[:3]
        movers_down = sorted(ms, key=lambda m: m["wow"])[:3]
        return {
            "intent": "overview",
            "total_revenue": total_rev, "total_gross_profit": total_gp,
            "revenue_wow_pct": round(rev_wow, 1),
            "n_up": len(up), "n_down": len(down), "n_churn_high": len(high),
            "top_up": [_brief(m) for m in movers_up],
            "top_down": [_brief(m) for m in movers_down],
            "scope": _scope(region, category),
        }

    # ---------- 4.1 Phát hiện giảm ----------
    def decline(self, region=None, category=None, top_n=10, **_) -> dict[str, Any]:
        ms = [m for m in self._filter(region, category) if m["wow"] < 0]
        ms.sort(key=lambda m: m["wow"])
        items = []
        for m in ms[:top_n]:
            items.append({
                **_brief(m),
                "txn_wow": round(m["txn_wow"], 1),
                "rr_wow": round(m["rr_wow"], 1),
                "aov_wow": round(m["aov_wow"], 1),
                "churn": m["churn"],
            })
        return {"intent": "decline", "count": len(ms), "items": items,
                "scope": _scope(region, category)}

    # ---------- 4.2 Tăng trưởng ----------
    def growth(self, region=None, category=None, top_n=10, **_) -> dict[str, Any]:
        ms = [m for m in self._filter(region, category) if m["wow"] > 0]
        ms.sort(key=lambda m: -m["wow"])
        items = [{**_brief(m)} for m in ms[: top_n or 10]]
        return {"intent": "growth", "count": len(ms), "items": items,
                "scope": _scope(region, category)}

    # ---------- Tăng đều / xu hướng tăng (nhiều tuần) ----------
    def uptrend(self, region=None, category=None, top_n=10, **_) -> dict[str, Any]:
        items = []
        for m in self._filter(region, category):
            rev = self._by_m[m["merchant_id"]]["revenue_vnd"].tolist()
            steps = [rev[i] > rev[i - 1] for i in range(1, len(rev))]
            streak = 0
            for up in reversed(steps):
                if up:
                    streak += 1
                else:
                    break
            if streak < 2:
                continue
            growth_total = (rev[-1] - rev[0]) / rev[0] * 100 if rev[0] else 0.0
            items.append({
                **_brief(m),
                "streak": streak,
                "total_steps": len(steps),
                "n_up_weeks": sum(steps),
                "growth_total_pct": round(growth_total, 1),
                "revenue_first": round(rev[0]),
                "revenue_first_fmt": _fmt_vnd(rev[0]),
                "monotonic": streak == len(steps),
            })
        items.sort(key=lambda x: (-x["streak"], -x["growth_total_pct"]))
        return {"intent": "uptrend", "count": len(items), "items": items[:top_n],
                "scope": _scope(region, category)}

    # ---------- 4.3 Voucher ----------
    def voucher(self, region=None, category=None, top_n=10, **_) -> dict[str, Any]:
        # giảm WoW + tỷ lệ quay lại giảm -> ưu tiên theo lợi nhuận gộp
        cands = [m for m in self._filter(region, category)
                 if m["wow"] < 0 and m["rr_wow"] < 0]
        cands.sort(key=lambda m: -m["gp_now"])
        items = []
        for m in cands[:top_n]:
            thin = m["margin"] < THIN_MARGIN
            if thin:
                rec = ("Biên lợi nhuận mỏng (~{:.0f}%) — KHÔNG giảm giá sâu; "
                       "dùng push notification giờ cao điểm + loyalty/tích điểm.").format(m["margin"] * 100)
            else:
                rec = ("Voucher giữ chân cho khách inactive > 30 ngày "
                       "+ push notification giờ cao điểm.")
            items.append({
                **_brief(m),
                "margin_pct": round(m["margin"] * 100, 1),
                "rr_wow": round(m["rr_wow"], 1),
                "thin_margin": thin,
                "recommendation": rec,
            })
        return {"intent": "voucher", "count": len(cands), "items": items,
                "scope": _scope(region, category)}

    # ---------- 4.4 Churn ----------
    def churn(self, region=None, category=None, level="Cao", top_n=20, **_) -> dict[str, Any]:
        ms = self._filter(region, category)
        wanted = {"Cao"} if level == "Cao" else {"Cao", "Trung bình"}
        risk = [m for m in ms if m["churn"] in wanted]
        # Cao trước, rồi theo mức giảm
        order = {"Cao": 0, "Trung bình": 1, "Thấp": 2}
        risk.sort(key=lambda m: (order[m["churn"]], m["wow"]))
        items = []
        for m in risk[:top_n]:
            items.append({
                **_brief(m),
                "churn": m["churn"],
                "consec_decline": m["consec"],
                "crash": m["crash"],
                "rr_now": round(m["rr_now"] * 100, 1),
                "reason": _churn_reason(m),
            })
        n_high = sum(1 for m in ms if m["churn"] == "Cao")
        n_med = sum(1 for m in ms if m["churn"] == "Trung bình")
        return {"intent": "churn", "n_high": n_high, "n_medium": n_med,
                "items": items, "scope": _scope(region, category)}

    # ---------- 4.6 High-value-at-risk ----------
    def at_risk(self, region=None, category=None, top_n=10, **_) -> dict[str, Any]:
        ms = self._filter(region, category)
        weight = {"Cao": 1.0, "Trung bình": 0.5}
        risk = [m for m in ms if m["churn"] in weight]
        for m in risk:
            m["_var"] = m["gp_last4"] * weight[m["churn"]]
        risk.sort(key=lambda m: -m["_var"])
        items = []
        for m in risk[:top_n]:
            items.append({
                **_brief(m),
                "churn": m["churn"],
                "gross_profit_last4": m["gp_last4"],
                "gross_profit_last4_fmt": _fmt_vnd(m["gp_last4"]),
                "value_at_risk": round(m["_var"]),
                "value_at_risk_fmt": _fmt_vnd(m["_var"]),
                "margin_pct": round(m["margin"] * 100, 1),
                "reason": _churn_reason(m),
            })
        return {"intent": "at_risk", "count": len(risk), "items": items,
                "scope": _scope(region, category)}

    # ---------- 4.7 Bóc tách nguyên nhân ----------
    def decompose(self, merchant_name=None, region=None, category=None,
                  question=None, **_) -> dict[str, Any]:
        target = None
        if merchant_name:
            key = str(merchant_name).lower().strip()
            for m in self._metrics.values():
                if key in str(m["name"]).lower():
                    target = m
                    break
        if target is None and question:
            # fallback (router không trích được tên) -> dò tên merchant trong câu hỏi
            low_q = str(question).lower()
            for m in self._metrics.values():
                if str(m["name"]).lower() in low_q:
                    target = m
                    break
        if target is None:
            # không nêu tên -> chọn merchant giảm mạnh nhất trong scope
            ms = sorted(self._filter(region, category), key=lambda m: m["wow"])
            target = ms[0] if ms else None
        if target is None:
            return {"intent": "decompose", "found": False}

        m = target
        # ΔRevenue ≈ Δtxn × AOV_prev + txn_prev × ΔAOV
        d_txn = m["txn_now"] - m["txn_prev"]
        d_aov = m["aov_now"] - m["aov_prev"]
        eff_qty = d_txn * m["aov_prev"]
        eff_aov = m["txn_prev"] * d_aov
        d_rev = m["rev_now"] - m["rev_prev"]
        residual = d_rev - eff_qty - eff_aov

        def pct(x):
            return round(x / m["rev_prev"] * 100, 1) if m["rev_prev"] else 0.0

        actions = []
        if m["txn_wow"] < -2:
            actions.append("Số lượng giảm → kéo traffic: ads tiếp cận / khuyến mãi đầu phễu.")
        if m["aov_wow"] < -2:
            actions.append("Giá trị đơn giảm → bán kèm / upsell / combo nâng giỏ hàng.")
        if m["rr_wow"] < -2:
            actions.append("Tỷ lệ quay lại giảm → loyalty / CSKH / chiến dịch win-back.")
        if not actions:
            actions.append("Các động lực ổn định — chưa cần can thiệp gấp.")

        return {
            "intent": "decompose", "found": True,
            **_brief(m),
            "qty_effect_pct": pct(eff_qty),
            "aov_effect_pct": pct(eff_aov),
            "residual_pct": pct(residual),
            "txn_wow": round(m["txn_wow"], 1),
            "aov_wow": round(m["aov_wow"], 1),
            "rr_wow": round(m["rr_wow"], 1),
            "actions": actions,
        }


def _brief(m: dict) -> dict:
    return {
        "merchant_id": m["merchant_id"],
        "name": m["name"],
        "category": m["category"],
        "region": m["region"],
        "wow_pct": round(m["wow"], 1),
        "revenue": round(m["rev_now"]),
        "revenue_fmt": _fmt_vnd(m["rev_now"]),
        "revenue_prev": round(m["rev_prev"]),
        "revenue_prev_fmt": _fmt_vnd(m["rev_prev"]),
        "gross_profit": round(m["gp_now"]),
        "gross_profit_fmt": _fmt_vnd(m["gp_now"]),
    }


def _churn_reason(m: dict) -> str:
    bits = []
    if m["consec"] >= 3:
        bits.append(f"giảm liên tục {m['consec']} tuần")
    elif m["consec"] == 2:
        bits.append("giảm 2 tuần liên tiếp")
    if m["crash"]:
        bits.append("tuần này sụp <70% trung bình 4 tuần")
    if m["low_ret"]:
        bits.append(f"tỷ lệ quay lại thấp ({m['rr_now']*100:.0f}%) và đang giảm")
    if m["wow"] < 0 and not bits:
        bits.append(f"doanh thu WoW {m['wow']:+.1f}%")
    return "; ".join(bits) or "ổn định"


def _scope(region, category) -> dict:
    return {"region": region, "category": category}
