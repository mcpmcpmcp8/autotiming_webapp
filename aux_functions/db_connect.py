import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

class DBConnect:

    @staticmethod    
    @st.cache_resource
    def get_client() -> bigquery.Client:
        """
        Get the bigquery client
        Returns:
            bigquery.Client
        """
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account_prod"]
        )
        client = bigquery.Client(credentials=credentials)
        return client
