import streamlit as st
from config import TEXT1_LANDING_PAGE, TEXT2_LANDING_PAGE

placeholder1 = st.empty()
placeholder2 = st.empty()
placeholder3 = st.empty()

placeholder1.markdown(TEXT1_LANDING_PAGE)
placeholder2.image(image="dashboard.png")
placeholder3.markdown(TEXT2_LANDING_PAGE)

st.sidebar.image(image="logo_sbic_round.png", use_column_width='auto')
