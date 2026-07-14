import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(
    page_title="Proyecciones PTAR & Planta", 
    page_icon="💧", 
    layout="wide"
)

# Título principal
st.title("💧 Sistema de Proyecciones de Agua (Planta y PTAR)")
st.markdown("---")

# 1. Datos históricos reales (obtenidos de tu imagen)
@st.cache_data
def obtener_datos_historicos():
    data = {
        'fecha': ['07/07/2026', '08/07/2026', '09/07/2026', '10/07/2026', '11/07/2026', '12/07/2026', '13/07/2026'],
        'numero_pollos': [16717, 28807, 27513, 34001, 25816, 0, 26520],
        'consumo_planta': [509.98, 667.88, 713.64, 797.64, 694.07, 74.84, 629.49],
        'consumo_ptar': [677.74, 685.28, 740.40, 724.92, 691.55, 236.60, 660.57]
    }
    return pd.DataFrame(data)

df = obtener_datos_historicos()

# 2. Entrenamiento de los modelos de regresión lineal
X = df[['numero_pollos']]

# Modelo Planta
modelo_planta = LinearRegression()
modelo_planta.fit(X, df['consumo_planta'])

# Modelo PTAR
modelo_ptar = LinearRegression()
modelo_ptar.fit(X, df['consumo_ptar'])

# 3. Diseño de la interfaz (Barra lateral para ingresar datos)
st.sidebar.header("⚙️ Parámetros de Hoy")
st.sidebar.markdown("Ingrese el volumen de producción planificado para calcular las proyecciones de consumo.")

pollos_hoy = st.sidebar.number_input(
    "🍗 Número de pollos para hoy:", 
    min_value=0, 
    max_value=50000, 
    value=25000, 
    step=500
)

# 4. Cálculo de Predicciones
pred_planta = max(0.0, modelo_planta.predict([[pollos_hoy]])[0])
pred_ptar = max(0.0, modelo_ptar.predict([[pollos_hoy]])[0])

# 5. Mostrar Resultados Principales (Métricas)
st.subheader("📊 Proyección de Consumo para Hoy")
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="🏭 Consumo Proyectado Planta", 
        value=f"{pred_planta:.2f} m³",
        help="Consumo estimado dentro de las instalaciones de procesamiento."
    )

with col2:
    st.metric(
        label="♻️ Consumo Proyectado PTAR", 
        value=f"{pred_ptar:.2f} m³",
        help="Volumen estimado que ingresará a la Planta de Tratamiento de Aguas Residuales."
    )

# 6. Visualización Gráfica de Tendencias
st.subheader("📈 Modelo de Regresión y Tendencia Histórica")

fig = go.Figure()

# Rango para dibujar la línea de regresión
rango_x = np.linspace(0, df['numero_pollos'].max() + 5000, 100).reshape(-1, 1)

# Planta
fig.add_trace(go.Scatter(x=df['numero_pollos'], y=df['consumo_planta'], mode='markers', name='Histórico Planta', marker=dict(color='#1f77b4', size=10)))
fig.add_trace(go.Scatter(x=rango_x.flatten(), y=modelo_planta.predict(rango_x), mode='lines', name='Línea Tendencia Planta', line=dict(color='#1f77b4', dash='dash')))

# PTAR
fig.add_trace(go.Scatter(x=df['numero_pollos'], y=df['consumo_ptar'], mode='markers', name='Histórico PTAR', marker=dict(color='#ff7f0e', size=10)))
fig.add_trace(go.Scatter(x=rango_x.flatten(), y=modelo_ptar.predict(rango_x), mode='lines', name='Línea Tendencia PTAR', line=dict(color='#ff7f0e', dash='dash')))

# Punto proyectado de Hoy
fig.add_trace(go.Scatter(
    x=[pollos_hoy, pollos_hoy], 
    y=[pred_planta, pred_ptar], 
    mode='markers+text', 
    name='PREDICCIÓN HOY',
    text=['Proyección Planta', 'Proyección PTAR'],
    textposition="top left",
    marker=dict(color='red', size=15, symbol='star')
))

fig.update_layout(
    xaxis_title="Número de Pollos en Producción",
    yaxis_title="Consumo de Agua (m³)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

st.plotly_chart(fig, use_container_width=True)

# 7. Tabla de datos históricos para auditoría
with st.expander("📂 Ver Registro de Datos Históricos"):
    st.dataframe(df.style.format({'consumo_planta': '{:.2f} m³', 'consumo_ptar': '{:.2f} m³', 'numero_pollos': '{:,}'}))
