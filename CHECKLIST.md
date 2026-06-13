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

## ⬜ BUILD AGENT v1 (cốt lõi)

### Backend phân tích — `pipeline.py`
- [ ] Đọc CSV/Excel bằng pandas; tự nhận diện schema, thiếu cột → báo rõ
- [ ] Tính chỉ số phái sinh: tỷ lệ khách quay lại, biên lợi nhuận, khách mới
- [ ] **4.1** Phát hiện merchant giảm (WoW âm + nguyên nhân định lượng)
- [ ] **4.2** Top N tăng trưởng (bảng xếp hạng)
- [ ] **4.3** Gợi ý voucher — ưu tiên theo lợi nhuận, cảnh báo merchant biên mỏng
- [ ] **4.4** Cảnh báo churn 3 mức (Cao/TB/Thấp) — quy tắc định lượng
- [ ] **4.5** Tổng quan danh mục (tổng doanh thu/lợi nhuận WoW + top mover)
- [ ] **4.6** Merchant quan trọng đang lung lay (churn × lợi nhuận)
- [ ] **4.7** Bóc tách nguyên nhân (số lượng / giá trị đơn / giữ chân)
- [ ] Mọi con số tính BẰNG CODE — không để LLM tự tính

### Tầng LLM (Qwen MaaS) — luồng 2 lượt
- [ ] Lượt 1: intent router → trả JSON `{intent, params}`, code dispatch (không dùng native tool-calling)
- [ ] Parse JSON có fallback; `unknown`/lỗi → gợi ý lại, không crash
- [ ] Lượt 2: diễn giải số đã tính → câu trả lời 4 phần (kết luận → số liệu → nguyên nhân → đề xuất)

### API + UI — `main.py`, `static/index.html`
- [ ] `GET /health` → 200 (BẮT BUỘC cho AgentBase)
- [ ] `GET /` → trả UI
- [ ] `POST /api/analyze` (JSON / multipart) cho web view
- [ ] `POST /invocations` (JSON transcript→analysis) cho BTC test
- [ ] Listen `0.0.0.0:8080`
- [ ] State DataFrame in-memory theo session (upload-rồi-hỏi cùng phiên)
- [ ] UI chat: upload kéo-thả, hiện trạng thái file (số merchant/tuần), chip gợi ý
- [ ] Render bảng, in đậm số liệu, badge màu churn (Cao=đỏ, TB=vàng), loading, báo lỗi

### Đóng gói
- [ ] `requirements.txt`
- [ ] `Dockerfile` (python-slim, EXPOSE 8080)
- [ ] `.env` (KHÔNG commit) + `.gitignore`
- [ ] Test local `localhost:8080` — chạy đủ 7 loại câu hỏi với CSV mẫu

---

## ⬜ TIÊU CHÍ PASS (BẮT BUỘC — đạt CẢ 3)

- [ ] Agent **RUNNING** trên AgentBase (BTC gọi thử ≥1 request thành công)
- [ ] **Video demo 2–3 phút**, xem được bằng `@vng.com.vn`, đúng track Data Analysis
- [ ] **README + mô tả ≤300 ký tự** đầy đủ problem/user/solution — không placeholder/lorem

---

## ⬜ DEPLOY

- [ ] Docker Desktop chạy nền
- [ ] Lấy từ portal: IAM Client ID/Secret + MaaS API Key → `.env`
- [ ] Xác nhận tên/path model **Qwen** thực tế trên portal
- [ ] Clone `greennode-agentbase-skills` vào folder **CÙNG CẤP** với agent
- [ ] Prompt deploy → điền Client ID/Secret + API Key + chọn Qwen + runtime `2×4`
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
- [ ] UI đẹp, hiện đại, 1 màn hình không cần hướng dẫn
- [ ] Câu trả lời luôn đúng cấu trúc 4 phần + giọng tư vấn
- [ ] Quay demo theo kịch bản spec mục 10, mạch lạc, 1 lần ăn ngay

---

## 🗓 ĐƯỜNG TỚI HẠN (gợi ý)

| Ngày | Việc |
|---|---|
| 13–14/06 | Build v1: pipeline + main + UI + Docker; test local |
| 15/06 | Deploy lên AgentBase → ACTIVE → test endpoint public |
| 16/06 | README + quay video demo; đệm sửa lỗi |
| **17/06 12:00** | **SUBMIT (cứng)** |
| 18/06 12:00 | Fail-fix (nếu cần) |

---

## 📁 FILE TRONG REPO

| File | Trạng thái |
|---|---|
| `CLAUDE.md` | Luật cuộc thi + quy trình deploy |
| `SPEC-Merchant-Growth-Agent.md` | Spec chính (đồng bộ) ✅ |
| `merchant_performance_sample.csv` | Dữ liệu mẫu đã verify ✅ |
| `make_sample_data.py` / `verify_sample_data.py` | Sinh + kiểm tra dữ liệu ✅ |
| `README.md` | Template — cần điền sau khi build |
| `pipeline.py` / `main.py` / `static/index.html` / `Dockerfile` / `requirements.txt` | ⬜ Chưa build |
