from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from memory_store import stream_answer_with_cache

# Streamlit 앱 기준 경로를 한 번만 잡아두면
# 실행 위치가 달라도 PDF와 .env를 안정적으로 찾을 수 있다.
BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "data" / "samsung_manual.pdf"


def _load_env() -> None:
    # Streamlit은 실행 위치가 바뀌는 경우가 있어서
    # 현재 파일 기준으로 가까운 .env 후보들을 순서대로 본다.
    current = Path(__file__).resolve()
    for candidate in (
        current.parent / ".env",
        current.parent.parent / ".env",
        current.parent.parent.parent / ".env",
    ):
        if candidate.exists():
            load_dotenv(candidate, override=False)


def _apply_styles() -> None:
    # 기본 Streamlit 느낌을 걷어내고
    # 첫 화면은 가운데 소개, 이후에는 채팅 중심 레이아웃처럼 보이게 조정한다.
    st.markdown(
        """
        <style>
        [data-testid="stHeader"] {
            height: 0;
            background: transparent;
        }
        [data-testid="stToolbar"] {
            right: 0.75rem;
            top: 0.5rem;
        }
        [data-testid="stDecoration"] {
            display: none;
        }
        .stApp {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        }
        .block-container {
            max-width: 780px;
            padding-top: 1.25rem;
            padding-bottom: 6rem;
        }
        .center-shell {
            min-height: calc(100vh - 12rem);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .center-card {
            width: 100%;
            max-width: 620px;
            text-align: center;
        }
        .center-title {
            font-size: 2rem;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: -0.02em;
            margin-bottom: 0.7rem;
        }
        .center-copy {
            color: #475569;
            font-size: 1rem;
            line-height: 1.7;
            margin-bottom: 1.1rem;
        }
        .hint-row {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_rag_chain(pdf_path: str, pdf_mtime: float):
    # PDF 수정 시간이 바뀌면 캐시를 자동 갱신하려고
    # 실제 사용하지 않는 pdf_mtime도 인자로 함께 받는다.
    del pdf_mtime
    from rag_chain import load_rag_chain

    return load_rag_chain(pdf_path)


def _render_history() -> None:
    # Streamlit은 rerun 기반이기 때문에
    # 저장된 대화 내역을 매번 다시 그려주는 방식으로 동작한다.
    for message in st.session_state.messages:
        avatar = "🧑" if message["role"] == "user" else "📖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])


def _load_chain():
    # 질문 입력보다 먼저 문서를 읽어두는 구조라서
    # 앱 진입 시점에 체인 준비 상태를 여기서 한 번 정리한다.
    if not os.getenv("OPENAI_API_KEY"):
        return None, "`OPENAI_API_KEY`가 설정되지 않았습니다. `.env` 파일을 확인해주세요."

    if not PDF_PATH.exists():
        return None, f"`data/{PDF_PATH.name}` 파일이 없습니다. PDF를 넣어주세요."

    try:
        with st.spinner("매뉴얼을 읽는 중입니다. 잠시만 기다려주세요..."):
            chain = get_rag_chain(str(PDF_PATH), PDF_PATH.stat().st_mtime)
        return chain, None
    except ModuleNotFoundError as exc:
        missing = exc.name or "필수 패키지"
        return None, f"`{missing}` 패키지가 없어 실행할 수 없습니다. 필요한 라이브러리를 먼저 설치해주세요."
    except Exception as exc:  # pragma: no cover
        return None, f"초기화 중 오류가 발생했습니다: {exc}"


def _render_center_intro(init_error: str | None) -> None:
    # 첫 질문 전에는 중앙 인트로 화면만 보여주고,
    # 대화가 시작되면 일반 채팅 화면으로 자연스럽게 넘어가게 한다.
    st.markdown('<div class="center-shell"><div class="center-card">', unsafe_allow_html=True)
    st.markdown('<div class="center-title">삼성 메모리카드 매뉴얼 챗봇</div>', unsafe_allow_html=True)

    if init_error:
        st.markdown('<div class="center-copy">지금은 준비를 마치지 못했어요.</div>', unsafe_allow_html=True)
        st.error(init_error)
    else:
        st.markdown(
            """
            <div class="center-copy">
                인증 유틸리티 사용 방법과 지원 조건을 매뉴얼 기준으로 바로 찾아드릴게요.
                궁금한 점을 아래 입력창에 적어보세요.
            </div>
            <div class="hint-row">
                예: 인증 가능한 제품 조건은 무엇인가요?<br/>
                예: 카드가 연결되지 않으면 어떤 메시지가 나오나요?
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)


_load_env()

st.set_page_config(
    page_title="삼성 메모리카드 매뉴얼 챗봇",
    page_icon="📖",
    layout="centered",
)

_apply_styles()

if "messages" not in st.session_state:
    # 첫 진입 시에는 안내 화면만 보이게 하고,
    # 실제 메시지는 첫 질문부터 쌓기 시작한다.
    st.session_state.messages = []

chain, init_error = _load_chain()

if st.session_state.messages:
    _render_history()
else:
    _render_center_intro(init_error)

user_question = st.chat_input("예: 지원 운영체제와 언어는 무엇인가요?")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_question)

    with st.chat_message("assistant", avatar="📖"):
        if chain is None:
            answer = init_error or "현재는 답변을 생성할 수 없습니다."
            st.markdown(answer)
        else:
            try:
                # 같은 질문은 인메모리 캐시에서 바로 꺼내고,
                # 처음 보는 질문만 실제 RAG 체인으로 흘려보낸다.
                answer = st.write_stream(stream_answer_with_cache(chain, user_question))
            except Exception as exc:  # pragma: no cover
                answer = f"답변 생성 중 오류가 발생했습니다: {exc}"
                st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
