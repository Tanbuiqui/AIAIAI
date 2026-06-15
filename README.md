# Merchant Growth Agent

> Trợ lý phân tích merchant cho Account Manager — hỏi bằng tiếng Việt, nhận insight và đề xuất hành động. Upload file giao dịch, hỏi tự nhiên, agent trả lời kèm số liệu + nguyên nhân + đề xuất.

**Track:** Data Analysis
**Cuộc thi:** Claw-a-thon 2026 — GreenNode AgentBase

---

## Mô tả ngắn (nộp form — ≤300 từ)

> Copy đoạn **tiếng Việt hoặc tiếng Anh** dưới đây dán vào ô "Bài mô tả ngắn" của form (BTC chấp nhận VN hoặc EN).

### 🇻🇳 Tiếng Việt

**Vấn đề.** Account Manager / Sales quản lý hàng chục merchant phải tự mở Excel, lọc và tính tay để biết merchant nào đang giảm, ai sắp rời bỏ, và tháng này có cán đích doanh số hay không. Việc này tốn hàng giờ mỗi tuần, dễ bỏ sót và thường phát hiện quá muộn để can thiệp.

**Người dùng mục tiêu.** Account Manager / Sales phụ trách một danh mục merchant (ví dụ đội kinh doanh cổng thanh toán).

**Cách agent giải quyết.** Người dùng upload file giao dịch theo ngày (CSV/Excel: ngành, merchant, ngày, TPV, số giao dịch, kênh thanh toán) rồi hỏi tự nhiên bằng tiếng Việt. Agent tính toàn bộ chỉ số **bằng code (pandas)** trên hai trục — theo **tuần** (WoW) và theo **tháng** (dự phóng cuối tháng bằng run-rate, so với tháng trước) — rồi dùng model **Qwen trên GreenNode AgentBase (MaaS)** để diễn giải thành **số liệu + nguyên nhân + đề xuất hành động**. Agent trả lời được: tổng quan danh mục, dự phóng "tháng này có cao hơn tháng trước không", merchant giảm/tăng, cảnh báo churn 3 mức, merchant quan trọng đang lung lay, bóc tách nguyên nhân (số lượng × giá trị đơn) và hỏi-đáp tự do (kể cả cơ cấu kênh thanh toán). Mọi con số do code tính, LLM chỉ diễn giải nên không bịa số. Agent đóng gói FastAPI, deploy public trên AgentBase với endpoint `/invocations`.

**Giá trị.** Giảm thời gian phân tích từ hàng giờ xuống vài giây mỗi ngày; phát hiện sớm merchant churn/giảm để giữ chân kịp thời; và biết trước tháng có đạt chỉ tiêu hay không để hành động ngay trong nửa cuối tháng.

### 🇬🇧 English

**Problem.** Account Managers / Sales reps managing dozens of merchants must open Excel and filter and compute by hand to learn which merchants are declining, who is about to churn, and whether this month will hit its revenue target. This takes hours every week, is error-prone, and issues are usually spotted too late to act.

**Target users.** Account Managers / Sales reps who own a merchant portfolio (e.g., a payment-gateway sales team).

**How the agent solves it.** Users upload a daily transaction file (CSV/Excel: category, merchant, date, TPV, transaction count, payment channel) and ask questions in natural Vietnamese. The agent computes every metric **in code (pandas)** on two axes — **weekly** (WoW) and **monthly** (month-end projection via run-rate, compared to the previous month) — then uses the **Qwen model on GreenNode AgentBase (MaaS)** to turn results into **numbers + root causes + recommended actions**. It answers: portfolio overview, the month-end forecast ("will this month beat last month?"), decliners/growers, 3-level churn alerts, high-value at-risk merchants, revenue decomposition (volume × order value), and free-form Q&A (including payment-channel mix). All numbers are code-computed; the LLM only explains, so it never fabricates figures. The agent is packaged as FastAPI and deployed publicly on AgentBase with an `/invocations` endpoint.

**Value.** Cuts analysis from hours to seconds each day, surfaces churning/declining merchants early enough to retain them, and tells AMs in advance whether the month will hit target so they can act in the second half of the month.

---

## Mô tả / Description (song ngữ)

**🇻🇳 Tiếng Việt**
> **Merchant Growth Agent** — Trợ lý phân tích merchant cho Account Manager. Upload file giao dịch (CSV/Excel, dữ liệu **theo ngày**) rồi hỏi tự nhiên bằng tiếng Việt; agent tính toán bằng code (pandas) và dùng Qwen (MaaS) để diễn giải thành **số liệu + nguyên nhân + đề xuất hành động**. Phân tích trên **2 trục**: theo **tuần** (WoW) và theo **tháng** — tháng chưa hết được **dự phóng cuối tháng** (run-rate) và so với tháng trước. Tính năng: tổng quan danh mục, **dự phóng cuối tháng vs tháng trước**, phát hiện merchant giảm, xếp hạng tăng trưởng, merchant tăng đều, cảnh báo churn 3 mức, ưu tiên "merchant đáng cứu" (churn × doanh số), bóc tách nguyên nhân (số lượng × giá trị đơn), biểu đồ xu hướng và hỏi-đáp tự do (kể cả cơ cấu kênh thanh toán). Mọi con số tính bằng code — LLM chỉ diễn giải, không bịa số. Giúp AM giảm thời gian phân tích từ hàng giờ xuống vài giây và biết sớm tháng này có cán đích hay không.

