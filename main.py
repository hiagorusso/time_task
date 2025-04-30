import streamlit as st
from views.dashboard import dashboard_view
from views.login import login_view
from views.relatorio import relatorio_view


st.set_page_config(page_title="Time Task", page_icon="🕐", layout="centered")

def app():
    if "usuario" not in st.session_state:
        login_view()
    else:
        dashboard_view()

if __name__ == "__main__":
    app()