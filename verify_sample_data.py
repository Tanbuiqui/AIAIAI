"""Kiểm tra dữ liệu mẫu (schema mới) khớp các kịch bản demo — dùng chính pipeline.

Chạy sau make_sample_data.py:  python verify_sample_data.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import pipeline as p

CSV = "merchant_performance_sample.csv"
df = p.load_dataframe(open(CSV, "rb").read(), CSV)
a = p.MerchantAnalyzer(df)
M = a._metrics


def show(title, names, check):
    print(f"\n## {title}")
    ok = True
    for n in names:
        m = next((x for x in M.values() if x["name"] == n), None)
        if m is None:
            print(f"  [FAIL] {n:32s} (không thấy)")
            ok = False
            continue
        passed = check(m)
        ok = ok and passed
        print(f"  [{'OK ' if passed else 'FAIL'}] {n:30s} "
              f"MoM={m['mom']:+6.1f}%  WoW={m['wow']:+6.1f}%  consec={m['consec']}  "
              f"crash={int(m['crash'])}  churn={m['churn']}")
    return ok


allok = True
allok &= show("sharp_decline -> MoM giảm rõ",
              ["Cafe Workspace", "Tạp Hóa Cô Ba", "Trà Sữa Mây", "Shop Giày Bước Chân"],
              lambda m: m["mom"] < -5)
allok &= show("voucher -> giảm + doanh số cao",
              ["Điện Tử Hoàng Gia", "Siêu Thị Mini An Khang"],
              lambda m: m["mom"] < 0 and m["rev_proj"] > 200_000_000)
allok &= show("growth -> MoM tăng",
              ["Bánh Ngọt Sweet Home", "Thời Trang Lyla", "Phụ Kiện Tech Zone",
               "Quán Ăn Ngon Mỗi Ngày", "Mỹ Phẩm Glow", "Hoa Tươi Mỗi Sáng"],
              lambda m: m["mom"] > 5 and m["up_streak"] >= 3)
allok &= show("churn_high_3wk -> >=3 tuần giảm (Cao)",
              ["Nhà Sách Tri Thức", "Đồ Chơi Tuổi Thơ", "Quán Nhậu Bờ Kè"],
              lambda m: m["consec"] >= 3 and m["churn"] == "Cao")
allok &= show("churn_high_crash -> sụp <70% TB4 (Cao)",
              ["Điện Máy Sáng Tạo", "Thời Trang Nam Phố"],
              lambda m: m["crash"] and m["churn"] == "Cao")
allok &= show("churn_medium -> đúng 2 tuần giảm (TB)",
              ["Trà Chanh Chém Gió", "Giày Dép Thời Thượng", "Phụ Kiện Điện Thoại Z"],
              lambda m: m["consec"] == 2 and m["churn"] == "Trung bình")
allok &= show("stable -> đứng yên (|MoM| nhỏ)",
              ["Phở Bắc Hà", "Cơm Tấm Sài Gòn", "Shop Đồng Hồ Luxury"],
              lambda m: abs(m["mom"]) <= 6)

n_high = sum(1 for m in M.values() if m["churn"] == "Cao")
n_med = sum(1 for m in M.values() if m["churn"] == "Trung bình")
fc = a.forecast()
print(f"\n## Tổng quan: churn Cao={n_high} TB={n_med} | "
      f"dự phóng tháng {fc['change_pct']:+}% (cao hơn={fc['n_higher']} thấp hơn={fc['n_lower']})")
print("\n=> KẾT QUẢ:", "TẤT CẢ KHỚP" if allok else "CÓ NHÓM CHƯA KHỚP — chỉnh seed/profile")
