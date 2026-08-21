import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import timedelta, datetime, timezone
from google.cloud import bigquery
from google.oauth2 import service_account

# ============================================================
# 1. CONFIGURACIÓN INICIAL
# ============================================================
st.set_page_config(
    page_title="PTAR · Santa Elena",
    page_icon=":factory:", # FAVorite ICON
    layout="wide",
    initial_sidebar_state="auto",
    menu_items = {
        'About': """
        PTAR : 
        
        https://cba-produccion.apps.ingprocesos.com/dashboard/ptar
        
        PRODUCCION:
        
        https://cba-produccion.apps.ingprocesos.com/dashboard/produccion
        
        RIEGO:
        
        https://cba-produccion.apps.ingprocesos.com/dashboard/riego
       
        DEMANDA:
        
        https://cba-produccion.apps.ingprocesos.com/dashboard/principal
        """
    }
    
)

#SESSION STATE PARA CAMBIAR ENTRE OPERADOR Y ADMINISTRADOR
if 'rol_usuario' not in st.session_state:
    st.session_state['rol_usuario'] = "operador"

# ============================================================
# 2. IDENTIDAD VISUAL — tokens + estilos globales
# ============================================================

PALETTE = {
    "dark":       "#04342C",
    "mid":        "#085041",
    "aqua":       "#14B8A6",
    "aqua_soft":  "#CCFBF1",
    "bg":         "#F4F8F7",
    "card":       "#FFFFFF",
    "border":     "#DCE8E5",
    "text":       "#0B1F1B",
    "text_soft":  "#54706A",
    "red":        "#DC2626",
    "amber":      "#D97706",
    "green":      "#15803D",
}

# Tema Plotly a medida
# visual que el resto del panel (en vez del azul/rojo por defecto).
pio.templates["ptar"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, sans-serif", color=PALETTE["text"], size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[PALETTE["mid"], PALETTE["aqua"], PALETTE["amber"], PALETTE["red"]],
        xaxis=dict(gridcolor=PALETTE["border"], zeroline=False, linecolor=PALETTE["border"]),
        yaxis=dict(gridcolor=PALETTE["border"], zeroline=False, linecolor=PALETTE["border"]),
        margin=dict(l=10, r=10, t=30, b=10),
    )
)
pio.templates.default = "ptar"

# ============================================================
# 2.5 BIGQUERY — variables de eficiencia en tiempo real
# ============================================================
# ⚠️ EDITA ESTA SECCIÓN con tus tablas reales. Cada variable vive en su
# propia tabla de BigQuery (una fila por lectura, con columna de fecha/hora
# y columna de valor). El resto del panel se arma solo a partir de esto.

REFRESH_SECONDS = 45  # cada cuánto se refresca sola la vista de Eficiencia

BQ_PROJECT = "tu-proyecto-gcp"  # <-- tu project_id de GCP

VARIABLES_EFICIENCIA = {
    "flujo": {
        "label": "Flujo tratado",
        "icon": "💧",
        "unit": "m³/h",
        "table": f"{BQ_PROJECT}.plantaPalmo.flujometro_ptar",
        "col_valor": "acumulador_corregido",
        "col_fecha": "fecha",
        "decimales": 1,
        "limite_max": None,
        "limite_min": None,
    },
    "consumo_energia": {
        "label": "Consumo energético",
        "icon": "⚡",
        "unit": "kWh",
        "table": f"{BQ_PROJECT}.plantaPalmo.consumo_energia",   # <-- edita el nombre real
        "col_valor": "consumo",                                  # <-- edita el nombre real
        "col_fecha": "fecha",                                    # <-- edita el nombre real
        "decimales": 1,
        "limite_max": None,
        "limite_min": None,
    },
    "eficiencia_tratamiento": {
        "label": "Eficiencia de tratamiento",
        "icon": "🧪",
        "unit": "%",
        "table": f"{BQ_PROJECT}.plantaPalmo.eficiencia_tratamiento",  # <-- edita el nombre real
        "col_valor": "eficiencia",                                     # <-- edita el nombre real
        "col_fecha": "fecha",                                          # <-- edita el nombre real
        "decimales": 1,
        "limite_max": 100,
        "limite_min": 70,
    },
}

