import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta

# 1. CONFIGURACIÓN INICIAL (Siempre al principio)
st.set_page_config(page_title="MES PTAR", layout="wide", initial_sidebar_state="expanded")

if 'rol_usuario' not in st.session_state:
    st.session_state['rol_usuario'] = "operador" 

# --- VENTANA EMERGENTE (POP-UP) ---
@st.dialog("ℹ️ Información Técnica del Parámetro")
def modal_info_parametro(parametro, conf_dict):
    st.markdown(f"### Detalle Operativo: {parametro}")
    st.write(f"**Unidad de medida:** {conf_dict['unidad']}")
    if conf_dict['max']:
        st.error(f"🚨 **Límite Máximo Permitido:** {conf_dict['max']} {conf_dict['unidad']}")
    if conf_dict['min']:
        st.warning(f"⚠️ **Límite Mínimo Permitido:** {conf_dict['min']} {conf_dict['unidad']}")
    
    st.markdown("---")
    st.write("**Protocolo de acción rápida:**")
    if parametro == "DQO":
        st.write("Si el valor excede el límite, verificar la dosificación de coagulante y el tiempo de retención.")
    elif parametro == "pH":
        st.write("Revisar bombas dosificadoras de soda cáustica/ácido en la entrada del sistema GEM.")
    else:
        st.write("Consultar manual de operaciones de la PTAR sección 4.2.")

# --- VISTAS DEL SISTEMA ---

def vista_panel_principal():
    st.title("🎛️ Panel Principal en Vivo")
    st.markdown("Monitorización en tiempo real del equipo GEM.")
    st.info("Aquí colocaremos los velocímetros y gráficos de estado de la máquina.")

def vista_eficiencia():
    st.title("⚖️ Eficiencia y Operación")
    st.info("Espacio para Gráfico de Tratamiento vs Consumo.")

def vista_calidad():
    st.title("🧪 Analítica de Calidad del Agua")
    st.markdown("Explorador de parámetros históricos filtrados por fecha.")
    
    config_params = {
        "pH": {"unidad": "adimensional", "color": "#1f77b4", "max": 8.0, "min": 6.5},
        "Conductividad": {"unidad": "µS/cm", "color": "#2ca02c", "max": 1000, "min": None},
        "DQO": {"unidad": "mg/L", "color": "#ff7f0e", "max": 500, "min": None},
        "SST": {"unidad": "mg/L", "color": "#9467bd", "max": 250, "min": None},
        "DBO": {"unidad": "mg/L", "color": "#8c564b", "max": 200, "min": None}
    }
    
    # Controles superiores
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        fecha_actual = pd.Timestamp.today().date()
        fecha_hace_15_dias = fecha_actual - timedelta(days=15)
        
        fechas_seleccionadas = st.date_input(
            "Seleccione el intervalo de fechas:",
            value=(fecha_hace_15_dias, fecha_actual),
            max_value=fecha_actual
        )
        
    with col2:
        parametro_seleccionado = st.selectbox(
            "Seleccione el parámetro:",
            list(config_params.keys())
        )
        conf = config_params[parametro_seleccionado]
        
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        # Disparador del pop-up
        if st.button("ℹ️ Ver Info Técnica", use_container_width=True):
            modal_info_parametro(parametro_seleccionado, conf)

    st.divider()
    
    # Validación: Esperar a que el usuario seleccione ambas fechas
    if len(fechas_seleccionadas) != 2:
        st.warning("⏳ Por favor, selecciona una fecha de inicio y una de fin en el calendario.")
        return 
    
    fecha_inicio, fecha_fin = fechas_seleccionadas
    
    # Notificación toast
    st.toast(f"Consultando {parametro_seleccionado} desde {fecha_inicio.strftime('%d/%m')} hasta {fecha_fin.strftime('%d/%m')}...", icon="🔍")
    
    # Simulación de datos basada en las fechas elegidas
    dias_rango = (fecha_fin - fecha_inicio).days + 1
    fechas_generadas = pd.date_range(start=fecha_inicio, end=fecha_fin).strftime("%Y-%m-%d")
    np.random.seed(42)
    df_db = pd.DataFrame({
        "Fecha": fechas_generadas,
        parametro_seleccionado: np.random.uniform(
            low=conf["min"] if conf["min"] else conf["max"]*0.5 if conf["max"] else 10,
            high=conf["max"]*1.1 if conf["max"] else 50, 
            size=dias_rango
        )
    })

    # Gráfico
    fig = px.line(df_db, x="Fecha", y=parametro_seleccionado, markers=True, color_discrete_sequence=[conf["color"]])
    if conf["max"]: fig.add_hline(y=conf["max"], line_dash="dash", line_color="red", annotation_text="Max")
    if conf["min"]: fig.add_hline(y=conf["min"], line_dash="dash", line_color="red", annotation_text="Min", annotation_position="bottom right")
    
    st.plotly_chart(fig, use_container_width=True)

def vista_costos():
    st.title("💰 Control de Costos")
    st.info("Espacio para control de energía y químicos.")

def vista_admin_usuarios():
    st.title("⚙️ Administración")
    st.info("Espacio para gestión de usuarios.")

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
        default_index=2, # Inicia en "Calidad" para que veas el resultado directo
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
