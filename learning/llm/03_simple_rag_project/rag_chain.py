from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def _load_env() -> None:
    # 단독 실행, Streamlit, API 서버 어디에서 불리든
    # 같은 방식으로 OpenAI 키를 찾도록 맞춘다.
    current = Path(__file__).resolve()
    for candidate in (
        current.parent / ".env",
        current.parent.parent / ".env",
        current.parent.parent.parent / ".env",
    ):
        if candidate.exists():
            load_dotenv(candidate, override=False)


def _format_docs(docs) -> str:
    # 모델이 근거를 더 쉽게 인용하도록
    # 페이지 번호를 문맥 문자열에 함께 붙여준다.
    formatted_docs = []
    for doc in docs:
        page = doc.metadata.get("page")
        if page is None:
            formatted_docs.append(doc.page_content)
            continue

        formatted_docs.append(f"[페이지 {page + 1}]\n{doc.page_content}")

    return "\n\n".join(formatted_docs)


def _all_docs(_: str, docs):
    # 작은 PDF는 검색보다 문서 전체를 통째로 보는 편이
    # 오히려 질문을 덜 놓치는 경우가 많다.
    return docs


def load_rag_chain(pdf_path: str, model: str = "gpt-4o-mini"):
    _load_env()

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_file}")

    # 1. PDF 로딩
    loader = PyPDFLoader(str(pdf_file))
    documents = loader.load()

    if not documents:
        raise ValueError("PDF에서 읽어온 문서가 없습니다.")

    # 텍스트 분할은 큰 문서용 기본 처리다.
    # 작은 문서에서는 아래에서 전체 문서를 그대로 쓰더라도,
    # 큰 문서로 확장될 경우를 대비해 분할 결과를 미리 만들어둔다.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    split_docs = splitter.split_documents(documents)

    # 문서가 짧으면 검색 품질보다 누락 없는 답변이 더 중요해서
    # 전체 문서를 그대로 컨텍스트로 넣는다.
    if len(documents) <= 10:
        retriever = RunnableLambda(lambda question: _all_docs(question, documents))
    else:
        # 문서가 커지면 의미 기반 검색과 키워드 검색을 섞어서
        # 표현이 다른 질문에도 덜 취약하게 만든다.
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        vector_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 6, "fetch_k": 12},
        )
        keyword_retriever = BM25Retriever.from_documents(split_docs)
        keyword_retriever.k = 4
        retriever = EnsembleRetriever(
            retrievers=[keyword_retriever, vector_retriever],
            weights=[0.45, 0.55],
        )

    # 답을 지나치게 소극적으로 막기보다,
    # 문서 범위 안에서 가장 가까운 정보를 먼저 설명하도록 유도한다.
    prompt = ChatPromptTemplate.from_template(
        """
너는 삼성전자 메모리카드 매뉴얼 전문 어시스턴트이다.
다음의 참고 문서를 바탕으로 질문에 정확하게 답하라.
참고 문서와 부분적으로라도 관련된 정보가 있으면, 그 범위 안에서 최대한 구체적으로 답하라.
질문 전체에 대한 직접 답이 없더라도 문서에서 확인되는 가장 가까운 정보를 먼저 설명하라.
정말로 관련 정보가 전혀 없을 때에만 "매뉴얼에서 확인되지 않습니다"라고 답하라.
이 매뉴얼의 범위가 특정 유틸리티나 인증 절차에 한정되어 보이면, 그 범위를 먼저 짧게 밝혀라.
가능하면 답변 끝에 근거가 된 페이지 번호를 함께 적어라.

[참고문서]
{context}

[질문]
{question}

한글로 간결하고 정확하게 답변하라.
"""
    )

    # temperature를 0으로 둬서
    # 매뉴얼형 질의응답에서는 답변 톤보다 일관성을 우선한다.
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        streaming=True,
    )

    # 최종 체인은 question -> context 구성 -> prompt -> llm -> 문자열 파싱 순서로 이어진다.
    rag_chain = (
        {
            "context": retriever | _format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
