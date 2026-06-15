"""Merchant Growth Agent — lõi phân tích (mọi con số tính BẰNG CODE).

Nguồn dữ liệu (schema atlas): Sub-cate, Merchant id, Merchant name, App id, Date,
TPV, Transaction, Transaction type, SOF. Dữ liệu THEO NGÀY, tháng hiện tại chưa hết.

Hai trục thời gian:
  • TUẦN  — gộp ngày -> tuần (chỉ tuần ĐỦ 7 ngày trong khoảng dữ liệu). Dùng cho
            churn / tăng đều / bóc tách (cần nhiều mốc).
  • THÁNG — tháng trước (đủ) vs tháng hiện tại DỰ PHÓNG cuối tháng (run-rate tuyến
            tính = đã đạt ÷ số ngày đã qua × số ngày cả tháng).

LLM chỉ diễn giải kết quả đã tính — không tự tính.
"""

from __future__ import annotations

import calendar
import io
from typing import Any

import pandas as pd

# ngưỡng coi là "đứng yên" (%): tránh đếm nhiễu nhỏ thành tăng/giảm
EPS = 2.0

# tên cột nguồn -> tên nội bộ
COLMAP = {
    "Sub-cate": "category",
    "Merchant id": "merchant_id",
    "Merchant name": "merchant_name",
    "App id": "app_id",
    "Date": "date",
    "TPV": "tpv",
    "Transaction": "txn",
    "Transaction type": "txn_type",
    "SOF": "sof",
}
REQUIRED_SRC = ["Sub-cate", "Merchant id", "Merchant name", "Date", "TPV", "Transaction"]


class SchemaError(ValueError):
    """File thiếu cột bắt buộc."""


