# 월마트 데이터 분석 프로젝트

## 프로젝트 개요

본 프로젝트는 월마트 고객의 구매 이력 데이터를 활용하여, **도시 유형(City_Category)**, **거주 기간(Stay_In_Current_City_Years)**, **제품 카테고리** 등의 변수가 **구매 금액(Purchase)**에 미치는 영향을 분석하는 데 목적이 있다.

단순한 평균 비교를 넘어, 마스킹된 범주형 변수의 특성을 고려한 **비모수 통계 검정**과 **효과 크기(Effect Size) 분석**을 통해 실무적으로 유의미한 차이가 존재하는지 검증한다.

주요 수행 내용은 다음과 같다:
- **데이터 전처리**: 마스킹된 범주형 변수 처리 및 데이터 타입 최적화
- **탐색적 데이터 분석(EDA)**: Boxplot, Violinplot을 활용한 구매 금액 분포 시각화
- **통계적 가설 검정**: 정규성을 따르지 않는 데이터 특성을 고려한 Kruskal-Wallis, Mann-Whitney U Test 수행
- **인사이트 도출**: 통계적 유의성(p-value)과 실질적 유의성(Effect Size)을 종합한 결론 도출

## 데이터 출처

- **출처**: Kaggle Walmart Dataset
- **데이터 상세**: 약 55만 건의 사용자 거래 내역과 10개의 특징 변수

**주요 컬럼:**
- `Purchase`: 구매 금액 (Target Variable)
- `City_Category`: 도시 유형 (A, B, C - 마스킹됨)
- `Stay_In_Current_City_Years`: 현재 도시 거주 기간
- `Product_Category_1`, `2`, `3`: 제품 카테고리 (마스킹됨)
- `Occupation`, `Marital_Status`, `Age`: 고객 인구통계학적 정보

## 기술 스택

- **Python**
- **Data Manipulation**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Statistics**: SciPy (Kruskal-Wallis, Chi-square 등)

## 분석 목표

- **구매 패턴 비교**: 도시 유형 및 거주 기간에 따른 구매 금액의 분포 차이 확인
- **통계적 타당성 확보**: 마스킹된 변수 간의 차이가 통계적으로 유의미한지 검증
- **실무적 인사이트**: 단순 통계 수치를 넘어, 교차 세그먼트(City x Product) 접근 필요성 등 전략적 제언 도출