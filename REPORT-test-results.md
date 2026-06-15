# Báo cáo test agent — Merchant Growth Agent

- Endpoint: https://endpoint-268d6ef8-5926-4ea2-b504-88118a19b760.agentbase-runtime.aiplatform.vngcloud.vn
- Dữ liệu: merchant_performance_sample.csv (40 merchant, tháng 2–6/2026)
- Kết quả: **18/18 ĐÚNG**

| # | Câu hỏi | Intent kỳ vọng | Intent thực | Thời gian | Kết quả |
|---|---|---|---|---|---|
| 1 | Tổng quan tháng này | overview | overview | 0.7s | ✅ ĐÚNG |
| 2 | Merchant nào giảm | decline | decline | 0.7s | ✅ ĐÚNG |
| 3 | Top 5 tăng trưởng | growth | growth | 0.8s | ✅ ĐÚNG |
| 4 | Ai tăng đều mỗi tuần? | uptrend | uptrend | 0.7s | ✅ ĐÚNG |
| 5 | Nên chạy voucher cho ai? | voucher | voucher | 0.7s | ✅ ĐÚNG |
| 6 | Ai sắp churn? | churn | churn | 0.7s | ✅ ĐÚNG |
| 7 | Ai quan trọng đang lung lay? | at_risk | at_risk | 0.7s | ✅ ĐÚNG |
| 8 | Vì sao Cafe Workspace giảm? | decompose | decompose | 0.7s | ✅ ĐÚNG |
| 9 | Dự phóng cuối tháng có cao hơn tháng trước không? | forecast | forecast | 0.7s | ✅ ĐÚNG |
| 10 | Cơ cấu thanh toán | payment | payment | 0.7s | ✅ ĐÚNG |
| 11 | tổng doanh số của paylater | payment | payment | 0.7s | ✅ ĐÚNG |
| 12 | tiệm bánh mì 36 tổng doanh thu | merchant | merchant | 0.7s | ✅ ĐÚNG |
| 13 | doanh số tháng 3 và tháng 4 của Cafe Workspace | merchant | merchant | 0.6s | ✅ ĐÚNG |
| 14 | trong tháng 2/2026 merchant nào có TPV cao nhất | month | month | 0.7s | ✅ ĐÚNG |
| 15 | tháng 1 merchant nào cao nhất | month | month | 0.7s | ✅ ĐÚNG |
| 16 | so sánh Cafe Workspace và Phở Bắc Hà | freeform | freeform | 1.6s | ✅ ĐÚNG |
| 17 | merchant nào dùng wallet nhiều nhất? | freeform | freeform | 2.5s | ✅ ĐÚNG |
| 18 | ngành F&B đang thế nào? | freeform | freeform | 3.2s | ✅ ĐÚNG |

## Trích câu trả lời

