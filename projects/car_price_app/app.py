import streamlit as st
from utils.predict import predict_prices

st.set_page_config(page_title="중고차 판매가격 예측", layout="centered")

def load_css():
    with open("styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

st.title("🚗 중고차 판매가격 예측")
st.caption("차량 정보를 입력하면 빠른 판매가 / 적정 판매가 / 최대 수익가를 보여줍니다.")

manufacturer_models = {
    "현대": [
        "그랜저", "쏘나타", "아반떼", "베뉴", "투싼", "싼타페", "팰리세이드",
        "스타리아", "엑센트", "i30", "i40", "스타렉스", "맥스크루즈",
        "베라크루즈", "벨로스터", "에쿠스", "캐스퍼", "제네시스 (구형)", "제네시스 쿠페"
    ],
    "기아": [
        "K3", "K5", "K7", "K8", "K9", "모닝", "레이", "셀토스", "스포티지",
        "쏘렌토", "카니발", "니로", "스팅어", "카렌스", "모하비", "프라이드"
    ],
    "제네시스": [
        "G80", "G90", "GV70", "GV80"
    ],
    "쉐보레": [
        "스파크", "말리부", "크루즈", "트랙스", "트레일블레이저", "이쿼녹스",
        "트래버스", "콜로라도", "캡티바", "올란도", "아베오", "알페온", "임팔라"
    ],
    "르노코리아": [
        "SM3", "SM5", "SM6", "SM7", "QM3", "QM5", "QM6", "XM3", "그랑 콜레오스"
    ],
    "쌍용/KG모빌리티": [
        "렉스턴", "렉스턴 스포츠", "코란도", "코란도 스포츠", "코란도 투리스모", "티볼리", "토레스"
    ]
}

color_options = ["흰색", "검정", "은색", "회색", "빨강", "파랑", "네이비", "녹색", "노랑", "주황", "갈색", "베이지", "기타"]
transmission_options = ["자동", "수동", "CVT", "DCT"]
vehicle_class_options = ["경차", "소형", "준중형", "중형", "준대형", "대형", "SUV", "RV/MPV", "스포츠카", "픽업트럭"]
seat_options = ["2인승", "4인승", "5인승", "6인승", "7인승", "8인승", "9인승 이상"]
fuel_options = ["가솔린", "디젤", "하이브리드", "LPG", "수소"]
count_options = ["없음", "1개", "2개", "3개", "4개", "5개 이상"]
option_choices = ["선루프", "LED 헤드램프", "주차감지센서", "후방카메라", "자동에어컨", "스마트키", "내비게이션", "열선시트", "통풍시트", "가죽시트"]

manufacturer = st.selectbox("제조사", list(manufacturer_models.keys()))
model = st.selectbox("모델", manufacturer_models[manufacturer])
trim = st.text_input("세부 트림", placeholder="예: 프레스티지")
year = st.number_input("연식", min_value=2000, max_value=2024, value=2020, step=1)
displacement = st.number_input("배기량(cc)", min_value=800, max_value=5000, value=1600, step=100)
fuel = st.selectbox("연료", fuel_options)
transmission = st.selectbox("변속기", transmission_options)
vehicle_class = st.selectbox("차급", vehicle_class_options)
seats = st.selectbox("좌석수", seat_options)
color = st.selectbox("색상", color_options)
mileage = st.number_input("주행거리(km)", min_value=0, max_value=500000, value=50000, step=1000)

accident = st.radio("사고 여부", ["무사고", "사고 이력 있음"], horizontal=True)

if accident == "사고 이력 있음":
    exchange_count = st.selectbox("교환 부위 개수", count_options)
    paint_count = st.selectbox("판금 부위 개수", count_options)
    insurance_count = st.selectbox("보험 이력 건수", count_options)
    corrosion = st.radio("부식 여부", ["없음", "있음"], horizontal=True)
else:
    exchange_count = "없음"
    paint_count = "없음"
    insurance_count = "없음"
    corrosion = "없음"

options = st.multiselect("주요 옵션", option_choices)

if st.button("예측하기", use_container_width=True):
    form_data = {
        "manufacturer": manufacturer,
        "model": model,
        "trim": trim,
        "year": year,
        "displacement": displacement,
        "fuel": fuel,
        "transmission": transmission,
        "vehicle_class": vehicle_class,
        "seats": seats,
        "color": color,
        "mileage": mileage,
        "accident": accident,
        "exchange_count": exchange_count,
        "paint_count": paint_count,
        "insurance_count": insurance_count,
        "corrosion": corrosion,
        "options": options,
    }

    try:
        preds = predict_prices(form_data)

        st.subheader("예측 결과")
        c1, c2, c3 = st.columns(3)
        st.markdown('<div class="section-title">추천 판매가격</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="result-card">
            <div class="price-sub">빠른 판매</div>
            <div class="price-main">{int(preds['빠른 판매']):,}만원</div>
            <div class="price-sub">1주 내 판매 가능</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="result-card recommend">
            <div class="badge-recommend">추천</div>
            <div class="price-sub">적정 판매</div>
            <div class="price-main">{int(preds['적정 판매']):,}만원</div>
            <div class="price-sub">2~3주 내 판매 가능</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="result-card">
            <div class="price-sub">최대 수익</div>
            <div class="price-main">{int(preds['최대 수익']):,}만원</div>
            <div class="price-sub">더 높은 판매가 기대</div>
        </div>
        """, unsafe_allow_html=True)

        st.success("예측이 완료되었습니다.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")