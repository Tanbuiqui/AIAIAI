# <Tên Agent>

> <Tagline — một câu mô tả ngắn gọn agent làm gì (≤300 ký tự, không để trống).>

**Track:** Chat Agent / Data Analysis / Coding & Automation
**Cuộc thi:** Claw-a-thon 2026 — GreenNode AgentBase

---

## Problem — Vấn đề
<Mô tả vấn đề thực tế mà agent giải quyết. Ai gặp vấn đề này? Tại sao nó đáng giải quyết?>

## User — Người dùng
<Đối tượng sử dụng agent (ví dụ: nhân viên phân tích, dev, người dùng phổ thông...).>

## Solution — Giải pháp
<Agent giải quyết vấn đề như thế nào? Luồng hoạt động chính, input → output.>

## Value — Giá trị
<Agent mang lại lợi ích gì? Tiết kiệm thời gian, tự động hóa, độ chính xác...>

---

## Tính năng chính
- <Tính năng 1>
- <Tính năng 2>
- <Tính năng 3>

## Kiến trúc

| Thành phần | Chi tiết |
|---|---|
| **LLM Model** | <Gemma / Qwen / Minimax> (qua GreenNode MaaS, OpenAI-compatible API) |
| **Skills** | <Mô tả các skill / tool / MCP agent sử dụng> |
| **Deploy** | GreenNode AgentBase (public endpoint) |

---

## Cách chạy (local)

### Yêu cầu
- Docker Desktop (đang chạy nền)
- Tài khoản GreenNode AI Portal (Client ID/Secret + API Key MaaS)

### Cấu hình
Tạo file `.env` (KHÔNG commit) theo mẫu:

```dotenv
GREENNODE_IAM_CLIENT_ID=<client-id>
GREENNODE_IAM_CLIENT_SECRET=<client-secret>
GREENNODE_MAAS_API_KEY=<api-key>
```

### Chạy
```bash
# <bổ sung lệnh chạy thực tế của agent, ví dụ:>
# python main.py
# npm start
```

---

## Deploy lên AgentBase
1. Clone bộ skill `greennode-agentbase-skills` vào folder cùng cấp với agent.
2. Prompt deploy qua skill, điền Client ID/Secret + API Key + chọn model + runtime size.
3. Đợi Docker build & push (~2–3 phút), kiểm tra status **ACTIVE** trên portal.
4. Lấy public endpoint.

**Endpoint:** `<điền-endpoint-sau-khi-deploy>`

---

## Demo
- **Video:** <link YouTube unlisted / OneDrive share internal — xem được bằng @vng.com.vn>

---

## Ghi chú
Agent được phát triển với sự hỗ trợ của Claude Code (chi phí do đội tự chi trả); agent runtime chạy bằng model MaaS do GreenNode cấp.
