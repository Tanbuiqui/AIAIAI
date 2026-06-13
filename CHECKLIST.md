# CHECKLIST — Merchant Growth Agent (Claw-a-thon 2026)

> Track: **Data Analysis** · Model runtime: **Qwen (MaaS)** · Deploy: **GreenNode AgentBase**
> Mốc cứng: **Submit 17/06 12:00** · Fail-fix 18/06 12:00 · Voting 22/06–03/07
> Cập nhật: 2026-06-13

---

## ✅ ĐÃ XONG — Dữ liệu & Spec

- [x] Chốt use case + track (Data Analysis)
- [x] Spec hoàn chỉnh, đồng bộ dataset — `SPEC-Merchant-Growth-Agent.md`
- [x] Dữ liệu mẫu: 40 merchant × 8 tuần × 11 cột = 320 dòng — `merchant_performance_sample.csv`
- [x] Script sinh dữ liệu (seed cố định, tái tạo được) — `make_sample_data.py`
- [x] Script verify mọi kịch bản + hợp lệ lợi nhuận — `verify_sample_data.py` → TẤT CẢ KHỚP
- [x] Mở rộng lên 7 phân tích (thêm tổng quan / at-risk / bóc tách nguyên nhân)

---

## ✅ BUILD AGENT v1 (cốt lõi) — XONG, test local PASS

### Backend phân tích — `pipeline.py` ✅
- [x] Đọc CSV/Excel bằng pandas; tự nhận diện schema, thiếu cột → báo rõ
- [x] Tính chỉ số phái sinh: tỷ lệ khách quay lại, biên lợi nhuận, khách mới
- [x] **4.1** Phát hiện merchant giảm (WoW âm + nguyên nhân định lượng)
- [x] **4.2** Top N tăng trưởng (bảng xếp hạng)
- [x] **4.3** Gợi ý voucher — ưu tiên theo lợi nhuận, cảnh báo merchant biên mỏng
- [x] **4.4** Cảnh báo churn 3 mức (Cao/TB/Thấp) — quy tắc định lượng (khớp verify: 8 Cao / 11 TB)
- [x] **4.5** Tổng quan danh mục (tổng doanh thu/lợi nhuận WoW + top mover)
- [x] **4.6** Merchant quan trọng đang lung lay (churn × lợi nhuận)
- [x] **4.7** Bóc tách nguyên nhân (số lượng / giá trị đơn / giữ chân)
- [x] **(mới) Tăng đều / xu hướng tăng** — merchant tăng liên tiếp nhiều tuần (dùng cả 8 tuần)
- [x] **(mới) `digest()`** — bảng toàn bộ chỉ số đã tính cho 40 merchant (phục vụ hỏi tự do)
- [x] **(mới) `series_all()`** — chuỗi doanh thu 8 tuần từng merchant (phục vụ line chart)
- [x] Mọi con số tính BẰNG CODE — không để LLM tự tính

### Tầng LLM (Qwen MaaS) — luồng 2 lượt — `llm.py` ✅
- [x] Lượt 1: intent router → trả JSON `{intent, params}`, code dispatch (không dùng native tool-calling)
- [x] Parse JSON có fallback; `unknown`/lỗi → gợi ý lại, không crash
- [x] Lượt 2: diễn giải số đã tính → câu trả lời 4 phần (kết luận → số liệu → nguyên nhân → đề xuất)
- [x] Fallback rule-based khi thiếu key MaaS → chạy/test local không cần MaaS
- [x] **(mới) Freeform Q&A**: câu lạ/so sánh/lọc → đưa cả `digest` cho LLM tự trả lời, vẫn không bịa số
- [x] **(mới) Router mở rộng**: thêm intent `uptrend`; bỏ từ khóa "top" gây nhầm growth/decline
- [x] **(mới) Fix Qwen3 "thinking"**: `extra_body={chat_template_kwargs:{enable_thinking:false}}` cho cả 3 lượt gọi
- [x] **ĐÃ TEST LIVE với Qwen MaaS thật** (`qwen/qwen3-5-27b`, `/health` báo `llm:true`): router hiểu NL, diễn giải 4 phần, freeform tổng hợp đúng số

### API + UI — `main.py`, `static/index.html` ✅
- [x] `GET /health` → 200 (BẮT BUỘC cho AgentBase)
- [x] `GET /` → trả UI
- [x] `POST /api/upload` + `POST /api/analyze` (JSON / multipart) cho web view
- [x] `POST /invocations` (JSON, hỗ trợ csv_text/file_base64 inline) cho BTC test
- [x] Listen `0.0.0.0:8080`
- [x] State DataFrame in-memory theo session (upload-rồi-hỏi cùng phiên); mất session → 409 báo upload lại
- [x] UI chat: upload kéo-thả, hiện trạng thái file (số merchant/tuần), chip gợi ý
- [x] Render bảng, in đậm số liệu, badge màu churn (Cao=đỏ, TB=vàng), loading, báo lỗi

### Đóng gói ✅
- [x] `requirements.txt`
- [x] `Dockerfile` (python:3.11-slim, EXPOSE 8080)
- [x] `.env` (KHÔNG commit) + `.gitignore` (đã có) + `.env.example`
- [x] Test local — chạy đủ 8 loại câu hỏi với CSV mẫu qua TestClient (ALL PASS)

---

## ✅ NÂNG CẤP UI/UX & TRỰC QUAN (đã làm thêm) — `static/index.html`

