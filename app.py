import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd

# 1. Configuración OBLIGATORIA (Debe ser la primera línea)
st.set_page_config(
    page_title="MES PTAR - Control",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Simulamos el rol actual (Esto luego vendrá de tu sistema de login)
# Cambia esto a "admin" para ver cómo cambia la barra lateral
if 'rol_usuario' not in st.session_state:
    st.session_state['rol_usuario'] = "operador" 

# --- FUNCIONES DE VISTAS (Módulos) ---

def vista_panel_principal():
    st.title("🎛️ Panel Principal en Vivo")
    st.markdown("Monitorización en tiempo real del equipo GEM.")
    
    # KPIs Rápidos
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tratamiento Diario", "1250 m³", "12 m³")
    col2.metric("Consumo Planta", "150 m³", "-5 m³", delta_color="inverse")
    col3.metric("Nivel Ecualizador", "68 %", "Normal", delta_color="off")
    col4.metric("Velocidad GEM", "1450 RPM", "Óptimo", delta_color="off")
    
    st.divider()
    
    # Zona para los gráficos (Gauges de presión, etc.)
    col_izq, col_der = st.columns([2, 1])
    with col_izq:
        st.info("Espacio reservado para el Velocímetro de Presión GEM (Plotly)")
    with col_der:
        st.info("Espacio reservado para la Dona de Disponibilidad (Plotly)")

def vista_eficiencia():
    st.title("⚖️ Eficiencia y Operación")
    st.markdown("Balance de masa y energía del turno.")
    st.info("Espacio reservado para Gráfico de Líneas: Tratamiento vs Consumo (Plotly)")
    st.info("Espacio reservado para Tabla Resumen Diario (st.dataframe con ProgressColumn)")

def vista_calidad():
    st.title("🧪 Calidad y Dosificación")
    st.markdown("Registro de parámetros físico-químicos.")
    
    with st.form("registro_calidad"):
        st.subheader("Ingreso de Resultados de Laboratorio")
        col1, col2 = st.columns(2)
        ph = col1.number_input("pH", min_value=0.0, max_value=14.0, value=7.0)
        turbidez = col2.number_input("Turbidez (NTU)", min_value=0.0)
        st.form_submit_button("Guardar Registro")

def vista_reportes():
    st.title("📊 Reportes Históricos")
    st.markdown("Exportación de datos de operación.")
    st.info("Espacio reservado para la Tabla Masiva (AG Grid o st.dataframe) con botón de descarga Excel.")

def vista_admin_usuarios():
    st.title("⚙️ Administración del Sistema")
    st.markdown("Gestión de accesos y configuración global.")
    
    tab1, tab2 = st.tabs(["Gestión de Usuarios", "Configuración de Alarmas"])
    
    with tab1:
        st.subheader("Usuarios Activos")
        # Tabla simulada de usuarios
        df_usuarios = pd.DataFrame({
            "Usuario": ["Juan Pérez", "María Gómez", "Admin Sist"],
            "Rol": ["Operador", "Supervisor", "Administrador"],
            "Estado": ["Activo", "Activo", "Activo"]
        })
        st.dataframe(df_usuarios, use_container_width=True)
        st.button("➕ Añadir Nuevo Usuario")
        
    with tab2:
        st.subheader("Límites Críticos del GEM")
        st.slider("Alarma Presión Máxima (Bar)", min_value=1.0, max_value=5.0, value=3.5)
        st.slider("Alarma Nivel Ecualizador (%)", min_value=50, max_value=100, value=85)
        st.button("💾 Guardar Cambios")

# --- MENÚ DE NAVEGACIÓN ---

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3268/3268800.png", width=60) # Icono generico PTAR
    st.markdown("### MES PTAR")
    
    # Definimos las opciones según el rol
    opciones_menu = ["Panel Principal", "Eficiencia", "Calidad", "Reportes"]
    iconos_menu = ["activity", "graph-up", "droplet", "file-earmark-spreadsheet"]
    
    if st.session_state['rol_usuario'] == "admin":
        opciones_menu.append("Administración")
        iconos_menu.append("gear")

    # Renderizamos el menú elegante
    seleccion = option_menu(
        menu_title=None,  
        options=opciones_menu,
        icons=iconos_menu, 
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "gray", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#005b96", "color": "white", "icon-color": "white"},
        }
    )
    
    st.divider()
    
    # Botón temporal para simular el cambio de rol
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
elif seleccion == "Reportes":
    vista_reportes()
elif seleccion == "Administración":
    vista_admin_usuarios()
