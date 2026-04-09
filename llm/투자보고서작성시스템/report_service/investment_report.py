from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def _load_env() -> None:
    current = Path(__file__).resolve()
    for candidate in (
        current.parents[2] / ".env",
        current.parents[1] / ".env",
        current.parents[3] / ".env",
    ):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_env()

REPORT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
당신은 중립적이고 신뢰할 수 있는 투자 분석가입니다.

작성 원칙:
- 보고서는 한국어로 작성합니다.
- 과장된 표현, 연출성 강한 말투, 감정 연기, 근거 없는 확신은 사용하지 않습니다.
- 제공된 기본 정보와 분기 재무 데이터를 바탕으로 사실과 해석을 구분해 설명합니다.
- 데이터가 비어 있거나 부족한 항목은 추정으로 채우지 말고 한계를 분명히 적습니다.
- 투자 조언처럼 단정하기보다 판단 근거와 확인 포인트를 구조적으로 정리합니다.

반드시 아래 형식을 지키세요.
1. 제목
2. 핵심 한줄 요약
3. 기업 개요와 최근 분기 핵심 포인트 3가지
4. 재무 흐름 요약
5. 주요 강점 2가지
6. 주요 리스크 2가지
7. 추가 확인이 필요한 체크포인트
8. 종합 판단: 매수 검토 / 관망 / 주의 중 하나
9. 짧은 결론

출력은 마크다운으로 작성하세요.
            """.strip(),
        ),
        (
            "human",
            """
현재 검토 상황: {status}
보고서 목표: {goal}
중점 질문: {question}

회사명: {company}
티커: {symbol}

[기본 정보]
{basic_info}

[분기 재무]
{financials}

위 자료만 바탕으로 투자 보고서를 작성해 주세요.
            """.strip(),
        ),
    ]
)


def investment_report(
    company: str,
    symbol: str,
    basic_info: str,
    financials: str,
    status: str = "처음 검토하는 종목이라 사업 구조와 재무 체력을 빠르게 파악해야 합니다.",
    goal: str = "지금 시점에서 매수 검토가 가능한지 판단 근거를 정리하고 싶습니다.",
    question: str = "이 종목의 강점과 약점을 균형 있게 정리해 주세요.",
) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.4"))

    llm = ChatOpenAI(model=model_name, temperature=temperature)
    prompt_value = REPORT_PROMPT.invoke(
        {
            "status": status,
            "goal": goal,
            "question": question,
            "company": company,
            "symbol": symbol,
            "basic_info": basic_info,
            "financials": financials,
        }
    )
    response = llm.invoke(prompt_value)
    return response.content
