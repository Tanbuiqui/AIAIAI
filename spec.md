# Spec Kit — Meeting Sticky Notes Agent

> Bản thiết kế (design doc) cho Claw-a-thon 2026. CHƯA code — đây là bản chốt ý tưởng + kiến trúc + việc cần làm.
> Cập nhật: 2026-06-12.

---

## 1. Tổng quan

| Mục | Nội dung |
|---|---|
| **Tên (tạm)** | MeetingNote / Sticky (chốt sau) |
| **Track** | Chat Agent |
| **Một câu** | Biến bản ghi âm / transcript cuộc họp lộn xộn thành **bảng sticky note** các việc cần làm, quyết định và câu hỏi mở. |
| **Model MaaS** | Minimax (tiếng Việt tốt, context dài). Dự phòng: Qwen. |
| **Runtime size** | `2x4-general` (đủ — không self-host model nặng). |

### Problem
Họp ở tập đoàn lớn (VNG) nhiều, nội dung trôi nhanh, người tham gia không nắm hết — quên ai phải làm gì, quyết định gì đã chốt.

### User
Nhân viên / team lead / PM dự VNG: sau cuộc họp cần nhanh chóng có danh sách việc + quyết định mà không phải ngồi nghe/đọc lại.

### Solution
Upload file ghi âm **hoặc** dán transcript → agent bóc băng (nếu audio) → LLM phân tích, **lọc nhiễu**, trích xuất → hiển thị bảng sticky note 4 nhóm, có trích dẫn câu gốc, cho sửa/xóa/copy.

### Value
Tiết kiệm 15–30 phút viết biên bản mỗi cuộc họp; không bỏ sót action item; ai cũng dùng được → tiềm năng vote cao.

---

## 2. Phạm vi (scope)

### v1 — BẮT BUỘC (để submit 17/06, đạt PASS)
- [ ] Input **dán transcript** (text dài) — đường đi cốt lõi, chắc ăn.
- [ ] LLM phân tích → 4 nhóm sticky note:
  - 🟡 Chủ đề / vấn đề chính
  - 🔴 Action items (người – việc – deadline – ưu tiên)
  - 🟢 Quyết định đã chốt
  - 🔵 Câu hỏi mở / cần follow-up
- [ ] Mỗi note kèm **câu trích dẫn gốc** (chống bịa).
- [ ] **Web view**: trang dán text + render bảng sticky note + nút copy/tải.
- [ ] `POST /invocations` (JSON) cho BTC test + `GET /health`.

### v2 — NÊN CÓ (làm nếu kịp, là điểm "wow")
- [ ] Input **upload file ghi âm** (.mp3/.m4a/.wav) → STT → transcript → cùng pipeline.
- [ ] Cho **sửa/xóa** note ngay trên bảng.
- [ ] Xuất Markdown / copy từng cột.

### v3 — STRETCH (sau submit, cho voting)
- [ ] Bot Telegram/Zalo (OpenClaw) gửi tóm tắt.
- [ ] Kéo bản ghi từ Zalo/Drive (cần OAuth — rủi ro thời gian + rule nội bộ).

> **Nguyên tắc:** v1 không có audio vẫn PASS được. Audio là "wow", không phải điều kiện sống còn → làm sau khi v1 chạy ổn.

---

## 3. Kiến trúc

```
[Trình duyệt - Web view]                         [Container trên AgentBase :8080]
 GET /            ──────────────────────────────►  trả index.html (UI)
 dán transcript / upload file
 POST /api/analyze (JSON hoặc multipart) ───────►  ┌─ (nếu audio) STT → transcript
                                                    ├─ chunk transcript
                                                    ├─ LLM MaaS: trích xuất theo tiêu chí
                                                    ├─ gộp + khử trùng lặp
                                                    └─ pass "critic" lọc nhiễu
 render sticky notes 🟡🔴🟢🔵  ◄───────── JSON ────  trả {topics, actions, decisions, questions}

 POST /invocations (JSON, chuẩn SDK) ───────────►  cùng pipeline (cho BTC verify)
 GET /health ───────────────────────────────────►  200
```

### Runtime contract (đã xác minh)
- Platform **chỉ ép**: listen `0.0.0.0:8080` + `GET /health` → 200. Route khác tùy mình.
- Dùng được FastAPI thuần (toàn quyền route + multipart + static) HOẶC SDK `GreenNodeAgentBaseApp`.
- **Quyết định:** dùng **FastAPI** trực tiếp để chủ động phục vụ HTML + upload file; vẫn expose `POST /invocations` (JSON transcript→analysis) để BTC test theo chuẩn SDK convention.

---

## 4. Thiết kế xử lý (phần "chất xám")

