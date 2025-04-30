import pandas as pd
from datetime import datetime
from supabase_client import supabase

def formatar_tempo(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"

def carregar_tarefas(user_id):
    response = supabase.table('tarefas').select('*').eq('user_id', user_id).execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=["id", "user_id", "nome", "status", "inicio", "fim", "total", "comentario", "pausas"])

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