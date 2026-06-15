"""Sinh dữ liệu mẫu cho Merchant Growth Agent (Claw-a-thon 2026) — SCHEMA MỚI.

Cột xuất (đúng nguồn atlas):
  Sub-cate, Merchant id, Merchant name, App id, Date, TPV, Transaction,
  Transaction type, SOF

- Dữ liệu THEO NGÀY: tháng 5 đầy đủ (01–31) + tháng 6 đến 15/06 (tháng chưa hết).
- Mỗi merchant/ngày tách thành nhiều dòng theo Transaction type
  (Payment Gateway / VietQR / Wallet). Dòng Wallet còn tách SOF (Paylater/Others);
  Payment Gateway & VietQR để trống SOF.
- Mỗi merchant gắn 1 "profile" có chủ đích để các kịch bản demo (giảm / tăng /
  churn / voucher / dự phóng cuối tháng) đều có merchant khớp — ở CẢ mức tuần
  (engine nội bộ) lẫn mức tháng (dự phóng vs tháng trước).
- Seed cố định -> tái tạo được.

Chạy:  python make_sample_data.py
Xuất:  merchant_performance_sample.csv  (UTF-8 có BOM)
"""

import csv
import random
from datetime import date, timedelta

SEED = 2026
OUT = "merchant_performance_sample.csv"
# Nhiều tháng đầy đủ (02–05) + tháng 6 đến 15 (chưa hết) -> agent dự phóng cuối tháng.
DATA_START = date(2026, 2, 1)
DATA_END = date(2026, 6, 15)

rng = random.Random(SEED)


def mondays(start: date, end: date) -> list[date]:
    """Danh sách thứ Hai của mọi tuần phủ [start, end]."""
    m = start - timedelta(days=start.weekday())
    out = []
    while m <= end:
        out.append(m)
        m += timedelta(weeks=1)
    return out


MONDAYS = mondays(DATA_START, DATA_END)   # ~19 mốc tuần
N_W = len(MONDAYS)

# Pattern tăng/giảm NEO VÀO CUỐI KỲ (không phụ thuộc số tháng lịch sử). Các tháng
# trước chỉ là nền (1.0 hoặc trend tăng); riêng vài tuần cuối tạo kịch bản demo.
# "tail" = hệ số cho len(tail) tuần CUỐI (kết thúc ở Monday cuối Jun15 — tuần lẻ).
_TAILS = {
    "sharp_decline":    [0.90, 0.78, 0.70],         # giảm 2 tuần đủ cuối -> decline
    "voucher":          [0.92, 0.82, 0.75],         # như trên + doanh số cao
    "churn_high_3wk":   [0.90, 0.80, 0.70, 0.62],   # >=3 tuần giảm -> churn Cao
    "churn_high_crash": [0.55, 0.50],               # sụp <70% TB4 -> churn Cao
    "churn_medium":     [1.05, 0.93, 0.86, 0.80],   # đúng 2 tuần giảm -> churn TB
    "stable":           [],
}


def build_wmult(profile: str, n: int) -> list[float]:
    if profile == "growth":   # tăng đều mỗi tuần (compounding) -> growth/uptrend/MoM+
        a = [0.70]
        for _ in range(n - 1):
            a.append(a[-1] * 1.035)
        return a
    base = [1.0] * n
    tail = _TAILS.get(profile, [])
    for i, v in enumerate(tail):
        base[n - len(tail) + i] = v
    return base


PROFILE_WMULT = {p: build_wmult(p, N_W) for p in
                 ["growth", "sharp_decline", "voucher", "churn_high_3wk",
                  "churn_high_crash", "churn_medium", "stable"]}

# base doanh số/NGÀY theo size (VND) — xấp xỉ
SIZE_BASE_DAILY = {"s": 2_600_000, "m": 7_900_000, "l": 20_000_000}

# AOV (VND) theo Sub-cate
AOV_BY_SUBCAT = {
    "Bakery & Dessert": 90_000, "Coffee & Tea": 60_000, "Restaurant": 150_000,
    "Fashion": 320_000, "Electronics": 1_800_000, "Grocery": 70_000,
    "Books & Stationery": 120_000, "Beauty & Cosmetics": 250_000, "Others": 180_000,
}

