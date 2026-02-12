import streamlit as st

# layout 요소
col1, col2 = st.columns(2)


with col1:
  st.metric(
    '오늘의 날씨',
    value='35도',
    delta='+3',
  )
  
with col2:
  st.metric(
    '오늘의 미세먼지',
    value='좋음',
    delta='-30',
    delta_color='inverse'
  )