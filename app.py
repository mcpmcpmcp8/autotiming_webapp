import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import altair as alt


credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)


@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_all_makes():
    query = """
    SELECT DISTINCT
      make_id,
      name as make
    FROM `autotiming-dev.metrics.make`
    ORDER BY make
    """
    return client.query(query).to_dataframe()


@st.cache_data(ttl=3600)
def get_models_for_make(selected_make_id):
    query = """
    SELECT DISTINCT
      mo.model_id,
      mo.name as model
    FROM `autotiming-dev.metrics.model` mo
    WHERE mo.make_id = @selected_make_id
    ORDER BY model
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("selected_make_id", "INT64", selected_make_id),
        ]
    )
    return client.query(query, job_config=job_config).to_dataframe()


@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_price_data(selected_make_id, selected_model_id):
    query = """
    SELECT
      ph.d AS day,
      CAST(AVG(ph.p) as INT) AS price
    FROM `autotiming-dev.metrics.ad_tracker_history` ad,
    UNNEST(price_history) AS ph
    WHERE ad.make_id = @selected_make_id
      AND ad.model_id = @selected_model_id
    GROUP BY day
    ORDER BY day
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("selected_make_id", "INT64", selected_make_id),
            bigquery.ScalarQueryParameter("selected_model_id", "INT64", selected_model_id),
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    return query_job.to_dataframe()


st.title("Análisis de Precios Promedio")

# 1. Filtro de marca (vacío por defecto)
makes_df = get_all_makes()
make_options = [""] + makes_df['make'].tolist()
selected_make = st.selectbox("Selecciona la marca:", options=make_options, index=0)

if selected_make and selected_make != "":
    # Obtener make_id seleccionado
    selected_make_id = int(makes_df[makes_df['make'] == selected_make]['make_id'].iloc[0])

    # 2. Filtro de modelo (vacío por defecto)
    models_df = get_models_for_make(selected_make_id)
    model_options = [""] + models_df['model'].tolist()
    selected_model = st.selectbox("Selecciona el modelo:", options=model_options, index=0)

    if selected_model and selected_model != "":
        # Obtener model_id seleccionado
        selected_model_id = int(models_df[models_df['model'] == selected_model]['model_id'].iloc[0])

        # 3. Consulta a la tabla grande usando make_id y model_id
        df = get_price_data(selected_make_id, selected_model_id)
        
        if not df.empty:
            # Calcular el rango del eje Y para mostrar mejor las variaciones
            min_price = df['price'].min()
            max_price = df['price'].max()
            price_range = max_price - min_price
            margin = price_range * 0.1  # 10% de margen

            # Crear el gráfico con Altair
            chart = alt.Chart(df).mark_line().encode(
                x='day:T',
                y=alt.Y('price:Q', scale=alt.Scale(domain=[min_price - margin, max_price + margin]))
            ).properties(
                width=700,
                height=400,
                title=f"Precio promedio para {selected_make} {selected_model}"
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("No hay datos disponibles para la selección actual.")