1. **Chunking**: transcript dài → cắt theo đoạn (~2–3k token/đoạn, có overlap) để tránh "lạc giữa bài".
2. **Tiêu chí lọc (trong prompt)**:
   - ✅ Giữ: cam kết làm việc / giao task / quyết định chốt / deadline nêu rõ.
   - ❌ Bỏ: chào hỏi, tán gẫu, lạc đề, ý chưa chốt, lặp lại.
   - Kèm vài ví dụ few-shot.
3. **Bắt trích dẫn bằng chứng**: mỗi note phải đính câu gốc; không tìm được → không tạo note.
4. **Output JSON có schema** cố định (dễ render).
5. **Gộp + khử trùng lặp** các note giống nhau từ nhiều chunk.
6. **Pass critic**: 1 lượt LLM rà lại loại note nhiễu/sai còn sót.

### JSON output (dự kiến)
```json
{
  "topics":    [{"title": "", "summary": ""}],
  "actions":   [{"owner": "", "task": "", "deadline": "", "priority": "high|med|low", "quote": ""}],
  "decisions": [{"decision": "", "quote": ""}],
  "questions": [{"question": "", "quote": ""}]
}
```

---

## 5. Tech stack & cấu trúc file (dự kiến)

```
meeting-agent/                     ← thư mục agent (repo này)
├── main.py                        ← FastAPI: /health, /, /api/analyze, /invocations
├── pipeline.py                    ← chunk + prompt + critic + gộp
├── stt.py                         ← (v2) bóc băng audio
├── static/index.html             ← web view (dán/upload + bảng sticky note)
├── requirements.txt
├── Dockerfile                     ← FROM python:3.13-slim, EXPOSE 8080
├── .env                           ← KHÔNG commit
├── .gitignore
├── README.md
└── spec.md                        ← file này
```

### Env vars
```dotenv
LLM_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1
LLM_API_KEY=<maas-api-key>
LLM_MODEL=<model path từ portal, vd minimax...>
# (v2 nếu dùng Whisper API ngoài)
OPENAI_API_KEY=<key-whisper-neu-dung>
# Deploy (IAM — runtime tự inject khi đã deploy)
GREENNODE_CLIENT_ID=<...>
GREENNODE_CLIENT_SECRET=<...>
```

---

## 6. Quy trình deploy (đã nắm)
1. Docker Desktop chạy nền.
2. Build & push image lên **AgentBase managed Container Registry**.
3. Tạo **Custom Agent runtime** (`POST /agent-runtimes`), flavor `2x4-general`, network PUBLIC.
4. Poll status đến **ACTIVE** → lấy public endpoint (HTTPS).
5. Test: mở endpoint trên Chrome (web view) + gọi `POST /invocations`.

---

## 7. Rủi ro & cách giảm

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| STT tiếng Việt sai (audio) | TB | v1 không phụ thuộc audio; có trích dẫn để soát; cho sửa note |
| Whisper API: phí + giới hạn 25MB/file | TB | File dài → nén/cắt; hoặc bỏ audio ở v1; khai báo model ngoài trong README |
| LLM bỏ sót / bịa note | Cao | Chunking + tiêu chí + bắt trích dẫn + pass critic + cho người sửa |
| Transcript quá dài vượt context | TB | Chunking map-reduce |
| Deadline 5 ngày | Cao | Khóa v1 trước, audio/UI đẹp sau |
| Quên giữ repo PUBLIC / agent RUNNING | Cao | Checklist trước submit |

---

## 8. Quyết định còn mở (cần chốt trước khi build)
1. **STT cho audio (v2):** OpenAI Whisper API (chính xác, tốn phí, khai báo) **hay** bỏ audio để chắc v1? → đề xuất: build v1 text trước, quyết audio sau.
2. **Tên agent + tagline** chính thức.
3. **Model MaaS:** Minimax (đề xuất) — xác nhận tên/path thực tế trên portal khi deploy.

---

## 9. TODO — việc cần làm (theo thứ tự)

### Chuẩn bị (chưa cần code)
- [ ] Lấy từ portal: IAM Client ID/Secret + MaaS API Key → lưu `.env`.
- [ ] Xác nhận Docker Desktop chạy được.
- [ ] Chốt 3 "quyết định còn mở" ở mục 8.

### Build v1
- [ ] `requirements.txt` + `Dockerfile` (port 8080, /health).
- [ ] `main.py`: FastAPI + 4 route.
- [ ] `pipeline.py`: chunk + prompt + schema + critic.
- [ ] `static/index.html`: dán text → bảng sticky note.
- [ ] Test local (`localhost:8080`) với transcript mẫu.

### Deploy + submit
- [ ] Deploy qua skill → ACTIVE → lấy endpoint.
- [ ] Test endpoint public.
- [ ] README đầy đủ (mô tả + cách chạy + khai báo model).
- [ ] Repo PUBLIC.
- [ ] Quay video demo 2–3 phút.
- [ ] Điền Submission Form (5 phần).

### v2 (nếu kịp)
- [ ] `stt.py` + upload file.
- [ ] Sửa/xóa note trên UI.
```
