# SPEC KIT — Merchant Growth Agent

> Spec cho Claude Code build agent dự thi Claw-a-thon 2026.
> Track: **Data Analysis** · Có web view · Model runtime: **Qwen (MaaS)** · Runtime size: 2×4 (nâng 4×4 nếu file lớn).

---

## 1. Tổng quan

**Tên agent:** Merchant Growth Agent
**Tagline:** Trợ lý phân tích merchant cho Account Manager — hỏi bằng tiếng Việt, nhận insight và đề xuất hành động.

**Problem:** Account Manager / Sales phải tự mở Excel, lọc, tính toán để biết merchant nào đang giảm, ai cần chăm sóc, ai sắp rời bỏ. Tốn thời gian, dễ bỏ sót, không kịp hành động.

**User:** Account Manager / Sales quản lý danh mục merchant.

**Solution:** Một trợ lý chat. User đổ file dữ liệu giao dịch merchant vào, hỏi tự nhiên, agent tự phân tích bằng code và trả lời kèm **số liệu + nguyên nhân + đề xuất hành động cụ thể**.

**Value:** Giảm thời gian phân tích từ hàng giờ xuống vài giây; phát hiện sớm merchant churn/giảm để can thiệp kịp; chuẩn hóa cách ra quyết định chăm sóc merchant.

---

## 2. Phạm vi (Scope)

**Trong phạm vi (v1 — bản dự thi):**
- Upload 1 file CSV/Excel dữ liệu giao dịch merchant.
- Hỏi-đáp bằng tiếng Việt qua giao diện chat web.
- 7 nhóm phân tích: tổng quan danh mục, phát hiện giảm, xếp hạng tăng trưởng, gợi ý voucher (theo lợi nhuận), cảnh báo churn 3 mức, merchant quan trọng đang lung lay (churn × lợi nhuận), bóc tách nguyên nhân tăng/giảm.
- Trả lời có số liệu chính xác (tính bằng code) + diễn giải + đề xuất.

**Ngoài phạm vi (không làm ở v1):**
- Kết nối hệ thống production / database thật của công ty (BỊ CẤM theo thể lệ).
- Dữ liệu khách hàng thật / PII (BỊ CẤM — chỉ dùng dữ liệu mẫu/ẩn danh).
- Đăng nhập đa người dùng, phân quyền, lưu lịch sử dài hạn.
- Tự động gửi email/notification (có thể nêu là hướng mở rộng).

---

## 3. Dữ liệu đầu vào

**File:** `merchant_performance_sample.csv` (dữ liệu giả lập, UTF-8).
**Đơn vị thời gian:** theo tuần. Tuần `week_start` lớn nhất = "tuần này / tuần hiện tại".

**Schema:**

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `merchant_id` | string | Mã merchant (vd M001) |
| `merchant_name` | string | Tên merchant |
| `category` | string | Ngành hàng (F&B, Thời trang, Điện tử...) |
| `region` | string | Khu vực (TP.HCM, Hà Nội...) |
| `week_start` | date (YYYY-MM-DD) | Thứ Hai đầu tuần |
| `transaction_count` | int | Số giao dịch trong tuần |
| `revenue_vnd` | int | Doanh thu trong tuần (VND) |
| `gross_profit_vnd` | int | Lợi nhuận gộp trong tuần (VND) — biên theo ngành |
| `unique_customers` | int | Số khách duy nhất trong tuần |
| `returning_customers` | int | Số khách quay lại (đã mua tuần trước đó) |
| `avg_order_value_vnd` | int | Giá trị đơn trung bình (VND) |

**Quy tắc đọc file:**
- Agent phải tự nhận diện schema; nếu thiếu cột thì báo rõ thay vì đoán.
- Hỗ trợ cả `.csv` và `.xlsx`. Encoding UTF-8 (có BOM).
- Tính các chỉ số phái sinh:
  - Tỷ lệ khách quay lại = `returning_customers / unique_customers`.
  - Biên lợi nhuận = `gross_profit_vnd / revenue_vnd` (phân biệt "doanh thu cao" vs "lợi nhuận cao": vd Điện tử biên ~19%, F&B/Làm đẹp ~60%).
  - Khách mới (ước lượng) = `unique_customers − returning_customers`.

### 3.1. Thiết kế dữ liệu mẫu (BẮT BUỘC làm trước khi code logic)

