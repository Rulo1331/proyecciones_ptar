import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MES PTAR", layout="wide", initial_sidebar_state="expanded")

if 'rol_usuario' not in st.session_state:
    st.session_state['rol_usuario'] = "operador" 

# --- SIMULADOR DE BASE DE DATOS ---
@st.cache_data
def cargar_datos_calidad(dias):
    """
    Simula: SELECT fecha, ph, dqo, sst, dbo, conductividad FROM calidad 
    WHERE fecha >= [hoy - dias]
    """
    fechas = pd.date_range(end=pd.Timestamp.today(), periods=dias).strftime("%Y-%m-%d")
    np.random.seed(42) # Para que los datos no cambien cada vez que haces clic
    
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
    st.title("🎛️ Panel Principal en Vivo")
    st.markdown("Monitorización en tiempo real del equipo GEM.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tratamiento Diario", "1250 m³", "12 m³")
    col2.metric("Consumo Planta", "150 m³", "-5 m³", delta_color="inverse")
    col3.metric("Nivel Ecualizador", "68 %", "Normal", delta_color="off")
    col4.metric("Velocidad GEM", "1450 RPM", "Óptimo", delta_color="off")
    
    st.divider()
    st.info("Aquí irán los indicadores en tiempo real (Velocímetros y Donas).")

def vista_eficiencia():
    st.title("⚖️ Eficiencia y Operación")
    st.info("Espacio para Gráfico de Tratamiento vs Consumo y Tabla Resumen.")

def vista_calidad():
    st.title("🧪 Calidad del Agua - Histórico")
    st.markdown("Visualización de parámetros físico-químicos registrados en la base de datos.")
    
    # Filtro Global que afecta a todas las pestañas
    col_filtro, _ = st.columns([1, 3])
    with col_filtro:
        dias_hist = st.slider("Días de histórico a consultar:", min_value=7, max_value=30, value=7)
    
    # Extraemos los datos de la DB
    df_db = cargar_datos_calidad(dias_hist)
    
    st.divider()

    # ENFOQUE 1: PESTAÑAS INDEPENDIENTES PARA LECTURA
    tab_ph, tab_cond, tab_dqo, tab_sst, tab_dbo = st.tabs([
        "pH", "Conductividad", "DQO", "SST", "DBO₅"
    ])
    
    with tab_ph:
        st.subheader("Evolución del pH")
        fig_ph = px.line(df_db, x="Fecha", y="pH", markers=True, color_discrete_sequence=["#1f77b4"])
        # Limites legales simulados
        fig_ph.add_hline(y=8.0, line_dash="dash", line_color="red", annotation_text="Max (8.0)")
        fig_ph.add_hline(y=6.5, line_dash="dash", line_color="red", annotation_text="Min (6.5)", annotation_position="bottom right")
        st.plotly_chart(fig_ph, use_container_width=True)
        
    with tab_cond:
        st.subheader("Conductividad (µS/cm)")
        fig_cond = px.area(df_db, x="Fecha", y="Conductividad", color_discrete_sequence=["#2ca02c"])
        st.plotly_chart(fig_cond, use_container_width=True)
        
    with tab_dqo:
        st.subheader("Demanda Química de Oxígeno (mg/L)")
        fig_dqo = px.bar(df_db, x="Fecha", y="DQO", color_discrete_sequence=["#ff7f0e"])
        fig_dqo.add_hline(y=500, line_dash="dash", line_color="red", annotation_text="Límite Legal (500)")
        st.plotly_chart(fig_dqo, use_container_width=True)
        
    with tab_sst:
        st.subheader("Sólidos Suspendidos Totales (mg/L)")
        fig_sst = px.line(df_db, x="Fecha", y="SST", markers=True, color_discrete_sequence=["#9467bd"])
        st.plotly_chart(fig_sst, use_container_width=True)
        
    with tab_dbo:
        st.subheader("Demanda Bioquímica de Oxígeno - DBO₅ (mg/L)")
        st.warning("Los datos mostrados corresponden a la fecha en que se tomó la muestra original.")
        fig_dbo = px.bar(df_db, x="Fecha", y="DBO", color_discrete_sequence=["#8c564b"])
        st.plotly_chart(fig_dbo, use_container_width=True)

def vista_costos():
    st.title("💰 Control de Costos")
    st.info("Espacio para control de energía, químicos y OPEX.")

def vista_admin_usuarios():
    st.title("⚙️ Administración")
    st.info("Espacio para gestión de usuarios y parámetros.")

# --- MENÚ DE NAVEGACIÓN LATERAL ---

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3268/3268800.png", width=60)
    st.markdown("### MES PTAR")
    
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
        default_index=2, # Iniciamos en la vista de Calidad por defecto para pruebas
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "gray", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#005b96", "color": "white", "icon-color": "white"},
        }
    )
    
    st.divider()
    st.markdown("**Control de Desarrollo:**")
    rol_actual = st.session_state['rol_usuario']
    nuevo_rol = st.radio("Simular vista como:", ["operador", "admin"], index=0 if rol_actual=="operador" else 1)
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
