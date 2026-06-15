"""Kiểm chứng DỰ PHÓNG cuối tháng (run-rate) khi tháng 6 CHƯA HẾT.

Cách test: sinh 'ground truth' tháng 6 ĐỦ (đến 30/06), rồi CẮT lại ở ngày
7/15/22 -> chạy engine -> so doanh số DỰ PHÓNG với THỰC TẾ cả tháng.
Run-rate đúng khi: stable/tăng-giảm-đều -> sai số nhỏ; merchant ĐỔI xu hướng
giữa tháng -> sai số lớn hơn (hạn chế cố hữu của run-rate tuyến tính).

Chạy:  python test_forecast.py
"""

import sys
from datetime import date, timedelta
from io import StringIO
import csv as _csv

sys.stdout.reconfigure(encoding="utf-8")

import random
import make_sample_data as mk
import pipeline as p

# --- 1) Sinh ground truth: tháng 6 ĐỦ (đến 30/06) ---
mk.DATA_END = date(2026, 6, 30)
mk.MONDAYS = mk.mondays(mk.DATA_START, mk.DATA_END)
mk.N_W = len(mk.MONDAYS)
mk.PROFILE_WMULT = {pf: mk.build_wmult(pf, mk.N_W) for pf in
                    ["growth", "sharp_decline", "voucher", "churn_high_3wk",
                     "churn_high_crash", "churn_medium", "stable"]}
mk.rng = random.Random(mk.SEED)
rows = mk.build_rows()

buf = StringIO()
w = _csv.writer(buf)
w.writerow(["Sub-cate", "Merchant id", "Merchant name", "App id", "Date",
            "TPV", "Transaction", "Transaction type", "SOF"])
w.writerows(rows)
full_df = p.load_dataframe(buf.getvalue().encode("utf-8"), "full.csv")

# THỰC TẾ tháng 6 đủ (per merchant)
jun = full_df[(full_df["date"].dt.year == 2026) & (full_df["date"].dt.month == 6)]
actual = jun.groupby("merchant_id")["tpv"].sum().to_dict()
actual_total = sum(actual.values())
name_of = full_df.groupby("merchant_id")["merchant_name"].first().to_dict()


def trunc(cutoff_day: int):
    d = full_df["date"]
    keep = ~((d.dt.year == 2026) & (d.dt.month == 6) & (d.dt.day > cutoff_day))
    return p.MerchantAnalyzer(full_df[keep].reset_index(drop=True))


print(f"THỰC TẾ tháng 6 (đủ 30 ngày): tổng doanh số = {p._fmt_vnd(actual_total)}\n")
print(f"{'Cắt ở ngày':>10} | {'dự phóng tổng':>18} | {'sai số tổng':>11} | {'sai số TB/merchant':>18}")
print("-" * 66)
for cut in (7, 15, 22):
    a = trunc(cut)
    proj = {m["merchant_id"]: m["rev_proj"] for m in a._metrics.values()}
    proj_total = sum(proj.values())
    err_total = (proj_total - actual_total) / actual_total * 100
    errs = [abs(proj[mid] - actual[mid]) / actual[mid] * 100
            for mid in actual if actual[mid] and mid in proj]
    mae = sum(errs) / len(errs)
    print(f"{cut:>10} | {p._fmt_vnd(proj_total):>18} | {err_total:>+10.1f}% | {mae:>16.1f}%")

# vài ví dụ ở mốc 15 (mốc giống dữ liệu nộp)
print("\nVí dụ tại mốc cắt = ngày 15 (proj vs thực tế tháng đủ):")
a15 = trunc(15)
ex = ["Phở Bắc Hà", "Bánh Ngọt Sweet Home", "Nhà Sách Tri Thức", "Điện Máy Sáng Tạo"]
for nm in ex:
    mid = next(k for k, v in name_of.items() if v == nm)
    m = a15._metrics[mid]
    err = (m["rev_proj"] - actual[mid]) / actual[mid] * 100
    print(f"  {nm:24s} dự phóng {p._fmt_vnd(m['rev_proj']):>16}  | thực tế {p._fmt_vnd(actual[mid]):>16}  | sai số {err:+5.1f}%")
