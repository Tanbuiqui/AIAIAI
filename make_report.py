"""Chạy lại tất cả câu hỏi đã test trong phiên lên endpoint deploy, đối chiếu với
số tính bằng code (ground truth), xuất REPORT-test-results.md.

Chạy: python make_report.py
"""
import json, base64, time, urllib.request
import pipeline as p

BASE = "https://endpoint-268d6ef8-5926-4ea2-b504-88118a19b760.agentbase-runtime.aiplatform.vngcloud.vn"
CSV = "merchant_performance_sample.csv"
csv_bytes = open(CSV, "rb").read()
b64 = base64.b64encode(csv_bytes).decode()
a = p.MerchantAnalyzer(p.load_dataframe(csv_bytes, CSV))

# ground truth bằng code
gt_pay = {s["name"]: s["tpv_fmt"] for s in a.payment()["sof"]}
gt_feb = a.month(question="tháng 2")["items"][0]["name"]
gt_bami = a.merchant(question="tiệm bánh mì 36")["revenue_proj_fmt"]
gt_growth = a.growth(period="month", top_n=1)["items"][0]["name"]
gt_wallet = max(a.digest(), key=lambda r: r["tpv_by_type"].get("Wallet", 0))["name"]

# (câu hỏi, intent mong đợi, hàm kiểm tra trên answer)
CASES = [
    ("Tổng quan tháng này", "overview", lambda s: "dự phóng" in s.lower() and "%" in s),
    ("Merchant nào giảm", "decline", lambda s: "giảm" in s.lower()),
    ("Top 5 tăng trưởng", "growth", lambda s: gt_growth in s),
    ("Ai tăng đều mỗi tuần?", "uptrend", lambda s: "tăng" in s.lower()),
    ("Nên chạy voucher cho ai?", "voucher", lambda s: "voucher" in s.lower() or "giữ chân" in s.lower()),
    ("Ai sắp churn?", "churn", lambda s: "churn" in s.lower()),
    ("Ai quan trọng đang lung lay?", "at_risk", lambda s: "nguy cơ" in s.lower() or "lung lay" in s.lower()),
    ("Vì sao Cafe Workspace giảm?", "decompose", lambda s: "Cafe Workspace" in s and ("giao dịch" in s.lower() or "AOV" in s)),
    ("Dự phóng cuối tháng có cao hơn tháng trước không?", "forecast", lambda s: ("cao hơn" in s.lower() or "thấp hơn" in s.lower())),
    ("Cơ cấu thanh toán", "payment", lambda s: gt_pay.get("Paylater", "x") in s),
    ("tổng doanh số của paylater", "payment", lambda s: gt_pay.get("Paylater", "x") in s),
    ("tiệm bánh mì 36 tổng doanh thu", "merchant", lambda s: gt_bami in s),
    ("doanh số tháng 3 và tháng 4 của Cafe Workspace", "merchant", lambda s: "2026-03" in s and "2026-04" in s),
    ("trong tháng 2/2026 merchant nào có TPV cao nhất", "month", lambda s: gt_feb in s),
    ("tháng 1 merchant nào cao nhất", "month", lambda s: "không có" in s.lower()),
    ("so sánh Cafe Workspace và Phở Bắc Hà", "freeform", lambda s: "Cafe Workspace" in s and "Phở Bắc Hà" in s),
    ("merchant nào dùng wallet nhiều nhất?", "freeform", lambda s: gt_wallet in s),
    ("ngành F&B đang thế nào?", "freeform", lambda s: len(s) > 40),
]


def ask(q):
    body = json.dumps({"question": q, "file_base64": b64}).encode()
    for _ in range(6):
        try:
            t0 = time.time()
            req = urllib.request.Request(BASE + "/invocations", data=body,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                j = json.loads(r.read().decode())
            return j.get("intent"), round(time.time() - t0, 1), (j.get("output") or j.get("error") or "")
        except urllib.error.HTTPError:
            time.sleep(15)
    return "ERR", 0, "(không gọi được)"


rows, npass = [], 0
for q, exp_intent, check in CASES:
    intent, lat, ans = ask(q)
    ok_intent = (intent == exp_intent)
    ok_ans = False
    try:
        ok_ans = bool(check(ans))
    except Exception:
        ok_ans = False
    verdict = "✅ ĐÚNG" if (ok_intent and ok_ans) else ("⚠️ XEM LẠI" if intent != "ERR" else "❌ LỖI")
    if ok_intent and ok_ans:
        npass += 1
    rows.append((q, exp_intent, intent, lat, verdict, ans.replace("\n", " ").strip()[:160]))
    print(f"[{verdict}] {lat:>4}s {intent:9s} {q[:40]}")

lines = [
    "# Báo cáo test agent — Merchant Growth Agent",
    "",
    f"- Endpoint: {BASE}",
    f"- Dữ liệu: {CSV} (40 merchant, tháng 2–6/2026)",
    f"- Kết quả: **{npass}/{len(CASES)} ĐÚNG**",
    "",
    "| # | Câu hỏi | Intent kỳ vọng | Intent thực | Thời gian | Kết quả |",
    "|---|---|---|---|---|---|",
]
for i, (q, ei, ai, lat, v, _ans) in enumerate(rows, 1):
    lines.append(f"| {i} | {q} | {ei} | {ai} | {lat}s | {v} |")
lines += ["", "## Trích câu trả lời", ""]
for i, (q, ei, ai, lat, v, ans) in enumerate(rows, 1):
    lines.append(f"**{i}. {q}** — {v} ({ai}, {lat}s)")
    lines.append(f"> {ans}")
    lines.append("")
open("REPORT-test-results.md", "w", encoding="utf-8").write("\n".join(lines))
print(f"\n=> {npass}/{len(CASES)} ĐÚNG. Report: REPORT-test-results.md")
