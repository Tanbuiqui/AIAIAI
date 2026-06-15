# 🎬 Kịch bản video demo — Merchant Growth Agent (~2:50)

> Mục tiêu: thể hiện agent **hay & thông minh** — hiểu tiếng Việt tự nhiên, **dự phóng cuối tháng**,
> ưu tiên theo **giá trị nguy cơ mất**, **bóc tách nguyên nhân định lượng**, và **không bịa số**
> (mọi con số tính bằng code, LLM chỉ diễn giải).
>
> Yêu cầu BTC: video **< 3 phút**, thấy rõ tương tác hỏi–đáp + kết quả, xem được bằng `@vng.com.vn`.
> Tông giọng: tự tin, gọn, như một AM thật đang dùng. Gõ câu hỏi xong **chờ kết quả hiện** rồi mới nói điểm nhấn.

| Thời điểm | Màn hình (thao tác) | Lời thoại | 💡 Điểm nhấn |
|---|---|---|---|
| **0:00–0:12** | Tiêu đề agent | "Đây là **Merchant Growth Agent** — trợ lý phân tích merchant cho Account Manager. Thay vì ngồi Excel hàng giờ, tôi chỉ cần **hỏi bằng tiếng Việt**." | Định vị vấn đề + lời hứa |
| **0:12–0:40** | Kéo-thả `merchant_performance_sample.csv` → status hiện *40 merchant · 5 tháng*. **ZOOM vào biểu đồ đường**: rê chuột 1–2s lên 1 đường để bật tooltip, bấm toggle 1 ngành để lọc | "Đổ vào file giao dịch **theo ngày, 5 tháng**. Agent tự đọc, tự dựng **biểu đồ xu hướng** — rê chuột là thấy doanh số từng tuần, lọc theo ngành ngay. Chưa hỏi gì đã thấy bức tranh." | Tự nhận diện dữ liệu + **biểu đồ tương tác** (zoom lúc load) |
| **0:40–1:05** | Gõ **"Tổng quan tháng này"** → KPI dự phóng + pill tăng/giảm/churn | "Lưu ý: **tháng 6 chưa hết** — agent hiểu điều đó và **dự phóng cả tháng** từ nhịp độ hiện tại, kèm số đã đạt 15/30 ngày." | Biết tháng dang dở → **run-rate**, không so thô |
| **1:05–1:30** | Gõ **"Dự phóng cuối tháng có cao hơn tháng trước không?"** → verdict **CAO/THẤP HƠN** + top tăng/giảm | "Câu mà sếp nào cũng hỏi: **tháng này có cán đích không?** Agent trả lời thẳng — cao hơn hay thấp hơn tháng trước, và **ai đang kéo xuống**." | Trả lời câu hỏi kinh doanh thật, có kết luận |
| **1:30–1:52** | Gõ **"Ai sắp churn?"** → badge 🔴🟡 + lý do | "Cảnh báo churn **3 mức**, kèm **lý do định lượng**: giảm liên tục mấy tuần, hay sụp đột ngột." | Phân loại có quy tắc + giải thích |
| **1:52–2:15** | Gõ **"Ai quan trọng đang lung lay?"** → bảng *giá trị nguy cơ mất* | "Đây là chỗ agent **khôn**: không chỉ ai sắp rời, mà **ai đáng cứu nhất** — giao của rủi ro **× doanh số**. Ưu tiên đúng tiền, không chỉ đúng tên." | Ưu tiên theo *value at risk* |
| **2:15–2:38** | Gõ **"Vì sao Cafe Workspace giảm?"** → bóc tách số lượng × giá trị đơn + đề xuất | "Hỏi **vì sao**, agent **bóc tách** giảm do **ít giao dịch** hay **giá trị đơn thấp**, rồi **đề xuất hành động** cụ thể." | Root-cause + action |
| **2:38–2:50** | Cuộn nhanh các thẻ số liệu/biểu đồ; **zoom nhẹ vào số tăng xanh / giảm đỏ** | "Quan trọng nhất: **mọi con số do code tính, AI chỉ diễn giải — nên không bao giờ bịa số.** Từ hàng giờ phân tích xuống **vài giây**." | Chốt: chính xác + tiết kiệm thời gian |

## 3 câu "đắt" cần nói rõ
1. *"Agent hiểu tháng chưa hết và **dự phóng cuối tháng** — không so liều."*
2. *"Nó ưu tiên **merchant đáng cứu** theo giá trị nguy cơ mất, chứ không chỉ ai doanh thu cao."*
3. *"**Số tính bằng code, LLM chỉ diễn giải** → đáng tin, không hallucinate."*

## Bonus (nếu còn thời gian, chèn ~10s trước câu chốt)
- Gõ **"Merchant nào dùng Wallet nhiều nhất?"** (câu *tự do*, ngoài menu) → "Kể cả câu **ngoài kịch bản**, agent vẫn trả lời từ **đúng số đã tính**." (cần bản deploy có Qwen).

## Mẹo quay
- Quay trên **endpoint AgentBase thật** (có Qwen) → câu trả lời mượt + câu tự do mới chạy.
- **Lúc vừa load CSV: zoom vào biểu đồ**, rê chuột bật tooltip, toggle ngành → cho thấy biểu đồ sống động.
- Số tăng xanh / giảm đỏ tự tô màu — zoom nhẹ khi nói "không bịa số".
- Tắt thông báo Teams/mail, phóng to trình duyệt cho chữ rõ.

## Up video & lấy link
- **OneDrive (khớp `@vng.com.vn`):** upload MP4 → Share → "People in VNG Group" / nhập email `@vng.com.vn` → Copy link.
- **YouTube:** upload → Visibility = **Unlisted** → Copy link.
- Kiểm tra: < 3 phút · thấy rõ hỏi–đáp + kết quả · mở được bằng tài khoản `@vng.com.vn` khác.