RANGO_HORAS = {"1 h": 1, "6 h": 6, "24 h": 24, "7 días": 24 * 7}


@st.cache_resource(show_spinner=False)
def get_bq_client():
    """Cliente de BigQuery reutilizado entre reruns — se crea una sola vez
    por sesión del servidor, no en cada refresco."""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_variable_data(table: str, col_valor: str, col_fecha: str, horas: int) -> pd.DataFrame:
    """Una sola consulta trae histórico + dato actual (última fila).
    Cacheada por REFRESH_SECONDS: aunque el fragmento se re-renderice más
    seguido por interacción del usuario, BigQuery solo se consulta una vez
    por ventana de refresco -> controla costo y latencia."""
    client = get_bq_client()
    query = f"""
        SELECT {col_fecha} AS fecha, {col_valor} AS valor
        FROM `{table}`
        WHERE {col_fecha} >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @horas HOUR)
        ORDER BY {col_fecha} ASC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("horas", "INT64", horas)]
    )
    df = client.query(query, job_config=job_config).to_dataframe()
    return df


def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

    :root {{
        --dark: {PALETTE['dark']};
        --mid: {PALETTE['mid']};
        --aqua: {PALETTE['aqua']};
        --aqua-soft: {PALETTE['aqua_soft']};
        --bg: {PALETTE['bg']};
        --card: {PALETTE['card']};
        --border: {PALETTE['border']};
        --text: {PALETTE['text']};
        --text-soft: {PALETTE['text_soft']};
        --red: {PALETTE['red']};
        --amber: {PALETTE['amber']};
        --green: {PALETTE['green']};
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }}

    h1, h2, h3, h4, .kpi-value, .brand-title {{
        font-family: 'Space Grotesk', sans-serif !important;
    }}

    /* --- Fondo general --- */
    [data-testid="stAppViewContainer"] {{
        background: var(--bg);
    }}
    [data-testid="stHeader"] {{
        background: transparent;
    }}

    /* --- Sidebar de planta --- */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--dark) 0%, var(--mid) 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }}
    [data-testid="stSidebar"] * {{
        color: #E7F3F0 !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.12);
    }}
    .sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0 2px 0;
    }}
    .sidebar-brand img {{
        width: 34px; height: 34px; border-radius: 8px;
        background: rgba(255,255,255,0.08);
        padding: 5px;
    }}
    .sidebar-brand-text .name {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        line-height: 1.1;
    }}
    .sidebar-brand-text .site {{
        font-size: 0.72rem;
        color: #9FC6BE !important;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }}

    /* --- LED de estado en vivo (mismo lenguaje que la automatización de sopladores) --- */
    .status-dot {{
        display: inline-block;
        width: 9px; height: 9px;
        border-radius: 50%;
        margin-right: 7px;
        position: relative;
        top: -1px;
    }}
    .status-dot.live {{ background: var(--green); box-shadow: 0 0 0 rgba(21,128,61,0.5); animation: pulse 2s infinite; }}
    .status-dot.warn {{ background: var(--amber); box-shadow: 0 0 0 rgba(217,119,6,0.5); animation: pulse 2s infinite; }}
    .status-dot.alert {{ background: var(--red); box-shadow: 0 0 0 rgba(220,38,38,0.5); animation: pulse 1.2s infinite; }}
    @keyframes pulse {{
        0%   {{ box-shadow: 0 0 0 0 currentColor; opacity: 1; }}
        70%  {{ box-shadow: 0 0 0 6px transparent; opacity: 0.85; }}
        100% {{ box-shadow: 0 0 0 0 transparent; opacity: 1; }}
    }}

    /* --- Encabezado de vista --- */
    .view-header {{
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        border-bottom: 1px solid var(--border);
        padding-bottom: 12px;
        margin-bottom: 22px;
    }}
    .view-header .title {{
        font-size: 1.65rem;
        font-weight: 700;
        color: var(--dark);
        margin: 0;
    }}
    .view-header .subtitle {{
        color: var(--text-soft);
        font-size: 0.92rem;
        margin-top: 2px;
    }}
    .view-header .badge {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: var(--mid);
        background: var(--aqua-soft);
        border: 1px solid var(--aqua);
        padding: 4px 10px;
        border-radius: 20px;
        white-space: nowrap;
    }}

    /* --- Tarjetas KPI --- */
    .kpi-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-left: 4px solid var(--mid);
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(4,52,44,0.04);
        height: 100%;
    }}
    .kpi-card.state-ok {{ border-left-color: var(--green); }}
    .kpi-card.state-warn {{ border-left-color: var(--amber); }}
    .kpi-card.state-alert {{ border-left-color: var(--red); }}
    .kpi-label {{
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--text-soft);
        margin-bottom: 4px;
    }}
    .kpi-value {{
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 1.55rem;
        color: var(--dark);
    }}
    .kpi-unit {{
        font-size: 0.78rem;
        color: var(--text-soft);
        margin-left: 4px;
    }}
    .kpi-sub {{
        font-size: 0.75rem;
        color: var(--text-soft);
        margin-top: 4px;
    }}

    /* --- Hero KPI (dato en vivo, más grande, para Eficiencia) --- */
    .hero-kpi {{
        background: linear-gradient(135deg, var(--card) 0%, var(--aqua-soft) 200%);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 22px 24px;
        position: relative;
        overflow: hidden;
    }}
    .hero-kpi.state-alert {{ border-color: var(--red); }}
    .hero-kpi.state-warn {{ border-color: var(--amber); }}
    .hero-kpi .hero-label {{
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-soft);
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .hero-kpi .hero-value {{
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 2.6rem;
        color: var(--dark);
        line-height: 1.15;
        margin-top: 4px;
    }}
    .hero-kpi .hero-unit {{
        font-size: 1rem;
        color: var(--text-soft);
        margin-left: 6px;
    }}
    .hero-kpi .hero-delta {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 6px;
        display: inline-block;
    }}
    .hero-delta.up {{ color: var(--green); }}
    .hero-delta.down {{ color: var(--red); }}
    .hero-delta.flat {{ color: var(--text-soft); }}
    .hero-kpi .hero-timestamp {{
        font-size: 0.75rem;
        color: var(--text-soft);
        margin-top: 10px;
    }}

    .live-caption {{
        font-size: 0.75rem;
        color: var(--text-soft);
        display: flex;
        align-items: center;
        margin-top: 10px;
    }}

    /* --- Placeholder "en construcción" --- */
    .placeholder-card {{
        border: 1px dashed var(--border);
        border-radius: 12px;
        padding: 34px 24px;
        text-align: center;
        color: var(--text-soft);
        background: repeating-linear-gradient(135deg, rgba(8,80,65,0.025) 0px, rgba(8,80,65,0.025) 10px, transparent 10px, transparent 20px);
    }}
    .placeholder-card .icon {{ font-size: 1.8rem; margin-bottom: 6px; }}
    .placeholder-card .title {{ font-family:'Space Grotesk',sans-serif; font-weight:600; color: var(--dark); font-size:1rem; margin-bottom:4px; }}

    /* --- Contenedores de control (filtros) --- */
    .filter-bar {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px 16px 4px 16px;
        margin-bottom: 18px;
    }}

    /* --- Botones --- */
    div.stButton > button {{
        background: var(--mid);
        color: #fff;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        transition: background 0.15s ease;
    }}
    div.stButton > button:hover {{
        background: var(--dark);
        color: #fff;
    }}

    /* --- Métricas nativas de Streamlit (por si se usan) --- */
    [data-testid="stMetric"] {{
        background: var(--card);
        border: 1px solid var(--border);
        border-left: 4px solid var(--mid);
        border-radius: 10px;
        padding: 12px 14px;
    }}

    /* --- Dataframes / tablas --- */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
    }}

    /* --- Alertas (usadas dentro del modal técnico) --- */
    [data-testid="stAlert"] {{
        border-radius: 8px;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_header(icon: str, title: str, subtitle: str, status: str = "live"):
    """Encabezado consistente para cada vista, con LED de estado en vivo."""
    labels = {"live": "EN LÍNEA", "warn": "ATENCIÓN", "alert": "CRÍTICO"}
    st.markdown(f"""
    <div class="view-header">
        <div>
            <p class="title">{icon} {title}</p>
            <p class="subtitle">{subtitle}</p>
        </div>
        <div class="badge"><span class="status-dot {status}"></span>{labels.get(status,'EN LÍNEA')}</div>
    </div>
    """, unsafe_allow_html=True)


def render_placeholder(icon: str, title: str, detail: str):
    st.markdown(f"""
    <div class="placeholder-card">
        <div class="icon">{icon}</div>
        <div class="title">{title}</div>
        <div>{detail}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 3. VENTANA EMERGENTE (POP-UP)
