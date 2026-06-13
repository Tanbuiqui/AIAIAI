# Merchant Growth Agent

> Trợ lý phân tích merchant cho Account Manager — hỏi bằng tiếng Việt, nhận insight và đề xuất hành động. Upload file giao dịch, hỏi tự nhiên, agent trả lời kèm số liệu + nguyên nhân + đề xuất.

**Track:** Data Analysis
**Cuộc thi:** Claw-a-thon 2026 — GreenNode AgentBase

---

## Mô tả / Description (song ngữ)

**🇻🇳 Tiếng Việt**
> **Merchant Growth Agent** — Trợ lý phân tích merchant cho Account Manager. Upload file giao dịch (CSV/Excel) rồi hỏi tự nhiên bằng tiếng Việt; agent tính toán bằng code (pandas) và dùng Qwen (MaaS) để diễn giải thành **số liệu + nguyên nhân + đề xuất hành động**. Tính năng: tổng quan danh mục, phát hiện merchant giảm, xếp hạng tăng trưởng, merchant tăng đều, cảnh báo churn 3 mức, ưu tiên "merchant đáng cứu" (churn × lợi nhuận), bóc tách nguyên nhân, biểu đồ xu hướng 8 tuần và hỏi-đáp tự do. Mọi con số tính bằng code — LLM chỉ diễn giải, không bịa số. Giúp AM giảm thời gian phân tích từ hàng giờ xuống vài giây và phát hiện sớm để giữ chân merchant.

**🇬🇧 English**
> **Merchant Growth Agent** — an analytics assistant for Account Managers. Upload a merchant transaction file (CSV/Excel) and ask questions in natural Vietnamese; the agent computes every metric in code (pandas) and uses Qwen (MaaS) to turn results into **numbers + root causes + recommended actions**. Features: portfolio overview, decline detection, growth ranking, steady-growth detection, 3-level churn alerts, "who's worth saving" prioritization (churn × profit), revenue decomposition, an 8-week trend chart, and free-form Q&A. All numbers are code-computed — the LLM only explains, never fabricates. It cuts analysis time from hours to seconds and surfaces at-risk merchants early so AMs can retain them.

---

## Problem — Vấn đề
Account Manager / Sales phải tự mở Excel, lọc và tính toán để biết merchant nào đang giảm, ai cần chăm sóc, ai sắp rời bỏ. Việc này tốn hàng giờ, dễ bỏ sót và thường phát hiện quá muộn để can thiệp.

## User — Người dùng
Account Manager / Sales quản lý một danh mục merchant.

## Solution — Giải pháp
Một trợ lý chat. User đổ file CSV/Excel giao dịch merchant vào → hỏi tự nhiên bằng tiếng Việt → agent **tính toán bằng code (pandas)** rồi trả lời kèm **số liệu chính xác + nguyên nhân định lượng + đề xuất hành động cụ thể**. LLM chỉ diễn giải kết quả đã tính — không tự bịa số.

## Value — Giá trị
Giảm thời gian phân tích từ hàng giờ xuống vài giây; phát hiện sớm merchant churn/giảm để can thiệp kịp; chuẩn hóa cách ra quyết định chăm sóc merchant; ưu tiên đúng theo **lợi nhuận** chứ không chỉ doanh thu.

---

## Tính năng chính (7 nhóm phân tích)
- **Tổng quan danh mục** — tổng doanh thu/lợi nhuận + % WoW, số merchant tăng/giảm/churn, top mover.
- **Phát hiện merchant giảm** — WoW âm + bóc nguyên nhân (giao dịch / khách quay lại / giá trị đơn).
- **Xếp hạng tăng trưởng** — Top N theo % tăng WoW.
- **Gợi ý voucher** — ưu tiên theo lợi nhuận gộp; cảnh báo merchant biên mỏng (vd điện tử ~19%) không nên giảm giá sâu.
- **Cảnh báo churn 3 mức** (Cao 🔴 / Trung bình 🟡 / Thấp 🟢) theo quy tắc định lượng.
- **Merchant quan trọng đang lung lay** — giao của churn × lợi nhuận cao, xếp theo *giá trị có nguy cơ mất*.
- **Bóc tách nguyên nhân tăng/giảm** — tách WoW thành số lượng / giá trị đơn / giữ chân → map ra hành động.

