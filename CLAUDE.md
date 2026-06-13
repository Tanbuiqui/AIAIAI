# Claw-a-thon 2026 — Tài liệu Build & Deploy Agent

> File context dùng cho Claude Code. Mục tiêu: build một AI agent và deploy thành công lên **GreenNode AgentBase** trước hạn nộp.
> Người dùng build bằng **Claude Code (tài khoản cá nhân)**; agent runtime chạy bằng **model MaaS** do BTC cấp.

---

## 0. TL;DR — Mental model

Triết lý cuộc thi: **"Chỉ cần prompt — vibe code lo phần còn lại."**
Vòng lặp tổng quát:

> mô tả use case → AI viết code → clone bộ skill cùng cấp → prompt deploy → kiểm tra ACTIVE + lấy endpoint → push GitHub → submit

Hạ tầng (GPU, container, DevOps) đã được trừu tượng hóa. Giá trị nằm ở **ý tưởng use case** và **cách agent giải quyết vấn đề thực tế**, không phải ở kỹ năng cấu hình server.

---

## 1. Thông tin cuộc thi

- **Tên:** Claw-a-thon 2026 — hackathon AI nội bộ VNG Group, do GreenNode tổ chức.
- **Đội:** tối đa 3 người. 1 cá nhân chỉ tham gia 1 đội, 1 bài nộp.
- **Output bắt buộc:** Agent phải deploy được lên **GreenNode AgentBase** (tool build chỉ là phương tiện).
- **Hạn chế:** Không dùng hệ thống production, không dùng tool nội bộ công ty.
- **Tổng giải thưởng:** lên đến 80 triệu (Nhất 15M, Nhì 10M, Ba 5M ×3 — tiền mặt; kèm credit POC tương ứng theo rulebook).

### 3 Tracks (chọn 1)
| Track | Mô tả |
|---|---|
| **Chat Agent** | Trợ lý hội thoại, chatbot, Q&A |
| **Data Analysis** | Phân tích dữ liệu, báo cáo tự động |
| **Coding & Automation** | Tự động hóa, workflow, scripting |

---

## 2. Timeline (mốc cứng)

| Mốc | Thời gian | Ghi chú |
|---|---|---|
| Build bắt đầu | 10/06 | Nhận account, deploy agent đầu tiên, 7 ngày build |
| **Submit Deadline** | **17/06 12:00** | Form tự đóng — KHÔNG gia hạn, KHÔNG ngoại lệ |
| Review Pass/Fail | 17–18/06 | Pass giữ nguyên; Fail nhận email + link sửa |
| **Fail Fix Deadline** | **18/06 12:00** | Cứng. Sau mốc này coi như rút lui |
| Cập nhật kết quả cuối | 19/06 | Thông báo pass/fail cuối |
| Community Voting | 22/06 – 03/07 11:00 | Toàn VNG Group (200+ người), 3 votes/người |
| Award Ceremony | 03/07 | Demo showcase, trao giải |

---

## 3. Ba thành phần của một AI Agent

| # | Thành phần | Ai lo | Trong Claw-a-thon |
|---|---|---|---|
| 01 | **LLM Model** (bộ não) | GreenNode cấp | API Key MaaS; chọn Gemma/Qwen/Minimax; gọi qua API chuẩn OpenAI-compatible; không cần host GPU |
| 02 | **Skills** (năng lực) | Vibe code tạo ra | Spec Kit (mô tả use case + I/O), Tool calls, MCP |
| 03 | **Deploy Platform** (runtime) | AgentBase | Public endpoint, container build & push pipeline, model routing tích hợp MaaS |

### Model MaaS — chọn theo use case
| Model | Nhà cung cấp | Mạnh ở | Phù hợp |
|---|---|---|---|
| **Gemma 4** | Google DeepMind | Nhẹ, latency thấp, tiếng Việt cơ bản | Task đơn giản |
| **Qwen 3** | Alibaba Cloud | Lý luận logic, coding, đa ngôn ngữ tốt | Data Analysis & Automation |
| **Minimax 2.5** | MiniMax AI | Hội thoại dài, context lớn, tiếng Việt tốt | Chat Agent & Q&A |

> Bộ skill AgentBase sẽ hỏi chọn model khi deploy. (Lưu ý: tên model trên portal có thể hiển thị khác chút, ví dụ `Gemma 3 27B` / `Qwen 2.5 72B` / `Minimax Text 01` — chọn theo đúng tên hệ thống hiển thị thực tế.)

---

## 4. Quy trình làm việc — 8 bước end-to-end

