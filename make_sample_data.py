"""Sinh dữ liệu mẫu cho Merchant Growth Agent (Claw-a-thon 2026).

40 merchant x 8 tuan. Du lieu KHONG ngau nhien thuan tuy: moi merchant duoc gan
mot "profile" co chu dich de cac kich ban demo (giam manh / tang truong / churn /
voucher) deu co merchant khop. Seed co dinh -> tai tao duoc.

Chay:  python make_sample_data.py
Xuat:  merchant_performance_sample.csv  (UTF-8 co BOM)
"""

import csv
import random
from datetime import date, timedelta

SEED = 2026
OUT = "merchant_performance_sample.csv"
N_WEEKS = 8
CURRENT_MONDAY = date(2026, 6, 8)  # tuan hien tai (week_start lon nhat)

rng = random.Random(SEED)
# RNG rieng cho bien loi nhuan -> them cot nay KHONG lam xao tron stream chinh,
# nen toan bo gia tri da verify giu nguyen.
margin_rng = random.Random(SEED + 7)

# 8 tuan: thu Hai, lui dan tu CURRENT_MONDAY
WEEKS = [CURRENT_MONDAY - timedelta(weeks=(N_WEEKS - 1 - i)) for i in range(N_WEEKS)]

REGIONS = ["TP.HCM", "Hà Nội", "Đà Nẵng"]

# (ten, nganh hang, profile, size)  -- size: s/m/l doi base revenue
MERCHANTS = [
    # --- sharp_decline (4): giam manh tuan nay ---
    ("Cafe Workspace", "F&B", "sharp_decline", "m"),
    ("Tạp Hóa Cô Ba", "Tạp hóa", "sharp_decline", "s"),
    ("Trà Sữa Mây", "F&B", "sharp_decline", "m"),
    ("Shop Giày Bước Chân", "Thời trang", "sharp_decline", "m"),
    # --- voucher (2): doanh thu CAO nhung dang giam + khach quay lai giam ---
    ("Điện Tử Hoàng Gia", "Điện tử", "voucher", "l"),
    ("Siêu Thị Mini An Khang", "Tạp hóa", "voucher", "l"),
    # --- growth (6): tang truong tot ---
    ("Bánh Ngọt Sweet Home", "F&B", "growth", "m"),
    ("Thời Trang Lyla", "Thời trang", "growth", "m"),
    ("Phụ Kiện Tech Zone", "Khác", "growth", "s"),
    ("Quán Ăn Ngon Mỗi Ngày", "F&B", "growth", "l"),
    ("Mỹ Phẩm Glow", "Làm đẹp", "growth", "m"),
    ("Hoa Tươi Mỗi Sáng", "Khác", "growth", "s"),
    # --- churn_high_3wk (3): giam lien tuc >=3 tuan ---
    ("Nhà Sách Tri Thức", "Sách", "churn_high_3wk", "m"),
    ("Đồ Chơi Tuổi Thơ", "Khác", "churn_high_3wk", "s"),
    ("Quán Nhậu Bờ Kè", "F&B", "churn_high_3wk", "m"),
    # --- churn_high_crash (2): tuan nay sup < 70% TB 4 tuan truoc ---
    ("Điện Máy Sáng Tạo", "Điện tử", "churn_high_crash", "l"),
    ("Thời Trang Nam Phố", "Thời trang", "churn_high_crash", "m"),
    # --- churn_high_lowreturn (2): ty le quay lai < 25% va dang giam ---
    ("Quán Cơm Văn Phòng 247", "F&B", "churn_high_lowreturn", "m"),
    ("Cửa Hàng Tiện Lợi Góc Phố", "Tạp hóa", "churn_high_lowreturn", "s"),
    # --- churn_medium (3): dung 2 tuan giam lien tiep ---
    ("Trà Chanh Chém Gió", "F&B", "churn_medium", "s"),
    ("Giày Dép Thời Thượng", "Thời trang", "churn_medium", "m"),
    ("Phụ Kiện Điện Thoại Z", "Điện tử", "churn_medium", "s"),
    # --- stable/noise (18): phong nen ---
    ("Phở Bắc Hà", "F&B", "stable", "m"),
    ("Cơm Tấm Sài Gòn", "F&B", "stable", "m"),
    ("Bún Bò O Hue", "F&B", "stable", "s"),
    ("Thời Trang Công Sở Lady", "Thời trang", "stable", "m"),
    ("Cửa Hàng Mẹ Và Bé", "Khác", "stable", "m"),
    ("Nhà Thuốc An Tâm", "Khác", "stable", "l"),
    ("Quán Cà Phê Sân Vườn", "F&B", "stable", "m"),
    ("Tiệm Bánh Mì 36", "F&B", "stable", "s"),
    ("Shop Đồng Hồ Luxury", "Thời trang", "stable", "l"),
    ("Điện Thoại Di Động FPT Mini", "Điện tử", "stable", "l"),
    ("Tạp Hóa Bình Dân", "Tạp hóa", "stable", "s"),
    ("Mỹ Phẩm Hàn Quốc K-Beauty", "Làm đẹp", "stable", "m"),
    ("Quán Lẩu Nướng 9999", "F&B", "stable", "m"),
    ("Văn Phòng Phẩm Hồng Hà", "Sách", "stable", "s"),
    ("Đồ Gia Dụng Tiện Ích", "Khác", "stable", "m"),
    ("Trà Sữa Gong Gong", "F&B", "stable", "m"),
    ("Thời Trang Trẻ Em Cute", "Thời trang", "stable", "s"),
    ("Hải Sản Tươi Sống Biển Đông", "F&B", "stable", "l"),
]

