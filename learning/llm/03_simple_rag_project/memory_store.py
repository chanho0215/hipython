from __future__ import annotations

from threading import Lock
from typing import Generator


class InMemoryAnswerStore:
    # 캐시 규칙이 달라졌을 때 이전 답변을 자연스럽게 무효화하려고 버전을 키에 포함한다.
    CACHE_VERSION = "v2"

    def __init__(self) -> None:
        self._lock = Lock()
        self._answers: dict[str, str] = {}

    @staticmethod
    def normalize(question: str) -> str:
        # 공백 차이나 대소문자 차이 때문에 같은 질문이 캐시를 놓치지 않게 정규화한다.
        return f"{InMemoryAnswerStore.CACHE_VERSION}::{' '.join(question.split()).strip().lower()}"

    def get(self, question: str) -> str | None:
        key = self.normalize(question)
        with self._lock:
            return self._answers.get(key)

    def set(self, question: str, answer: str) -> None:
        key = self.normalize(question)
        cleaned_answer = answer.strip()
        if not key or not cleaned_answer:
            return

        with self._lock:
            self._answers[key] = cleaned_answer


ANSWER_STORE = InMemoryAnswerStore()


def stream_answer_with_cache(chain, question: str, chunk_size: int = 24) -> Generator[str, None, None]:
    # 캐시 히트여도 한 번에 전체 문자열을 주지 않고 잘라서 내보내면
    # 프론트에서는 기존 스트리밍 UX를 그대로 유지할 수 있다.
    cached_answer = ANSWER_STORE.get(question)
    if cached_answer is not None:
        for start in range(0, len(cached_answer), chunk_size):
            yield cached_answer[start : start + chunk_size]
        return

    # 처음 보는 질문만 실제 체인을 호출하고,
    # 스트리밍하면서 동시에 최종 답변을 모아 캐시에 저장한다.
    chunks: list[str] = []
    for chunk in chain.stream(question):
        chunks.append(chunk)
        yield chunk

    ANSWER_STORE.set(question, "".join(chunks))
