import streamlit as st
from supabase import create_client

@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

def buscar_gastos():
    resposta = (
        supabase
        .table("gastos")
        .select("*")
        .order("data", desc=True)
        .execute()
    )
    return resposta.data

def adicionar_gasto(dados):
    return (
        supabase
        .table("gastos")
        .insert(dados)
        .execute()
    )