# (tên, Sub-cate, profile, size)
MERCHANTS = [
    # --- sharp_decline ---
    ("Cafe Workspace", "Coffee & Tea", "sharp_decline", "m"),
    ("Tạp Hóa Cô Ba", "Grocery", "sharp_decline", "s"),
    ("Trà Sữa Mây", "Coffee & Tea", "sharp_decline", "m"),
    ("Shop Giày Bước Chân", "Fashion", "sharp_decline", "m"),
    ("Quán Cơm Văn Phòng 247", "Restaurant", "sharp_decline", "m"),
    ("Cửa Hàng Tiện Lợi Góc Phố", "Grocery", "sharp_decline", "s"),
    # --- voucher (doanh số cao + đang giảm) ---
    ("Điện Tử Hoàng Gia", "Electronics", "voucher", "l"),
    ("Siêu Thị Mini An Khang", "Grocery", "voucher", "l"),
    # --- growth ---
    ("Bánh Ngọt Sweet Home", "Bakery & Dessert", "growth", "m"),
    ("Thời Trang Lyla", "Fashion", "growth", "m"),
    ("Phụ Kiện Tech Zone", "Others", "growth", "s"),
    ("Quán Ăn Ngon Mỗi Ngày", "Restaurant", "growth", "l"),
    ("Mỹ Phẩm Glow", "Beauty & Cosmetics", "growth", "m"),
    ("Hoa Tươi Mỗi Sáng", "Others", "growth", "s"),
    # --- churn cao: 3 tuần giảm ---
    ("Nhà Sách Tri Thức", "Books & Stationery", "churn_high_3wk", "m"),
    ("Đồ Chơi Tuổi Thơ", "Others", "churn_high_3wk", "s"),
    ("Quán Nhậu Bờ Kè", "Restaurant", "churn_high_3wk", "m"),
    # --- churn cao: crash ---
    ("Điện Máy Sáng Tạo", "Electronics", "churn_high_crash", "l"),
    ("Thời Trang Nam Phố", "Fashion", "churn_high_crash", "m"),
    # --- churn trung bình ---
    ("Trà Chanh Chém Gió", "Coffee & Tea", "churn_medium", "s"),
    ("Giày Dép Thời Thượng", "Fashion", "churn_medium", "m"),
    ("Phụ Kiện Điện Thoại Z", "Others", "churn_medium", "m"),
    # --- stable (nền) ---
    ("Phở Bắc Hà", "Restaurant", "stable", "m"),
    ("Cơm Tấm Sài Gòn", "Restaurant", "stable", "m"),
    ("Bún Bò O Hue", "Restaurant", "stable", "s"),
    ("Thời Trang Công Sở Lady", "Fashion", "stable", "m"),
    ("Cửa Hàng Mẹ Và Bé", "Others", "stable", "m"),
    ("Nhà Thuốc An Tâm", "Others", "stable", "l"),
    ("Quán Cà Phê Sân Vườn", "Coffee & Tea", "stable", "m"),
    ("Tiệm Bánh Mì 36", "Bakery & Dessert", "stable", "s"),
    ("Shop Đồng Hồ Luxury", "Fashion", "stable", "l"),
    ("Điện Thoại Di Động FPT Mini", "Electronics", "stable", "l"),
    ("Tạp Hóa Bình Dân", "Grocery", "stable", "s"),
    ("Mỹ Phẩm Hàn Quốc K-Beauty", "Beauty & Cosmetics", "stable", "m"),
    ("Quán Lẩu Nướng 9999", "Restaurant", "stable", "m"),
    ("Văn Phòng Phẩm Hồng Hà", "Books & Stationery", "stable", "s"),
    ("Đồ Gia Dụng Tiện Ích", "Others", "stable", "m"),
    ("Trà Sữa Gong Gong", "Coffee & Tea", "stable", "m"),
    ("Thời Trang Trẻ Em Cute", "Fashion", "stable", "s"),
    ("Hải Sản Tươi Sống Biển Đông", "Restaurant", "stable", "l"),
]