**🇬🇧 English**
> **Merchant Growth Agent** — an analytics assistant for Account Managers. Upload a **daily** merchant transaction file (CSV/Excel) and ask questions in natural Vietnamese; the agent computes every metric in code (pandas) and uses Qwen (MaaS) to turn results into **numbers + root causes + recommended actions**. It analyzes on **two axes**: by **week** (WoW) and by **month** — the in-progress month is **projected to month-end** (run-rate) and compared against the previous month. Features: portfolio overview, **month-end forecast vs last month**, decline detection, growth ranking, steady-growth detection, 3-level churn alerts, "who's worth saving" prioritization (churn × revenue), revenue decomposition (volume × order value), a trend chart, and free-form Q&A (incl. payment-method mix). All numbers are code-computed — the LLM only explains, never fabricates. It cuts analysis time from hours to seconds and tells AMs early whether the month will hit target.

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

## Tính năng chính
- **Tổng quan danh mục** — tổng doanh số (TPV) + % thay đổi (tháng dự phóng / WoW), số merchant tăng/giảm/churn, top mover.
- **Dự phóng cuối tháng vs tháng trước** — tháng chưa hết → ước lượng run-rate cả tháng, trả lời "cao hơn tháng trước không", liệt kê merchant dự phóng tăng/giảm.
- **Phát hiện merchant giảm** — thay đổi âm + bóc nguyên nhân (số lượng giao dịch / giá trị đơn).
- **Xếp hạng tăng trưởng** — Top N theo % tăng (tháng hoặc tuần).
- **Merchant tăng đều** — tăng liên tiếp nhiều tuần.
- **Gợi ý voucher** — merchant đang giảm, ưu tiên theo **doanh số (TPV)**.
- **Cảnh báo churn 3 mức** (Cao 🔴 / Trung bình 🟡 / Thấp 🟢) — theo xu hướng doanh số/giao dịch (giảm ≥3 tuần liên tiếp hoặc sụp <70% TB 4 tuần).
- **Merchant quan trọng đang lung lay** — churn × doanh số dự phóng, xếp theo *giá trị có nguy cơ mất*.
- **Bóc tách nguyên nhân tăng/giảm** — tách thành số lượng × giá trị đơn → map ra hành động.
- **Hỏi-đáp tự do** — gồm cơ cấu kênh thanh toán (Payment Gateway / VietQR / Wallet, tỷ trọng Paylater).

> Mọi con số được tính **bằng code**; mô hình LLM chỉ diễn giải kết quả đã tính.

### Dữ liệu đầu vào (schema)
9 cột: `Sub-cate` (ngành), `Merchant id`, `Merchant name`, `App id`, `Date` (theo ngày), `TPV` (doanh số), `Transaction` (số giao dịch), `Transaction type` (Payment Gateway / VietQR / Wallet), `SOF` (Paylater / Others — chỉ khi Wallet). Cần tháng trước **đủ** + tháng hiện tại (có thể chưa hết) để dự phóng.

## Kiến trúc

| Thành phần | Chi tiết |
|---|---|
| **LLM Model** | Qwen (qua GreenNode MaaS, API OpenAI-compatible) — luồng 2 lượt: ① intent router trả JSON `{intent, params}` → code dispatch; ② diễn giải số đã tính thành câu trả lời. |
| **Backend** | FastAPI + pandas. Toàn bộ tính toán ở `pipeline.py`; tầng LLM ở `llm.py`. Nếu thiếu key MaaS, agent tự fallback rule-based (vẫn chạy đầy đủ). |
| **Skills** | Intent-routing tự dispatch (không phụ thuộc native function-calling của model). |
| **Deploy** | GreenNode AgentBase (Docker build & push tự động, public endpoint). |

### File chính
- `pipeline.py` — lõi phân tích (engine tuần + dự phóng tháng, mọi con số tính bằng code)
- `llm.py` — tầng LLM 2 lượt + fallback rule-based
- `main.py` — FastAPI: `/health`, `/`, `/api/upload`, `/api/analyze`, `/invocations`
- `static/index.html` — web view chat (upload kéo-thả, chip gợi ý, badge churn, biểu đồ)
- `merchant_performance_sample.csv` — dữ liệu mẫu (40 merchant, theo ngày, **5 tháng**: 02–05 đủ + tháng 6 đến 15/06)
- `make_sample_data.py` / `verify_sample_data.py` — sinh & kiểm tra dữ liệu mẫu

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

Kịch bản demo gợi ý: upload `merchant_performance_sample.csv` → "Tổng quan tháng này" → "Dự phóng cuối tháng có cao hơn tháng trước không?" → "Merchant nào giảm?" → "Ai sắp churn?" → "Ai quan trọng đang lung lay?" → "Top 5 tăng trưởng".

---

## Ghi chú
Agent được phát triển với sự hỗ trợ của **Claude Code (tài khoản cá nhân, chi phí do đội tự chi trả)**; agent **runtime chạy bằng model MaaS** do GreenNode cấp.
