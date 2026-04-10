import streamlit as st

st.title('안녕하세요')
st.write('Hello Streamlit!!!')

st.divider()

#사용자 입력을 받는 요소
name = st.text_input('이름 :')

st.write(name)



#### 버튼

def bt1_click():
  st.write('그렇구나.. 잘했어.. ')
  
  
btn1 = st.button('눌러봐')
if btn1 : 
  bt1_click()
  #st.write('정말 눌렀어??')
  

  
  
  
#### 판다스 사용하기
import pandas as pd
df = pd.read_csv('./data/vehicle_prod.csv')

# log 출력하기
print(df.info())


st.write(df.head())