def load_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    """Đọc CSV/Excel (schema atlas) từ bytes, chuẩn hóa tên cột nội bộ."""
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(content))
    else:
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1")

    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_SRC if c not in df.columns]
    if missing:
        raise SchemaError(
            "File thiếu cột bắt buộc: " + ", ".join(missing)
            + ". Cần tối thiểu: " + ", ".join(REQUIRED_SRC)
        )

    df = df.rename(columns={k: v for k, v in COLMAP.items() if k in df.columns})
    for opt in ("app_id", "txn_type", "sof"):
        if opt not in df.columns:
            df[opt] = ""
    df["tpv"] = pd.to_numeric(df["tpv"], errors="coerce")
    df["txn"] = pd.to_numeric(df["txn"], errors="coerce")
    df = df.dropna(subset=["merchant_id", "date", "tpv", "txn"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["merchant_id"] = df["merchant_id"].astype(str)
    df = df.sort_values(["merchant_id", "date"]).reset_index(drop=True)
    if df.empty:
        raise SchemaError("File không có dòng dữ liệu hợp lệ.")
    return df


def _fmt_vnd(x: float) -> str:
    return f"{round(x):,} đ".replace(",", ".")


def _monday(ts: pd.Timestamp) -> pd.Timestamp:
    return (ts - pd.Timedelta(days=int(ts.weekday()))).normalize()


class MerchantAnalyzer:
    """Giữ 1 DataFrame đã nạp; expose các nhóm phân tích (tuần + tháng)."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.min_date = df["date"].min().normalize()
        self.max_date = df["date"].max().normalize()
        cy, cm = int(self.max_date.year), int(self.max_date.month)
        self.cur_y, self.cur_m = cy, cm
        self.prev_y, self.prev_m = (cy - 1, 12) if cm == 1 else (cy, cm - 1)
        self.days_elapsed = int(self.max_date.day)
        self.days_in_month = calendar.monthrange(cy, cm)[1]
        self.days_prev_month = calendar.monthrange(self.prev_y, self.prev_m)[1]

        # gộp nhiều dòng (theo transaction type/SOF) -> 1 dòng/merchant/ngày
        daily = (df.groupby(["merchant_id", "date"], as_index=False)
                   .agg(tpv=("tpv", "sum"), txn=("txn", "sum")))
        meta_cols = (df.groupby("merchant_id")
                       .agg(name=("merchant_name", "first"),
                            category=("category", "first"),
                            app_id=("app_id", "first")))
        self._daily = {mid: g.sort_values("date").reset_index(drop=True)
                       for mid, g in daily.groupby("merchant_id")}
        self._info = meta_cols.to_dict("index")
        self._pay = self._payment_mix()

        # tuần ĐỦ (Mon..Sun nằm trọn trong [min, max])
        self._complete_mondays = self._calc_complete_mondays()
        self._metrics = {mid: self._compute(mid, g) for mid, g in self._daily.items()}

    # ---------- chuẩn bị ----------
    def _calc_complete_mondays(self) -> list[pd.Timestamp]:
        out = []
        m = _monday(self.min_date)
        while m <= self.max_date:
            if m >= self.min_date and (m + pd.Timedelta(days=6)) <= self.max_date:
                out.append(m)
            m += pd.Timedelta(weeks=1)
        return out

    def _payment_mix(self) -> dict[str, dict]:
        out = {}
        for mid, g in self.df.groupby("merchant_id"):
            tot = g["tpv"].sum() or 1
            by_type = g.groupby("txn_type")["tpv"].sum()
            mix = {str(k): round(v / tot * 100, 1) for k, v in by_type.items() if str(k)}
            # số tuyệt đối theo TỪNG kênh (sum riêng từng loại)
            tpv_by_type = {str(k): float(v) for k, v in by_type.items() if str(k)}
            wal = g[g["txn_type"].astype(str).str.lower() == "wallet"]
            wal_tot = wal["tpv"].sum() or 0
            # số tuyệt đối theo TỪNG SOF (Paylater / Others) — sum riêng từng loại
            by_sof = wal.groupby("sof")["tpv"].sum()
            tpv_by_sof = {str(k): float(v) for k, v in by_sof.items()
                          if str(k) and str(k).lower() != "nan"}
            pl = tpv_by_sof.get("Paylater", 0.0)
            paylater_pct = round(pl / wal_tot * 100, 1) if wal_tot else 0.0
            out[str(mid)] = {"mix": mix, "paylater_pct": paylater_pct,
                             "tpv_by_type": tpv_by_type, "tpv_by_sof": tpv_by_sof}
        return out

    def _weekly(self, g: pd.DataFrame) -> tuple[list[float], list[float]]:
        """(rev_tuần, txn_tuần) cho các tuần ĐỦ, theo thứ tự thời gian."""
        gg = g.copy()
        gg["mon"] = gg["date"].apply(_monday)
        agg = gg.groupby("mon").agg(tpv=("tpv", "sum"), txn=("txn", "sum"))
        rev, txn = [], []
        for mon in self._complete_mondays:
            if mon in agg.index:
                rev.append(float(agg.loc[mon, "tpv"]))
                txn.append(float(agg.loc[mon, "txn"]))
        return rev, txn

    def _compute(self, mid: str, g: pd.DataFrame) -> dict[str, Any]:
        info = self._info[mid]
        d = g["date"]
        cur_mask = (d.dt.year == self.cur_y) & (d.dt.month == self.cur_m)
        prev_mask = (d.dt.year == self.prev_y) & (d.dt.month == self.prev_m)
        rev_mtd = float(g.loc[cur_mask, "tpv"].sum())
        txn_mtd = float(g.loc[cur_mask, "txn"].sum())
        rev_prev = float(g.loc[prev_mask, "tpv"].sum())
        txn_prev_m = float(g.loc[prev_mask, "txn"].sum())
        # so theo NHỊP ĐỘ NGÀY (trung hòa số ngày tháng) rồi mới dự phóng cả tháng
        may_daily = rev_prev / self.days_prev_month if self.days_prev_month else 0.0
        jun_daily = rev_mtd / self.days_elapsed if self.days_elapsed else 0.0
        txn_may_daily = txn_prev_m / self.days_prev_month if self.days_prev_month else 0.0
        txn_jun_daily = txn_mtd / self.days_elapsed if self.days_elapsed else 0.0
        rev_proj = jun_daily * self.days_in_month
        txn_proj = txn_jun_daily * self.days_in_month
        mom = (jun_daily - may_daily) / may_daily * 100 if may_daily else 0.0
        txn_mom = (txn_jun_daily - txn_may_daily) / txn_may_daily * 100 if txn_may_daily else 0.0
        aov_prev_m = rev_prev / txn_prev_m if txn_prev_m else 0.0
        aov_proj = rev_mtd / txn_mtd if txn_mtd else 0.0
        aov_mom = (aov_proj - aov_prev_m) / aov_prev_m * 100 if aov_prev_m else 0.0

        rev, txn = self._weekly(g)
        n = len(rev)
        aov = [rev[i] / txn[i] if txn[i] else 0.0 for i in range(n)]
        wow = (rev[-1] - rev[-2]) / rev[-2] * 100 if n > 1 and rev[-2] else 0.0
        txn_wow = (txn[-1] - txn[-2]) / txn[-2] * 100 if n > 1 and txn[-2] else 0.0
        aov_wow = (aov[-1] - aov[-2]) / aov[-2] * 100 if n > 1 and aov[-2] else 0.0

        # đếm chuỗi tăng/giảm liên tiếp — bỏ qua dao động <1% (nhiễu) để khỏi đếm giả
        consec = 0
        for i in range(n - 1, 0, -1):
            if rev[i] < rev[i - 1] * 0.99:
                consec += 1
            else:
                break
        up_streak = 0
        for i in range(n - 1, 0, -1):
            if rev[i] > rev[i - 1] * 1.01:
                up_streak += 1
            else:
                break
        avg_prev4 = sum(rev[-5:-1]) / len(rev[-5:-1]) if n > 1 else (rev[-1] if rev else 0)
        crash = bool(rev and avg_prev4 and rev[-1] < 0.7 * avg_prev4)

        if consec >= 3 or crash:
            churn = "Cao"
        elif consec == 2:
            churn = "Trung bình"
        else:
            churn = "Thấp"

        return dict(
            merchant_id=mid, name=info["name"], category=info["category"],
            app_id=info["app_id"],
            # tháng
            rev_prev=rev_prev, rev_mtd=rev_mtd, rev_proj=rev_proj, mom=mom,
            txn_prev_m=txn_prev_m, txn_proj=txn_proj, txn_mom=txn_mom,
            aov_prev_m=aov_prev_m, aov_proj=aov_proj, aov_mom=aov_mom,
            may_daily=may_daily, jun_daily=jun_daily,
            txn_may_daily=txn_may_daily, txn_jun_daily=txn_jun_daily,
            # tuần
            w_rev=rev, w_txn=txn,
            w_rev_now=rev[-1] if rev else 0.0, w_rev_prev=rev[-2] if n > 1 else (rev[-1] if rev else 0.0),
            w_txn_now=txn[-1] if txn else 0.0, w_txn_prev=txn[-2] if n > 1 else (txn[-1] if txn else 0.0),
            w_aov_now=aov[-1] if aov else 0.0, w_aov_prev=aov[-2] if n > 1 else (aov[-1] if aov else 0.0),
            wow=wow, txn_wow=txn_wow, aov_wow=aov_wow,
            consec=consec, up_streak=up_streak, crash=crash, churn=churn,
            pay=self._pay.get(mid, {"mix": {}, "paylater_pct": 0.0}),
        )

    # ---------- chọn trục thời gian ----------
    def _pv(self, m: dict, period: str) -> tuple[float, float, float]:
        """(now, prev, change%) theo period 'month' | 'week'."""
        if period == "week":
            return m["w_rev_now"], m["w_rev_prev"], m["wow"]
        return m["rev_proj"], m["rev_prev"], m["mom"]

    def _filter(self, category: str | None) -> list[dict]:
        out = list(self._metrics.values())
        if category:
            c = str(category).lower()
            out = [m for m in out if c in str(m["category"]).lower()]
        return out

    def _brief(self, m: dict, period: str) -> dict:
        now, prev, change = self._pv(m, period)
        return {
            "merchant_id": m["merchant_id"], "name": m["name"],
            "category": m["category"], "app_id": m["app_id"],
            "change_pct": round(change, 1),
            "revenue": round(now), "revenue_fmt": _fmt_vnd(now),
            "revenue_prev": round(prev), "revenue_prev_fmt": _fmt_vnd(prev),
            "revenue_mtd": round(m["rev_mtd"]), "revenue_mtd_fmt": _fmt_vnd(m["rev_mtd"]),
            "revenue_proj": round(m["rev_proj"]), "revenue_proj_fmt": _fmt_vnd(m["rev_proj"]),
            "revenue_prev_month": round(m["rev_prev"]), "revenue_prev_month_fmt": _fmt_vnd(m["rev_prev"]),
        }

    # ---------- meta / series / digest ----------
    def meta(self) -> dict[str, Any]:
        return {
            "n_merchants": len(self._daily),
            "n_weeks": len(self._complete_mondays),
            "current_month": f"{self.cur_y}-{self.cur_m:02d}",
            "prev_month": f"{self.prev_y}-{self.prev_m:02d}",
            "data_from": self.min_date.date().isoformat(),
            "data_to": self.max_date.date().isoformat(),
            "days_elapsed": self.days_elapsed,
            "days_in_month": self.days_in_month,
            "categories": sorted(self.df["category"].dropna().astype(str).unique().tolist()),
        }

    def series_all(self) -> dict[str, Any]:
        weeks = [m.date().isoformat() for m in self._complete_mondays]
        merchants = []
        for mid, m in self._metrics.items():
            merchants.append({
                "id": mid, "name": m["name"], "category": m["category"],
                "revenue": [int(x) for x in m["w_rev"]],
            })
        return {"weeks": weeks, "merchants": merchants}

    def merchant_names(self) -> list[str]:
        return [m["name"] for m in self._metrics.values()]

    # ---------- Cơ cấu thanh toán (sum riêng từng kênh + từng SOF) ----------
    def payment(self, category=None, **_) -> dict[str, Any]:
        df = self.df
        if category:
            c = str(category).lower()
            df = df[df["category"].astype(str).str.lower().str.contains(c, na=False)]
        total = float(df["tpv"].sum())
        tt = df.groupby("txn_type").agg(tpv=("tpv", "sum"), txn=("txn", "sum"))
        types = []
        for k, row in tt.iterrows():
            if not str(k):
                continue
            types.append({"name": str(k), "tpv": round(row["tpv"]), "tpv_fmt": _fmt_vnd(row["tpv"]),
                          "txn": int(row["txn"]),
                          "pct": round(row["tpv"] / total * 100, 1) if total else 0.0})
        types.sort(key=lambda x: -x["tpv"])
        wal = df[df["txn_type"].astype(str).str.lower() == "wallet"]
        wal_tot = float(wal["tpv"].sum())
        ss = wal.groupby("sof").agg(tpv=("tpv", "sum"), txn=("txn", "sum"))
        sof = []
        for k, row in ss.iterrows():
            if not str(k) or str(k).lower() == "nan":
                continue
            sof.append({"name": str(k), "tpv": round(row["tpv"]), "tpv_fmt": _fmt_vnd(row["tpv"]),
                        "txn": int(row["txn"]),
                        "pct_wallet": round(row["tpv"] / wal_tot * 100, 1) if wal_tot else 0.0,
                        "pct_total": round(row["tpv"] / total * 100, 1) if total else 0.0})
        sof.sort(key=lambda x: -x["tpv"])
        return {"intent": "payment", "scope": _scope(category),
                "total_tpv": round(total), "total_tpv_fmt": _fmt_vnd(total),
                "wallet_tpv": round(wal_tot), "wallet_tpv_fmt": _fmt_vnd(wal_tot),
                "types": types, "sof": sof}

    # ---------- Tra cứu 1 merchant (tính bằng code, tức thì, không cần LLM) ----------
    def merchant(self, merchant_name=None, question=None, **_) -> dict[str, Any]:
        target = None
        if merchant_name:
            key = str(merchant_name).lower().strip()
            target = next((m for m in self._metrics.values()
                           if key in str(m["name"]).lower()), None)
        if target is None and question:
            low = str(question).lower()
            target = next((m for m in self._metrics.values()
                           if str(m["name"]).lower() in low), None)
        if target is None:
            return {"intent": "merchant", "found": False}
        m = target
        pay = m["pay"]
        return {
            "intent": "merchant", "found": True,
            "name": m["name"], "category": m["category"],
            "revenue_proj_fmt": _fmt_vnd(m["rev_proj"]),
            "revenue_mtd_fmt": _fmt_vnd(m["rev_mtd"]),
            "revenue_prev_fmt": _fmt_vnd(m["rev_prev"]),
            "mom_pct": round(m["mom"], 1), "wow_pct": round(m["wow"], 1),
            "txn_week": round(m["w_txn_now"]), "aov_fmt": _fmt_vnd(m["w_aov_now"]),
            "churn": m["churn"], "consec": m["consec"], "up_streak": m["up_streak"],
            "payment_mix": pay["mix"], "wallet_paylater_pct": pay["paylater_pct"],
        }

    def digest(self) -> list[dict[str, Any]]:
        rows = []
        for m in self._metrics.values():
            rows.append({
                "name": m["name"], "category": m["category"],
                "revenue_prev_month": round(m["rev_prev"]),
                "revenue_mtd": round(m["rev_mtd"]),
                "revenue_proj_month_end": round(m["rev_proj"]),
                "mom_pct": round(m["mom"], 1),
                "wow_pct": round(m["wow"], 1),
                "txn_now_week": round(m["w_txn_now"]),
                "aov_now": round(m["w_aov_now"]),
                "churn_risk": m["churn"],
                "weeks_declining_streak": m["consec"],
                "weeks_increasing_streak": m["up_streak"],
                "payment_mix_pct": m["pay"]["mix"],
                "wallet_paylater_pct": m["pay"]["paylater_pct"],
                # số tuyệt đối (toàn kỳ) — CỘNG các giá trị này để ra tổng theo kênh/SOF
                "tpv_by_type": {k: round(v) for k, v in m["pay"]["tpv_by_type"].items()},
                "tpv_by_sof": {k: round(v) for k, v in m["pay"]["tpv_by_sof"].items()},
            })
        return rows

    # ---------- Tổng quan ----------
    def overview(self, category=None, period="month", **_) -> dict[str, Any]:
        ms = self._filter(category)
        now = sum(self._pv(m, period)[0] for m in ms)
        prev = sum(self._pv(m, period)[1] for m in ms)
        mtd = sum(m["rev_mtd"] for m in ms)
        if period == "month":   # trung hòa số ngày tháng
            pd_ = sum(m["may_daily"] for m in ms)
            cd_ = sum(m["jun_daily"] for m in ms)
            change = (cd_ - pd_) / pd_ * 100 if pd_ else 0.0
        else:
            change = (now - prev) / prev * 100 if prev else 0.0
        up = [m for m in ms if self._pv(m, period)[2] > EPS]
        down = [m for m in ms if self._pv(m, period)[2] < -EPS]
        high = [m for m in ms if m["churn"] == "Cao"]
        movers_up = sorted(ms, key=lambda m: -self._pv(m, period)[2])[:3]
        movers_down = sorted(ms, key=lambda m: self._pv(m, period)[2])[:3]
        return {
            "intent": "overview", "period": period,
            "total_now": round(now), "total_prev": round(prev), "total_mtd": round(mtd),
            "change_pct": round(change, 1),
            "n_up": len(up), "n_down": len(down), "n_churn_high": len(high),
            "top_up": [self._brief(m, period) for m in movers_up],
            "top_down": [self._brief(m, period) for m in movers_down],
            "scope": _scope(category),
        }

    # ---------- Phát hiện giảm ----------
    def decline(self, category=None, period="month", top_n=10, **_) -> dict[str, Any]:
        ms = [m for m in self._filter(category) if self._pv(m, period)[2] < -EPS]
        ms.sort(key=lambda m: self._pv(m, period)[2])
        items = []
        for m in ms[:top_n]:
            tw = m["txn_mom"] if period == "month" else m["txn_wow"]
            aw = m["aov_mom"] if period == "month" else m["aov_wow"]
            items.append({**self._brief(m, period),
                          "txn_chg": round(tw, 1), "aov_chg": round(aw, 1),
                          "churn": m["churn"]})
        return {"intent": "decline", "period": period, "count": len(ms),
                "items": items, "scope": _scope(category)}

    # ---------- Tăng trưởng ----------
    def growth(self, category=None, period="month", top_n=10, **_) -> dict[str, Any]:
        ms = [m for m in self._filter(category) if self._pv(m, period)[2] > EPS]
        ms.sort(key=lambda m: -self._pv(m, period)[2])
        items = [self._brief(m, period) for m in ms[: top_n or 10]]
        return {"intent": "growth", "period": period, "count": len(ms),
                "items": items, "scope": _scope(category)}

    # ---------- Tăng đều (nhiều tuần) ----------
    def uptrend(self, category=None, top_n=10, **_) -> dict[str, Any]:
        items = []
        for m in self._filter(category):
            rev = m["w_rev"]
            if m["up_streak"] < 2 or len(rev) < 2:
                continue
            growth_total = (rev[-1] - rev[0]) / rev[0] * 100 if rev[0] else 0.0
            items.append({**self._brief(m, "week"),
                          "streak": m["up_streak"], "total_steps": len(rev) - 1,
                          "growth_total_pct": round(growth_total, 1),
                          "revenue_first_fmt": _fmt_vnd(rev[0]),
                          "monotonic": m["up_streak"] == len(rev) - 1})
        items.sort(key=lambda x: (-x["streak"], -x["growth_total_pct"]))
        return {"intent": "uptrend", "count": len(items), "items": items[:top_n],
                "scope": _scope(category)}

    # ---------- Voucher (xếp theo TPV) ----------
    def voucher(self, category=None, period="month", top_n=10, **_) -> dict[str, Any]:
        cands = [m for m in self._filter(category) if self._pv(m, period)[2] < -EPS]
        cands.sort(key=lambda m: -self._pv(m, period)[0])   # ưu tiên doanh số (TPV) lớn
        items = []
        for m in cands[:top_n]:
            items.append({**self._brief(m, period), "churn": m["churn"],
                          "recommendation": (
                              "Doanh số đang giảm nhưng quy mô lớn — ưu tiên giữ chân: "
                              "voucher cho khách inactive >30 ngày + push notification giờ cao điểm.")})
        return {"intent": "voucher", "period": period, "count": len(cands),
                "items": items, "scope": _scope(category)}

    # ---------- Churn (theo tuần) ----------
    def churn(self, category=None, level="Cao", top_n=20, **_) -> dict[str, Any]:
        ms = self._filter(category)
        wanted = {"Cao"} if level == "Cao" else {"Cao", "Trung bình"}
        risk = [m for m in ms if m["churn"] in wanted]
        order = {"Cao": 0, "Trung bình": 1, "Thấp": 2}
        risk.sort(key=lambda m: (order[m["churn"]], m["wow"]))
        items = []
        for m in risk[:top_n]:
            items.append({**self._brief(m, "month"), "churn": m["churn"],
                          "consec_decline": m["consec"], "crash": m["crash"],
                          "wow_pct": round(m["wow"], 1), "reason": _churn_reason(m)})
        n_high = sum(1 for m in ms if m["churn"] == "Cao")
        n_med = sum(1 for m in ms if m["churn"] == "Trung bình")
        return {"intent": "churn", "n_high": n_high, "n_medium": n_med,
                "items": items, "scope": _scope(category)}

    # ---------- Merchant quan trọng đang lung lay ----------
    def at_risk(self, category=None, top_n=10, **_) -> dict[str, Any]:
        weight = {"Cao": 1.0, "Trung bình": 0.5}
        risk = [m for m in self._filter(category) if m["churn"] in weight]
        for m in risk:
            m["_var"] = m["rev_proj"] * weight[m["churn"]]
        risk.sort(key=lambda m: -m["_var"])
        items = []
        for m in risk[:top_n]:
            items.append({**self._brief(m, "month"), "churn": m["churn"],
                          "value_at_risk": round(m["_var"]),
                          "value_at_risk_fmt": _fmt_vnd(m["_var"]),
                          "reason": _churn_reason(m)})
        return {"intent": "at_risk", "count": len(risk), "items": items,
                "scope": _scope(category)}

    # ---------- Bóc tách nguyên nhân ----------
    def decompose(self, merchant_name=None, category=None, period="month",
                  question=None, **_) -> dict[str, Any]:
        target = None
        if merchant_name:
            key = str(merchant_name).lower().strip()
            target = next((m for m in self._metrics.values()
                           if key in str(m["name"]).lower()), None)
        if target is None and question:
            low_q = str(question).lower()
            target = next((m for m in self._metrics.values()
                           if str(m["name"]).lower() in low_q), None)
        if target is None:
            ms = sorted(self._filter(category), key=lambda m: self._pv(m, period)[2])
            target = ms[0] if ms else None
        if target is None:
            return {"intent": "decompose", "found": False}

        m = target
        if period == "week":
            txn_now, txn_prev = m["w_txn_now"], m["w_txn_prev"]
            aov_now, aov_prev = m["w_aov_now"], m["w_aov_prev"]
            txn_chg, aov_chg = m["txn_wow"], m["aov_wow"]
            now_r, prev_r = m["w_rev_now"], m["w_rev_prev"]
        else:
            # mức tháng: bóc tách theo NHỊP ĐỘ NGÀY (đồng nhất với mom)
            txn_now, txn_prev = m["txn_jun_daily"], m["txn_may_daily"]
            aov_now, aov_prev = m["aov_proj"], m["aov_prev_m"]
            txn_chg, aov_chg = m["txn_mom"], m["aov_mom"]
            now_r, prev_r = m["jun_daily"], m["may_daily"]
        change = self._pv(m, period)[2]
        eff_qty = (txn_now - txn_prev) * aov_prev
        eff_aov = txn_prev * (aov_now - aov_prev)
        residual = (now_r - prev_r) - eff_qty - eff_aov

        def pct(x):
            return round(x / prev_r * 100, 1) if prev_r else 0.0

        actions = []
        if txn_chg < -2:
            actions.append("Số lượng giảm → kéo traffic: ads tiếp cận / khuyến mãi đầu phễu.")
        if aov_chg < -2:
            actions.append("Giá trị đơn giảm → bán kèm / upsell / combo nâng giỏ hàng.")
        if not actions:
            actions.append("Các động lực ổn định — chưa cần can thiệp gấp.")

        return {"intent": "decompose", "found": True, "period": period,
                **self._brief(m, period),
                "qty_effect_pct": pct(eff_qty), "aov_effect_pct": pct(eff_aov),
                "residual_pct": pct(residual),
                "txn_chg": round(txn_chg, 1), "aov_chg": round(aov_chg, 1),
                "actions": actions}

    # ---------- Dự phóng cuối tháng vs tháng trước ----------
    def forecast(self, category=None, top_n=10, **_) -> dict[str, Any]:
        ms = self._filter(category)
        tot_prev = sum(m["rev_prev"] for m in ms)
        tot_proj = sum(m["rev_proj"] for m in ms)
        tot_mtd = sum(m["rev_mtd"] for m in ms)
        # so theo nhịp độ ngày (trung hòa số ngày tháng)
        prev_daily = sum(m["may_daily"] for m in ms)
        cur_daily = sum(m["jun_daily"] for m in ms)
        change = (cur_daily - prev_daily) / prev_daily * 100 if prev_daily else 0.0
        ranked = sorted(ms, key=lambda m: -m["mom"])
        higher = [self._brief(m, "month") for m in ranked if m["mom"] > EPS][:top_n]
        lower = [self._brief(m, "month") for m in sorted(ms, key=lambda m: m["mom"])
                 if m["mom"] < -EPS][:top_n]
        return {
            "intent": "forecast",
            "total_prev_month": round(tot_prev), "total_mtd": round(tot_mtd),
            "total_proj_month_end": round(tot_proj), "change_pct": round(change, 1),
            "is_higher": cur_daily > prev_daily,
            "days_elapsed": self.days_elapsed, "days_in_month": self.days_in_month,
            "n_higher": sum(1 for m in ms if m["mom"] > EPS),
            "n_lower": sum(1 for m in ms if m["mom"] < -EPS),
            "top_higher": higher, "top_lower": lower,
            "scope": _scope(category),
        }


def _churn_reason(m: dict) -> str:
    bits = []
    if m["consec"] >= 3:
        bits.append(f"giảm liên tục {m['consec']} tuần")
    elif m["consec"] == 2:
        bits.append("giảm 2 tuần liên tiếp")
    if m["crash"]:
        bits.append("tuần này sụp <70% trung bình 4 tuần")
    if m["wow"] < 0 and not bits:
        bits.append(f"doanh số WoW {m['wow']:+.1f}%")
    return "; ".join(bits) or "ổn định"


def _scope(category) -> dict:
    return {"category": category}
