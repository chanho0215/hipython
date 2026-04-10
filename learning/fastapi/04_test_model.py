# test_model.py

from transformers import pipeline

# 모델 로드 (처음 실행 시 다운로드)
classifier = pipeline(
    "text-classification",
    model="snunlp/KR-FinBert-SC"
)

# 테스트 문장
sentences = [
    "삼성전자 영업이익 10조 돌파, 사상 최대 실적",
    "코스피 급락, 외국인 대규모 매도세",
    "한국은행 기준금리 동결 결정"
]

for sentence in sentences:
    result = classifier(sentence)
    print(f"텍스트: {sentence}")
    print(f"결과: {result}")
    print()