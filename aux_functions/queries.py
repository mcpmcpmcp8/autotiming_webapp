import streamlit as st
import pandas as pd
from google.cloud import bigquery

class Queries:

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_makes(_client: bigquery.Client) -> pd.DataFrame:
        """
        Get all makes
        Args:
            client: bigquery.Client
        Returns:
            df: pd.DataFrame
        """
        query = """
        SELECT DISTINCT
            make_id,
            name as make
        FROM `autotiming-dev.metrics.make`
        ORDER BY make
        """
        return _client.query(query).to_dataframe()

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_models_for_make(_client: bigquery.Client, selected_make_id: int) -> pd.DataFrame:
        """
        Get all models for a make
        Args:
            client: bigquery.Client
            selected_make_id: int
        Returns:
            df: pd.DataFrame
        """
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
        return _client.query(query, job_config=job_config).to_dataframe()

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_price_per_day(_client: bigquery.Client, selected_make_id: int, selected_model_id: int) -> pd.DataFrame:
        """
        Get the price per day grouped by attributes given a make and model
        Args:
            client: bigquery.Client
            selected_make_id: int
            selected_model_id: int
        Returns:
            df: pd.DataFrame
        """
        query = """
        SELECT
            ph.d AS day,
            year_manufactured AS year,
            km.km_class_id AS km_class_id,
            km.name AS km_range,
            hp.hp_class_id AS hp_class_id,
            hp.name AS hp_range,
            tt.name AS transmission_type,
            ft.name AS fuel_type,
            CAST(AVG(ph.p) as INT) AS price
        FROM `autotiming-dev.metrics.ad_tracker_history` ad,
        UNNEST(price_history) AS ph
        INNER JOIN `autotiming-dev.metrics.km_class` km 
            ON km.km_class_id = ad.km_class_id
        INNER JOIN `autotiming-dev.metrics.hp_class` hp
            ON hp.hp_class_id = ad.hp_class_id
        INNER JOIN `autotiming-dev.metrics.transmission_type` tt
            ON tt.transmission_type_id = ad.transmission_type_id
        INNER JOIN `autotiming-dev.metrics.fuel_type` ft
            ON ft.fuel_type_id = ad.fuel_type_id
        WHERE ad.make_id = @selected_make_id
        AND ad.model_id = @selected_model_id
        GROUP BY ALL
        ORDER BY day
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("selected_make_id", "INT64", selected_make_id),
                bigquery.ScalarQueryParameter("selected_model_id", "INT64", selected_model_id),
            ]
        )
        query_job = _client.query(query, job_config=job_config)
        return query_job.to_dataframe()

