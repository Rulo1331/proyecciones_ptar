import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account

# 1. Configuración de la página
st.set_page_config(
    page_title="Proyecciones PTAR & Planta", 
    page_icon="💧", 
    layout="wide"
)

# Título principal
st.title("💧 Proyección de Consumo de Agua - CBA Santa Elena")
st.markdown("---")

# 2. Configuración de Conexión a BigQuery
@st.cache_resource
def get_bigquery_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

@st.cache_data(ttl=300) # Se actualiza cada 5 minutos
def run_query(sql: str) -> pd.DataFrame:
    client = get_bigquery_client()
    return client.query(sql).to_dataframe()

# 3. Obtención de datos históricos desde BigQuery
@st.cache_data(ttl=300)
def obtener_datos_historicos():
    dataset_id = st.secrets["bigquery"]["dataset_id"]
    project_id = st.secrets["gcp_service_account"]["project_id"]
    
    sql = f"""
        SELECT 
            fecha, 
            total_pollos, 
            consumo_planta, 
            procesamiento_ptar 
        FROM `{project_id}.{dataset_id}.cba_4_parametros_produccion`
        ORDER BY fecha ASC
    """
    df = run_query(sql)
    
    # Limpieza básica: Eliminar filas con valores nulos
    df = df.dropna(subset=['total_pollos', 'consumo_planta', 'procesamiento_ptar'])
    
    return df

# Cargar los datos
try:
    df = obtener_datos_historicos()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# Verificar que hay suficientes datos
if df.empty or len(df) < 2:
    st.warning("No hay suficientes datos históricos en la base de datos para generar proyecciones.")
    st.stop()

# 4. Obtener el dato más reciente (última fila del DataFrame)
ultimo_registro = df.iloc[-1]
fecha_reciente = ultimo_registro['fecha']
pollos_reciente = ultimo_registro['total_pollos']

# 5. Entrenamiento de los modelos de regresión lineal
X = df[['total_pollos']]

# Modelo Planta
modelo_planta = LinearRegression()
modelo_planta.fit(X, df['consumo_planta'])

# Modelo PTAR
modelo_ptar = LinearRegression()
modelo_ptar.fit(X, df['procesamiento_ptar'])

# 6. Diseño de la interfaz (Barra lateral de solo lectura)
st.sidebar.header("⚙️ Parámetros Actuales")
st.sidebar.markdown("Datos obtenidos de la base de datos:")

st.sidebar.info(f"📅 **Fecha del último registro:**\n\n{fecha_reciente}")

st.sidebar.metric(
    label="🍗 Número de pollos:", 
    value=f"{int(pollos_reciente):,}"
)

# 7. Cálculo de Predicciones usando el dato más reciente
X_pred = pd.DataFrame({'total_pollos': [pollos_reciente]})

pred_planta = max(0.0, modelo_planta.predict(X_pred)[0])
pred_ptar = max(0.0, modelo_ptar.predict(X_pred)[0])

# 8. Mostrar Resultados Principales (Métricas)
st.subheader(f"📊 Proyección de Consumo para el {fecha_reciente}")
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="🏭 Consumo Proyectado Planta", 
        value=f"{pred_planta:.2f} m³",
        help="Consumo estimado dentro de las instalaciones de procesamiento."
    )

with col2:
    st.metric(
        label="♻️ Volumen de Procesamiento PTAR", 
        value=f"{pred_ptar:.2f} m³",
        help="Volumen estimado que ingresará a la Planta de Tratamiento de Aguas Residuales."
    )

st.markdown("---")

# 9. Visualización Gráfica de Tendencias
st.subheader("📈 Gráfico de Tendencia Histórica")

fig = go.Figure()

# Rango para dibujar la línea de regresión
rango_x = np.linspace(0, df['total_pollos'].max() + 5000, 100)
rango_x_df = pd.DataFrame({'total_pollos': rango_x})

# Planta
fig.add_trace(go.Scatter(x=df['total_pollos'], y=df['consumo_planta'], mode='markers', name='Histórico Planta', marker=dict(color='#1f77b4', size=10)))
fig.add_trace(go.Scatter(x=rango_x, y=modelo_planta.predict(rango_x_df), mode='lines', name='Línea Tendencia Planta', line=dict(color='#1f77b4', dash='dash')))

# PTAR
fig.add_trace(go.Scatter(x=df['total_pollos'], y=df['procesamiento_ptar'], mode='markers', name='Histórico PTAR', marker=dict(color='#ff7f0e', size=10)))
fig.add_trace(go.Scatter(x=rango_x, y=modelo_ptar.predict(rango_x_df), mode='lines', name='Línea Tendencia PTAR', line=dict(color='#ff7f0e', dash='dash')))

# Punto proyectado Actual
fig.add_trace(go.Scatter(
    x=[pollos_reciente, pollos_reciente], 
    y=[pred_planta, pred_ptar], 
    mode='markers+text', 
    name='PREDICCIÓN ACTUAL',
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

# 10. Tabla de datos históricos para auditoría
with st.expander("📂 Ver Registro de Datos Históricos (Desde BigQuery)"):
    st.dataframe(df.style.format({
        'consumo_planta': '{:.2f} m³', 
        'procesamiento_ptar': '{:.2f} m³', 
        'total_pollos': '{:,}'
    }))
