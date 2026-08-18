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
    np.random.seed(42) # Para consistencia en la simulación
    
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
    st.title("🧪 Analítica de Calidad del Agua")
    st.markdown("Explorador de parámetros histórico extraído desde la base de datos.")
    
    # 1. Controles Superiores (Filtro de días y Selector de Parámetro)
    col_filtro, col_param = st.columns([1, 2])
    
    with col_filtro:
        dias_hist = st.slider("Días a consultar:", min_value=7, max_value=30, value=14)
        
    with col_param:
        parametro_seleccionado = st.selectbox(
            "Seleccione el parámetro a visualizar:",
            ["pH", "Conductividad", "DQO", "SST", "DBO"]
        )
        
    st.divider()
    
    # 2. Extraemos los datos de la DB según los días seleccionados
    df_db = cargar_datos_calidad(dias_hist)
    
    # 3. Mapeo de unidades y límites de alerta dinámicos
    config_params = {
        "pH": {"unidad": "", "color": "#1f77b4", "max": 8.0, "min": 6.5},
        "Conductividad": {"unidad": "µS/cm", "color": "#2ca02c", "max": None, "min": None},
        "DQO": {"unidad": "mg/L", "color": "#ff7f0e", "max": 500, "min": None},
        "SST": {"unidad": "mg/L", "color": "#9467bd", "max": 250, "min": None},
        "DBO": {"unidad": "mg/L", "color": "#8c564b", "max": 200, "min": None}
    }
    
    conf = config_params[parametro_seleccionado]
    titulo_grafico = f"Tendencia de {parametro_seleccionado} {f'({conf['unidad']})' if conf['unidad'] else ''}"
    
    # 4. Generación del gráfico único dinámico
    fig = px.line(
        df_db, 
        x="Fecha", 
        y=parametro_seleccionado, 
        title=titulo_grafico,
        markers=True,
        color_discrete_sequence=[conf["color"]]
    )
    
    # Agregar líneas de límite si existen en la configuración
    if conf["max"] is not None:
        fig.add_hline(y=conf["max"], line_dash="dash", line_color="red", annotation_text=f"Límite Máx ({conf['max']})")
    if conf["min"] is not None:
        fig.add_hline(y=conf["min"], line_dash="dash", line_color="red", annotation_text=f"Límite Mín ({conf['min']})", annotation_position="bottom right")

    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # 5. Tabla de Datos Ocultable (Expander)
    with st.expander(f"Ver tabla de datos en crudo para {parametro_seleccionado}"):
        st.dataframe(
            df_db[["Fecha", parametro_seleccionado]], 
            use_container_width=True, 
            hide_index=True
        )

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
        default_index=2, # Iniciamos en la vista de Calidad
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
