import streamlit as st
import altair as alt
import polars as pl

from streamlit import session_state as ss

from aux_functions.db_connect import DBConnect
from aux_functions.queries import Queries
from aux_functions.css import hide_streamlit_style
from aux_functions.filters import apply_filter_style

# Hide streamlit style and apply custom filter styles
hide_streamlit_style()
apply_filter_style()

# initialize filters
selected_make = None
selected_model = None
selected_hp_range = None
selected_transmission = None
selected_km_range = None
selected_year = None
selected_fuel_type = None

with st.spinner("Cargando datos..."):
    # Initialize the bigquery client
    try:
        db_connect = DBConnect()
        bigquery_client = db_connect.get_client()
    except Exception as e:
        st.error(f"Error connecting to BigQuery: {e}")
        st.stop()

    # Get makes first (lightweight query)
    makes_df = Queries.get_all_makes(bigquery_client)

def on_makes_change():
    # delete all filter session states except make_selected
    for key in list(ss.keys()):
        if key not in ['make_selected', 'make_id']:
            del ss[key]

def clear_filters():
    """Clear all filter values from session state"""
    # List of all filter keys to clear
    filter_keys = [
        'hp_range_selected',
        'transmission_selected',
        'km_range_selected',
        'year_selected',
        'fuel_type_selected'
    ]
    
    # Clear each filter from session state
    for key in filter_keys:
        if key in ss:
            del ss[key]
    
    st.rerun()

with st.container():
    st.markdown('<div class="filter-title">Selección de Vehículo</div>', unsafe_allow_html=True)
    # Make filter
    selected_make = st.selectbox(
        label="Marca:",
        options=[""] + makes_df.select("make").to_series().to_list(),
        key="make_selected",
        on_change=on_makes_change,
    )
    
    # Store the make_id when a make is selected
    if selected_make:
        selected_make_id = makes_df.filter(pl.col("make") == selected_make).select("make_id").item()
        ss.make_id = selected_make_id
        
        # Load the dataset filtered by make_id (much smaller dataset)
        with st.spinner("Cargando datos de la marca seleccionada..."):
            df = Queries.get_dataset_by_make(bigquery_client, selected_make_id)
            df_filtered = df
            
        # Model filter
        selected_model = st.selectbox(
            label="Modelo:",
            options=[""] + df.select("model").unique().sort("model").to_series().to_list(),
            key="model_selected",
        )
        if selected_model:
            df_filtered = df_filtered.filter(pl.col("model") == selected_model)

            # rest of the filters
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.markdown('<div class="filter-title">Estado del Vehículo</div>', unsafe_allow_html=True)

                selected_km_range = st.selectbox(
                    label="Kilometraje:",
                    options=[""] + df_filtered.select(["km_range", "km_class_id"]).unique().sort("km_class_id").select("km_range").to_series().to_list(),
                    key="km_range_selected"
                )
                if selected_km_range:
                    df_filtered = df_filtered.filter(pl.col("km_range") == selected_km_range)
                    selected_year = st.selectbox(
                        label="Año",
                        options=[""] + df_filtered.select("year").unique().sort("year", descending=True).to_series().to_list(),
                        key="year_selected"
                    )
                    if selected_year:
                        df_filtered = df_filtered.filter(pl.col("year") == selected_year)

                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                
                if selected_km_range and selected_year:
                    st.markdown('<div class="filter-title">Características Técnicas</div>', unsafe_allow_html=True)
                    selected_hp_range = st.selectbox(
                        label="Potencia (CV):",
                        options=[""] + df_filtered.select(["hp_range", "hp_class_id"]).unique().sort("hp_class_id").select("hp_range").to_series().to_list(),
                        key="hp_range_selected",
                    )
                    if selected_hp_range:
                        df_filtered = df_filtered.filter(pl.col("hp_range") == selected_hp_range)

                        selected_transmission = st.selectbox(
                            label="Transmisión:",
                            options=[""] + df_filtered.select("transmission_type").unique().select("transmission_type").to_series().to_list(),
                            key="transmission_selected"
                        )
                        if selected_transmission:
                            df_filtered = df_filtered.filter(pl.col("transmission_type") == selected_transmission)

                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)

                if selected_hp_range and selected_transmission:
                    st.markdown('<div class="filter-title">Características Adicionales</div>', unsafe_allow_html=True)
                    selected_fuel_type = st.selectbox(
                        label="Combustible:",
                        options=[""] + df_filtered.select("fuel_type").unique().select("fuel_type").to_series().to_list(),
                        key="fuel_type_selected"
                    )
                    if selected_fuel_type:
                        df_filtered = df_filtered.filter(pl.col("fuel_type") == selected_fuel_type)

                st.markdown('</div>', unsafe_allow_html=True)

        # button to clear all filters
        if st.button(
            label="Limpiar Filtros",
            key="clear_filters_button",
            use_container_width=False,
        ):
            clear_filters()

        if selected_model:
            # Group by day and calculate average price
            df_avg = (df_filtered
                      .group_by("day")
                      .agg(pl.col("price").mean().alias("price"))
                      .with_columns(pl.col("price").cast(pl.Int32))
                      .sort("day"))
            
            # Convert to pandas for Altair (since Altair works better with pandas)
            df_avg_pandas = df_avg.to_pandas()
            
            min_price = df_avg.select(pl.col("price").min()).item()
            max_price = df_avg.select(pl.col("price").max()).item()
            price_range = max_price - min_price
            margin = price_range * 0.5
            chart = alt.Chart(df_avg_pandas).mark_line(interpolate='basis').encode(
                x=alt.X(
                    'day:T', 
                    axis=alt.Axis(
                        title=None,
                        format='%b %d'
                    )
                ),
                y=alt.Y('price:Q', scale=alt.Scale(domain=[min_price - margin, max_price + margin]), axis=alt.Axis(title='€'))
            ).properties(
                width=700,
                height=400,
                title={
                    "text": f"Precio promedio",
                    "anchor": "middle",
                    "align": "center"
                }
            )

            # Display chart in a container for better styling
            with st.container():
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.altair_chart(chart, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Por favor, selecciona una marca para continuar.")