| Bước | Việc | Chi tiết |
|---|---|---|
| 1 | **Login Portal** | Đổi mật khẩu, lấy Client ID, Client Secret, API Key |
| 2 | **Tạo GitHub Repo** | Tạo repo mới, để PUBLIC, copy link |
| 3 | **Build Agent** | Mở Claude Code, clone repo về local, viết agent |
| 4 | **Import Skill AgentBase** | Clone bộ skill vào folder **cùng cấp** với folder agent |
| 5 | **Chạy Prompt Deploy** | Prompt Claude Code: "Dùng skill này để deploy agent lên AgentBase" |
| 6 | **Điền thông tin** | Client ID/Secret, API Key, chọn model, chọn runtime size |
| 7 | **Docker Build & Push** | Đợi ~2–3 phút, kiểm tra agent ACTIVE trên portal, lấy endpoint |
| 8 | **Push GitHub** | Push source code lên repo, copy link để submit |

### Chi tiết bước 4–7 (phần deploy)

**Bước 4 — Import Skill AgentBase**
- Mở terminal tại folder chứa agent.
- Clone bộ skill:
  ```bash
  git clone https://github.com/vngcloud/greennode-agentbase-skills
  ```
- ⚠️ Cấu trúc đúng: skill và agent phải **CÙNG CẤP**, không lồng vào nhau.
  ```
  workspace/
  ├── my-agent/                      ← folder agent
  └── greennode-agentbase-skills/    ← bộ skill (cùng cấp)
  ```

**Bước 5 — Chạy Prompt Deploy**
- Mở Claude Code trong folder agent.
- Prompt: `"Dùng skill trong folder này để deploy agent lên AgentBase"`.
- Skill sẽ hỏi lần lượt từng thông tin cần thiết.

**Bước 6 — Điền thông tin**
- **Client ID + Secret:** lấy từ portal — mục IAM.
- **API Key:** lấy từ portal — mục API Keys (MaaS).
- **Model:** Gemma / Qwen / Minimax (theo use case).
- **Runtime size:** `2×4` (standard) hoặc `4×4` (nếu cần RAM lớn hơn).

**Bước 7 — Verify & lấy Endpoint**
- Đợi Docker build + push (~2–3 phút).
- Portal → AgentBase: kiểm tra status **ACTIVE**.
- Copy endpoint, cập nhật config từ local → public.
- Test nhanh: gọi thử API hoặc mở web view.

> Bộ skill cung cấp slash command như `/agentbase-wizard`, `/agentbase-deploy`, `/agentbase-monitor` (theo README repo). Skill là Markdown + shell thuần, chạy trong mọi tool đọc được `SKILL.md`.

---

## 5. Công cụ & môi trường

| Nhóm | Công cụ | Dùng để |
|---|---|---|
| Vibe code | **Claude Code** (đang dùng — tài khoản cá nhân) | Viết & build agent |
| AI Stack | GreenNode AI Portal | Quản lý account, API Key, IAM, AgentBase runtime, Open-claw |
| Models (MaaS) | Gemma, Qwen, Minimax | Model chạy agent (đã cấp sẵn) |
| Deploy | Bộ skill `vngcloud/greennode-agentbase-skills` | Đóng gói & deploy bằng prompt |
| Support | **Docker Desktop**, **GitHub + Git CLI** | Build/push image; push source code để submit |

### Docker Desktop
- Bộ skill tự build & push image — bạn KHÔNG gõ lệnh Docker thủ công.
- Chỉ cần cài và **để app đang chạy** khi deploy.
- Tải: docker.com/products/docker-desktop (Windows & macOS).

### GitHub
- Push source code để nộp bài + để voting page hiển thị đúng.
- ⚠️ Repo phải để **PUBLIC** từ lúc nộp đến hết voting 03/07.

> **LƯU Ý CHO TÀI KHOẢN CÁ NHÂN:** KHÔNG set các biến `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` để trỏ Claude Code sang Minimax MaaS. Cứ để Claude Code chạy bằng tài khoản riêng. Đoạn `export ... minimax ...` trong slide chỉ dành cho người KHÔNG có tài khoản Claude và muốn dùng credit cuộc thi để code — không áp dụng cho bạn. Kiểm tra bằng `/status`: base URL phải là của Anthropic, model không phải `minimax/...`.

---

## 6. Bảo mật credential (QUAN TRỌNG)

Thông tin cần để deploy: **IAM Client ID + Client Secret** và **API Key (MaaS)**. Đây là thông tin nhạy cảm, tương đương mật khẩu.

Quy tắc bắt buộc:
- **KHÔNG** dán Client Secret / API Key vào chat, tin nhắn, hay commit lên GitHub.
- Đặt chúng trong file `.env` ở local và thêm `.env` vào `.gitignore`.
- Thể lệ cấm rò rỉ/chia sẻ token; lạm dụng có thể bị **loại đội + thu hồi account + đưa credit về 0**.
- Nếu key đã từng lộ ra ngoài máy → **rotate (tạo lại) ngay** trong portal và báo BTC.

