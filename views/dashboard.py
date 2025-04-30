import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    carregar_tarefas,
    salvar_tarefa,
    deletar_tarefa,
    nova_tarefa,
    pausar_tarefa_ativa,
    formatar_tempo,
    obter_nome_usuario
)
from supabase_client import supabase
from views.relatorio import relatorio_view

def dashboard_view():
    user_email = st.session_state.usuario.email
    user_id = st.session_state.usuario.id
    nome_usuario = obter_nome_usuario(user_id, user_email)

    if 'tela_atual' not in st.session_state:
        st.session_state.tela_atual = 'tarefas'

    st.title("🕐 Time Task")
    st.title(f"Bem-vindo, {nome_usuario}!")

    # Menu lateral
    with st.sidebar:
        st.header("⚙️ Configurações")
        st.markdown(f"**Usuário:** {nome_usuario}")

        if st.button("📋 Voltar para Tarefas", use_container_width=True):
            st.session_state.tela_atual = 'tarefas'
            st.rerun()

        if st.button("👤 Editar Perfil", use_container_width=True):
            st.session_state.tela_atual = 'editar_perfil'
            st.rerun()

        if st.button("📊 Relatórios e Estatísticas", use_container_width=True):
            st.session_state.tela_atual = 'relatorio'
            st.rerun()

        if st.button("🚪 Sair", use_container_width=True):
            del st.session_state.usuario
            st.success("Você saiu!")
            st.rerun()

    # Tela de editar perfil
    if st.session_state.tela_atual == 'editar_perfil':
        st.divider()
        with st.container(border=True):
            st.subheader("👤 Perfil do Usuário")
            novo_nome = st.text_input("Editar seu nome", value=nome_usuario)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Salvar Nome"):
                    if novo_nome.strip():
                        supabase.table("usuarios").upsert({
                            "user_id": user_id,
                            "nome": novo_nome.strip()
                        }).execute()
                        st.success("Nome atualizado com sucesso!")
                        st.session_state.tela_atual = 'tarefas'
                        st.rerun()
                    else:
                        st.warning("O nome não pode estar vazio.")
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.tela_atual = 'tarefas'
                    st.rerun()

    # Tela de relatório
    elif st.session_state.tela_atual == 'relatorio':
        st.divider()
        with st.container(border=True):
            relatorio_view(user_id)

    # Tela principal: tarefas
    else:
        df = carregar_tarefas(user_id)
        tarefa_ativa = df[(df["status"] == "ativa")]
        if not tarefa_ativa.empty:
            tarefa = tarefa_ativa.iloc[0]
            tempo_decorrido = (datetime.now() - datetime.fromisoformat(tarefa['inicio'])).total_seconds() + tarefa['total']
            st.info(f"🔵 Tarefa ativa: **{tarefa['nome']}** — ⏱️ {formatar_tempo(tempo_decorrido)}")

        with st.form("nova_tarefa"):
            nome = st.text_input("➕ Nome da nova tarefa")
            if st.form_submit_button("Criar tarefa 🚀") and nome:
                nova_tarefa(nome, user_id)
                st.success("Tarefa criada!")
                st.rerun()

        st.subheader("📋 Suas Tarefas")
        for _, tarefa in df[df["status"] != "concluída"].iterrows():
            if tarefa["user_id"] != user_id:
                continue
            with st.expander(f"📝 {tarefa['nome']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                if tarefa['status'] == 'pausada':
                    if col1.button("▶️ Iniciar", key=f"start_{tarefa['id']}"):
                        pausar_tarefa_ativa(user_id)
                        tarefa = tarefa.to_dict()
                        tarefa['status'] = 'ativa'
                        tarefa['inicio'] = datetime.now().isoformat()
                        salvar_tarefa(tarefa)
                        st.rerun()
                elif tarefa['status'] == 'ativa':
                    if col1.button("⏸️ Pausar", key=f"pause_{tarefa['id']}"):
                        tarefa = tarefa.to_dict()
                        tempo_passado = (datetime.now() - datetime.fromisoformat(tarefa['inicio'])).total_seconds()
                        tarefa['total'] += tempo_passado
                        tarefa['status'] = 'pausada'
                        tarefa['inicio'] = None
                        tarefa['pausas'] += 1
                        salvar_tarefa(tarefa)
                        st.rerun()
                if col2.button("✅ Concluir", key=f"finish_{tarefa['id']}"):
                    tarefa = tarefa.to_dict()
                    if tarefa['status'] == 'ativa':
                        tempo_passado = (datetime.now() - datetime.fromisoformat(tarefa['inicio'])).total_seconds()
                        tarefa['total'] += tempo_passado
                    tarefa['fim'] = datetime.now().isoformat()
                    tarefa['status'] = 'concluída'
                    salvar_tarefa(tarefa)
                    st.success("Tarefa concluída!")
                    st.rerun()
                if col3.button("🗑️ Deletar", key=f"delete_{tarefa['id']}"):
                    deletar_tarefa(tarefa['id'])
                    st.warning("Tarefa deletada.")
                    st.rerun()

        # Tarefas concluídas
        concluidas = df[(df["status"] == "concluída") & (df["user_id"] == user_id)]
        if not concluidas.empty:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                col1.markdown("### ✅ Tarefas Concluídas")

                if "confirmar_limpar" not in st.session_state:
                    st.session_state.confirmar_limpar = False

                if not st.session_state.confirmar_limpar:
                    if col2.button("🧹 Limpar Todas", use_container_width=True):
                        st.session_state.confirmar_limpar = True
                        st.rerun()
                else:
                    confirmar_col1, confirmar_col2 = st.columns(2)
                    if confirmar_col1.button("✅ Confirmar", use_container_width=True):
                        for idx, tarefa in concluidas.iterrows():
                            deletar_tarefa(tarefa['id'])
                        st.success("Todas as tarefas concluídas foram apagadas! 🚮")
                        st.session_state.confirmar_limpar = False
                        st.rerun()
                    if confirmar_col2.button("❌ Cancelar", use_container_width=True):
                        st.session_state.confirmar_limpar = False
                        st.rerun()

                st.divider()
                cols = st.columns(3)
                for idx, tarefa in enumerate(concluidas.itertuples()):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"**📌 {tarefa.nome}**")
                            st.caption(f"⏱️ Tempo Total: {formatar_tempo(tarefa.total)}")
                            st.caption(f"⏸️ Pausas: {tarefa.pausas}")
                            if st.button("🗑️ Apagar", key=f"delete_finalizada_{tarefa.id}"):
                                deletar_tarefa(tarefa.id)
                                st.success(f"Tarefa '{tarefa.nome}' apagada!")
                                st.rerun()
        else:
            st.info("Nenhuma tarefa concluída ainda.")
