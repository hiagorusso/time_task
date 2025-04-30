# relatorio.py
import streamlit as st
import pandas as pd
import io
from utils import carregar_tarefas, formatar_tempo

def relatorio_view(user_id):
    st.subheader("📊 Relatórios e Estatísticas")

    df = carregar_tarefas(user_id)

    if df.empty:
        st.info("Nenhuma tarefa encontrada para exibir.")
        return

    # Formatar tempo total
    df['tempo_total'] = df['total'].apply(formatar_tempo)
    df = df.rename(columns={
        "nome": "Nome",
        "status": "Status",
        "tempo_total": "Tempo Total",
        "comentario": "Comentário",
        "pausas": "Pausas",
        "inicio": "Início",
        "fim": "Fim"
    })

    # Filtros opcionais
    status_filtro = st.selectbox("Filtrar por status", ["Todas"] + df["Status"].unique().tolist())
    if status_filtro != "Todas":
        df = df[df["Status"] == status_filtro]

    st.dataframe(df[["Nome", "Status", "Tempo Total", "Pausas", "Comentário", "Início", "Fim"]])


    # Exportar
    with st.container(border=False):
        col1, col2 = st.columns(2)
        buffer = io.BytesIO()
        with col1:
            df.to_excel(buffer, index=False)
            st.download_button("⬇️ Baixar Excel", buffer.getvalue(), file_name="relatorio_tarefas.xlsx")

        with col2:
            if st.button("🔙 Voltar"):
                st.session_state.tela_atual = 'tarefas'
                st.rerun()
