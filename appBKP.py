import streamlit as st
import pandas as pd
import io
from datetime import datetime
from supabase import create_client, Client

from streamlit_autorefresh import st_autorefresh

# Configurações do Supabase
SUPABASE_URL = "https://qppotvdhplujczuaxcid.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwcG90dmRocGx1amN6dWF4Y2lkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NDUxNjksImV4cCI6MjA2MTQyMTE2OX0.CwpOichnksU2AfEr8kLNAs48beMRpuFc8dnA2gv3ND0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Time Task", page_icon="🕐", layout="centered")

# Funções auxiliares
def formatar_tempo(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"

def carregar_tarefas(user_id):
    response = supabase.table('tarefas').select('*').eq('user_id', user_id).execute()
    if response.data:
        df = pd.DataFrame(response.data)
    else:
        df = pd.DataFrame(columns=["id", "user_id", "nome", "status", "inicio", "fim", "total", "comentario", "pausas"])
    return df

def salvar_tarefa(tarefa):
    tarefa = dict(tarefa)
    if 'id' in tarefa and tarefa['id']:
        supabase.table('tarefas').update(tarefa).eq('id', tarefa['id']).execute()
    else:
        supabase.table('tarefas').insert(tarefa).execute()

def deletar_tarefa(id):
    supabase.table('tarefas').delete().eq('id', id).execute()

def nova_tarefa(nome, user_id):
    tarefa = {
        "user_id": user_id,
        "nome": nome,
        "status": "pausada",
        "inicio": None,
        "fim": None,
        "total": 0.0,
        "comentario": "",
        "pausas": 0
    }
    salvar_tarefa(tarefa)

def pausar_tarefa_ativa(user_id):
    df = carregar_tarefas(user_id)
    tarefa_ativa = df[(df["status"] == "ativa")]
    for _, tarefa in tarefa_ativa.iterrows():
        tarefa = tarefa.to_dict()
        tempo_passado = (datetime.now() - datetime.fromisoformat(tarefa['inicio'])).total_seconds()
        tarefa['total'] += tempo_passado
        tarefa['status'] = 'pausada'
        tarefa['inicio'] = None
        tarefa['pausas'] += 1
        salvar_tarefa(tarefa)

def obter_nome_usuario(user_id, email_fallback):
    res = supabase.table("usuarios").select("nome").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]['nome']
    return email_fallback

# Função principal
def app():
    if 'usuario' not in st.session_state:
        with st.container(border=True):
            st.title("🔐 Login")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Entrar 🔑", use_container_width=True):
                    try:
                        user = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                        st.session_state.usuario = user.user
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error("Erro no login: Verifique email e senha.")
            with col2:
                if st.button("Cadastrar ✍️", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": email, "password": senha})
                        st.success("Cadastro realizado! Agora faça login.")
                    except Exception as e:
                        st.error("Erro ao cadastrar: " + str(e))
        return

    st.title("🕐 Time Task")
    user_email = st.session_state.usuario.email
    user_id = st.session_state.usuario.id
    nome_usuario = obter_nome_usuario(user_id, user_email)
    st.title(f"Bem-vindo, {nome_usuario}!")

    # Menu lateral
    with st.sidebar:
        st.header("⚙️ Configurações")
        st.markdown(f"**Usuário:** {nome_usuario}")

        # Inicializa estado do modo de edição
        if 'modo_editar_perfil' not in st.session_state:
            st.session_state.modo_editar_perfil = False

        if st.button("👤 Editar Perfil", use_container_width=True):
            st.session_state.modo_editar_perfil = True

        if st.button("📊 Relatórios e Estatísticas", use_container_width=True):
            st.session_state.modo_relatorio = True

        if st.button("🚪 Sair", use_container_width=True):
            del st.session_state.usuario
            st.success("Você saiu!")
            st.rerun()

    # Conteúdo fora do sidebar para editar o nome
    if st.session_state.get("modo_editar_perfil", False):
        st.divider()
        with st.container(border=True):
            st.subheader("👤 Perfil do Usuário")
            novo_nome = st.text_input("Editar seu nome", value=nome_usuario)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Salvar Nome"):
                    if novo_nome.strip():
                        supabase.table("usuarios").upsert({"user_id": user_id, "nome": novo_nome.strip()}).execute()
                        st.success("Nome atualizado com sucesso!")
                        st.session_state.modo_editar_perfil = False
                        st.rerun()
                    else:
                        st.warning("O nome não pode estar vazio.")
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.modo_editar_perfil = False
                    st.rerun()

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
    for idx, tarefa in df[df["status"] != "concluída"].iterrows():
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

if __name__ == "__main__":
    app()