> Logic churn cần ≥3 tuần giảm liên tiếp & so trung bình 4 tuần → **phải có ≥8 tuần dữ liệu**. Dữ liệu **không** được sinh thuần ngẫu nhiên, mà phải **cài cắm có chủ đích** để mỗi kịch bản demo đều có merchant khớp.

- **Quy mô:** 40 merchant × 8 tuần (week_start: Thứ Hai, từ ~21/04 đến 08/06/2026; "tuần hiện tại" = 08/06).
- **Phân bố:** trộn category (F&B, Thời trang, Điện tử, Tạp hóa, Sách...) và region (TP.HCM, Hà Nội, Đà Nẵng).
- **Các nhóm cài cắm sẵn (mỗi nhóm vài merchant):**
  - **Giảm mạnh tuần này** (cho 4.1): WoW revenue âm rõ rệt (−15%…−35%), kèm transaction_count và tỷ lệ quay lại cũng giảm → để diễn giải nguyên nhân.
  - **Tăng trưởng tốt** (cho 4.2): WoW dương ổn định, vài merchant tăng vọt để lên top.
  - **Churn risk Cao** (cho 4.4): ≥3 tuần giảm liên tiếp HOẶC tuần này < 70% trung bình 4 tuần trước HOẶC tỷ lệ quay lại < 25% và giảm.
  - **Churn risk Trung bình:** đúng 2 tuần giảm liên tiếp.
  - **Voucher mục tiêu** (cho 4.3): merchant doanh thu cao (giá trị lớn) nhưng đang giảm + tỷ lệ quay lại giảm.
  - **Nhóm ổn định/nhiễu:** dao động nhẹ quanh mức nền → làm "phông nền" cho phân tích thật.
- **Tính nhất quán nội tại:** `revenue_vnd = transaction_count × avg_order_value_vnd`; `0 < gross_profit_vnd < revenue_vnd` (biên theo ngành); `returning_customers ≤ unique_customers`.
- **Tên merchant tiếng Việt** gợi nhớ (vd: Nhà Sách Tri Thức, Cafe Workspace, Tạp Hóa Cô Ba, Điện Tử Hoàng Gia...) để demo sinh động.
- **Artifact (ĐÃ TẠO & VERIFY):**
  - `make_sample_data.py` — sinh dữ liệu, seed cố định `2026` (margin dùng RNG riêng → tái tạo được).
  - `merchant_performance_sample.csv` — 40 merchant × 8 tuần × **11 cột** = 320 dòng, UTF-8 BOM.
  - `verify_sample_data.py` — tái hiện logic mục 4, xác nhận mọi nhóm cài cắm khớp (giảm/tăng/churn Cao×3 dạng/churn TB/voucher) + tính hợp lệ lợi nhuận. Đã chạy: **TẤT CẢ KHỚP** (8 churn Cao, 11 TB; 23 giảm / 16 tăng tuần hiện tại).

---

## 4. Yêu cầu chức năng (7 nhóm phân tích)

> **NGUYÊN TẮC VÀNG:** Mọi con số phải được **tính bằng code thật** (pandas hoặc tương đương). Model LLM chỉ diễn giải kết quả đã tính thành câu trả lời + đề xuất. **Model KHÔNG được tự tính nhẩm hay bịa số.**

### 4.1. Phát hiện merchant giảm doanh số ("tuần này")
- Tính **% thay đổi doanh thu tuần hiện tại so với tuần liền trước** (WoW) cho từng merchant.
- Liệt kê merchant có WoW âm, sắp xếp giảm dần mức độ.
- Với mỗi merchant giảm, tính thêm nguyên nhân khả dĩ: thay đổi `transaction_count` (WoW), thay đổi tỷ lệ khách quay lại (WoW), thay đổi `avg_order_value`.
- **Output mẫu:** "Merchant ABC giảm 18% doanh thu tuần qua. Nguyên nhân: tần suất giao dịch giảm 15%, tỷ lệ khách quay lại giảm 12%."

### 4.2. Xếp hạng tăng trưởng
- Top N (mặc định 10) merchant theo % tăng doanh thu WoW.
- Cho phép hỏi theo khoảng thời gian khác (vd so với 4 tuần trước) nếu user yêu cầu.
- Hiển thị dạng bảng: hạng, tên, doanh thu, % tăng.

