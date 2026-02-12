import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="홈카페", layout="centered")

# 스타일 적용
st.markdown("""
<style>
body {
    background-color: #111;
}

.main {
    background-color: #111;
}

.block-container {
    background-color: #1c1c1c;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.6);
}

h1 {
    text-align: center;
    letter-spacing: 2px;
}

.menu-item {
    border-bottom: 1px solid #333;
    padding: 6px 0;
}

.menu-item:last-child {
    border-bottom: none;
}

.stButton > button {
    background-color: #c49b63;
    color: #111;
    border-radius: 25px;
    padding: 10px 24px;
    border: none;
}

.stButton > button:hover {
    background-color: #e6b980;
}
</style>
""", unsafe_allow_html=True)

# 제목
st.markdown("<h1>HOME CAFE MENU</h1>", unsafe_allow_html=True)

# 메뉴 리스트
menu = ["아메리카노", "카페라떼", "바닐라라떼", "카푸치노", "브루잉커피"]

for item in menu:
    st.markdown(f"<div class='menu-item'>{item}</div>", unsafe_allow_html=True)

# 이미지
st.image(
    "image/vertical-shot-person-pouring-coffee-glass-black-background.jpg",
    use_container_width=True
)

# 버튼
if st.button("주문하기"):
    st.success("주문 기능은 연습용입니다 ☕")

st.caption("어서오세요 ☕")