# base revenue theo size (VND/tuan, xap xi)
SIZE_BASE = {"s": 18_000_000, "m": 55_000_000, "l": 140_000_000}
# base avg order value theo nganh (VND)
AOV_BY_CAT = {
    "F&B": 85_000, "Thời trang": 320_000, "Điện tử": 1_800_000,
    "Tạp hóa": 70_000, "Sách": 120_000, "Làm đẹp": 250_000, "Khác": 180_000,
}
# bien loi nhuan gop (gross margin) dien hinh theo nganh -> de phan biet
# "doanh thu cao" vs "loi nhuan cao" (vd dien tu doanh thu lon nhung bien mong).
MARGIN_BY_CAT = {
    "F&B": 0.62, "Thời trang": 0.55, "Điện tử": 0.18,
    "Tạp hóa": 0.24, "Sách": 0.35, "Làm đẹp": 0.60, "Khác": 0.42,
}


def jitter(x, pct):
    """nhieu nhe +/- pct quanh x."""
    return x * (1 + rng.uniform(-pct, pct))


def trajectory(profile):
    """Tra ve (rev_mult[8], ret_rate[8]) theo profile.

    rev_mult: he so doanh thu tuong doi (drive qua transaction_count).
    ret_rate: ty le khach quay lai moi tuan.
    """
    base_ret = rng.uniform(0.38, 0.50)

    if profile == "sharp_decline":
        mult = [jitter(1.0, 0.04) for _ in range(7)]
        mult.append(rng.uniform(0.65, 0.83))  # tuan nay giam 17-35%
        ret = [jitter(base_ret, 0.05) for _ in range(7)]
        ret.append(ret[6] * rng.uniform(0.80, 0.90))  # quay lai cung giam
        return mult, ret

    if profile == "voucher":  # nhu sharp_decline nhung gia tri cao
        mult = [jitter(1.0, 0.04) for _ in range(7)]
        mult.append(rng.uniform(0.70, 0.85))
        ret = [jitter(base_ret, 0.05) for _ in range(7)]
        ret.append(ret[6] * rng.uniform(0.78, 0.88))
        return mult, ret

    if profile == "growth":
        # tang don dieu: moi tuan nhan he so > 1 -> WoW luon duong, consec=0
        mult = [rng.uniform(0.80, 0.86)]
        for _ in range(7):
            mult.append(mult[-1] * rng.uniform(1.025, 1.06))
        ret = [min(0.7, base_ret + 0.012 * i) for i in range(8)]
        return mult, ret

    if profile == "churn_high_3wk":
        # 4 tuan dau on dinh, 3 tuan cuoi giam lien tiep nghiem ngat
        head = [jitter(1.0, 0.03) for _ in range(5)]  # w0..w4
        w5 = head[4] * rng.uniform(0.86, 0.90)
        w6 = w5 * rng.uniform(0.84, 0.90)
        w7 = w6 * rng.uniform(0.82, 0.90)
        mult = head + [w5, w6, w7]
        ret = [jitter(base_ret, 0.04) for _ in range(5)]
        ret += [ret[4] * 0.9, ret[4] * 0.82, ret[4] * 0.74]
        return mult, ret

    if profile == "churn_high_crash":
        mult = [jitter(1.0, 0.04) for _ in range(7)]
        mult.append(rng.uniform(0.45, 0.60))  # sup vs TB 4 tuan truoc
        ret = [jitter(base_ret, 0.05) for _ in range(7)]
        ret.append(ret[6] * rng.uniform(0.70, 0.82))
        return mult, ret

    if profile == "churn_high_lowreturn":
        # doanh thu hoi giam, ty le quay lai luon < 25% va giam dan
        mult = [jitter(1.0 - 0.015 * i, 0.03) for i in range(8)]
        start_ret = rng.uniform(0.235, 0.245)
        ret = [start_ret - 0.012 * i for i in range(8)]  # ket thuc ~0.16
        return mult, ret

    if profile == "churn_medium":
        # dung 2 tuan giam lien tiep cuoi: w4->w5 TANG, w5->w6 giam, w6->w7 giam
        head = [jitter(1.0, 0.03) for _ in range(5)]  # w0..w4
        w5 = head[4] * rng.uniform(1.04, 1.09)  # tang -> chan chuoi 3 tuan
        w6 = w5 * rng.uniform(0.88, 0.93)
        w7 = w6 * rng.uniform(0.86, 0.92)
        mult = head + [w5, w6, w7]
        ret = [jitter(base_ret, 0.04) for _ in range(8)]
        return mult, ret

    # stable
    mult = [jitter(1.0, 0.06) for _ in range(8)]
    ret = [jitter(base_ret, 0.05) for _ in range(8)]
    return mult, ret


