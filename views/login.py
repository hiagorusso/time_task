import streamlit as st
from supabase_client import supabase

def login_view():
    if 'modo_login' not in st.session_state:
        st.session_state.modo_login = 'login'  # ou 'cadastro'

    with st.container(border=True):
        if st.session_state.modo_login == 'login':
            st.title("🔐 Login")
        else:
            st.title("📝 Cadastro")

        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")

        if st.session_state.modo_login == 'cadastro':
            nome = st.text_input("Nome completo")

        col1, col2 = st.columns(2)

        if st.session_state.modo_login == 'login':
            with col1:
                if st.button("Entrar 🔑", use_container_width=True):
                    try:
                        user = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": senha
                        })
                        st.session_state.usuario = user.user
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    except Exception:
                        st.error("Erro no login: Verifique email e senha.")
            with col2:
                if st.button("Ir para Cadastro 📝", use_container_width=True):
                    st.session_state.modo_login = 'cadastro'
                    st.rerun()
        else:
            with col1:
                if st.button("Cadastrar ✅", use_container_width=True):
                    if not nome.strip():
                        st.warning("O nome não pode estar vazio.")
                    else:
                        try:
                            user = supabase.auth.sign_up({
                                "email": email,
                                "password": senha
                            })
                            user_id = user.user.id
                            # Grava nome na tabela usuarios
                            supabase.table("usuarios").upsert({
                                "user_id": user_id,
                                "nome": nome.strip()
                            }).execute()
                            st.success("Cadastro realizado com sucesso! Faça login agora.")
                            st.session_state.modo_login = 'login'
                            st.rerun()
                        except Exception as e:
                            st.error("Erro ao cadastrar: " + str(e))
            with col2:
                if st.button("Voltar para Login 🔙", use_container_width=True):
                    st.session_state.modo_login = 'login'
                    st.rerun()
