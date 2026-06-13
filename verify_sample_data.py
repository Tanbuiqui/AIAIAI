"""Kiem tra du lieu mau co khop cac kich ban demo khong (stdlib thuan).

Tai hien dung logic phan tich o spec muc 4 va xac nhan tung merchant cai cam
roi vao dung nhom mong doi. Chay sau make_sample_data.py.
"""

import csv
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

CSV = "merchant_performance_sample.csv"

rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
by_m = defaultdict(list)
for r in rows:
    by_m[r["merchant_id"]].append(r)

# sap xep theo tuan
for mid in by_m:
    by_m[mid].sort(key=lambda r: r["week_start"])

def series(recs, col):
    return [float(r[col]) for r in recs]

def ret_rate(r):
    u = float(r["unique_customers"])
    return float(r["returning_customers"]) / u if u else 0.0

results = {}
for mid, recs in by_m.items():
    name = recs[0]["merchant_name"]
    rev = series(recs, "revenue_vnd")
    wow = (rev[-1] - rev[-2]) / rev[-2] * 100  # % WoW tuan hien tai

    # so tuan giam lien tiep o cuoi chuoi
    consec = 0
    for i in range(len(rev) - 1, 0, -1):
        if rev[i] < rev[i - 1]:
            consec += 1
        else:
            break

    avg_prev4 = sum(rev[-5:-1]) / 4
    crash = rev[-1] < 0.7 * avg_prev4

    rr = [ret_rate(r) for r in recs]
    low_ret = rr[-1] < 0.25 and rr[-1] < rr[-4]

    # phan loai churn (spec 4.4)
    if consec >= 3 or crash or low_ret:
        churn = "Cao"
    elif consec == 2 or (rr[-1] < rr[-2] * 0.9):
        churn = "Trung binh"
    else:
        churn = "Thap"

    results[name] = dict(wow=wow, consec=consec, crash=crash,
                         low_ret=low_ret, rr_now=rr[-1], churn=churn,
                         rev_now=rev[-1])

def show(title, names, check):
    print(f"\n## {title}")
    ok = True
    for n in names:
        r = results[n]
        passed = check(r)
        ok = ok and passed
        mark = "OK " if passed else "FAIL"
        print(f"  [{mark}] {n:32s} WoW={r['wow']:+6.1f}%  consec={r['consec']}  "
              f"crash={int(r['crash'])}  rr={r['rr_now']:.2f}  churn={r['churn']}")
    return ok

allok = True
allok &= show("sharp_decline -> WoW am ro ret (4.1)",
     ["Cafe Workspace", "Tạp Hóa Cô Ba", "Trà Sữa Mây", "Shop Giày Bước Chân"],
     lambda r: r["wow"] <= -12)

allok &= show("voucher -> giam + gia tri cao (4.3)",
     ["Điện Tử Hoàng Gia", "Siêu Thị Mini An Khang"],
     lambda r: r["wow"] < 0 and r["rev_now"] > 50_000_000)

allok &= show("growth -> WoW duong (4.2)",
     ["Bánh Ngọt Sweet Home", "Thời Trang Lyla", "Phụ Kiện Tech Zone",
      "Quán Ăn Ngon Mỗi Ngày", "Mỹ Phẩm Glow", "Hoa Tươi Mỗi Sáng"],
     lambda r: r["wow"] > 0)

allok &= show("churn_high_3wk -> >=3 tuan giam (4.4 Cao)",
     ["Nhà Sách Tri Thức", "Đồ Chơi Tuổi Thơ", "Quán Nhậu Bờ Kè"],
     lambda r: r["consec"] >= 3 and r["churn"] == "Cao")

allok &= show("churn_high_crash -> sup <70% TB4 (4.4 Cao)",
     ["Điện Máy Sáng Tạo", "Thời Trang Nam Phố"],
     lambda r: r["crash"] and r["churn"] == "Cao")

allok &= show("churn_high_lowreturn -> rr<25% giam (4.4 Cao)",
     ["Quán Cơm Văn Phòng 247", "Cửa Hàng Tiện Lợi Góc Phố"],
     lambda r: r["low_ret"] and r["churn"] == "Cao")

allok &= show("churn_medium -> dung 2 tuan giam (4.4 TB)",
     ["Trà Chanh Chém Gió", "Giày Dép Thời Thượng", "Phụ Kiện Điện Thoại Z"],
     lambda r: r["consec"] == 2)

# thong ke tong
n_high = sum(1 for r in results.values() if r["churn"] == "Cao")
n_med = sum(1 for r in results.values() if r["churn"] == "Trung binh")
n_decline = sum(1 for r in results.values() if r["wow"] < 0)
n_growth = sum(1 for r in results.values() if r["wow"] > 0)
print(f"\n## Tong quan: churn Cao={n_high}  TB={n_med}  | WoW giam={n_decline}  tang={n_growth}")

# --- kiem tra cot loi nhuan ---
profit_ok = True
cat_margin = defaultdict(list)
for r in rows:
    rev = float(r["revenue_vnd"])
    gp = float(r["gross_profit_vnd"])
    if not (0 < gp < rev):  # loi nhuan gop phai duong va nho hon doanh thu
        profit_ok = False
    cat_margin[r["category"]].append(gp / rev if rev else 0)
allok &= profit_ok
print(f"\n## Loi nhuan: gross_profit hop le (0 < gp < revenue) = {profit_ok}")
print("   Bien loi nhuan TB theo nganh:")
for cat in sorted(cat_margin):
    m = sum(cat_margin[cat]) / len(cat_margin[cat])
    print(f"     {cat:12s} {m*100:5.1f}%")
# vi du: doanh thu cao != loi nhuan cao
top_rev = sorted(results.items(), key=lambda kv: -kv[1]["rev_now"])[:5]
print("   Top 5 doanh thu tuan nay (de doi chieu voi loi nhuan o backend):")
for n, r in top_rev:
    print(f"     {n:32s} rev={r['rev_now']:>14,.0f}")
print("\n=> KET QUA:", "TAT CA KHOP" if allok else "CO NHOM CHUA KHOP - can chinh seed/profile")
