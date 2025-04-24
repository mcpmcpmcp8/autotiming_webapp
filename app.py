import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account


credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)


st.title("Consulta BigQuery desde Streamlit")

query = """
    SELECT *
    FROM `autotiming-dev.metrics.fuel_type`
"""

# Ejecutar consulta
query_job = client.query(query)
df = query_job.to_dataframe()

# Mostrar resultado
st.write("Datos desde BigQuery:")
st.dataframe(df)