### 4.3. Gợi ý chạy voucher
Quy tắc đề xuất voucher (tính bằng code):
- Merchant có doanh thu giảm WoW **và** tỷ lệ khách quay lại giảm → đề xuất voucher giữ chân.
- Đề xuất cụ thể theo mẫu: "Voucher [mệnh giá] cho khách inactive > 30 ngày" + "Push notification giờ cao điểm".
- **Ưu tiên theo lợi nhuận, không chỉ doanh thu:** ưu tiên merchant **lợi nhuận gộp cao** đang giảm. Cảnh báo khi đề xuất giảm giá cho merchant **biên lợi nhuận mỏng** (vd điện tử ~19%) vì voucher dễ ăn vào lãi; nhóm này nên dùng push/loyalty thay vì giảm giá sâu.

### 4.4. Cảnh báo churn
Quy tắc xác định nguy cơ churn (tính bằng code, gán mức Cao/Trung bình/Thấp):
- **Cao:** doanh thu giảm liên tục ≥ 3 tuần gần nhất, HOẶC tuần hiện tại giảm > 30% so với trung bình 4 tuần trước, HOẶC tỷ lệ khách quay lại < 25% và đang giảm.
- **Trung bình:** giảm 2 tuần liên tiếp, hoặc tỷ lệ khách quay lại giảm đáng kể.
- **Thấp:** còn lại.
- Output: danh sách merchant churn risk Cao kèm lý do định lượng + đề xuất hành động.

### 4.5. Tổng quan danh mục (Portfolio overview)
> Màn hình mở đầu / câu hỏi "tuần này danh mục thế nào". Cho AM bức tranh trước khi đào sâu.
- Cho **tuần hiện tại vs tuần liền trước**, tính (bằng code):
  - Tổng `revenue_vnd` và tổng `gross_profit_vnd` toàn danh mục + % WoW.
  - Số merchant **tăng / giảm / churn risk Cao**.
  - **Top mover**: 2–3 merchant tăng mạnh nhất & giảm mạnh nhất (theo % WoW doanh thu).
- (Tùy chọn) phân rã nhanh theo `category` hoặc `region`: ngành/khu vực nào kéo lên, đè xuống.
- **Output:** 1 đoạn tóm tắt + vài số nổi bật in đậm. Gợi ý chạy ngay sau khi upload file.

### 4.6. Merchant quan trọng đang lung lay (High-value-at-risk)
> Câu hỏi cốt tử của AM: "không cứu tất cả — cứu đúng merchant ĐÁNG tiền."
- Lấy **giao** của: churn risk (Cao, có thể gồm cả Trung bình) **và** lợi nhuận gộp lớn.
- Sắp xếp theo **"giá trị có nguy cơ mất"** ≈ lợi nhuận gộp gần đây (vd tổng 4 tuần) × trọng số mức rủi ro (Cao > TB).
- Lưu ý cột lợi nhuận: ưu tiên theo `gross_profit_vnd`, KHÔNG chỉ doanh thu (merchant biên mỏng dù doanh thu lớn thì giá trị mất thật sự nhỏ hơn).
- **Output:** danh sách ưu tiên cứu — mỗi dòng: tên, lợi nhuận gộp, mức churn, lý do định lượng, đề xuất giữ chân.

### 4.7. Bóc tách nguyên nhân tăng/giảm (Revenue decomposition)
> Trả lời "giảm/tăng VÌ SAO" theo 3 động lực → mỗi nguyên nhân ra một hành động marketing khác nhau.
- Cho 1 merchant (hoặc nhóm) đang thay đổi, tách WoW doanh thu thành 3 hiệu ứng (tính bằng code):
  - **Số lượng** (`transaction_count` WoW) — traffic / lượt mua.
  - **Giá trị đơn** (`avg_order_value_vnd` WoW) — kích cỡ giỏ hàng.
  - **Giữ chân** (tỷ lệ khách quay lại WoW) — chất lượng/độ trung thành của khách.
- Ước lượng đóng góp mỗi yếu tố: `ΔRevenue ≈ Δtxn × AOV + txn × ΔAOV` (phần dư gán nhiễu/khách).
- **Map nguyên nhân → hành động:** txn giảm → kéo traffic / ads / khuyến mãi tiếp cận; AOV giảm → bán kèm / upsell / combo; tỷ lệ quay lại giảm → loyalty / CSKH / win-back.
- **Output mẫu:** "Giảm 18% = −12% do ít giao dịch hơn, −6% do đơn nhỏ hơn → ưu tiên kéo traffic, chưa cần lo giá."

