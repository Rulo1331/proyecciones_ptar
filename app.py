import streamlit as st

# Configuración de la página principal
st.set_page_config(
    page_title="Portal de Dashboards",
    page_icon="📊",
    layout="centered"
)

# Título y bienvenida
st.title("📊 Portal Principal de Dashboards")
st.markdown("Bienvenido al sistema. Selecciona el dashboard al que deseas ingresar:")
st.markdown("---")

# Crear columnas para organizar los botones en una cuadrícula (2x2)
col1, col2 = st.columns(2)

with col1:
    # Botón 1: Lleva a tu código actual
    if st.button("💧 Proyección de Consumo", use_container_width=True):
        st.switch_page("vista_proyecciones.py")
        
    # Botón 3
    if st.button("🏭 Dashboard Producción", use_container_width=True):
        st.switch_page("pages/3_dashboard_tres.py")

with col2:
    # Botón 2
    if st.button("📈 Dashboard Financiero", use_container_width=True):
        st.switch_page("pages/2_dashboard_dos.py")
        
    # Botón 4
    if st.button("⚙️ Configuración y Reportes", use_container_width=True):
        st.switch_page("pages/4_dashboard_cuatro.py")

# Opcional: Agregar información al pie de página
st.markdown("---")
st.caption("Sistema de Dashboards Integrados - Versión 1.0")
