import streamlit as st
import polars as pl
from google.cloud import bigquery

class Queries:

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_makes(_client: bigquery.Client) -> pl.DataFrame:
        """
        Get all makes
        Args:
            client: bigquery.Client
        Returns:
            df: pl.DataFrame
        """
        query = """
        SELECT DISTINCT
            make_id,
            name as make
        FROM `autotiming-prod.metrics.make`
        ORDER BY make
        """
        pandas_df = _client.query(query).to_dataframe()
        return pl.from_pandas(pandas_df)

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_models_for_make(_client: bigquery.Client, selected_make_id: int) -> pl.DataFrame:
        """
        Get all models for a make
        Args:
            client: bigquery.Client
            selected_make_id: int
        Returns:
            df: pl.DataFrame
        """
        query = """
        SELECT DISTINCT
            mo.model_id,
            mo.name as model
        FROM `autotiming-prod.metrics.model` mo
        WHERE mo.make_id = @selected_make_id
        ORDER BY model
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("selected_make_id", "INT64", selected_make_id),
            ]
        )
        pandas_df = _client.query(query, job_config=job_config).to_dataframe()
        return pl.from_pandas(pandas_df)

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_price_per_day(_client: bigquery.Client, selected_make_id: int, selected_model_id: int) -> pl.DataFrame:
        """
        Get the price per day grouped by attributes given a make and model
        Args:
            client: bigquery.Client
            selected_make_id: int
            selected_model_id: int
        Returns:
            df: pl.DataFrame
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
        FROM `autotiming-prod.metrics.ad_tracker_history` ad,
        UNNEST(price_history) AS ph
        INNER JOIN `autotiming-prod.metrics.km_class` km 
            ON km.km_class_id = ad.km_class_id
        INNER JOIN `autotiming-prod.metrics.hp_class` hp
            ON hp.hp_class_id = ad.hp_class_id
        INNER JOIN `autotiming-prod.metrics.transmission_type` tt
            ON tt.transmission_type_id = ad.transmission_type_id
        INNER JOIN `autotiming-prod.metrics.fuel_type` ft
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
        pandas_df = query_job.to_dataframe()
        return pl.from_pandas(pandas_df)

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_dataset_by_make(_client: bigquery.Client, selected_make_id: int) -> pl.DataFrame:
        """
        Get the price per day grouped by all attributes filtered by make_id
        Args:
            client: bigquery.Client
            selected_make_id: int
        Returns:
            df: pl.DataFrame
        """
        query = """
        SELECT
            ad.make_id,
            ma.name AS make,
            ad.model_id,
            mo.name AS model,
            ph.d AS day,
            year_manufactured AS year,
            km.km_class_id AS km_class_id,
            km.name AS km_range,
            hp.hp_class_id AS hp_class_id,
            hp.name AS hp_range,
            tt.name AS transmission_type,
            ft.name AS fuel_type,
            CAST(AVG(ph.p) as INT) AS price
        FROM `autotiming-prod.metrics.ad_tracker_history` ad,
        UNNEST(price_history) AS ph
        INNER JOIN `autotiming-prod.metrics.make` ma
            ON ma.make_id = ad.make_id
        INNER JOIN `autotiming-prod.metrics.model` mo
            ON mo.model_id = ad.model_id
        INNER JOIN `autotiming-prod.metrics.km_class` km 
            ON km.km_class_id = ad.km_class_id
        INNER JOIN `autotiming-prod.metrics.hp_class` hp
            ON hp.hp_class_id = ad.hp_class_id
        INNER JOIN `autotiming-prod.metrics.transmission_type` tt
            ON tt.transmission_type_id = ad.transmission_type_id
        INNER JOIN `autotiming-prod.metrics.fuel_type` ft
            ON ft.fuel_type_id = ad.fuel_type_id
        WHERE ad.make_id = @selected_make_id
        GROUP BY ALL
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("selected_make_id", "INT64", selected_make_id),
            ]
        )
        pandas_df = _client.query(query, job_config=job_config).to_dataframe()
        return pl.from_pandas(pandas_df)

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_dataset(_client: bigquery.Client) -> pl.DataFrame:
        """
        Get the price per day grouped by all attributes
        Args:
            client: bigquery.Client
        Returns:
            df: pl.DataFrame
        """
        query = """
        SELECT
            ad.make_id,
            ma.name AS make,
            ad.model_id,
            mo.name AS model,
            ph.d AS day,
            year_manufactured AS year,
            km.km_class_id AS km_class_id,
            km.name AS km_range,
            hp.hp_class_id AS hp_class_id,
            hp.name AS hp_range,
            tt.name AS transmission_type,
            ft.name AS fuel_type,
            CAST(AVG(ph.p) as INT) AS price
        FROM `autotiming-prod.metrics.ad_tracker_history` ad,
        UNNEST(price_history) AS ph
        INNER JOIN `autotiming-prod.metrics.make` ma
            ON ma.make_id = ad.make_id
        INNER JOIN `autotiming-prod.metrics.model` mo
            ON mo.model_id = ad.model_id
        INNER JOIN `autotiming-prod.metrics.km_class` km 
            ON km.km_class_id = ad.km_class_id
        INNER JOIN `autotiming-prod.metrics.hp_class` hp
            ON hp.hp_class_id = ad.hp_class_id
        INNER JOIN `autotiming-prod.metrics.transmission_type` tt
            ON tt.transmission_type_id = ad.transmission_type_id
        INNER JOIN `autotiming-prod.metrics.fuel_type` ft
            ON ft.fuel_type_id = ad.fuel_type_id
        GROUP BY ALL
        """
        pandas_df = _client.query(query).to_dataframe()
        return pl.from_pandas(pandas_df)