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

    return bigquery.Client(
        credentials=credentials,
        project=credentials.project_id
    )


@st.cache_data(ttl=120)
def run_query(sql: str) -> pd.DataFrame:
    client = get_bigquery_client()
    return client.query(sql).to_dataframe()


# 3. Obtención de datos desde BigQuery
@st.cache_data(ttl=120)
def obtener_datos_completos():

    dataset_id = st.secrets["bigquery"]["dataset_id"]
    project_id = st.secrets["gcp_service_account"]["project_id"]

    sql = f"""
        SELECT 
            fecha, 
            total_pollos, 
            consumo_planta, 
            procesamiento_ptar,
            litros_pollo
        FROM `{project_id}.{dataset_id}.cba_4_parametros_produccion`
        ORDER BY fecha ASC
    """

    # Traemos todos los datos
    df_bruto = run_query(sql)

    return df_bruto


# Cargar los datos
try:
    df_bruto = obtener_datos_completos()

except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()


if df_bruto.empty:
    st.warning("La base de datos está vacía.")
    st.stop()


# 4. Separar lógica:
# Último registro vs Datos de entrenamiento

# A) Extraemos el último registro
ultimo_registro = df_bruto.iloc[-1]

fecha_reciente = ultimo_registro["fecha"]
pollos_reciente = ultimo_registro["total_pollos"]


if pd.isna(pollos_reciente):

    st.warning(
        f"El registro de la fecha {fecha_reciente} "
        "no tiene número de pollos. "
        "Por favor, actualiza la base de datos."
    )

    st.stop()


# B) Filtramos solo los registros COMPLETOS para entrenar el modelo

df_entrenamiento = df_bruto.dropna(
    subset=[
        "total_pollos",
        "consumo_planta",
        "procesamiento_ptar"
    ]
)


if len(df_entrenamiento) < 2:

    st.warning(
        "No hay suficientes días con datos completos "
        "(pollos + consumos) para generar el modelo."
    )

    st.stop()


# 5. Entrenamiento de los modelos de regresión lineal

X = df_entrenamiento[["total_pollos"]]


# Modelo Planta
modelo_planta = LinearRegression()

modelo_planta.fit(
    X,
    df_entrenamiento["consumo_planta"]
)


# Modelo PTAR
modelo_ptar = LinearRegression()

modelo_ptar.fit(
    X,
    df_entrenamiento["procesamiento_ptar"]
)


# 6. Diseño de la interfaz
# Barra lateral

st.sidebar.header("⚙️ Parámetros del Día")

st.sidebar.markdown(
    "Datos del último registro en BD:"
)


st.sidebar.info(
    f"📅 **Fecha de evaluación:**\n\n"
    f"{fecha_reciente}"
)


st.sidebar.metric(
    label="🍗 Total de pollos ingresados:",
    value=f"{int(pollos_reciente):,}"
)


# Mostrar litros/pollo del último registro
litros_pollo_reciente = ultimo_registro["litros_pollo"]

if pd.notnull(litros_pollo_reciente):

    st.sidebar.metric(
        label="💧 Litros por pollo:",
        value=f"{litros_pollo_reciente:.2f} L/pollo"
    )

else:

    st.sidebar.metric(
        label="💧 Litros por pollo:",
        value="Pendiente"
    )


# Indicador visual de si el día ya se cerró

if (
    pd.isna(ultimo_registro["consumo_planta"])
    or pd.isna(ultimo_registro["procesamiento_ptar"])
):

    st.sidebar.warning(
        "⏳ **Estado del día:** "
        "Abierto. Esperando datos de consumo final."
    )

else:

    st.sidebar.success(
        "✅ **Estado del día:** "
        "Cerrado. Consumos registrados."
    )


# 7. Cálculo de Predicciones

X_pred = pd.DataFrame({
    "total_pollos": [pollos_reciente]
})


pred_planta = max(
    0.0,
    modelo_planta.predict(X_pred)[0]
)


pred_ptar = max(
    0.0,
    modelo_ptar.predict(X_pred)[0]
)