> Mọi con số được tính **bằng code**; mô hình LLM chỉ diễn giải kết quả đã tính.

## Kiến trúc

| Thành phần | Chi tiết |
|---|---|
| **LLM Model** | Qwen (qua GreenNode MaaS, API OpenAI-compatible) — luồng 2 lượt: ① intent router trả JSON `{intent, params}` → code dispatch; ② diễn giải số đã tính thành câu trả lời. |
| **Backend** | FastAPI + pandas. Toàn bộ tính toán ở `pipeline.py`; tầng LLM ở `llm.py`. Nếu thiếu key MaaS, agent tự fallback rule-based (vẫn chạy đầy đủ). |
| **Skills** | Intent-routing tự dispatch (không phụ thuộc native function-calling của model). |
| **Deploy** | GreenNode AgentBase (Docker build & push tự động, public endpoint). |

### File chính
- `pipeline.py` — lõi phân tích (7 nhóm, mọi con số tính bằng code)
- `llm.py` — tầng LLM 2 lượt + fallback rule-based
- `main.py` — FastAPI: `/health`, `/`, `/api/upload`, `/api/analyze`, `/invocations`
- `static/index.html` — web view chat (upload kéo-thả, chip gợi ý, badge churn)
- `merchant_performance_sample.csv` — dữ liệu mẫu (40 merchant × 8 tuần)

---

## Cách chạy (local)

### Yêu cầu
- Python 3.11+ (hoặc Docker Desktop)

### Cấu hình (tùy chọn)
LLM MaaS là tùy chọn — thiếu key vẫn chạy bằng fallback. Để dùng Qwen, copy `.env.example` → `.env` và điền:

```dotenv
LLM_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1
LLM_API_KEY=<maas-api-key>
LLM_MODEL=<ten-model-Qwen-tren-portal>
```

### Chạy
```bash
pip install -r requirements.txt
python main.py          # mở http://localhost:8080
```

Hoặc bằng Docker:
```bash
docker build -t merchant-growth-agent .
docker run -p 8080:8080 --env-file .env merchant-growth-agent
```

### API
- `GET /health` → `{"status":"ok"}`
- `POST /api/upload` (multipart `file`) → `{session_id, meta}`
- `POST /api/analyze` → `{session_id, question}` → câu trả lời markdown
- `POST /invocations` → `{question, csv_text | file_base64}` (chuẩn cho BTC test)

---

## Deploy lên AgentBase
1. Mở Docker Desktop (chạy nền).
2. Clone bộ skill `greennode-agentbase-skills` vào folder **cùng cấp** với agent.
3. Prompt deploy qua skill → điền IAM Client ID/Secret + MaaS API Key + chọn **Qwen** + runtime **2×4**.
4. Đợi Docker build & push (~2–3 phút), kiểm tra status **ACTIVE** trên portal.
5. Lấy public endpoint.

**Endpoint:** https://endpoint-268d6ef8-5926-4ea2-b504-88118a19b760.agentbase-runtime.aiplatform.vngcloud.vn

- Web view: mở endpoint trên trình duyệt
- API test: `POST {endpoint}/invocations` với `{"question": "...", "file_base64": "<csv base64>"}` (hoặc `csv_text`)
- Health: `GET {endpoint}/health` → `{"status":"ok","llm":true}`

---

## Demo
- **Video:** `<link YouTube unlisted / OneDrive share internal — xem được bằng @vng.com.vn>`

Kịch bản demo gợi ý: upload `merchant_performance_sample.csv` → "Merchant nào giảm tuần này?" → "Ai sắp churn?" → "Nên chạy voucher cho ai?" → "Ai quan trọng đang lung lay?" → "Top 5 tăng trưởng ở TP.HCM".

---

## Ghi chú
Agent được phát triển với sự hỗ trợ của **Claude Code (tài khoản cá nhân, chi phí do đội tự chi trả)**; agent **runtime chạy bằng model MaaS** do GreenNode cấp.