**1. Tổng quan tháng này** — ✅ ĐÚNG (overview, 0.7s)
> **Tháng 2026-06 (dự phóng cuối tháng)**: tổng doanh số **10.881.471.008 đ** (giảm **-5.5%** vs tháng trước (dự phóng)). - Đã đạt đến nay: **5.440.735.504 đ** (1

**2. Merchant nào giảm** — ✅ ĐÚNG (decline, 0.7s)
> **16** merchant giảm doanh số (tháng). Sắp theo mức giảm:  | Merchant | Ngành | Thay đổi | Giao dịch | Giá trị đơn | Churn | |---|---|---|---|---|---| | Thời Tr

**3. Top 5 tăng trưởng** — ✅ ĐÚNG (growth, 0.8s)
> **Top 5 tăng trưởng** (tháng):  | # | Merchant | Ngành | Doanh số | % tăng | |---|---|---|---|---| | 1 | Hoa Tươi Mỗi Sáng | Others | 99.558.238 đ | **+12.2%** 

**4. Ai tăng đều mỗi tuần?** — ✅ ĐÚNG (uptrend, 0.7s)
> **6** merchant tăng đều (xếp theo số tuần tăng liên tiếp & mức tăng cả kỳ):  | # | Merchant | Ngành | Tăng liên tiếp | Tăng cả kỳ | Doanh số tuần | |---|---|---

**5. Nên chạy voucher cho ai?** — ✅ ĐÚNG (voucher, 0.7s)
> **10** merchant nên chạy chương trình giữ chân (ưu tiên theo doanh số):  - **Điện Tử Hoàng Gia** (Electronics, doanh số 559.826.700 đ) — thay đổi -13.4%, churn 

**6. Ai sắp churn?** — ✅ ĐÚNG (churn, 0.7s)
> Cảnh báo churn: **5** Cao 🔴, **11** Trung bình 🟡. Danh sách ưu tiên:  - 🔴 Cao **Thời Trang Nam Phố** (Fashion) — WoW -45.8%; tuần này sụp <70% trung bình 4 tuần

**7. Ai quan trọng đang lung lay?** — ✅ ĐÚNG (at_risk, 0.7s)
> **Merchant quan trọng đang lung lay** — ưu tiên cứu theo *giá trị có nguy cơ mất* (doanh số dự phóng tháng × trọng số rủi ro):  | # | Merchant | Doanh số dự phó

**8. Vì sao Cafe Workspace giảm?** — ✅ ĐÚNG (decompose, 0.7s)
> **Cafe Workspace** giảm **-17.3%** doanh số (tháng). Bóc tách động lực:  - **Số lượng giao dịch:** -17.3% → đóng góp ~-17.3% doanh số - **Giá trị đơn (AOV):** +

**9. Dự phóng cuối tháng có cao hơn tháng trước không?** — ✅ ĐÚNG (forecast, 0.7s)
> Dự phóng cuối tháng 2026-06: tổng doanh số **10.881.471.008 đ** — **THẤP HƠN ⚠️** tháng trước (**11.900.379.807 đ**), thay đổi **-5.5%**.  - Đã đạt 15/30 ngày: 

**10. Cơ cấu thanh toán** — ✅ ĐÚNG (payment, 0.7s)
> **Cơ cấu thanh toán** — tổng TPV **49.933.579.853 đ** (toàn kỳ dữ liệu):  | Kênh | TPV | Giao dịch | % tổng | |---|---|---|---| | Payment Gateway | 20.889.281.6

**11. tổng doanh số của paylater** — ✅ ĐÚNG (payment, 0.7s)
> **Cơ cấu thanh toán** — tổng TPV **49.933.579.853 đ** (toàn kỳ dữ liệu):  | Kênh | TPV | Giao dịch | % tổng | |---|---|---|---| | Payment Gateway | 20.889.281.6

**12. tiệm bánh mì 36 tổng doanh thu** — ✅ ĐÚNG (merchant, 0.7s)
> **Tiệm Bánh Mì 36** (Bakery & Dessert) — tình hình:  - 💰 Dự phóng cuối tháng: **73.620.702 đ** (-1.0% vs tháng trước) - Đã đạt tháng này: 36.810.351 đ · tháng t

**13. doanh số tháng 3 và tháng 4 của Cafe Workspace** — ✅ ĐÚNG (merchant, 0.6s)
> **Cafe Workspace** (Coffee & Tea) — tình hình:  - 💰 Dự phóng cuối tháng: **204.325.682 đ** (-17.3% vs tháng trước) - Đã đạt tháng này: 102.162.841 đ · tháng trư

**14. trong tháng 2/2026 merchant nào có TPV cao nhất** — ✅ ĐÚNG (month, 0.7s)
> **Top 10 merchant theo TPV — tháng 2026-02** (tổng 10.057.047.383 đ, 40 merchant):  | # | Merchant | Ngành | TPV | |---|---|---|---| | 1 | Shop Đồng Hồ Luxury |

**15. tháng 1 merchant nào cao nhất** — ✅ ĐÚNG (month, 0.7s)
> Không có dữ liệu cho tháng **2026-01**. Các tháng có sẵn: 2026-02, 2026-03, 2026-04, 2026-05, 2026-06.

**16. so sánh Cafe Workspace và Phở Bắc Hà** — ✅ ĐÚNG (freeform, 1.6s)
> Phở Bắc Hà vận hành ổn định hơn Cafe Workspace với dự phóng doanh thu tháng này cao hơn (**220.6M** vs **204.3M**) và rủi ro rời bỏ Thấp.  *   **Tăng trưởng (Mo

**17. merchant nào dùng wallet nhiều nhất?** — ✅ ĐÚNG (freeform, 2.5s)
> Merchant dùng Wallet nhiều nhất là **Quán Ăn Ngon Mỗi Ngày** với tổng doanh số Wallet đạt **905.622.131**.  *   **Quán Ăn Ngon Mỗi Ngày**: 905.622.131 *   **Điệ

**18. ngành F&B đang thế nào?** — ✅ ĐÚNG (freeform, 3.2s)
> Ngành F&B (Restaurant, Coffee & Tea, Bakery & Dessert) có sự phân hóa mạnh: nhóm quy mô lớn tăng trưởng tốt, nhóm nhỏ sụt giảm.  *   **Tăng trưởng:** Bánh Ngọt 