# 8. Mostrar Resultados Principales

st.subheader(
    f"📊 Proyección de Consumo para el {fecha_reciente}"
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        label="🏭 Consumo Proyectado Planta",
        value=f"{pred_planta:.2f} m³",
        help=(
            "Consumo estimado dentro de las instalaciones "
            "basado en los pollos de hoy."
        )
    )


with col2:

    st.metric(
        label="♻️ Volumen de Procesamiento PTAR",
        value=f"{pred_ptar:.2f} m³",
        help=(
            "Volumen estimado hacia la PTAR "
            "basado en los pollos de hoy."
        )
    )


with col3:

    if pd.notnull(litros_pollo_reciente):

        st.metric(
            label="💧 Litros por Pollo",
            value=f"{litros_pollo_reciente:.2f} L/pollo",
            help=(
                "Consumo de agua por cada pollo "
                "procesado."
            )
        )

    else:

        st.metric(
            label="💧 Litros por Pollo",
            value="Pendiente"
        )


st.markdown("---")


# 9. Visualización Gráfica de Tendencias

st.subheader("📈 Gráfico de Tendencia Histórica")


fig = go.Figure()


# Rango para dibujar la línea de regresión

rango_x = np.linspace(
    0,
    df_entrenamiento["total_pollos"].max() + 5000,
    100
)


rango_x_df = pd.DataFrame({
    "total_pollos": rango_x
})


# Planta
fig.add_trace(
    go.Scatter(
        x=df_entrenamiento["total_pollos"],
        y=df_entrenamiento["consumo_planta"],
        mode="markers",
        name="Histórico Planta",
        marker=dict(
            color="#1f77b4",
            size=10
        )
    )
)


fig.add_trace(
    go.Scatter(
        x=rango_x,
        y=modelo_planta.predict(rango_x_df),
        mode="lines",
        name="Línea Tendencia Planta",
        line=dict(
            color="#1f77b4",
            dash="dash"
        )
    )
)


# PTAR
fig.add_trace(
    go.Scatter(
        x=df_entrenamiento["total_pollos"],
        y=df_entrenamiento["procesamiento_ptar"],
        mode="markers",
        name="Histórico PTAR",
        marker=dict(
            color="#ff7f0e",
            size=10
        )
    )
)


fig.add_trace(
    go.Scatter(
        x=rango_x,
        y=modelo_ptar.predict(rango_x_df),
        mode="lines",
        name="Línea Tendencia PTAR",
        line=dict(
            color="#ff7f0e",
            dash="dash"
        )
    )
)


# Punto proyectado actual

fig.add_trace(
    go.Scatter(
        x=[
            pollos_reciente,
            pollos_reciente
        ],

        y=[
            pred_planta,
            pred_ptar
        ],

        mode="markers+text",

        name="PREDICCIÓN ACTUAL",

        text=[
            "Proyección Planta",
            "Proyección PTAR"
        ],

        textposition="top left",

        marker=dict(
            color="red",
            size=15,
            symbol="star"
        )
    )
)


fig.update_layout(

    xaxis_title="Número de Pollos en Producción",

    yaxis_title="Consumo de Agua (m³)",

    hovermode="x unified",

    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# 10. Tabla de datos históricos

with st.expander(
    "📂 Ver Registro de Datos Históricos "
    "(Incluyendo días abiertos)"
):

    # Formateo de columnas

    formato_columnas = {

        "consumo_planta":
            lambda x:
                f"{x:.2f} m³"
                if pd.notnull(x)
                else "⏳ Pendiente",

        "procesamiento_ptar":
            lambda x:
                f"{x:.2f} m³"
                if pd.notnull(x)
                else "⏳ Pendiente",

        "litros_pollo":
            lambda x:
                f"{x:.2f} L/pollo"
                if pd.notnull(x)
                else "⏳ Pendiente",

        "total_pollos":
            lambda x:
                f"{int(x):,}"
                if pd.notnull(x)
                else "0"
    }


    st.dataframe(
        df_bruto.style.format(formato_columnas),
        use_container_width=True
    )
