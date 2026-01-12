from __future__ import annotations
import streamlit as st
import pandas as pd

from app_lib.privacy import password_gate, safe_warning, mask_name
from app_lib.schema import ColumnMap, available_columns
from app_lib.transform import build_client_table
from app_lib.rules import classify_farol
from app_lib.credit import credit_eligibility, score_priority_credit
from app_lib.viz import plot_bar, plot_hist, plot_farol_donut

st.set_page_config(
    page_title="Carteira PF | Encarteiramento + Crédito",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

password_gate()

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
      div[data-testid="stMetricValue"] { font-size: 1.6rem; }
      .small-muted { color: rgba(230,232,238,0.7); font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Carteira PF da Agência")
st.caption("Encarteiramento (farol) + insights gerenciais para concessão de crédito em encarteirados")

with st.sidebar:
    st.markdown("### Proteção de dados")
    st.markdown(
        """
        <div class="small-muted">
        O CSV é lido apenas na sessão do navegador. Não é salvo em disco pelo app e não deve ser versionado no GitHub.
        </div>
        """,
        unsafe_allow_html=True,
    )

    salario_minimo = st.number_input("Salário mínimo (R$)", min_value=1.0, value=1412.0, step=10.0)

    st.markdown("### Upload do CSV")
    uploaded = st.file_uploader("Envie o CSV da carteira", type=["csv"], accept_multiple_files=False)

if not uploaded:
    st.info("Envie o CSV na barra lateral para iniciar.")
    st.stop()

try:
    raw = pd.read_csv(uploaded, sep=None, engine="python", encoding_errors="ignore")
except Exception:
    raw = pd.read_csv(uploaded, sep=";", engine="python", encoding_errors="ignore")

if raw.empty:
    safe_warning("Arquivo carregado, mas sem linhas.")
    st.stop()

st.success(f"Arquivo carregado com {len(raw):,} linhas e {raw.shape[1]} colunas.")

# Column mapping UI
st.markdown("## Configuração de colunas")
st.caption("Mapeie as colunas do seu CSV para os campos necessários. O mapeamento fica só nesta sessão.")

if "colmap" not in st.session_state:
    st.session_state.colmap = {}

with st.expander("Mapear colunas", expanded=True):
    cols = available_columns(raw)

    def pick(label, key, container):
        current = st.session_state.colmap.get(key, "")
        chosen = container.selectbox(label, cols, index=cols.index(current) if current in cols else 0)
        st.session_state.colmap[key] = chosen

    c1, c2, c3 = st.columns(3)
    pick("ID do cliente (código ou CPF tokenizado)", "client_id", c1)
    pick("Nome do cliente", "client_name", c2)
    pick("Data de nascimento", "birth_date", c3)

    pick("Renda (valor)", "income_value", c1)
    pick("Data da renda/faturamento", "income_date", c2)
    pick("Vínculo empregatício", "employment_link", c3)

    pick("Data do último movimento em conta", "last_movement_date", c1)
    pick("Tipo de conta (corrente, poupança, etc)", "account_type", c2)
    pick("Carteira atual", "portfolio", c3)

    pick("Restrição impeditiva (bool/flag)", "has_restrictive_flag", c1)
    pick("Em prejuízo (bool/flag)", "is_in_loss_flag", c2)
    pick("Escore (N01..N09)", "score_band", c3)

    pick("Estágio final (01..03)", "final_stage", c1)
    pick("Maior atraso em dias", "max_delay_days", c2)
    pick("Contato válido (bool/flag)", "has_valid_contact", c3)

    pick("Conta principal na agência (bool/flag)", "agency_is_main", c1)
    pick("Potencialidade (%)", "potential_pct", c2)
    pick("Saldo médio / aplicações (R$)", "avg_balance", c3)

    st.markdown("#### Campos opcionais (produto)")
    c4, c5, c6 = st.columns(3)
    pick("Nome do produto", "product_name", c4)
    pick("Grupo do produto", "product_group", c5)
    pick("Data início contrato", "contract_start_date", c6)

needed = [
    "client_id", "client_name", "last_movement_date", "account_type",
    "income_value", "income_date", "score_band", "final_stage",
    "max_delay_days", "has_valid_contact", "agency_is_main"
]
missing = [k for k in needed if not st.session_state.colmap.get(k)]
if missing:
    safe_warning(f"Mapeie pelo menos estes campos para seguir: {', '.join(missing)}")
    st.stop()

colmap = ColumnMap(mapping=st.session_state.colmap)

clients = build_client_table(raw, colmap)
clients = classify_farol(clients, salario_minimo=salario_minimo)

clients["credit_eligible"] = credit_eligibility(clients)
clients["credit_priority_score"] = score_priority_credit(clients, salario_minimo=salario_minimo)

# Global filters
st.markdown("## Filtros")
f1, f2, f3, f4 = st.columns(4)

farol_sel = f1.multiselect("Farol", ["Verde", "Vermelho", "Cinza"], default=["Verde", "Vermelho", "Cinza"])
portfolio_options = sorted([p for p in clients["portfolio"].dropna().unique().tolist() if str(p).strip()])
portfolio_sel = f2.multiselect("Carteira", portfolio_options, default=[])
min_income = f3.number_input("Renda mínima (R$)", min_value=0.0, value=0.0, step=100.0)
only_main = f4.checkbox("Somente conta principal na agência", value=False)

flt = clients.copy()
flt = flt[flt["farol"].isin(farol_sel)]
if portfolio_sel:
    flt = flt[flt["portfolio"].isin(portfolio_sel)]
flt = flt[flt["income_value"].fillna(0) >= min_income]
if only_main:
    flt = flt[flt["agency_is_main"].fillna(False)]

tabs = st.tabs(["Visão Executiva", "Perfil", "Encarteiramento", "Crédito Gerencial", "Lista Acionável"])

def metric_card(col, label, value, help_text=None):
    if help_text:
        col.metric(label, value, help=help_text)
    else:
        col.metric(label, value)

with tabs[0]:
    st.subheader("Visão Executiva")
    total_clients = flt["client_id"].nunique()
    green = int((flt["farol"] == "Verde").sum())
    red = int((flt["farol"] == "Vermelho").sum())
    gray = int((flt["farol"] == "Cinza").sum())

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    metric_card(m1, "Clientes únicos", f"{total_clients:,}")
    metric_card(m2, "Verde", f"{green:,}")
    metric_card(m3, "Vermelho", f"{red:,}")
    metric_card(m4, "Cinza", f"{gray:,}")
    metric_card(m5, "Renda mediana", f"R$ {flt['income_value'].median():,.0f}")
    metric_card(m6, "Produtos por cliente", f"{flt['products_count'].mean():.1f}")

    c1, c2 = st.columns([1, 1])
    farol_counts = flt["farol"].value_counts().reindex(["Verde", "Vermelho", "Cinza"]).dropna()
    c1.plotly_chart(plot_farol_donut(farol_counts, "Distribuição do farol"), use_container_width=True)

    by_port = (
        flt.groupby("portfolio", dropna=False)["client_id"]
        .nunique()
        .sort_values(ascending=True)
        .reset_index()
        .rename(columns={"client_id": "clientes"})
    )
    c2.plotly_chart(plot_bar(by_port, x="clientes", y="portfolio", title="Clientes por carteira"), use_container_width=True)

with tabs[1]:
    st.subheader("Perfil do público")
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(plot_hist(flt["age"], "Distribuição de idade (anos)"), use_container_width=True)
    c2.plotly_chart(plot_hist(flt["income_value"], "Distribuição de renda"), use_container_width=True)
    c3.plotly_chart(plot_hist(flt["months_since_movement"], "Recência de movimentação (meses)"), use_container_width=True)

    emp = (
        flt.assign(emp=flt["employment_link"].fillna("Não informado").astype(str).str.strip())
        .groupby("emp")["client_id"]
        .nunique()
        .sort_values(ascending=False)
        .head(12)
        .reset_index()
        .rename(columns={"client_id": "clientes"})
    )
    st.plotly_chart(plot_bar(emp.sort_values("clientes"), x="clientes", y="emp", title="Vínculo empregatício (Top 12)"), use_container_width=True)

with tabs[2]:
    st.subheader("Encarteiramento")
    st.caption("Farol aplicado por premissas. Motivos aparecem por cliente na lista acionável.")

    c1, c2 = st.columns([1, 1])

    red_df = flt[flt["farol"] == "Vermelho"].copy()
    if not red_df.empty:
        exploded = red_df.explode("farol_motivos")
        top_reasons = (
            exploded["farol_motivos"]
            .fillna("Sem motivo")
            .value_counts()
            .head(12)
            .reset_index()
            .rename(columns={"index": "motivo", "farol_motivos": "qtde"})
            .sort_values("qtde")
        )
        c1.plotly_chart(plot_bar(top_reasons, x="qtde", y="motivo", title="Principais motivos do Vermelho"), use_container_width=True)
    else:
        c1.info("Sem clientes Vermelho no filtro atual.")

    green_by_port = (
        flt[flt["farol"] == "Verde"]
        .groupby("portfolio")["client_id"]
        .nunique()
        .sort_values(ascending=True)
        .reset_index()
        .rename(columns={"client_id": "clientes_verde"})
    )
    c2.plotly_chart(plot_bar(green_by_port, x="clientes_verde", y="portfolio", title="Verde por carteira"), use_container_width=True)

with tabs[3]:
    st.subheader("Crédito Gerencial")
    base_enc = flt[flt["farol"] == "Verde"].copy()
    if base_enc.empty:
        st.info("Sem encarteirados (Verde) no filtro atual.")
        st.stop()

    eligible = int(base_enc["credit_eligible"].sum())
    pct_eligible = eligible / len(base_enc) if len(base_enc) else 0

    m1, m2, m3, m4 = st.columns(4)
    metric_card(m1, "Encarteirados", f"{len(base_enc):,}")
    metric_card(m2, "Elegíveis a crédito hoje", f"{eligible:,}", help_text="Sem prejuízo, sem restrição, atraso < 60, renda atualizada, contato válido, mov <= 6m")
    metric_card(m3, "% elegíveis", f"{pct_eligible:.0%}")
    metric_card(m4, "Score médio de prioridade", f"{base_enc['credit_priority_score'].mean():.1f}")

    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(plot_hist(base_enc["credit_priority_score"], "Score de prioridade de crédito (0-100)", nbins=24), use_container_width=True)

    delay = base_enc["max_delay_days"].fillna(0)
    delay_bucket = pd.cut(delay, bins=[-1, 0, 15, 30, 59, 9999], labels=["0", "1-15", "16-30", "31-59", "60+"])
    dly = delay_bucket.value_counts().sort_index().reset_index()
    dly.columns = ["bucket_atraso", "clientes"]
    c2.plotly_chart(plot_bar(dly, x="clientes", y="bucket_atraso", title="Atraso em dias (encarteirados)"), use_container_width=True)

    sb = base_enc["score_band"].fillna("Não informado").astype(str).str.upper().str.strip()
    sbc = sb.value_counts().reset_index()
    sbc.columns = ["score", "clientes"]
    sbc = sbc.sort_values("clientes")
    c3.plotly_chart(plot_bar(sbc, x="clientes", y="score", title="Distribuição de escore"), use_container_width=True)

    st.markdown("### Top oportunidades para oferta de crédito")
    topn = st.slider("Quantidade", min_value=20, max_value=300, value=80, step=10)
    only_eligible = st.checkbox("Mostrar somente elegíveis", value=True)

    view = base_enc.copy()
    if only_eligible:
        view = view[view["credit_eligible"]]

    view = view.sort_values("credit_priority_score", ascending=False).head(topn)

    show_pii = st.checkbox("Mostrar nomes completos", value=False, help="Deixe desligado em apresentações.")
    view_display = view.copy()
    if not show_pii:
        view_display["client_name"] = view_display["client_name"].apply(mask_name)

    out_cols = [
        "client_name", "age", "income_value", "employment_link", "score_band", "final_stage",
        "max_delay_days", "months_since_movement", "products_count", "avg_balance",
        "credit_eligible", "credit_priority_score", "farol_motivos"
    ]
    out_cols = [c for c in out_cols if c in view_display.columns]
    st.dataframe(view_display[out_cols], use_container_width=True, height=520)

with tabs[4]:
    st.subheader("Lista Acionável")
    st.caption("Filtre e priorize por crédito, potencialidade ou renda. Nomes podem ser mascarados.")

    sort_mode = st.selectbox("Ordenar por", ["Prioridade de crédito", "Potencialidade", "Renda", "Recência de movimento"])
    df_list = flt.copy()

    if sort_mode == "Prioridade de crédito":
        df_list = df_list.sort_values("credit_priority_score", ascending=False)
    elif sort_mode == "Potencialidade":
        df_list = df_list.sort_values("potential_pct", ascending=False)
    elif sort_mode == "Renda":
        df_list = df_list.sort_values("income_value", ascending=False)
    else:
        df_list = df_list.sort_values("months_since_movement", ascending=True)

    show_pii2 = st.checkbox("Mostrar nomes completos na lista", value=False)
    if not show_pii2:
        df_list["client_name"] = df_list["client_name"].apply(mask_name)

    out_cols = [
        "client_name", "farol", "portfolio", "age", "income_value", "employment_link",
        "score_band", "final_stage", "max_delay_days", "months_since_movement",
        "has_valid_contact", "agency_is_main", "avg_balance", "potential_pct",
        "products_count", "products_list", "credit_eligible", "credit_priority_score", "farol_motivos"
    ]
    out_cols = [c for c in out_cols if c in df_list.columns]

    st.dataframe(df_list[out_cols], use_container_width=True, height=680)