# ============================================================
@st.dialog("ℹ️ Información Técnica del Parámetro")
def modal_info_parametro(parametro, conf_dict):
    st.markdown(f"#### Detalle operativo — {parametro}")
    st.markdown(
        f"<span style='font-family:JetBrains Mono, monospace; color:{PALETTE['text_soft']};'>"
        f"Unidad de medida: <b>{conf_dict['unidad']}</b></span>",
        unsafe_allow_html=True
    )
    if conf_dict['max']:
        st.error(f"🚨 Límite máximo permitido: **{conf_dict['max']} {conf_dict['unidad']}**")
    if conf_dict['min']:
        st.warning(f"⚠️ Límite mínimo permitido: **{conf_dict['min']} {conf_dict['unidad']}**")

    st.divider()
    st.markdown("**Protocolo de acción rápida**")
    if parametro == "DQO":
        st.write("Si el valor excede el límite, verificar la dosificación de coagulante y el tiempo de retención.")
    elif parametro == "pH":
        st.write("Revisar bombas dosificadoras de soda cáustica/ácido en la entrada del sistema GEM.")
    else:
        st.write("Consultar manual de operaciones de la PTAR sección 4.2.")


# ============================================================
# 4. VISTAS DEL SISTEMA
# ============================================================

def vista_panel_principal():
    render_header("🎛️", "Panel Principal en Vivo", "Monitorización en tiempo real del equipo GEM.", status="live")
    cols = st.columns(3)
    with cols[0]:
        render_placeholder("⏱️", "Velocímetros de proceso", "Próximamente: caudal, presión y RPM en vivo.")
    with cols[1]:
        render_placeholder("📡", "Estado de sensores", "Próximamente: enlace LoRaWAN por equipo.")
    with cols[2]:
        render_placeholder("🔔", "Alertas activas", "Próximamente: eventos y notificaciones Telegram.")


