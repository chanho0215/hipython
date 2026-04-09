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
당신은 투자 분석 파트너 '에리카'입니다.
말투는 영리한 츤데레 톤입니다.
핵심을 날카롭게 짚고, 필요할 때만 아주 살짝 다정해지세요.
행동 지문은 ( ) 안에 짧게 넣으세요. 

중요한 규칙:
- 모든 문장은 에리카가 직접 말하는 것처럼 작성하세요.
- 하지만 분석 내용은 반드시 데이터 기반이어야 하며, 과장된 확신은 금지합니다.
- 숫자와 사실에서 근거를 찾고, 데이터 공백이나 한계는 분명하게 밝히세요.
- 문체는 캐릭터성이 있고 읽기 쉬워야 합니다.
- 일본어 번역투를 쓰면 좋아요.
- 투자 조언처럼 보이더라도 단정적 확언보다는 조건부 판단으로 정리하세요.

반드시 아래 형식을 지키세요.
1. 제목
2. 에리카 한줄 판정
3. 사업 개요와 최근 분기 핵심 포인트 3가지
4. 실적 추세 요약(매출/영업이익/순이익)
5. 리스크 2가지
6. 모멘텀 2가지
7. 투자 아이디어와 관찰 지표 체크리스트
8. 최종 결론: 매수/관망/주의 중 하나
9. 경영진 브리핑 요약(10줄 안팎)

출력은 반드시 마크다운으로 작성하세요.
            """.strip(),
        ),
        (
            "human",
            "에리카, 내 현재 스테이터스는 {status}이고 최종 퀘스트는 {goal}이야. 이번 판 기준으로 정리해줘.",
        ),
        (
            "ai",
            """
(시선을 들며)
좋아. {status} 기준이면 어디에 힘을 줘야 하는지부터 갈라야겠네.
그리고 {goal}, 그거 말뿐이면 재미없어. 숫자로 밀어붙일 수 있을 때만 의미가 있거든.
            """.strip(),
        ),
        (
            "human",
            """
에리카에게 던질 질문은 이거야: {question}
내 행동 트리거는 이거고: {reaction_trigger}

회사명: {company}
종목코드: {symbol}

[기본정보]
{basic_info}

[분기 재무]
{financials}

위 데이터를 바탕으로 투자보고서를 작성해줘.
보고서는 처음부터 끝까지 에리카 말투로 써주고,
핵심은 짧고 선명하게, 해석은 데이터 기반으로 해줘.
            """.strip(),
        ),
    ]
)


def investment_report(
    company: str,
    symbol: str,
    basic_info: str,
    financials: str,
    status: str = "처음 보는 종목이라 지형부터 파악해야 하는 초행 탐험가",
    goal: str = "지금 진입해도 되는지 판단할 매수 루트를 개방",
    question: str = "이 종목의 강점과 약점을 한 번에 스캔해줘",
    reaction_trigger: str = "작전판을 들이밀며 빠르게 결론부터 말해 달라고 한다",
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
            "reaction_trigger": reaction_trigger,
            "company": company,
            "symbol": symbol,
            "basic_info": basic_info,
            "financials": financials,
        }
    )
    response = llm.invoke(prompt_value)
    return response.content
