import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURACIÓN INICIAL Y ESTILOS GLOBALES
st.set_page_config(page_title="MES PTAR", layout="wide", initial_sidebar_state="expanded")

# Inyección de CSS para diseño industrial (MES/SCADA)
st.markdown("""
<style>
    /* Ocultar elementos por defecto para dar aspecto de sistema embebido */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Dar espacio y quitar el padding superior molesto */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Estilo de tarjetas para las métricas */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #005b96;
    }
    
    /* Estilo para el título principal */
    h1 {
        color: #003366 !important;
        border-bottom: 2px solid #005b96;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

if 'rol_usuario' not in st.session_state:
    st.session_state['rol_usuario'] = "operador" 

# --- SIMULADOR DE BASE DE DATOS ---
@st.cache_data
def cargar_datos_calidad(dias):
    """Simula la extracción de datos de la DB."""
    fechas = pd.date_range(end=pd.Timestamp.today(), periods=dias).strftime("%Y-%m-%d")
    np.random.seed(42)
    
    df = pd.DataFrame({
        "Fecha": fechas,
        "pH": np.random.uniform(6.8, 7.8, dias),
        "Conductividad": np.random.uniform(800, 950, dias),
        "DQO": np.random.uniform(400, 550, dias),
        "SST": np.random.uniform(180, 250, dias),
        "DBO": np.random.uniform(150, 210, dias)
    })
    return df

# --- VISTAS DEL SISTEMA ---

def vista_panel_principal():
    st.title("Panel Principal en Vivo")
    st.caption("Monitorización en tiempo real del equipo GEM")
    
    # KPIs Principales
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(label="Tratamiento Diario", value="1,250 m³", delta="12 m³")
    with col2: st.metric(label="Consumo Planta", value="150 m³", delta="-5 m³", delta_color="inverse")
    with col3: st.metric(label="Nivel Ecualizador", value="68 %", delta="Normal", delta_color="off")
    with col4: st.metric(label="Velocidad GEM", value="1,450 RPM", delta="Óptimo", delta_color="off")
    
    st.markdown("<br>", unsafe_allow_html=True) # Espaciador
    
    # Placeholder visual para los gráficos SCADA
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.info("🟢 **Estado del Equipo:** Aquí se integrará el velocímetro de RPM (Ej. Gauge de Plotly).")
    with col_graf2:
        st.info("🟢 **Nivel de Tanques:** Aquí se integrará el diagrama P&ID o donas de nivel.")

def vista_eficiencia():
    st.title("Eficiencia y Operación")
    st.markdown("Módulo de análisis de rendimiento energético e hidráulico.")
    
    # En lugar de un st.info vacío, usamos un diseño de "Próximamente" elegante
    col1, col2, col3 = st.columns(3)
    for i, modulo in enumerate(["Gráfico Tratamiento vs Consumo", "Tabla Resumen de Eficiencia", "Histórico de Horas de Operación"]):
        with [col1, col2, col3][i]:
            st.markdown(
                f"<div style='border: 2px dashed #cccccc; border-radius: 10px; padding: 40px; text-align: center; color: #666;'>"
                f"🔄<br><b>{modulo}</b><br><span style='font-size: 0.8em;'>En desarrollo</span></div>", 
                unsafe_allow_html=True
            )

def vista_calidad():
    st.title("Analítica de Calidad del Agua")
    st.markdown("Explorador de parámetros histórico extraído desde la base de datos.")
    
    # Controles Superiores
    col_filtro, col_param = st.columns([1, 2])
    with col_filtro:
        dias_hist = st.slider("Días a consultar:", min_value=7, max_value=30, value=14)
    with col_param:
        parametro_seleccionado = st.selectbox(
            "Parámetro a visualizar:", ["pH", "Conductividad", "DQO", "SST", "DBO"]
        )
        
    # Extracción de datos
    df_db = cargar_datos_calidad(dias_hist)
    conf = {
        "pH": {"unidad": "", "color": "#1f77b4", "max": 8.0, "min": 6.5},
        "Conductividad": {"unidad": "µS/cm", "color": "#2ca02c", "max": None, "min": None},
        "DQO": {"unidad": "mg/L", "color": "#ff7f0e", "max": 500, "min": None},
        "SST": {"unidad": "mg/L", "color": "#9467bd", "max": 250, "min": None},
        "DBO": {"unidad": "mg/L", "color": "#8c564b", "max": 200, "min": None}
    }[parametro_seleccionado]
    
    # NUEVO: KPIs dinámicos de resumen (Da contexto inmediato al usuario)
    serie = df_db[parametro_seleccionado]
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Promedio", f"{serie.mean():.2f} {conf['unidad']}")
    col_kpi2.metric("Máximo", f"{serie.max():.2f} {conf['unidad']}", delta="Pico")
    col_kpi3.metric("Mínimo", f"{serie.min():.2f} {conf['unidad']}", delta="Valle", delta_color="inverse")
    col_kpi4.metric("Desv. Estándar", f"{serie.std():.2f}")
    
    st.divider()
    
    # Gráfico
    titulo_grafico = f"Tendencia de {parametro_seleccionado} {f'({conf[\"unidad\"]})' if conf['unidad'] else ''}"
    fig = px.line(df_db, x="Fecha", y=parametro_seleccionado, title=titulo_grafico, markers=True, color_discrete_sequence=[conf["color"]])
    
    if conf["max"] is not None:
        fig.add_hline(y=conf["max"], line_dash="dash", line_color="red", annotation_text=f"Límite Máx ({conf['max']})")
    if conf["min"] is not None:
        fig.add_hline(y=conf["min"], line_dash="dash", line_color="red", annotation_text=f"Límite Mín ({conf['min']})", annotation_position="bottom right")

    # Mejora del layout de Plotly
    fig.update_layout(
        height=400, 
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)', # Fondo transparente para integrarse con la tarjeta
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de Datos
    with st.expander(f"Ver tabla de datos en crudo para {parametro_seleccionado}"):
        st.dataframe(df_db[["Fecha", parametro_seleccionado]], use_container_width=True, hide_index=True)

def vista_costos():
    st.title("Control de Costos")
    st.markdown("Seguimiento de OPEX, energía y consumo de químicos.")
    st.info("Espacio reservado para la integración con el sistema ERP/Contable.")

def vista_admin_usuarios():
    st.title("Administración del Sistema")
    st.warning("⚠️ Zona restringida solo para usuarios con rol 'admin'.")
    st.info("Espacio para gestión de usuarios, roles y configuración de alarmas.")

# --- MENÚ DE NAVEGACIÓN LATERAL ---
with st.sidebar:
    # Se elimina la imagen externa para mejorar velocidad de carga en la nube
    st.markdown("<h1 style='text-align:center; color:#005b96; font-size: 2.5rem;'>💧</h1>", unsafe_allow_html=True)
    st.markdown("### MES PTAR")
    st.caption("Sistema de Ejecución Manufacturera")
    
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
        default_index=2,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#005b96", "font-size": "20px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"2px", "--hover-color": "#f0f4f8", "color": "#333"},
            "nav-link-selected": {"background-color": "#005b96", "color": "white", "icon-color": "white", "border-radius": "5px"},
        }
    )
    
    st.divider()
    
    # Mejora visual del simulador de roles
    st.markdown("**Control de Desarrollo:**")
    rol_actual = st.session_state['rol_usuario']
    nuevo_rol = st.radio(
        "Simular vista como:", 
        ["operador", "admin"], 
        index=0 if rol_actual=="operador" else 1,
        horizontal=True # Ahorra espacio vertical
    )
    if nuevo_rol != rol_actual:
        st.session_state['rol_usuario'] = nuevo_rol
        st.rerun()

# --- ENRUTADOR ---
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