Mẫu `.env` (điền giá trị thật của bạn, KHÔNG commit file này):
```dotenv
GREENNODE_IAM_CLIENT_ID=<client-id-cua-ban>
GREENNODE_IAM_CLIENT_SECRET=<client-secret-cua-ban>
GREENNODE_MAAS_API_KEY=<api-key-cua-ban>
```

Mẫu `.gitignore`:
```gitignore
.env
.env.*
*.key
__pycache__/
node_modules/
```

---

## 7. Yêu cầu nộp bài

### 5 phần trong Submission Form
1. **Thông tin đội** — tên đội unique, tối đa 60 ký tự.
2. **Track** — Chat Agent / Data Analysis / Coding & Automation.
3. **Thành viên** — Team Lead bắt buộc; thành viên 2–3 tùy chọn (email `@vng.com.vn`).
4. **Thông tin dự án** — Tên agent · Tagline · Problem · Solution · Value · Voter guide.
5. **Links** — AgentBase project link + Video demo (YouTube unlisted / OneDrive share internal).

### Tiêu chí PASS (phải đạt CẢ 3)
1. Agent đang **RUNNING** trên AgentBase (BTC gọi thử ≥1 request thành công).
2. **Video demo** 2–3 phút, xem được bằng tài khoản `@vng.com.vn`, đúng track đã đăng ký.
3. **Mô tả use case** đầy đủ: README + mô tả ≤300 ký tự; nêu rõ problem, user, solution. Không để trống / placeholder / lorem ipsum.

> Lý do FAIL phổ biến: **agent không chạy** hoặc **repo để private**.

### Checklist trước khi submit
- [ ] Agent đang RUNNING trên AgentBase.
- [ ] Video accessible bằng `@vng.com.vn` (YouTube unlisted hoặc OneDrive share internal).
- [ ] GitHub repo để PUBLIC (từ lúc submit đến hết voting 03/07).
- [ ] README không để trống (tối thiểu: tên agent, mô tả, cách chạy).
- [ ] **Khai báo trong README:** "Agent phát triển với hỗ trợ của Claude Code (tài khoản cá nhân, chi phí do đội tự chi trả); agent runtime chạy bằng model MaaS." (theo FAQ rulebook — dùng model ngoài MaaS phải khai báo + tự chịu chi phí).

---

## 8. Quy trình sau submit

**PASS** → nhận email xác nhận; giữ agent RUNNING + repo PUBLIC; vào vòng voting 22/06–03/07.

**FAIL** → nhận email kèm lý do + link chỉnh sửa; sửa trước **18/06 12:00 (cứng)**; sau đó coi như rút lui.

---

## 9. CHECKLIST — Việc đầu tiên cần làm (cá nhân hóa cho Claude Code)

### A. Setup tài nguyên & môi trường
- [ ] **Kiểm tra email BTC**: có đủ account portal + mật khẩu tạm, Client ID, Client Secret, API Key. Thiếu → báo BTC qua Teams ngay.
- [ ] **Đăng nhập GreenNode AI Portal + đổi mật khẩu** (OTP về SĐT đã đăng ký).
- [ ] **Rotate lại API Key + Client Secret** nếu chúng đã từng lộ ra ngoài; lưu giá trị mới vào `.env`.
- [ ] **Kiểm tra Claude Code chạy đúng tài khoản cá nhân**: gõ `/status`, xác nhận base URL của Anthropic (không phải minimax/vngcloud). Dọn biến `ANTHROPIC_*` cũ trong `.zshrc`/`.bashrc` nếu có.
- [ ] **Cài Docker Desktop** và mở cho chạy nền.
- [ ] **Chuẩn bị GitHub** (account + Git CLI). Tạo repo mới, để PUBLIC, copy link.
- [ ] **Clone bộ skill** `greennode-agentbase-skills` vào folder cùng cấp với agent.
- [ ] **Đặt nhắc lịch cứng**: 17/06 12:00 Submit + mốc đệm riêng (vd 16/06 tối).
- [ ] **Vào Group Teams** hỗ trợ (QR / link email).
- [ ] **Ghi sẵn dòng khai báo README** (Claude Code + runtime MaaS).
- [ ] (Khuyến nghị) Nhắn BTC xác nhận: dùng Claude Code để build có cần khai báo gì thêm không.

### B. Build agent đầu tiên
- [ ] Chốt **use case** + chọn **track**.
- [ ] Viết **Spec Kit**: problem, user, input/output, kịch bản sử dụng.
- [ ] Prompt Claude Code build agent theo spec.
- [ ] Kết nối tool/MCP nếu cần (gọi dịch vụ bên ngoài).
- [ ] Test agent ở local.