- [x] Biểu đồ **2 cột** (tuần trước xám / tuần này màu) cho tổng quan/tăng/giảm — ghi rõ **số tiền** + %WoW
- [x] **Line chart 8 tuần** toàn merchant: tô màu theo ngành, điểm + số tiền theo tuần, tooltip
- [x] **Bộ lọc line chart**: ô tìm theo tên, checkbox 40 merchant, toggle theo ngành, chọn tất cả/bỏ chọn
- [x] Mặc định chọn **2 cao nhất + 2 thấp nhất**; tick là tự **dồn lên đầu**; nhãn số tiền **giãn không chồng**
- [x] Tên merchant gắn **bên trái** đường line (thay mốc tiền) khi chọn ít
- [x] Ô tổng quan (tăng/giảm/churn) **bấm được** → liệt kê đúng danh sách merchant nhóm đó
- [x] Badge churn màu, render bảng, chip gợi ý (+ "Ai tăng đều mỗi tuần?")

---

## ⬜ TIÊU CHÍ PASS (BẮT BUỘC — đạt CẢ 3)

- [ ] Agent **RUNNING** trên AgentBase (BTC gọi thử ≥1 request thành công)
- [ ] **Video demo 2–3 phút**, xem được bằng `@vng.com.vn`, đúng track Data Analysis
- [ ] **README + mô tả ≤300 ký tự** đầy đủ problem/user/solution — không placeholder/lorem

---

## ⬜ DEPLOY

- [x] Lấy từ portal: IAM Client ID/Secret + MaaS API Key (đã nhận qua email) → `.env`
- [x] Xác nhận model **Qwen** thực tế: `qwen/qwen3-5-27b` (Qwen 3.5 27B — ENABLED, loại CHAT)
- [ ] Docker Desktop chạy nền
- [ ] Clone `greennode-agentbase-skills` vào folder **CÙNG CẤP** với agent
- [ ] Prompt deploy → điền Client ID/Secret + API Key + chọn Qwen 3.5 27B + runtime `2×4`
- [ ] Đợi Docker build & push (~2–3 phút)
- [ ] Kiểm tra status **ACTIVE** trên portal → lấy endpoint public
- [ ] Test endpoint public: mở web view + gọi `POST /invocations`

---

## ⬜ SUBMISSION FORM (5 phần)

- [ ] Tên đội (unique, ≤60 ký tự)
- [ ] Track: **Data Analysis**
- [ ] Thành viên — Team Lead bắt buộc; email `@vng.com.vn`
- [ ] Thông tin dự án: tên agent · tagline · problem · solution · value · voter guide
- [ ] Links: AgentBase project link + video demo (YouTube unlisted / OneDrive internal)

---

## ⬜ CHECKLIST CỨNG TRƯỚC KHI BẤM NỘP

- [ ] Agent đang RUNNING
- [ ] Repo để **PUBLIC** (giữ đến hết voting 03/07)
- [ ] Video accessible bằng `@vng.com.vn`
- [ ] README có dòng **khai báo**: phát triển bằng Claude Code (Max cá nhân, đội tự chi trả); runtime chạy model MaaS
- [ ] KHÔNG có credential trong repo (check `.env` đã ignore)
- [ ] Nhắc lịch: 16/06 tối (đệm) + 17/06 12:00 (cứng)

---

## 🌟 ĐỂ "IDEAL" — tăng sức thuyết phục voting (nên có nếu kịp)

- [ ] Demo insight "doanh thu cao ≠ lợi nhuận cao" (tận dụng cột lợi nhuận)
- [ ] Demo "merchant quan trọng đang lung lay" — câu hỏi sát thực tế AM nhất
- [x] UI đẹp, hiện đại, 1 màn hình không cần hướng dẫn (chart cột + line + bộ lọc + pill bấm được)
- [ ] Câu trả lời luôn đúng cấu trúc 4 phần + giọng tư vấn
- [ ] Quay demo theo kịch bản spec mục 10, mạch lạc, 1 lần ăn ngay

---

## 🗓 ĐƯỜNG TỚI HẠN (gợi ý)

| Ngày | Việc | Trạng thái |
|---|---|---|
| 13–14/06 | Build v1: pipeline + main + UI + Docker; test local | ✅ XONG (13/06) |
| 13/06 | Lấy key MaaS → `.env` → test LLM thật (router + freeform) | ✅ XONG — Qwen `llm:true` |
| 14–15/06 | Deploy lên AgentBase → ACTIVE → test endpoint public | ⬜ |
| 16/06 | README (điền endpoint) + quay video demo; đệm sửa lỗi | ⬜ |
| **17/06 12:00** | **SUBMIT (cứng)** | ⬜ |
| 18/06 12:00 | Fail-fix (nếu cần) | ⬜ |

---

## 📁 FILE TRONG REPO

| File | Trạng thái |
|---|---|
| `CLAUDE.md` | Luật cuộc thi + quy trình deploy |
| `SPEC-Merchant-Growth-Agent.md` | Spec chính (đồng bộ) ✅ |
| `merchant_performance_sample.csv` | Dữ liệu mẫu đã verify ✅ |
| `make_sample_data.py` / `verify_sample_data.py` | Sinh + kiểm tra dữ liệu ✅ |
| `README.md` | Đã điền (Merchant Growth Agent + khai báo) ✅ |
| `pipeline.py` / `llm.py` / `main.py` / `static/index.html` | Đã build + test local PASS ✅ |
| `Dockerfile` / `requirements.txt` / `.env.example` | ✅ |
