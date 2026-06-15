"""Merchant Growth Agent — FastAPI server (AgentBase runtime).

Routes:
  GET  /health        -> 200 (BẮT BUỘC cho AgentBase)
  GET  /              -> web view (static/index.html)
  POST /api/upload    -> nạp CSV/Excel, tạo session, trả meta
  POST /api/analyze   -> {session_id, question} -> câu trả lời markdown
  POST /invocations   -> chuẩn SDK cho BTC test (JSON, có thể kèm dữ liệu inline)

State: DataFrame in-memory theo session_id (đủ cho demo 1 người dùng).
Container có thể restart -> báo "chưa có dữ liệu, hãy upload lại" thay vì crash.
"""

from __future__ import annotations

import base64
import os
import uuid
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import llm
from pipeline import MerchantAnalyzer, SchemaError, load_dataframe

app = FastAPI(title="Merchant Growth Agent", version="1.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# session_id -> MerchantAnalyzer (in-memory)
SESSIONS: dict[str, MerchantAnalyzer] = {}

# map intent -> phương thức phân tích
DISPATCH = {
    "overview": "overview", "decline": "decline", "growth": "growth",
    "uptrend": "uptrend", "voucher": "voucher", "churn": "churn",
    "at_risk": "at_risk", "decompose": "decompose", "forecast": "forecast",
}


# ---------------- models ----------------
class AnalyzeIn(BaseModel):
    session_id: str | None = None
    question: str


class InvocationIn(BaseModel):
    question: str | None = None
    session_id: str | None = None
    # dữ liệu inline (BTC test không qua upload UI): base64 hoặc CSV text
    file_base64: str | None = None
    csv_text: str | None = None
    filename: str | None = "data.csv"


# ---------------- helpers ----------------
def _run_analysis(analyzer: MerchantAnalyzer, question: str) -> dict[str, Any]:
    routed = llm.route_intent(question)
    intent = routed.get("intent", "unknown")
    params = routed.get("params") or {}
    method = DISPATCH.get(intent)
    if method:
        kwargs = _clean_params(params)
        if intent == "decompose":
            kwargs["question"] = question  # giúp dò tên merchant khi router không trích được
        result = getattr(analyzer, method)(**kwargs)
        answer = llm.interpret(question, result, analyzer.meta())
        return {"intent": intent, "params": params, "result": result, "answer": answer}

    # freeform / unknown / câu lạ -> để LLM tự trả lời dựa trên TOÀN BỘ số liệu đã tính
    ans = llm.interpret_freeform(question, analyzer.digest(), analyzer.meta())
    if ans:
        return {"intent": "freeform", "params": params,
                "result": {"intent": "freeform"}, "answer": ans}

    # không có LLM (fallback) -> gợi ý lại các hướng hỏi
    result = {"intent": "unknown"}
    return {"intent": intent, "params": params, "result": result,
            "answer": llm.render_fallback(result, analyzer.meta())}


def _clean_params(params: dict) -> dict:
    out = {}
    for k in ("category", "merchant_name"):
        v = params.get(k)
        if v not in (None, "", "null"):
            out[k] = v
    period = params.get("period")
    out["period"] = "week" if str(period).lower() == "week" else "month"
    if params.get("top_n"):
        try:
            out["top_n"] = int(params["top_n"])
        except (ValueError, TypeError):
            pass
    return out


# ---------------- routes ----------------
@app.get("/health")
def health():
    return {"status": "ok", "llm": llm.llm_available()}


@app.get("/")
def index():
    path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({"message": "Merchant Growth Agent — POST /invocations"}, 200)


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    content = await file.read()
    try:
        df = load_dataframe(content, file.filename or "")
        analyzer = MerchantAnalyzer(df)
    except SchemaError as e:
        return JSONResponse({"error": str(e)}, 400)
    except Exception as e:
        return JSONResponse({"error": f"Không đọc được file: {e}"}, 400)
    sid = uuid.uuid4().hex
    SESSIONS[sid] = analyzer
    return {"session_id": sid, "meta": analyzer.meta(), "series": analyzer.series_all()}


@app.post("/api/analyze")
def api_analyze(body: AnalyzeIn):
    analyzer = SESSIONS.get(body.session_id or "")
    if analyzer is None:
        return JSONResponse(
            {"error": "Chưa có dữ liệu (hoặc phiên đã hết). Hãy upload lại file CSV/Excel."},
            409,
        )
    return _run_analysis(analyzer, body.question)


@app.post("/invocations")
def invocations(body: InvocationIn):
    """Chuẩn cho BTC test. Cho phép nạp dữ liệu inline + hỏi trong 1 request."""
    analyzer = SESSIONS.get(body.session_id or "")

    # nạp dữ liệu inline nếu gửi kèm
    if analyzer is None and (body.file_base64 or body.csv_text):
        try:
            if body.file_base64:
                content = base64.b64decode(body.file_base64)
            else:
                content = body.csv_text.encode("utf-8")
            df = load_dataframe(content, body.filename or "data.csv")
            analyzer = MerchantAnalyzer(df)
            sid = uuid.uuid4().hex
            SESSIONS[sid] = analyzer
        except Exception as e:
            return JSONResponse({"error": f"Không đọc được dữ liệu inline: {e}"}, 400)

    if analyzer is None:
        return JSONResponse(
            {"error": "Chưa có dữ liệu. Gửi kèm csv_text/file_base64 hoặc upload trước."},
            409,
        )

    question = body.question or "Tổng quan tuần này"
    out = _run_analysis(analyzer, question)
    return {"output": out["answer"], **out, "meta": analyzer.meta()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
