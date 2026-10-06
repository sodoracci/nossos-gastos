import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from database import buscar_gastos, adicionar_gasto

st.set_page_config(page_title="Nossa Organização", page_icon="💞", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
.hero {
  background: linear-gradient(135deg,#3b1f2b,#6f3550,#9a557b);
  border-radius: 22px; padding: 24px 28px; color: white; margin-bottom: 18px;
}
.card {
  padding: 18px; border-radius: 18px;
  border: 1px solid rgba(120,120,120,.18);
  background: rgba(255,255,255,.03);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>💞 Nossa Organização</h1>
  <p>Organizar hoje para construir juntos amanhã.</p>
</div>
""", unsafe_allow_html=True)

pagina = st.sidebar.radio("Navegação", ["🏠 Resumo", "➕ Novo gasto", "📋 Histórico"])

def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

@st.cache_data(ttl=20)
def carregar():
    dados = buscar_gastos()
    df = pd.DataFrame(dados or [])
    if df.empty:
        return pd.DataFrame(columns=["id","data","pessoa","descricao","categoria","tipo","valor","status","observacao"])
    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df

df = carregar()

if pagina == "🏠 Resumo":
    renda_lucas = 3168.90
    renda_julia = 1400.00
    renda_total = renda_lucas + renda_julia

    total = float(df["valor"].sum()) if not df.empty else 0.0
    total_lucas = float(df.loc[df["pessoa"].eq("Lucas"), "valor"].sum()) if "pessoa" in df.columns else 0.0
    total_julia = float(df.loc[df["pessoa"].eq("Julia"), "valor"].sum()) if "pessoa" in df.columns else 0.0
    saldo = renda_total - total

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Renda do casal", moeda(renda_total))
    c2.metric("Gastos registrados", moeda(total))
    c3.metric("Saldo estimado", moeda(saldo))
    c4.metric("Registros", len(df))

    a, b = st.columns(2)
    with a:
        st.markdown(f'<div class="card"><b>Lucas</b><h3>{moeda(renda_lucas)}</h3><p>Gastos: {moeda(total_lucas)}</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="card"><b>Julia</b><h3>{moeda(renda_julia)}</h3><p>Gastos: {moeda(total_julia)}</p></div>', unsafe_allow_html=True)

    st.markdown("### 📊 Visão dos gastos")
    if df.empty:
        st.info("Ainda não há gastos cadastrados.")
    else:
        g1, g2 = st.columns(2)
        with g1:
            pc = df.groupby("categoria", dropna=False)["valor"].sum().reset_index()
            fig = px.pie(pc, names="categoria", values="valor", hole=0.55, title="Gastos por categoria")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            pp = df.groupby("pessoa", dropna=False)["valor"].sum().reset_index()
            fig = px.bar(pp, x="pessoa", y="valor", title="Gastos por pessoa")
            st.plotly_chart(fig, use_container_width=True)

elif pagina == "➕ Novo gasto":
    st.subheader("Registrar novo gasto")
    categorias = ["Moradia","Alimentação","Mercado","Transporte","Combustível","Dívidas","Assinaturas","Lazer","Saúde","Compras","Família","Presentes","Educação","Carro","Outros"]

    with st.form("novo_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            pessoa = st.selectbox("Pessoa", ["Lucas", "Julia"])
            descricao = st.text_input("Descrição")
            categoria = st.selectbox("Categoria", categorias)
            tipo = st.selectbox("Tipo", ["Fixo", "Variável"])
        with c2:
            valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f")
            data_gasto = st.date_input("Data", value=date.today())
            status = st.selectbox("Status", ["Pago", "Pendente"])
            observacao = st.text_area("Observação")
        salvar = st.form_submit_button("💾 Registrar gasto", use_container_width=True)

    if salvar:
        if not descricao.strip():
            st.error("Preencha a descrição.")
        elif valor <= 0:
            st.error("Informe um valor maior que zero.")
        else:
            adicionar_gasto({
                "data": str(data_gasto),
                "pessoa": pessoa,
                "descricao": descricao.strip(),
                "categoria": categoria,
                "tipo": tipo,
                "valor": float(valor),
                "status": status,
                "observacao": observacao.strip(),
            })
            carregar.clear()
            st.success("✅ Gasto registrado com sucesso.")

else:
    st.subheader("📋 Histórico")
    if df.empty:
        st.info("Nenhum gasto cadastrado.")
    else:
        st.dataframe(
            df.sort_values("data", ascending=False),
            use_container_width=True,
            hide_index=True
        )
