import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta

# --- 1. DEFINICIÓN DEL POP-UP (Debe ir antes de usarlo) ---
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
        st.write("Si el valor excede el límite, verificar la dosificación de coagulante y el tiempo de retención en el ecualizador.")
    elif parametro == "pH":
        st.write("Revisar bombas dosificadoras de soda cáustica/ácido en la entrada del sistema GEM.")
    else:
        st.write("Consultar manual de operaciones de la PTAR sección 4.2.")

# --- 2. VISTA PRINCIPAL DE CALIDAD ---
def vista_calidad():
    st.title("🧪 Analítica de Calidad del Agua")
    st.markdown("Explorador de parámetros históricos.")
    
    # Configuración de los parámetros (Diccionario)
    config_params = {
        "pH": {"unidad": "adimensional", "color": "#1f77b4", "max": 8.0, "min": 6.5},
        "Conductividad": {"unidad": "µS/cm", "color": "#2ca02c", "max": 1000, "min": None},
        "DQO": {"unidad": "mg/L", "color": "#ff7f0e", "max": 500, "min": None},
        "SST": {"unidad": "mg/L", "color": "#9467bd", "max": 250, "min": None},
        "DBO": {"unidad": "mg/L", "color": "#8c564b", "max": 200, "min": None}
    }
    
    # --- CONTROLES SUPERIORES ---
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Selector de Fecha (Rango)
        fecha_actual = pd.Timestamp.today().date()
        fecha_hace_15_dias = fecha_actual - timedelta(days=15)
        
        fechas_seleccionadas = st.date_input(
            "Seleccione el intervalo de fechas:",
            value=(fecha_hace_15_dias, fecha_actual), # Rango por defecto
            max_value=fecha_actual
        )
        
    with col2:
        parametro_seleccionado = st.selectbox(
            "Seleccione el parámetro:",
            list(config_params.keys())
        )
        conf = config_params[parametro_seleccionado]
        
    with col3:
        st.markdown("<br>", unsafe_allow_html=True) # Espacio para alinear el botón
        # Botón para disparar el Pop-up (Modal)
        if st.button("ℹ️ Ver Info Técnica", use_container_width=True):
            modal_info_parametro(parametro_seleccionado, conf)

    st.divider()
    
    # --- LÓGICA DE VALIDACIÓN DE FECHAS ---
    # st.date_input devuelve una tupla. Si el usuario solo ha hecho el primer click, 
    # la tupla tiene 1 elemento. Debemos esperar a que tenga 2 (inicio y fin).
    if len(fechas_seleccionadas) != 2:
        st.warning("⏳ Por favor, selecciona una fecha de fin en el calendario.")
        return # Detiene la ejecución hasta que se seleccione el rango completo
    
    fecha_inicio, fecha_fin = fechas_seleccionadas
    
    # Mostrar un toast (notificación) simulando la consulta a la DB
    st.toast(f"Consultando datos desde {fecha_inicio.strftime('%d/%m')} hasta {fecha_fin.strftime('%d/%m')}...", icon="🔍")

    # --- AQUÍ VA TU CONSULTA SQL REAL ---
    # query = f"SELECT * FROM calidad WHERE fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
    # df_db = pd.read_sql(query, conexion)
    
    # Simulación de datos para este ejemplo
    dias_rango = (fecha_fin - fecha_inicio).days + 1
    fechas_generadas = pd.date_range(start=fecha_inicio, end=fecha_fin).strftime("%Y-%m-%d")
    df_db = pd.DataFrame({
        "Fecha": fechas_generadas,
        parametro_seleccionado: np.random.uniform(
            low=conf["min"] if conf["min"] else conf["max"]*0.5 if conf["max"] else 10,
            high=conf["max"]*1.2 if conf["max"] else 50, 
            size=dias_rango
        )
    })

    # --- GRÁFICO ---
    fig = px.line(df_db, x="Fecha", y=parametro_seleccionado, markers=True, color_discrete_sequence=[conf["color"]])
    if conf["max"]: fig.add_hline(y=conf["max"], line_dash="dash", line_color="red", annotation_text="Max")
    if conf["min"]: fig.add_hline(y=conf["min"], line_dash="dash", line_color="red", annotation_text="Min", annotation_position="bottom right")
    
    st.plotly_chart(fig, use_container_width=True)