def build_rows():
    rows = []
    for idx, (name, cat, profile, size) in enumerate(MERCHANTS):
        mid = f"M{idx + 1:03d}"
        region = REGIONS[idx % len(REGIONS)]
        base_rev = SIZE_BASE[size] * rng.uniform(0.85, 1.15)
        # AOV co dinh moi merchant (ve 1 lan) -> khong tao nhieu WoW gia tao;
        # trend doanh thu chi den tu mult (transaction_count).
        aov = max(10_000, round(jitter(AOV_BY_CAT[cat], 0.05)))
        base_txn = max(5, round(base_rev / aov))
        u_ratio = rng.uniform(0.58, 0.82)
        # bien loi nhuan co dinh moi merchant (rng rieng) ~ +/-15% quanh nen nganh
        margin = max(0.05, min(0.9, MARGIN_BY_CAT[cat] * margin_rng.uniform(0.85, 1.15)))

        mult, ret = trajectory(profile)
        for w in range(N_WEEKS):
            txn = max(1, round(base_txn * mult[w] * (1 + rng.uniform(-0.015, 0.015))))
            revenue = txn * aov
            unique = max(1, min(txn, round(txn * u_ratio * (1 + rng.uniform(-0.04, 0.04)))))
            rrate = min(0.95, max(0.0, ret[w]))
            returning = min(unique, round(unique * rrate))
            rows.append({
                "merchant_id": mid,
                "merchant_name": name,
                "category": cat,
                "region": region,
                "week_start": WEEKS[w].isoformat(),
                "transaction_count": txn,
                "revenue_vnd": revenue,
                "gross_profit_vnd": round(revenue * margin),
                "unique_customers": unique,
                "returning_customers": returning,
                "avg_order_value_vnd": aov,
            })
    return rows


def main():
    rows = build_rows()
    fields = ["merchant_id", "merchant_name", "category", "region", "week_start",
              "transaction_count", "revenue_vnd", "gross_profit_vnd",
              "unique_customers", "returning_customers", "avg_order_value_vnd"]
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"OK: {OUT} | {len(MERCHANTS)} merchant x {N_WEEKS} tuan = {len(rows)} dong")
    print(f"Tuan: {WEEKS[0].isoformat()} -> {WEEKS[-1].isoformat()} (hien tai)")


if __name__ == "__main__":
    main()
