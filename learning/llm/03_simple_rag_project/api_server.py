from __future__ import annotations

import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from memory_store import stream_answer_with_cache
from rag_chain import load_rag_chain

# API 서버도 Streamlit과 같은 PDF를 바라보게 해두면
# UI만 달라도 같은 RAG 로직을 공유할 수 있다.
BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "data" / "samsung_manual.pdf"

app = FastAPI(title="Samsung Manual RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    # 지금은 단순한 단일 질문만 받지만,
    # 이후 대화형 컨텍스트를 붙일 수 있게 요청 모델을 분리해둔다.
    question: str


class ChainState:
    def __init__(self) -> None:
        # 체인 준비 상태를 별도 객체로 분리해두면
        # startup / health / chat에서 같은 상태를 안전하게 공유하기 쉽다.
        self.lock = threading.Lock()
        self.status = "loading"
        self.message = "매뉴얼을 읽는 중입니다."
        self.chain = None

    def set_ready(self, chain) -> None:
        with self.lock:
            self.chain = chain
            self.status = "ready"
            self.message = "매뉴얼 준비가 완료되었습니다."

    def set_error(self, message: str) -> None:
        with self.lock:
            self.chain = None
            self.status = "error"
            self.message = message

    def snapshot(self) -> dict[str, str]:
        with self.lock:
            return {"status": self.status, "message": self.message}

    def get_chain(self):
        with self.lock:
            return self.chain


state = ChainState()


def _build_chain() -> None:
    # FastAPI 서버는 먼저 뜨고, 무거운 문서 로딩은 백그라운드에서 진행한다.
    # 이렇게 해야 프론트가 health를 보면서 "읽는 중" 상태를 표현할 수 있다.
    try:
        if not PDF_PATH.exists():
            raise FileNotFoundError(f"`data/{PDF_PATH.name}` 파일이 없습니다.")

        chain = load_rag_chain(str(PDF_PATH))
        state.set_ready(chain)
    except Exception as exc:  # pragma: no cover
        state.set_error(str(exc))


@app.on_event("startup")
def startup_event() -> None:
    # startup 훅에서 별도 스레드로 체인을 만들면
    # API 프로세스가 시작 단계에서 오래 막히지 않는다.
    thread = threading.Thread(target=_build_chain, daemon=True)
    thread.start()


@app.get("/health")
def health() -> dict[str, str]:
    # 프론트는 이 엔드포인트를 주기적으로 호출하면서
    # "로딩 중 / 준비 완료 / 오류" 상태를 결정한다.
    return state.snapshot()


@app.post("/chat")
def chat(payload: ChatRequest):
    chain = state.get_chain()
    if chain is None:
        snapshot = state.snapshot()
        raise HTTPException(status_code=503, detail=snapshot["message"])

    def generate():
        # 스트리밍 응답과 캐시 저장을 같은 제너레이터에서 처리한다.
        for chunk in stream_answer_with_cache(chain, payload.question):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