def _estado_por_umbral(valor, conf):
    """Determina el estado semáforo de una lectura frente a sus límites."""
    if conf["limite_max"] is not None and valor > conf["limite_max"]:
        return "state-alert"
    if conf["limite_min"] is not None and valor < conf["limite_min"]:
        return "state-alert"
    return "state-ok"


def _delta_html(actual, anterior):
    if anterior is None or pd.isna(anterior) or anterior == 0:
        return '<span class="hero-delta flat">— sin punto de comparación</span>'
    diff = actual - anterior
    pct = (diff / anterior) * 100
    if abs(pct) < 0.05:
        return '<span class="hero-delta flat">≈ sin cambio</span>'
    flecha = "▲" if diff > 0 else "▼"
    clase = "up" if diff > 0 else "down"
    return f'<span class="hero-delta {clase}">{flecha} {abs(pct):.1f}% vs. lectura anterior</span>'


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def panel_eficiencia_vivo():
    """Fragmento auto-actualizable: solo esta sección se vuelve a renderizar
    cada REFRESH_SECONDS, sin recargar el resto de la app (sidebar, otras
    vistas, estado de sesión) -> no afecta la experiencia del usuario."""

    # --- Selector de variable: cada una en su propio carril, nunca mezcladas ---
    claves = list(VARIABLES_EFICIENCIA.keys())
    etiquetas = [f"{VARIABLES_EFICIENCIA[k]['icon']} {VARIABLES_EFICIENCIA[k]['label']}" for k in claves]

    seleccion_idx = option_menu(
        menu_title=None,
        options=etiquetas,
        icons=["dot"] * len(etiquetas),
        orientation="horizontal",
        default_index=0,
        key="pill_variable_eficiencia",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "border": f"1px solid {PALETTE['border']}", "border-radius": "10px"},
            "icon": {"display": "none"},
            "nav-link": {
                "font-size": "13.5px", "text-align": "center", "margin": "3px",
                "border-radius": "8px", "color": PALETTE["text_soft"], "font-weight": "500",
                "--hover-color": PALETTE["aqua_soft"],
            },
            "nav-link-selected": {"background-color": PALETTE["mid"], "color": "#fff", "font-weight": "600"},
        }
    )
    var_key = claves[etiquetas.index(seleccion_idx)]
    conf = VARIABLES_EFICIENCIA[var_key]

    rango_label = st.radio(
        "Rango histórico", list(RANGO_HORAS.keys()), index=2,
        horizontal=True, key="rango_horas_eficiencia", label_visibility="collapsed"
    )
    horas = RANGO_HORAS[rango_label]

    # --- Consulta a BigQuery (cacheada por REFRESH_SECONDS) ---
    try:
        df = fetch_variable_data(conf["table"], conf["col_valor"], conf["col_fecha"], horas)
    except Exception as e:
        st.error(
            "No se pudo consultar BigQuery para esta variable. "
            "Revisa que la tabla exista y que las credenciales en Secrets sean correctas."
        )
        st.caption(f"Detalle técnico: {e}")
        return

    if df.empty:
        st.warning(f"Sin lecturas de **{conf['label']}** en las últimas {rango_label}.")
        return

    df["fecha"] = pd.to_datetime(df["fecha"])
    ultimo = df.iloc[-1]
    anterior = df.iloc[-2]["valor"] if len(df) > 1 else None
    estado = _estado_por_umbral(ultimo["valor"], conf)

    ahora = pd.Timestamp.now(tz=ultimo["fecha"].tz) if ultimo["fecha"].tzinfo else pd.Timestamp.now()
    segundos_atras = max(int((ahora - ultimo["fecha"]).total_seconds()), 0)
    hace_txt = f"hace {segundos_atras}s" if segundos_atras < 90 else f"hace {segundos_atras // 60} min"

    col_hero, col_chart = st.columns([1, 2.2], gap="large")

    with col_hero:
        st.markdown(f"""
        <div class="hero-kpi {estado}">
            <div class="hero-label"><span class="status-dot live"></span>{conf['label']}</div>
            <div><span class="hero-value">{ultimo['valor']:.{conf['decimales']}f}</span><span class="hero-unit">{conf['unit']}</span></div>
            {_delta_html(ultimo['valor'], anterior)}
            <div class="hero-timestamp">Última lectura: {hace_txt} · {ultimo['fecha'].strftime('%d/%m %H:%M:%S')}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_chart:
        fig = px.area(df, x="fecha", y="valor", color_discrete_sequence=[PALETTE["mid"]])
        fig.update_traces(line_width=2, fillcolor="rgba(8,80,65,0.08)")
        if conf["limite_max"] is not None:
            fig.add_hline(y=conf["limite_max"], line_dash="dash", line_color=PALETTE["red"], annotation_text="Máx")
        if conf["limite_min"] is not None:
            fig.add_hline(y=conf["limite_min"], line_dash="dash", line_color=PALETTE["amber"], annotation_text="Mín")
        fig.update_layout(height=280, showlegend=False, xaxis_title=None, yaxis_title=conf["unit"])
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{var_key}")

    st.markdown(
        f'<div class="live-caption"><span class="status-dot live"></span>'
        f'Auto-actualización cada {REFRESH_SECONDS}s · consulta a BigQuery cacheada para no sobrecargar la app</div>',
        unsafe_allow_html=True
    )


def vista_eficiencia():
    render_header("⚖️", "Eficiencia y Operación", "Variables de proceso en tiempo real, desde BigQuery.", status="live")
    panel_eficiencia_vivo()


def vista_calidad():
    render_header("🧪", "Analítica de Calidad del Agua", "Explorador de parámetros históricos filtrados por fecha.", status="live")

    config_params = {
        "pH":            {"unidad": "adimensional", "color": PALETTE["mid"],   "max": 8.0,  "min": 6.5},
        "Conductividad": {"unidad": "µS/cm",         "color": PALETTE["aqua"],  "max": 1000, "min": None},
        "DQO":           {"unidad": "mg/L",          "color": PALETTE["amber"], "max": 500,  "min": None},
        "SST":           {"unidad": "mg/L",          "color": PALETTE["mid"],   "max": 250,  "min": None},
        "DBO":           {"unidad": "mg/L",          "color": PALETTE["aqua"],  "max": 200,  "min": None},
    }

    with st.container():
        st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            fecha_actual = pd.Timestamp.today().date()
            fecha_hace_15_dias = fecha_actual - timedelta(days=15)
            fechas_seleccionadas = st.date_input(
                "Intervalo de fechas",
                value=(fecha_hace_15_dias, fecha_actual),
                max_value=fecha_actual
            )

        with col2:
            parametro_seleccionado = st.selectbox("Parámetro", list(config_params.keys()))
            conf = config_params[parametro_seleccionado]

        with col3:
            st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
            if st.button("ℹ️ Info técnica", use_container_width=True):
                modal_info_parametro(parametro_seleccionado, conf)
        st.markdown('</div>', unsafe_allow_html=True)

    if len(fechas_seleccionadas) != 2:
        st.warning("⏳ Por favor, selecciona una fecha de inicio y una de fin en el calendario.")
        return

    fecha_inicio, fecha_fin = fechas_seleccionadas
    st.toast(f"Consultando {parametro_seleccionado} desde {fecha_inicio.strftime('%d/%m')} hasta {fecha_fin.strftime('%d/%m')}...", icon="🔍")

    dias_rango = (fecha_fin - fecha_inicio).days + 1
    fechas_generadas = pd.date_range(start=fecha_inicio, end=fecha_fin).strftime("%Y-%m-%d")
    np.random.seed(42)
    df_db = pd.DataFrame({
        "Fecha": fechas_generadas,
        parametro_seleccionado: np.random.uniform(
            low=conf["min"] if conf["min"] else conf["max"] * 0.5 if conf["max"] else 10,
            high=conf["max"] * 1.1 if conf["max"] else 50,
            size=dias_rango
        )
    })

    # --- Tarjetas KPI: último valor, promedio, estado frente al límite ---
    ultimo_valor = df_db[parametro_seleccionado].iloc[-1]
    promedio = df_db[parametro_seleccionado].mean()
    limite = conf["max"] if conf["max"] else conf["min"]
    if conf["max"] and ultimo_valor > conf["max"]:
        estado, estado_txt = "state-alert", "Por encima del límite"
    elif conf["min"] and ultimo_valor < conf["min"]:
        estado, estado_txt = "state-alert", "Por debajo del límite"
    else:
        estado, estado_txt = "state-ok", "Dentro de rango"

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""
        <div class="kpi-card {estado}">
            <div class="kpi-label">Último valor registrado</div>
            <div class="kpi-value">{ultimo_valor:.1f}<span class="kpi-unit">{conf['unidad']}</span></div>
            <div class="kpi-sub">{estado_txt}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Promedio del periodo</div>
            <div class="kpi-value">{promedio:.1f}<span class="kpi-unit">{conf['unidad']}</span></div>
            <div class="kpi-sub">{dias_rango} día(s) analizados</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Límite normativo</div>
            <div class="kpi-value">{limite if limite else '—'}<span class="kpi-unit">{conf['unidad']}</span></div>
            <div class="kpi-sub">{"Máximo" if conf["max"] else "Mínimo"} permitido</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    fig = px.line(df_db, x="Fecha", y=parametro_seleccionado, markers=True,
                   color_discrete_sequence=[conf["color"]])
    fig.update_traces(line_width=2.5, marker_size=6)
    if conf["max"]:
        fig.add_hline(y=conf["max"], line_dash="dash", line_color=PALETTE["red"], annotation_text="Máx")
    if conf["min"]:
        fig.add_hline(y=conf["min"], line_dash="dash", line_color=PALETTE["red"], annotation_text="Mín",
                       annotation_position="bottom right")
    st.plotly_chart(fig, use_container_width=True)


def vista_costos():
    render_header("💰", "Control de Costos", "Energía y consumo de químicos del proceso.", status="live")
    render_placeholder("🧾", "Panel de costos", "Espacio reservado para el control de energía y químicos.")


def vista_admin_usuarios():
    render_header("⚙️", "Administración", "Gestión de usuarios y roles del sistema.", status="live")
    render_placeholder("👥", "Gestión de usuarios", "Espacio reservado para administración de accesos.")


# ============================================================
# 5. MENÚ DE NAVEGACIÓN LATERAL
# ============================================================
inject_css()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <img src="https://cdn-icons-png.flaticon.com/512/3268/3268800.png">
        <div class="sidebar-brand-text">
            <div class="name">MES PTAR</div>
            <div class="site">Grupo Rocío · Santa Elena</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    opciones_menu = ["Panel Principal", "Eficiencia", "Calidad", "Costos"]
    iconos_menu = ["activity", "graph-up", "droplet", "currency-dollar"]

    if st.session_state['rol_usuario'] == "admin":
        opciones_menu.append("Administración")
        iconos_menu.append("gear")

    seleccion = option_menu(
        menu_title=None,
        options=opciones_menu,
        icons=iconos_menu,
        menu_icon="cast",
        default_index=2,  # Inicia en "Calidad"
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#9FC6BE", "font-size": "16px"},
            "nav-link": {
                "font-size": "14.5px", "text-align": "left", "margin": "2px 0",
                "border-radius": "8px", "color": "#E7F3F0",
                "--hover-color": "rgba(255,255,255,0.08)",
            },
            "nav-link-selected": {"background-color": PALETTE["aqua"], "color": PALETTE["dark"], "font-weight": "600"},
        }
    )

    st.divider()
    st.markdown("<span style='font-size:0.75rem; letter-spacing:0.04em; color:#9FC6BE; text-transform:uppercase;'>Control de desarrollo</span>", unsafe_allow_html=True)
    rol_actual = st.session_state['rol_usuario']
    nuevo_rol = st.radio("Simular vista como:", ["operador", "admin"], index=0 if rol_actual == "operador" else 1, label_visibility="collapsed")
    if nuevo_rol != rol_actual:
        st.session_state['rol_usuario'] = nuevo_rol
        st.rerun()

# ============================================================
# 6. ENRUTADOR
# ============================================================
if seleccion == "Panel Principal":
    vista_panel_principal()
elif seleccion == "Eficiencia":
    vista_eficiencia()
elif seleccion == "Calidad":
    vista_calidad()
elif seleccion == "Costos":
    vista_costos()
elif seleccion == "Administración":
    vista_admin_usuarios()
