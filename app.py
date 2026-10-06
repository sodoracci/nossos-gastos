import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from pathlib import Path
from calendar import monthrange

from database import (
    buscar_registros,
    adicionar_registro,
    salvar_flag,
    atualizar_status,
    excluir_registro,
)

st.set_page_config(
    page_title="Nossa Organização",
    page_icon="💞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# SEGURANÇA
# =========================================================
def exigir_pin():
    try:
        pin_correto = str(st.secrets["APP_PIN"])
    except Exception:
        st.error("🔐 Falta configurar APP_PIN nos Secrets do Streamlit Cloud.")
        st.code('APP_PIN = "crie-um-pin-para-voces"')
        st.stop()

    if st.session_state.get("autenticado"):
        return

    st.markdown(
        """
        <div class="login-box">
            <div style="font-size:44px">💞</div>
            <h2>Nossa Organização</h2>
            <p>Um espaço só de vocês dois.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    pin = st.text_input("PIN de acesso", type="password", placeholder="Digite o PIN")
    if st.button("Entrar", use_container_width=True, type="primary"):
        if pin == pin_correto:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("PIN incorreto.")
    st.stop()

# =========================================================
# ESTILO
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --vinho:#4D2334;
        --rosa:#9A557B;
        --rosa2:#B9678F;
        --creme:#F4E8D4;
        --azul:#245A8D;
        --azul-claro:#E8F1FA;
        --julia-claro:#F8EAF2;
        --verde:#2E7D32;
        --amarelo:#A86D00;
        --vermelho:#A33A3A;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.15rem;
        padding-bottom: 4rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(150,150,150,.12);
    }

    .hero {
        background:
          radial-gradient(circle at 90% 15%, rgba(255,255,255,.12), transparent 20%),
          linear-gradient(135deg, #3A1B29 0%, #692E49 55%, #A14E78 100%);
        border-radius: 28px;
        padding: 28px 32px;
        color: #FFF9F1;
        margin-bottom: 18px;
        box-shadow: 0 16px 40px rgba(0,0,0,.12);
    }

    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
        line-height: 1.05;
    }

    .hero .subtitle {
        margin-top: 10px;
        opacity: .88;
        font-size: 1.05rem;
    }

    .quote {
        margin-top: 18px;
        background: rgba(255,255,255,.10);
        border: 1px solid rgba(255,255,255,.12);
        padding: 12px 15px;
        border-radius: 14px;
        font-style: italic;
    }

    .kpi {
        border: 1px solid rgba(135,135,135,.16);
        background: rgba(255,255,255,.025);
        border-radius: 20px;
        padding: 16px 18px;
        min-height: 125px;
    }
    .kpi .label {
        opacity: .68;
        font-size: .88rem;
        margin-bottom: 8px;
    }
    .kpi .value {
        font-size: 1.72rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .kpi .detail {
        opacity: .74;
        font-size: .86rem;
        margin-top: 10px;
    }

    .person {
        border-radius: 22px;
        padding: 18px 20px;
        border: 1px solid rgba(135,135,135,.14);
    }
    .lucas { background: linear-gradient(135deg, rgba(36,90,141,.14), rgba(36,90,141,.03)); }
    .julia { background: linear-gradient(135deg, rgba(154,85,123,.16), rgba(154,85,123,.03)); }

    .section-title {
        font-size: 1.45rem;
        font-weight: 800;
        margin: 26px 0 12px 0;
    }

    .pill {
        display:inline-block;
        padding:5px 10px;
        border-radius:999px;
        font-size:.78rem;
        font-weight:700;
        margin-right:6px;
    }

    .login-box {
        max-width: 520px;
        margin: 8vh auto 24px auto;
        text-align:center;
        padding: 32px;
        border-radius: 28px;
        background: linear-gradient(135deg, rgba(77,35,52,.18), rgba(154,85,123,.08));
        border: 1px solid rgba(154,85,123,.20);
    }

    .note {
        border-left: 4px solid #9A557B;
        padding: 12px 14px;
        background: rgba(154,85,123,.06);
        border-radius: 0 14px 14px 0;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
    }

    .stButton > button {
        border-radius: 12px;
        font-weight: 700;
    }

    @media (max-width: 800px) {
        .hero h1 { font-size: 1.8rem; }
        .hero { padding: 22px; }
        .kpi .value { font-size: 1.35rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

exigir_pin()

# =========================================================
# DADOS BASE
# =========================================================
RENDA_LUCAS = 3168.90
RENDA_JULIA = 1400.00
RENDA_TOTAL = RENDA_LUCAS + RENDA_JULIA

# Descontos conhecidos do salário do Lucas (informativo/editável na tela de configuração)
DESCONTOS_LUCAS = {
    "Alimentação": 60.00,
    "Seguro de vida": 1.00,
    "Cesta básica": 50.00,
    "Empréstimo BB em folha": 898.00,
}

CONTAS = [
    # JULIA - FIXAS
    {"id":"julia_telefone","pessoa":"Julia","descricao":"Telefone","categoria":"Telefone","tipo":"Fixo","valor":66.00,"dia":5},
    {"id":"julia_faculdade","pessoa":"Julia","descricao":"Faculdade","categoria":"Educação","tipo":"Fixo","valor":123.00,"dia":20},

    # JULIA - PARCELAS
    {"id":"julia_gro","pessoa":"Julia","descricao":"Empréstimo GRO","categoria":"Empréstimos","tipo":"Parcela","valor":403.70,"inicio":"2026-05","fim":"2026-10"},
    {"id":"julia_lais","pessoa":"Julia","descricao":"Laís - Prima","categoria":"Compras","tipo":"Parcela","valor":133.89,"inicio":"2026-09","fim":"2026-10"},
    {"id":"julia_magalu","pessoa":"Julia","descricao":"Magalu","categoria":"Compras","tipo":"Parcela","valor":236.17,"inicio":"2026-10","fim":"2026-10"},
    {"id":"julia_ca","pessoa":"Julia","descricao":"C&A","categoria":"Compras","tipo":"Parcela","valor":40.00,"inicio":"2026-09","fim":"2026-11"},
    {"id":"julia_itau","pessoa":"Julia","descricao":"Empréstimo Itaú","categoria":"Empréstimos","tipo":"Parcela","valor":234.76,"inicio":"2026-04","fim":"2027-03"},
    {"id":"julia_renner","pessoa":"Julia","descricao":"Renner","categoria":"Compras","tipo":"Parcela","valor":39.00,"inicio":"2025-07","fim":"2027-06"},
    {"id":"julia_carro","pessoa":"Julia","descricao":"Carro","categoria":"Carro","tipo":"Parcela","valor":375.00,"inicio":"2026-10","fim":"2027-07"},
    {"id":"julia_facio","pessoa":"Julia","descricao":"Fácio","categoria":"Empréstimos","tipo":"Parcela","valor":374.00,"inicio":"2026-10","fim":"2026-10"},
    {"id":"julia_bilib","pessoa":"Julia","descricao":"Bilib","categoria":"Empréstimos","tipo":"Parcela","valor":284.00,"inicio":"2026-10","fim":"2026-10"},
    {"id":"julia_shopee_out","pessoa":"Julia","descricao":"Shopee - Out/26","categoria":"Compras","tipo":"Parcela","valor":711.46,"inicio":"2026-10","fim":"2026-10"},
    {"id":"julia_shopee_nov","pessoa":"Julia","descricao":"Shopee - Nov/26","categoria":"Compras","tipo":"Parcela","valor":449.77,"inicio":"2026-11","fim":"2026-11"},
    {"id":"julia_shopee_dez","pessoa":"Julia","descricao":"Shopee - Dez/26","categoria":"Compras","tipo":"Parcela","valor":238.79,"inicio":"2026-12","fim":"2026-12"},
    {"id":"julia_doc_carro","pessoa":"Julia","descricao":"Documento do carro","categoria":"Carro","tipo":"Parcela","valor":600.00,"inicio":"2026-10","fim":"2026-10"},
    {"id":"julia_boticario_1","pessoa":"Julia","descricao":"O Boticário - 66,66","categoria":"Compras","tipo":"Parcela","valor":66.66,"inicio":"2026-09","fim":"2026-11"},
    {"id":"julia_boticario_2","pessoa":"Julia","descricao":"O Boticário - 95,38","categoria":"Compras","tipo":"Parcela","valor":95.38,"inicio":"2026-09","fim":"2026-11"},
    {"id":"julia_boticario_3","pessoa":"Julia","descricao":"O Boticário - 79,90","categoria":"Compras","tipo":"Parcela","valor":79.90,"inicio":"2026-10","fim":"2026-10"},
    {"id":"julia_riachuelo","pessoa":"Julia","descricao":"Riachuelo","categoria":"Compras","tipo":"Parcela","valor":375.66,"inicio":"2026-10","fim":"2026-12"},

    # LUCAS - FIXAS
    {"id":"lucas_telefone","pessoa":"Lucas","descricao":"Telefone","categoria":"Telefone","tipo":"Fixo","valor":34.00,"dia":15},
    {"id":"lucas_faculdade","pessoa":"Lucas","descricao":"Faculdade","categoria":"Educação","tipo":"Fixo","valor":138.00,"dia":15},

    # LUCAS - PARCELAS
    {"id":"lucas_nubank","pessoa":"Lucas","descricao":"Nubank","categoria":"Cartão","tipo":"Parcela","valor":289.93,"inicio":"2026-10","fim":"2027-04"},
    {"id":"lucas_lopes","pessoa":"Lucas","descricao":"Lopes","categoria":"Empréstimos","tipo":"Parcela","valor":311.00,"inicio":"2026-10","fim":"2026-11"},
    {"id":"lucas_jeitto","pessoa":"Lucas","descricao":"Jeitto","categoria":"Empréstimos","tipo":"Parcela","valor":54.31,"inicio":"2026-10","fim":"2026-12"},
    {"id":"lucas_picpay","pessoa":"Lucas","descricao":"PicPay","categoria":"Empréstimos","tipo":"Parcela","valor":211.28,"inicio":"2026-10","fim":"2026-10"},
    {"id":"lucas_carro","pessoa":"Lucas","descricao":"Carro","categoria":"Carro","tipo":"Parcela","valor":375.00,"inicio":"2026-10","fim":"2027-07"},
]

OPCIONAIS = [
    {"pessoa":"Julia","descricao":"Nubank (se usar)","valor":400.00,"dia":20},
    {"pessoa":"Julia","descricao":"PicPay (se usar)","valor":100.00,"dia":20},
]

NEGOCIAR = [
    {"pessoa":"Julia","descricao":"Simplific","valor":525.84},
    {"pessoa":"Lucas","descricao":"SuperSim","valor":633.84},
    {"pessoa":"Lucas","descricao":"Banco do Brasil","valor":1600.00},
    {"pessoa":"Lucas","descricao":"Renner","valor":2600.00},
    {"pessoa":"Lucas","descricao":"CAEDU","valor":496.00},
    {"pessoa":"Lucas","descricao":"Credsystem","valor":2769.12},
]

FRASES = [
    "Juntar dinheiro também é uma forma de amar o nosso futuro.",
    "Cada conta organizada compra um pouco mais de tranquilidade.",
    "Pequenos sacrifícios hoje. Liberdade para escolher amanhã.",
    "Nosso objetivo não é só economizar — é construir opções juntos.",
    "Um passo por mês ainda é avanço. O importante é não perder a direção.",
]

# =========================================================
# HELPERS
# =========================================================
def moeda(v):
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def mes_key(dt):
    return f"{dt.year:04d}-{dt.month:02d}"

def add_months(dt, n):
    year = dt.year + (dt.month - 1 + n) // 12
    month = (dt.month - 1 + n) % 12 + 1
    return date(year, month, 1)

def mes_label(dt):
    meses = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
    return f"{meses[dt.month-1]}/{str(dt.year)[2:]}"

def ativa_no_mes(conta, mk):
    if conta["tipo"] == "Fixo":
        return True
    if conta["tipo"] == "Parcela":
        return conta["inicio"] <= mk <= conta["fim"]
    return False

@st.cache_data(ttl=15)
def carregar_registros():
    dados = buscar_registros()
    df = pd.DataFrame(dados or [])
    if df.empty:
        return pd.DataFrame(columns=[
            "id","data","pessoa","descricao","categoria","tipo",
            "valor","status","observacao"
        ])
    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df

df = carregar_registros()

def flags_do_mes(mk):
    if df.empty:
        return set()
    f = df[
        (df["categoria"] == "__FLAG__") &
        (df["observacao"] == mk)
    ]
    return set(f["descricao"].astype(str).tolist())

def registros_financeiros():
    if df.empty:
        return df.copy()
    return df[
        ~df["categoria"].isin(["__FLAG__"]) &
        ~df["tipo"].isin(["Investimento"])
    ].copy()

def registros_investimentos():
    if df.empty:
        return df.copy()
    return df[df["tipo"] == "Investimento"].copy()

# =========================================================
# MÊS-BASE
# =========================================================
hoje = date.today()
mes_base = date(hoje.year, hoje.month, 1)
mk_base = mes_key(mes_base)
flags = flags_do_mes(mk_base)

scheduled_base = [c for c in CONTAS if ativa_no_mes(c, mk_base)]
scheduled_total = sum(c["valor"] for c in scheduled_base)
scheduled_paid = sum(c["valor"] for c in scheduled_base if c["id"] in flags)
scheduled_pending = scheduled_total - scheduled_paid

df_fin = registros_financeiros()
if not df_fin.empty:
    df_mes = df_fin[
        (df_fin["data"].dt.year == mes_base.year) &
        (df_fin["data"].dt.month == mes_base.month)
    ].copy()
else:
    df_mes = df_fin.copy()

extras_total = float(df_mes["valor"].sum()) if not df_mes.empty else 0.0
extras_paid = float(df_mes.loc[df_mes["status"].eq("Pago"), "valor"].sum()) if not df_mes.empty else 0.0
extras_pending = float(df_mes.loc[~df_mes["status"].eq("Pago"), "valor"].sum()) if not df_mes.empty else 0.0

compromissos_mes = scheduled_total + extras_total
pago_mes = scheduled_paid + extras_paid
pendente_mes = scheduled_pending + extras_pending
saldo_pos_compromissos = RENDA_TOTAL - compromissos_mes

# dívida futura estimada
divida_parcelada = 0.0
for c in CONTAS:
    if c["tipo"] != "Parcela":
        continue
    current = mes_base
    while mes_key(current) <= c["fim"]:
        if mes_key(current) >= c["inicio"]:
            divida_parcelada += c["valor"]
        current = add_months(current, 1)

divida_negociar = sum(x["valor"] for x in NEGOCIAR)

# =========================================================
# HEADER
# =========================================================
frase = FRASES[hoje.day % len(FRASES)]

h1, h2 = st.columns([3.2, 1])
with h1:
    st.markdown(
        f"""
        <div class="hero">
            <h1>💞 Nossa Organização</h1>
            <div class="subtitle">Lucas & Julia • organização financeira do casal</div>
            <div class="quote">“{frase}”</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h2:
    foto = Path("foto.jpg")
    if foto.exists():
        st.image(str(foto), use_container_width=True)
    else:
        st.markdown(
            """
            <div class="person julia" style="text-align:center; min-height:190px; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:48px">📸</div>
                <b>Foto de vocês</b>
                <small style="opacity:.65">adicione um arquivo <code>foto.jpg</code> no GitHub</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## 💞 Nossa Organização")
pagina = st.sidebar.radio(
    "Navegação",
    [
        "🏠 Resumo",
        "✅ Contas do mês",
        "➕ Novo gasto",
        "💳 Dívidas & parcelas",
        "📈 Investimentos",
        "🎯 Metas",
        "📋 Histórico",
    ],
)
st.sidebar.caption(f"Mês-base: {mes_label(mes_base)}")
if st.sidebar.button("Sair"):
    st.session_state["autenticado"] = False
    st.rerun()

# =========================================================
# PÁGINA: RESUMO
# =========================================================
if pagina == "🏠 Resumo":
    k1, k2, k3, k4 = st.columns(4)

    cards = [
        ("Renda do casal", RENDA_TOTAL, "Lucas + Julia"),
        ("Compromissos do mês", compromissos_mes, f"{mes_label(mes_base)}"),
        ("Já pago", pago_mes, "contas marcadas + gastos pagos"),
        ("Ainda a pagar", pendente_mes, "o que falta quitar"),
    ]
    for col, (label, value, detail) in zip([k1,k2,k3,k4], cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi">
                    <div class="label">{label}</div>
                    <div class="value">{moeda(value)}</div>
                    <div class="detail">{detail}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">👥 Visão individual</div>', unsafe_allow_html=True)
    l, j = st.columns(2)

    def pessoa_numeros(nome, renda):
        sched = sum(c["valor"] for c in scheduled_base if c["pessoa"] == nome)
        paid_sched = sum(c["valor"] for c in scheduled_base if c["pessoa"] == nome and c["id"] in flags)
        extra = float(df_mes.loc[df_mes["pessoa"].eq(nome), "valor"].sum()) if not df_mes.empty else 0.0
        extra_paid = float(df_mes.loc[(df_mes["pessoa"].eq(nome)) & (df_mes["status"].eq("Pago")), "valor"].sum()) if not df_mes.empty else 0.0
        comp = sched + extra
        paid = paid_sched + extra_paid
        pend = comp - paid
        return comp, paid, pend, renda - comp

    luc_comp, luc_paid, luc_pend, luc_saldo = pessoa_numeros("Lucas", RENDA_LUCAS)
    jul_comp, jul_paid, jul_pend, jul_saldo = pessoa_numeros("Julia", RENDA_JULIA)

    with l:
        st.markdown(
            f"""
            <div class="person lucas">
                <div style="opacity:.7;font-size:.85rem">LUCAS</div>
                <h2 style="margin:.2rem 0 .8rem 0">{moeda(RENDA_LUCAS)}</h2>
                <b>Compromissos:</b> {moeda(luc_comp)}<br>
                <b>Pago:</b> {moeda(luc_paid)}<br>
                <b>Pendente:</b> {moeda(luc_pend)}<br>
                <b>Saldo pós-contas:</b> {moeda(luc_saldo)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with j:
        st.markdown(
            f"""
            <div class="person julia">
                <div style="opacity:.7;font-size:.85rem">JULIA</div>
                <h2 style="margin:.2rem 0 .8rem 0">{moeda(RENDA_JULIA)}</h2>
                <b>Compromissos:</b> {moeda(jul_comp)}<br>
                <b>Pago:</b> {moeda(jul_paid)}<br>
                <b>Pendente:</b> {moeda(jul_pend)}<br>
                <b>Saldo pós-contas:</b> {moeda(jul_saldo)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">📆 Próximos 6 meses</div>', unsafe_allow_html=True)
    forecast = []
    for i in range(6):
        m = add_months(mes_base, i)
        mk = mes_key(m)
        sched = sum(c["valor"] for c in CONTAS if ativa_no_mes(c, mk))
        dyn = 0.0
        if not df_fin.empty:
            d = df_fin[(df_fin["data"].dt.year == m.year) & (df_fin["data"].dt.month == m.month)]
            dyn = float(d["valor"].sum())
        pend = sched + dyn
        if i == 0:
            pend -= scheduled_paid + extras_paid
        forecast.append({"Mês":mes_label(m),"A pagar":round(pend,2),"Renda referência":RENDA_TOTAL,"Saldo projetado":round(RENDA_TOTAL-(sched+dyn),2)})

    fdf = pd.DataFrame(forecast)
    c1, c2 = st.columns([1.5,1])
    with c1:
        fig = px.bar(
            fdf,
            x="Mês",
            y="A pagar",
            text_auto=".2s",
            title="Valor pendente / previsto",
        )
        fig.update_layout(margin=dict(l=10,r=10,t=55,b=10), height=360)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.dataframe(
            fdf.style.format({"A pagar":moeda,"Renda referência":moeda,"Saldo projetado":moeda}),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown('<div class="section-title">📊 Composição deste mês</div>', unsafe_allow_html=True)
    comp_rows = []
    for c in scheduled_base:
        comp_rows.append({"Pessoa":c["pessoa"],"Categoria":c["categoria"],"Valor":c["valor"]})
    if not df_mes.empty:
        for _, r in df_mes.iterrows():
            comp_rows.append({"Pessoa":r["pessoa"],"Categoria":r["categoria"],"Valor":r["valor"]})
    comp_df = pd.DataFrame(comp_rows)

    if not comp_df.empty:
        a,b = st.columns(2)
        with a:
            cat = comp_df.groupby("Categoria")["Valor"].sum().reset_index()
            fig = px.pie(cat, names="Categoria", values="Valor", hole=.55, title="Por categoria")
            fig.update_layout(height=390, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig, use_container_width=True)
        with b:
            pp = comp_df.groupby("Pessoa")["Valor"].sum().reset_index()
            fig = px.bar(pp, x="Pessoa", y="Valor", title="Lucas x Julia")
            fig.update_layout(height=390, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"""
        <div class="note">
            <b>Dívida parcelada estimada restante:</b> {moeda(divida_parcelada)} &nbsp; • &nbsp;
            <b>A negociar:</b> {moeda(divida_negociar)}
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# PÁGINA: CONTAS DO MÊS / FLAG
# =========================================================
elif pagina == "✅ Contas do mês":
    st.subheader(f"✅ Contas de {mes_label(mes_base)}")
    st.caption("Marque como pago e clique em **Salvar flags**. A conta sai do total pendente deste mês, mas continua nos meses futuros quando for recorrente/parcela.")

    rows = []
    for c in scheduled_base:
        rows.append({
            "ID":c["id"],
            "Pessoa":c["pessoa"],
            "Conta":c["descricao"],
            "Categoria":c["categoria"],
            "Tipo":c["tipo"],
            "Valor":c["valor"],
            "Pago":c["id"] in flags,
        })

    contas_df = pd.DataFrame(rows)

    if contas_df.empty:
        st.info("Nenhuma conta prevista para este mês.")
    else:
        edited = st.data_editor(
            contas_df,
            use_container_width=True,
            hide_index=True,
            disabled=["ID","Pessoa","Conta","Categoria","Tipo","Valor"],
            column_config={
                "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Pago": st.column_config.CheckboxColumn("Pago?", help="Marque quando a conta estiver quitada."),
            },
            key="editor_flags",
        )

        if st.button("💾 Salvar flags", type="primary", use_container_width=True):
            for _, row in edited.iterrows():
                salvar_flag(
                    conta_id=row["ID"],
                    pessoa=row["Pessoa"],
                    mes_ref=mk_base,
                    pago=bool(row["Pago"]),
                )
            carregar_registros.clear()
            st.success("Status atualizado.")
            st.rerun()

        st.divider()
        st.markdown("### Gastos extras lançados neste mês")
        if df_mes.empty:
            st.info("Nenhum gasto extra cadastrado.")
        else:
            show = df_mes[["id","pessoa","descricao","categoria","tipo","valor","status","data"]].copy()
            st.dataframe(show, use_container_width=True, hide_index=True)

# =========================================================
# PÁGINA: NOVO GASTO
# =========================================================
elif pagina == "➕ Novo gasto":
    st.subheader("➕ Registrar gasto")
    st.caption("Use para mercado, gasolina, lazer, compras e qualquer gasto que não esteja nas contas-base.")

    categorias = ["Moradia","Alimentação","Mercado","Transporte","Combustível","Dívidas","Assinaturas","Lazer","Saúde","Compras","Família","Presentes","Educação","Carro","Outros"]

    with st.form("novo_gasto", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            pessoa = st.selectbox("Quem gastou?", ["Lucas","Julia"])
            descricao = st.text_input("Descrição", placeholder="Ex.: Mercado do mês")
            categoria = st.selectbox("Categoria", categorias)
            tipo = st.selectbox("Tipo", ["Fixo extra","Variável","Avulso"])
        with c2:
            valor = st.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
            data_gasto = st.date_input("Data", value=date.today())
            status = st.selectbox("Status", ["Pendente","Pago"])
            observacao = st.text_area("Observação", placeholder="Opcional")

        salvar = st.form_submit_button("Registrar gasto", type="primary", use_container_width=True)

    if salvar:
        if not descricao.strip():
            st.error("Informe a descrição.")
        elif valor <= 0:
            st.error("Informe um valor maior que zero.")
        else:
            adicionar_registro({
                "data":str(data_gasto),
                "pessoa":pessoa,
                "descricao":descricao.strip(),
                "categoria":categoria,
                "tipo":tipo,
                "valor":float(valor),
                "status":status,
                "observacao":observacao.strip(),
            })
            carregar_registros.clear()
            st.success("Gasto registrado.")
            st.rerun()

# =========================================================
# PÁGINA: DÍVIDAS
# =========================================================
elif pagina == "💳 Dívidas & parcelas":
    st.subheader("💳 Dívidas, parcelas e negociações")

    d1,d2,d3 = st.columns(3)
    d1.metric("Parcelado restante", moeda(divida_parcelada))
    d2.metric("A negociar", moeda(divida_negociar))
    d3.metric("Total mapeado", moeda(divida_parcelada + divida_negociar))

    st.markdown("### Parcelamentos ativos")
    parcelas = []
    for c in CONTAS:
        if c["tipo"] == "Parcela" and c["fim"] >= mk_base:
            parcelas.append({
                "Pessoa":c["pessoa"],
                "Conta":c["descricao"],
                "Parcela":c["valor"],
                "Início":c["inicio"],
                "Final":c["fim"],
            })
    pdf = pd.DataFrame(parcelas)
    st.dataframe(pdf, use_container_width=True, hide_index=True)

    st.markdown("### A negociar")
    ndf = pd.DataFrame(NEGOCIAR)
    ndf.columns = ["Pessoa","Credor","Valor"]
    st.dataframe(
        ndf.style.format({"Valor":moeda}),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Gastos condicionais / se usar")
    odf = pd.DataFrame(OPCIONAIS)
    odf.columns = ["Pessoa","Conta","Limite/Valor","Dia"]
    st.dataframe(
        odf.style.format({"Limite/Valor":moeda}),
        use_container_width=True,
        hide_index=True,
    )

# =========================================================
# PÁGINA: INVESTIMENTOS
# =========================================================
elif pagina == "📈 Investimentos":
    st.subheader("📈 Investimentos")
    inv = registros_investimentos()

    total_inv = float(inv["valor"].sum()) if not inv.empty else 0.0
    luc_inv = float(inv.loc[inv["pessoa"].eq("Lucas"),"valor"].sum()) if not inv.empty else 0.0
    jul_inv = float(inv.loc[inv["pessoa"].eq("Julia"),"valor"].sum()) if not inv.empty else 0.0

    a,b,c = st.columns(3)
    a.metric("Patrimônio registrado", moeda(total_inv))
    b.metric("Lucas", moeda(luc_inv))
    c.metric("Julia", moeda(jul_inv))

    with st.expander("➕ Registrar investimento", expanded=inv.empty):
        with st.form("form_investimento", clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1:
                pessoa = st.selectbox("Pessoa", ["Lucas","Julia"], key="inv_pessoa")
                descricao = st.text_input("Produto / objetivo", placeholder="Ex.: Reserva de emergência")
                categoria = st.selectbox("Categoria", ["Reserva","Renda fixa","ETF","Ações","Dólar","Outro"])
            with c2:
                valor = st.number_input("Valor atual/aporte", min_value=0.0, step=50.0)
                data_inv = st.date_input("Data", value=date.today(), key="inv_data")
                obs = st.text_area("Instituição / observação")
            go = st.form_submit_button("Salvar investimento", type="primary", use_container_width=True)

        if go:
            if not descricao.strip() or valor <= 0:
                st.error("Informe descrição e valor.")
            else:
                adicionar_registro({
                    "data":str(data_inv),
                    "pessoa":pessoa,
                    "descricao":descricao.strip(),
                    "categoria":categoria,
                    "tipo":"Investimento",
                    "valor":float(valor),
                    "status":"Concluído",
                    "observacao":obs.strip(),
                })
                carregar_registros.clear()
                st.success("Investimento registrado.")
                st.rerun()

    if inv.empty:
        st.info("Nenhum investimento registrado ainda.")
    else:
        st.dataframe(
            inv[["data","pessoa","descricao","categoria","valor","observacao"]].sort_values("data",ascending=False),
            use_container_width=True,
            hide_index=True,
        )

# =========================================================
# PÁGINA: METAS
# =========================================================
elif pagina == "🎯 Metas":
    st.subheader("🎯 Metas do casal")
    st.caption("As metas abaixo são calculadoras rápidas. O patrimônio registrado vem da área de Investimentos.")

    inv = registros_investimentos()
    patrimonio = float(inv["valor"].sum()) if not inv.empty else 0.0

    meta_reserva = st.number_input("Meta da reserva de emergência", min_value=0.0, value=10000.0, step=500.0)
    progresso = 0 if meta_reserva <= 0 else min(patrimonio/meta_reserva, 1.0)
    st.progress(progresso)
    st.write(f"**{progresso*100:.1f}%** concluído • {moeda(patrimonio)} de {moeda(meta_reserva)}")

    st.markdown("### Quanto precisamos guardar por mês?")
    meta = st.number_input("Valor do próximo objetivo", min_value=0.0, value=5000.0, step=500.0)
    meses = st.slider("Prazo em meses", 1, 36, 12)
    aporte = meta/meses if meses else 0
    st.metric("Aporte mensal necessário", moeda(aporte))

    st.markdown(
        """
        <div class="note">
            <b>Regra do casal:</b> primeiro organização e reserva; depois aceleração de patrimônio.
            Investimento não deve ser confundido com consumo.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# PÁGINA: HISTÓRICO
# =========================================================
elif pagina == "📋 Histórico":
    st.subheader("📋 Histórico de movimentações")

    hist = df[
        ~df["categoria"].eq("__FLAG__")
    ].copy() if not df.empty else df.copy()

    if hist.empty:
        st.info("Nenhuma movimentação cadastrada.")
    else:
        c1,c2,c3 = st.columns(3)
        with c1:
            pessoas = ["Todos"] + sorted(hist["pessoa"].dropna().unique().tolist())
            fp = st.selectbox("Pessoa", pessoas)
        with c2:
            cats = ["Todas"] + sorted(hist["categoria"].dropna().unique().tolist())
            fc = st.selectbox("Categoria", cats)
        with c3:
            tipos = ["Todos"] + sorted(hist["tipo"].dropna().unique().tolist())
            ft = st.selectbox("Tipo", tipos)

        filtrado = hist.copy()
        if fp != "Todos":
            filtrado = filtrado[filtrado["pessoa"] == fp]
        if fc != "Todas":
            filtrado = filtrado[filtrado["categoria"] == fc]
        if ft != "Todos":
            filtrado = filtrado[filtrado["tipo"] == ft]

        st.metric("Total filtrado", moeda(filtrado["valor"].sum()))

        cols = ["id","data","pessoa","descricao","categoria","tipo","valor","status","observacao"]
        st.dataframe(
            filtrado[cols].sort_values("data",ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Alterar status / excluir registro")
        ids = filtrado["id"].dropna().astype(int).tolist()
        if ids:
            selecionado = st.selectbox("ID do registro", ids)
            row = filtrado[filtrado["id"].astype(int) == int(selecionado)].iloc[0]
            st.caption(f'{row["pessoa"]} • {row["descricao"]} • {moeda(row["valor"])}')

            a,b = st.columns(2)
            with a:
                novo_status = st.selectbox("Novo status", ["Pendente","Pago","Concluído"], index=1 if row["status"]=="Pago" else 0)
                if st.button("Atualizar status", use_container_width=True):
                    atualizar_status(int(selecionado), novo_status)
                    carregar_registros.clear()
                    st.success("Status atualizado.")
                    st.rerun()
            with b:
                st.write("")
                st.write("")
                if st.button("🗑️ Excluir registro", use_container_width=True):
                    excluir_registro(int(selecionado))
                    carregar_registros.clear()
                    st.success("Registro excluído.")
                    st.rerun()