### C. Deploy & verify
- [ ] Prompt deploy qua bộ skill; điền Client ID/Secret + API Key + model + runtime size.
- [ ] Đợi Docker build/push; kiểm tra **ACTIVE** trên portal; lấy endpoint public.
- [ ] Test endpoint (gọi API / mở web view).
- [ ] Push source code lên GitHub (repo PUBLIC).

### D. Submit
- [ ] Quay video demo 2–3 phút (accessible bằng `@vng.com.vn`).
- [ ] Hoàn thiện README (mô tả + cách chạy + khai báo model).
- [ ] Điền Submission Form đầy đủ 5 phần.
- [ ] Chạy lại checklist mục 7 trước khi bấm nộp.

---

## 10. Prompt mẫu để bắt đầu (gợi ý từ BTC)

- `Tạo giúp tôi một agent đọc và phân tích các bài báo mới nhất trên VNExpress trong 1 tuần qua qua giao diện chat`
- `Tạo giúp tôi một agent tổng hợp video trên Youtube từ link tôi đưa vào qua website`
- `Tạo giúp tôi bảng so sánh giá H100 từ top 10 nhà cung cấp cloud theo thời gian thực`
- `Tạo giúp tôi agent tổng hợp lịch họp và gửi qua Telegram mỗi đầu tuần`

---

## 11. Hỗ trợ

- **Group Teams chung cuộc thi** (link gửi qua email) — raise lỗi nhanh, SLA 4 giờ trong giờ làm việc.
- **Repo bộ skill:** https://github.com/vngcloud/greennode-agentbase-skills
- Lỗi thường gặp (Troubleshooting trong User Guide): chưa nhận email, chưa cài Docker, skill đặt sai cấp thư mục, agent không ACTIVE, repo còn private.

# context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding. A single unrouted command can dump 56 KB into context and waste the entire session.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Any Bash command containing `curl` or `wget` is intercepted and replaced with an error message. Do NOT retry.
Instead use:
- `ctx_fetch_and_index(url, source)` to fetch and index web pages
- `ctx_execute(language: "javascript", code: "const r = await fetch(...)")` to run HTTP calls in sandbox

### Inline HTTP — BLOCKED
Any Bash command containing `fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, or `http.request(` is intercepted and replaced with an error message. Do NOT retry with Bash.
Instead use:
- `ctx_execute(language, code)` to run HTTP calls in sandbox — only stdout enters context

### WebFetch — BLOCKED
WebFetch calls are denied entirely. The URL is extracted and you are told to use `ctx_fetch_and_index` instead.
Instead use:
- `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` to query the indexed content

## REDIRECTED tools — use sandbox equivalents

### Bash (>20 lines output)
Bash is ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`, and other short-output commands.
For everything else, use:
- `ctx_batch_execute(commands, queries)` — run multiple commands + search in ONE call
- `ctx_execute(language: "shell", code: "...")` — run in sandbox, only stdout enters context

### Read (for analysis)
If you are reading a file to **Edit** it → Read is correct (Edit needs content in context).
If you are reading to **analyze, explore, or summarize** → use `ctx_execute_file(path, language, code)` instead. Only your printed summary enters context. The raw file content stays in the sandbox.

### Grep (large results)
Grep results can flood context. Use `ctx_execute(language: "shell", code: "grep ...")` to run searches in sandbox. Only your printed summary enters context.

## Tool selection hierarchy

1. **GATHER**: `ctx_batch_execute(commands, queries)` — Primary tool. Runs all commands, auto-indexes output, returns search results. ONE call replaces 30+ individual calls.
2. **FOLLOW-UP**: `ctx_search(queries: ["q1", "q2", ...])` — Query indexed content. Pass ALL questions as array in ONE call.
3. **PROCESSING**: `ctx_execute(language, code)` | `ctx_execute_file(path, language, code)` — Sandbox execution. Only stdout enters context.
4. **WEB**: `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` — Fetch, chunk, index, query. Raw HTML never enters context.
5. **INDEX**: `ctx_index(content, source)` — Store content in FTS5 knowledge base for later search.

## Subagent routing

When spawning subagents (Agent/Task tool), the routing block is automatically injected into their prompt. Bash-type subagents are upgraded to general-purpose so they have access to MCP tools. You do NOT need to manually instruct subagents about context-mode.

## Output constraints

- Keep responses under 500 words.
- Write artifacts (code, configs, PRDs) to FILES — never return them as inline text. Return only: file path + 1-line description.
- When indexing content, use descriptive source labels so others can `ctx_search(source: "label")` later.

## ctx commands

| Command | Action |
|---------|--------|
| `ctx stats` | Call the `ctx_stats` MCP tool and display the full output verbatim |
| `ctx doctor` | Call the `ctx_doctor` MCP tool, run the returned shell command, display as checklist |
| `ctx upgrade` | Call the `ctx_upgrade` MCP tool, run the returned shell command, display as checklist |
