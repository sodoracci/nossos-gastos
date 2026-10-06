import streamlit as st
from supabase import create_client

@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

def buscar_registros():
    resposta = (
        supabase
        .table("gastos")
        .select("*")
        .order("data", desc=True)
        .execute()
    )
    return resposta.data

def adicionar_registro(dados):
    return supabase.table("gastos").insert(dados).execute()

def atualizar_status(registro_id, novo_status):
    return (
        supabase
        .table("gastos")
        .update({"status": novo_status})
        .eq("id", registro_id)
        .execute()
    )

def excluir_registro(registro_id):
    return (
        supabase
        .table("gastos")
        .delete()
        .eq("id", registro_id)
        .execute()
    )

def salvar_flag(conta_id, pessoa, mes_ref, pago):
    consulta = (
        supabase
        .table("gastos")
        .select("id")
        .eq("categoria", "__FLAG__")
        .eq("descricao", conta_id)
        .eq("observacao", mes_ref)
        .execute()
    )

    existentes = consulta.data or []

    if pago:
        if not existentes:
            supabase.table("gastos").insert({
                "data": f"{mes_ref}-01",
                "pessoa": pessoa,
                "descricao": conta_id,
                "categoria": "__FLAG__",
                "tipo": "Flag",
                "valor": 0,
                "status": "Pago",
                "observacao": mes_ref,
            }).execute()
    else:
        for item in existentes:
            supabase.table("gastos").delete().eq("id", item["id"]).execute()
