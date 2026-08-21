import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import timedelta

# ============================================================
# 1. CONFIGURACIÓN INICIAL
# ============================================================
st.set_page_config(
    page_title="PTAR · Santa Elena",
    page_icon=":factory:", # FAVorite ICON
    layout="wide",
    initial_sidebar_state="auto",
    menu_items = {
        'Get help': 'https://cba-produccion.apps.ingprocesos.com/dashboard/ptar',
        'About': "https://cba-produccion.apps.ingprocesos.com/dashboard/principal",
        'About': "https://cba-produccion.apps.ingprocesos.com/dashboard/ptar"
    }
    
)

if 'rol_usuario' not in st.session_state:
    st.session_state['rol_usuario'] = "operador"

# ============================================================
# 2. IDENTIDAD VISUAL — tokens + estilos globales
# ============================================================
# Paleta heredada del stack Node-RED de la planta (mismo verde-teal
# oscuro #04342C / #085041 usado en los tableros de campo), extendida
# con un acento aqua para datos en vivo y colores de estado semáforo
# consistentes con la automatización de sopladores (verde/ámbar/rojo).

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

# Tema Plotly a medida, para que los gráficos hablen el mismo idioma
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


def vista_eficiencia():
    render_header("⚖️", "Eficiencia y Operación", "Tratamiento vs. consumo energético del sistema.", status="live")
    render_placeholder("📈", "Gráfico de tratamiento vs. consumo", "Espacio reservado para el análisis comparativo.")


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