### 4.8. Hỏi-đáp tự do
- User hỏi tự nhiên bằng tiếng Việt; agent map câu hỏi vào các phân tích trên (hoặc kết hợp), tính toán, rồi trả lời.
- Ví dụ câu hỏi: "Merchant nào ở TP.HCM giảm mạnh nhất tuần này?", "So sánh F&B với Thời trang về tăng trưởng", "Top 5 cần chăm sóc gấp".

---

## 5. Định dạng câu trả lời

Mỗi câu trả lời phân tích nên có cấu trúc:
1. **Kết luận ngắn** (1 câu, có số liệu in đậm).
2. **Số liệu chi tiết** — bảng nếu là danh sách/xếp hạng.
3. **Nguyên nhân** — gạch đầu dòng định lượng.
4. **Đề xuất hành động** — cụ thể, làm được ngay.

Yêu cầu trình bày: số liệu in đậm; bảng xếp hạng gọn; badge màu cho mức churn (Cao = đỏ, Trung bình = vàng); ngôn ngữ tiếng Việt, súc tích, giọng tư vấn.

---

## 6. Giao diện web (UI)

**Mục tiêu:** đẹp, hiện đại, dễ dùng — 1 màn hình, không cần hướng dẫn.

**Bố cục:**
- **Thanh trên:** tên agent + nút **Upload CSV/Excel** (kéo-thả được). Hiện trạng thái file đã nạp (số merchant, số tuần, tuần hiện tại).
- **Khu giữa:** khung chat hội thoại (tin nhắn user phải, agent trái).
- **Chip gợi ý sẵn** (bấm là gửi luôn): "Tổng quan tuần này", "Merchant nào giảm tuần này?", "Top 10 tăng trưởng", "Ai sắp churn?", "Ai quan trọng đang lung lay?", "Nên chạy voucher cho ai?".
- **Render câu trả lời:** hỗ trợ bảng, in đậm số liệu, badge cảnh báo màu.

**Trải nghiệm:** loading khi đang phân tích; báo lỗi rõ ràng nếu file sai định dạng; responsive cơ bản.

---

## 7. Kiến trúc kỹ thuật

- **Backend (phân tích + API):** đọc CSV/Excel (pandas), thực hiện toàn bộ tính toán ở mục 4, expose API nhận câu hỏi + trả về kết quả đã tính.
- **Tầng LLM (Qwen qua MaaS) — luồng 2 lượt gọi:**
  1. **Intent routing (LLM lượt 1):** nhận câu hỏi tiếng Việt → LLM trả về **JSON** `{intent, params}` (xem schema dưới). Code đọc JSON, **switch-case tự gọi đúng hàm phân tích** trong backend. *Không phụ thuộc native tool/function calling của model* — chỉ cần model trả JSON đúng định dạng (ép bằng prompt + ví dụ few-shot + parse có fallback).
  2. **Diễn giải (LLM lượt 2):** code chạy hàm phân tích → ra **số liệu đã tính** → đưa số liệu này (không phải raw CSV) cho LLM để diễn giải thành câu trả lời + đề xuất hành động.
- **Frontend:** giao diện chat web như mục 6, gọi API backend.
- **Đóng gói & deploy:** qua bộ skill AgentBase (Docker build & push tự động), lấy endpoint public.

> **Vì sao intent-routing thay vì tool-calling:** Qwen qua MaaS GreenNode chưa đảm bảo hỗ trợ native function calling ổn định qua API OpenAI-compatible. Để LLM tự trả JSON intent rồi code tự dispatch là cách an toàn, không phụ thuộc khả năng tool của model, và dễ debug.

### Intent schema (LLM lượt 1 phải trả đúng)
```json
{
  "intent": "overview | decline | growth | voucher | churn | at_risk | decompose | freeform | unknown",
  "params": {
    "region": "TP.HCM | Hà Nội | null",
    "category": "F&B | Thời trang | ... | null",
    "top_n": 10,
    "merchant_name": "null"
  }
}
```
- `intent` map 1-1 vào các hàm: `overview`→4.5, `decline`→4.1, `growth`→4.2, `voucher`→4.3, `churn`→4.4, `at_risk`→4.6, `decompose`→4.7 (cần `merchant_name` hoặc nhóm), `freeform`→tổng hợp/4.8.
- Parse fail hoặc `unknown` → trả câu hỏi gợi ý lại + các chip mẫu (không crash).