TXN_TYPES = ["Payment Gateway", "VietQR", "Wallet"]


def jitter(x, pct):
    return x * (1 + rng.uniform(-pct, pct))


def dow_factor(d: date) -> float:
    """Nhịp ngày trong tuần (cuối tuần cao hơn) — nhẹ."""
    wd = d.weekday()
    if wd >= 5:        # T7, CN
        return 1.10
    if wd == 4:        # T6
        return 1.05
    return 1.0


def split_rows(merch, d, txn, tpv):
    """Tách 1 ngày của merchant thành các dòng theo Transaction type + SOF."""
    mid, name, sub, app_id, pg, vq, paylater = merch
    rows = []
    # Payment Gateway
    t_pg, v_pg = round(txn * pg), round(tpv * pg)
    # VietQR
    t_vq, v_vq = round(txn * vq), round(tpv * vq)
    # Wallet = phần còn lại
    t_wl, v_wl = txn - t_pg - t_vq, tpv - v_pg - v_vq
    if t_pg > 0:
        rows.append((sub, mid, name, app_id, d.isoformat(), v_pg, t_pg, "Payment Gateway", ""))
    if t_vq > 0:
        rows.append((sub, mid, name, app_id, d.isoformat(), v_vq, t_vq, "VietQR", ""))
    if t_wl > 0:
        t_pl, v_pl = round(t_wl * paylater), round(v_wl * paylater)
        t_ot, v_ot = t_wl - t_pl, v_wl - v_pl
        if t_pl > 0:
            rows.append((sub, mid, name, app_id, d.isoformat(), v_pl, t_pl, "Wallet", "Paylater"))
        if t_ot > 0:
            rows.append((sub, mid, name, app_id, d.isoformat(), v_ot, t_ot, "Wallet", "Others"))
    return rows


def build_rows():
    midx = {m: i for i, m in enumerate(MONDAYS)}
    rows = []
    days = [DATA_START + timedelta(days=i) for i in range((DATA_END - DATA_START).days + 1)]

    for idx, (name, sub, profile, size) in enumerate(MERCHANTS):
        mid = f"{100001 + idx}"          # 6 số
        app_id = f"{2001 + idx}"         # 4 số
        aov = max(10_000, round(jitter(AOV_BY_SUBCAT[sub], 0.05)))
        base_daily_tpv = SIZE_BASE_DAILY[size] * jitter(1.0, 0.15)
        base_txn = max(1, round(base_daily_tpv / aov))
        # tỷ trọng kênh thanh toán cố định mỗi merchant
        pg = max(0.15, jitter(0.42, 0.18))
        vq = max(0.15, jitter(0.33, 0.18))
        s = pg + vq + max(0.12, jitter(0.25, 0.18))
        pg, vq = pg / s, vq / s          # phần còn lại là Wallet
        paylater = min(0.6, max(0.1, jitter(0.30, 0.25)))
        merch = (mid, name, sub, app_id, pg, vq, paylater)

        wmult = PROFILE_WMULT[profile]
        for d in days:
            mon = d - timedelta(days=d.weekday())
            lvl = wmult[midx[mon]]
            txn = max(1, round(base_txn * lvl * dow_factor(d) * jitter(1.0, 0.02)))
            tpv = round(txn * aov * jitter(1.0, 0.01))
            rows.append((d, idx, merch, txn, tpv))

    # phẳng hóa thành dòng CSV (tách theo transaction type)
    out = []
    for d, _idx, merch, txn, tpv in rows:
        out.extend(split_rows(merch, d, txn, tpv))
    return out


def main():
    rows = build_rows()
    fields = ["Sub-cate", "Merchant id", "Merchant name", "App id", "Date",
              "TPV", "Transaction", "Transaction type", "SOF"]
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(fields)
        w.writerows(rows)
    print(f"OK: {OUT} | {len(MERCHANTS)} merchant | {DATA_START} -> {DATA_END} "
          f"| {len(rows)} dòng (đã tách theo Transaction type + SOF)")


if __name__ == "__main__":
    main()
