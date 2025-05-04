import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import altair as alt

# Add custom CSS to hide the GitHub icon
st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)


@st.cache_data(ttl=3600, show_spinner=False)
def get_all_makes():
    query = """
    SELECT DISTINCT
      make_id,
      name as make
    FROM `autotiming-dev.metrics.make`
    ORDER BY make
    """
    return client.query(query).to_dataframe()


@st.cache_data(ttl=3600, show_spinner=False)
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


@st.cache_data(ttl=3600, show_spinner=False)
def get_price_data(selected_make_id, selected_model_id):
    query = """
    SELECT
      ph.d AS day,
      CAST(AVG(ph.p) as INT) AS price
    FROM `autotiming-dev.metrics.ad_tracker_history` ad,
    UNNEST(price_history) AS ph
    WHERE ad.make_id = @selected_make_id
      AND ad.model_id = @selected_model_id
    GROUP BY 1
    ORDER BY 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("selected_make_id", "INT64", selected_make_id),
            bigquery.ScalarQueryParameter("selected_model_id", "INT64", selected_model_id),
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    return query_job.to_dataframe()


@st.cache_data(ttl=3600, show_spinner=False)
def get_price_data_by_km(selected_make_id, selected_model_id):
    query = """
    SELECT
      ph.d AS day,
      km.name AS km,
      CAST(AVG(ph.p) as INT) AS price
    FROM `autotiming-dev.metrics.ad_tracker_history` ad,
    UNNEST(price_history) AS ph
    INNER JOIN `autotiming-dev.metrics.km_class` km 
        ON km.km_class_id = ad.km_class_id
    WHERE ad.make_id = @selected_make_id
      AND ad.model_id = @selected_model_id
    GROUP BY 1, 2
    ORDER BY 1
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

# 1. Filter of make (empty by default)
makes_df = get_all_makes()
make_options = [""] + makes_df['make'].tolist()
selected_make = st.selectbox("Selecciona la marca:", options=make_options, index=0)

if selected_make and selected_make != "":
    # Get selected make_id
    selected_make_id = int(makes_df[makes_df['make'] == selected_make]['make_id'].iloc[0])

    # 2. Filter of model (empty by default)
    models_df = get_models_for_make(selected_make_id)
    model_options = [""] + models_df['model'].tolist()
    selected_model = st.selectbox("Selecciona el modelo:", options=model_options, index=0)

    if selected_model and selected_model != "":
        selected_model_id = int(models_df[models_df['model'] == selected_model]['model_id'].iloc[0])

        # 3. Get all data by km
        df = get_price_data_by_km(selected_make_id, selected_model_id)

        if not df.empty:
            # Show km filter
            km_options = [""] + sorted(df['km'].unique().tolist())
            selected_km = st.selectbox("Select the km range:", options=km_options, index=0)

            # Filter in memory if the user selects a km
            if selected_km and selected_km != "":
                filtered_df = df[df['km'] == selected_km]
            else:
                filtered_df = df

            if not filtered_df.empty:
                min_price = filtered_df['price'].min()
                max_price = filtered_df['price'].max()
                price_range = max_price - min_price
                margin = price_range * 0.1

                chart = alt.Chart(filtered_df).mark_line().encode(
                    x='day:T',
                    y=alt.Y('price:Q', scale=alt.Scale(domain=[min_price - margin, max_price + margin]))
                ).properties(
                    width=700,
                    height=400,
                    title=f"Precio promedio para {selected_make} {selected_model} ({selected_km if selected_km else 'Todos los km'})"
                )

                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("No hay datos disponibles para la selección actual.")
        else:
            st.warning("No hay datos disponibles para la selección actual.")