**Chống bịa số:** LLM **không** nhận raw CSV để tự suy luận; lượt 1 chỉ phân loại ý định, lượt 2 chỉ nhận **kết quả số đã được code tính sẵn** rồi diễn giải.

### State giữ file đã upload
- Lưu DataFrame **in-memory theo session** (dict keyed theo session_id, sinh khi upload). Đủ cho demo 1 người dùng.
- ⚠️ AgentBase có thể restart/scale container → state mất. **Ràng buộc demo:** upload file rồi hỏi liền trong **cùng phiên**; nếu mất state, agent báo "chưa có dữ liệu, hãy upload lại" thay vì crash.
- Không ghi file khách lên đĩa lâu dài (tránh PII residue); xử lý in-memory.

---

## 8. Model & Runtime

- **Model runtime:** Qwen (MaaS) — mạnh lý luận/phân tích, tiếng Việt tốt. Cấu hình lúc deploy qua bộ skill.
- **Runtime size:** 2×4 (đủ cho file mẫu); cân nhắc 4×4 nếu mở rộng dữ liệu lớn.
- **Build tool:** Claude Code (tài khoản Max cá nhân) — khai báo trong README theo FAQ rulebook.

---

## 9. Tiêu chí nghiệm thu (Acceptance / khớp tiêu chí PASS)

- [ ] Upload file mẫu → agent xác nhận đã nạp (số merchant, số tuần).
- [ ] Hỏi "tổng quan tuần này" → tổng doanh thu/lợi nhuận + % WoW + số merchant tăng/giảm + top mover.
- [ ] Hỏi "merchant nào giảm tuần này" → trả về danh sách đúng + % WoW + nguyên nhân định lượng.
- [ ] Hỏi "ai quan trọng đang lung lay" → danh sách churn risk × lợi nhuận cao, ưu tiên theo giá trị có nguy cơ mất.
- [ ] Hỏi "vì sao [merchant] giảm" → bóc tách số lượng / giá trị đơn / giữ chân + hành động tương ứng.
- [ ] Hỏi "top 10 tăng trưởng" → bảng xếp hạng đúng theo dữ liệu.
- [ ] Hỏi "ai sắp churn" → danh sách churn risk Cao + lý do + đề xuất.
- [ ] Hỏi "nên chạy voucher cho ai" → đề xuất cụ thể có mệnh giá/đối tượng.
- [ ] Số liệu agent trả về **khớp với tính toán code** (không bịa).
- [ ] Agent **RUNNING** trên AgentBase, BTC gọi được ≥1 request.
- [ ] Giao diện web mở được qua endpoint public.
- [ ] README đầy đủ (tên agent, mô tả, cách chạy, khai báo Claude Code Max + Qwen MaaS).
- [ ] Repo PUBLIC; video demo 2–3 phút.

---

## 10. Kịch bản demo (gợi ý quay video 2–3 phút)

1. Mở giao diện, kéo-thả file `merchant_performance_sample.csv`. Agent xác nhận: 40 merchant, 8 tuần, tuần hiện tại 08/06.
2. Bấm chip "Merchant nào giảm tuần này?" → agent chỉ ra nhóm giảm mạnh (Nhà Sách Tri Thức, Cafe Workspace, Tạp Hóa Cô Ba...) kèm % và nguyên nhân.
3. Hỏi "Ai sắp churn?" → danh sách churn risk Cao + badge đỏ + đề xuất.
4. Hỏi "Nên chạy voucher cho ai?" → đề xuất voucher cụ thể.
5. Hỏi tự do: "Top 5 merchant tăng trưởng ở TP.HCM" → bảng xếp hạng.
6. Chốt: nhấn mạnh AM tiết kiệm thời gian, phát hiện sớm, hành động ngay.

---

## 11. Hướng mở rộng (nếu còn thời gian / nói trong phần Value)

- Tự động gửi cảnh báo churn qua Telegram/email mỗi đầu tuần.
- Thêm biểu đồ xu hướng (line chart) cho từng merchant.
- So sánh theo ngành hàng / khu vực.
- Cho phép upload nhiều kỳ dữ liệu để phân tích dài hạn.
