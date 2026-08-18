import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd

st.set_page_config(page_title="MES PTAR", layout="wide", initial_sidebar_state="expanded")

if 'rol_usuario' not in st.session_state:
    st.session_state['rol_usuario'] = "operador" 

# --- VISTAS CON SUB-PESTAÑAS ---

def vista_panel_principal():
    st.title("🎛️ Panel Principal en Vivo")
    
    # Subvistas usando Tabs
    tab_general, tab_sensores = st.tabs(["Visión General", "Detalle de Sensores"])
    
    with tab_general:
        st.markdown("### Estado Actual de Planta")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tratamiento Diario", "1250 m³", "12 m³")
        col2.metric("Consumo Planta", "150 m³", "-5 m³", delta_color="inverse")
        col3.metric("Nivel Ecualizador", "68 %", "Normal", delta_color="off")
        col4.metric("Velocidad GEM", "1450 RPM", "Óptimo", delta_color="off")
        st.info("Espacio para Gráficos de Velocímetro y Disponibilidad")
        
    with tab_sensores:
        st.markdown("### Lecturas Crudas en Tiempo Real")
        st.dataframe(pd.DataFrame({
            "Sensor": ["Presión Entrada", "Temperatura Motor", "Caudalímetro"],
            "Valor": ["2.4 Bar", "65 °C", "45 L/s"],
            "Estado": ["🟢 OK", "🟢 OK", "🟡 Alerta Baja"]
        }), hide_index=True)

def vista_eficiencia():
    st.title("⚖️ Eficiencia y Operación")
    
    tab_balance, tab_paros = st.tabs(["Balance de Caudales", "Registro de Paros"])
    
    with tab_balance:
        st.info("Espacio para Gráfico de Líneas: Tratamiento vs Consumo")
    
    with tab_paros:
        st.info("Espacio para Tabla de Tiempos Muertos y Justificaciones")

def vista_calidad():
    st.title("🧪 Calidad del Agua")
    
    tab_ingreso, tab_tendencias = st.tabs(["Ingreso de Laboratorio", "Tendencias Históricas"])
    
    with tab_ingreso:
        st.markdown("### Registro de Parámetros Físico-Químicos")
        with st.form("registro_calidad_completo"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=7.2, step=0.1)
                conductividad = st.number_input("Conductividad (µS/cm)", min_value=0.0, value=850.0)
            with col2:
                dbo = st.number_input("DBO₅ (mg/L)", min_value=0.0, value=250.0)
                dqo = st.number_input("DQO (mg/L)", min_value=0.0, value=600.0)
            with col3:
                sst = st.number_input("SST (mg/L)", min_value=0.0, value=300.0)
                observaciones = st.text_input("Observaciones (Opcional)")
            
            st.form_submit_button("Guardar Resultados")
            
    with tab_tendencias:
        st.info("Espacio para gráficas mostrando la reducción de DQO y SST a lo largo del mes.")

def vista_costos():
    st.title("💰 Control de Costos")
    
    tab_energia, tab_quimicos, tab_resumen = st.tabs(["Energía", "Químicos", "Resumen Financiero"])
    
    with tab_energia:
        st.markdown("### Eficiencia Energética (kWh / m³)")
        st.info("Gráfico comparando consumo eléctrico del GEM vs agua tratada.")
        
    with tab_quimicos:
        st.markdown("### Dosificación y Costo de Reactivos")
        col1, col2 = st.columns(2)
        col1.metric("Costo Floculante (Semana)", "$ 450", "+$20")
        col2.metric("Costo Coagulante (Semana)", "$ 320", "-$15")
        st.info("Tabla de consumo de químicos por lote.")
        
    with tab_resumen:
        st.markdown("### Costo Total por Metro Cúbico Tratado")
        st.metric("OPEX / m³ (Mes actual)", "$ 1.15 / m³", "-$ 0.05", delta_color="inverse")

def vista_admin_usuarios():
    st.title("⚙️ Administración")
    
    tab_usuarios, tab_alarmas = st.tabs(["Gestión de Usuarios", "Configuración de Alarmas"])
    with tab_usuarios:
        st.info("Tabla interactiva para editar usuarios.")
    with tab_alarmas:
        st.info("Configuración de límites máximos para presión, DQO, etc.")

# --- MENÚ DE NAVEGACIÓN LATERAL ---

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3268/3268800.png", width=60)
    st.markdown("### MES PTAR")
    
    # Se añade "Costos" a las opciones
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
        default_index=0,
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
