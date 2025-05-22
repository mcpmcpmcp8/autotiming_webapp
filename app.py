import streamlit as st
import altair as alt

from streamlit import session_state as ss

from aux_functions.db_connect import DBConnect
from aux_functions.queries import Queries
from aux_functions.css import hide_streamlit_style
from aux_functions.filters import apply_filter_style

# Hide streamlit style and apply custom filter styles
hide_streamlit_style()
apply_filter_style()

# Initialize the bigquery client
try:
    db_connect = DBConnect()
    bigquery_client = db_connect.get_client()
except Exception as e:
    st.error(f"Error connecting to BigQuery: {e}")
    st.stop()

# initialize filters
selected_make = None
selected_model = None
selected_hp_range = None
selected_transmission = None
selected_km_range = None
selected_year = None
selected_fuel_type = None

# Title
st.title("Evolución del Precio de Coches", anchor=False)

# Get initial dataset
df = Queries.get_all_dataset(bigquery_client)
df_filtered = df

def on_makes_change():
    # delete all filter session states except make_selected
    for key in list(ss.keys()):
        if key != 'make_selected':
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
        options=[""] + df.make.drop_duplicates().sort_values().tolist(),
        key="make_selected",
        on_change=on_makes_change,
    )
    if selected_make:
        df_filtered = df[df['make'] == selected_make]
        # Model filter
        selected_model = st.selectbox(
            label="Modelo:",
            options=[""] + df[df['make'] == ss.make_selected]['model'].drop_duplicates().sort_values().tolist(),
            key="model_selected",
        )
        if selected_model:
            df_filtered = df_filtered[df_filtered['model'] == selected_model]

            # rest of the filters
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.markdown('<div class="filter-title">Características Técnicas</div>', unsafe_allow_html=True)

                selected_hp_range = st.selectbox(
                    label="Potencia (CV):",
                    options=[""] + df_filtered[['hp_range','hp_class_id']].drop_duplicates().sort_values('hp_class_id')['hp_range'].tolist(),
                    key="hp_range_selected",
                )
                if selected_hp_range:
                    df_filtered = df_filtered[df_filtered['hp_range'] == selected_hp_range]

                    selected_transmission = st.selectbox(
                        label="Transmisión:",
                        options=[""] + df_filtered[['transmission_type']].drop_duplicates()['transmission_type'].tolist(),
                        key="transmission_selected"
                    )
                    if selected_transmission:
                        df_filtered = df_filtered[df_filtered['transmission_type'] == selected_transmission]

                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)

                if selected_hp_range and selected_transmission:
                    st.markdown('<div class="filter-title">Estado del Vehículo</div>', unsafe_allow_html=True)
                    selected_km_range = st.selectbox(
                        label="Kilometraje:",
                        options=[""] + df_filtered[['km_range','km_class_id']].drop_duplicates().sort_values('km_class_id')['km_range'].tolist(),
                        key="km_range_selected"
                    )
                    if selected_km_range:
                        df_filtered = df_filtered[df_filtered['km_range'] == selected_km_range]

                        selected_year = st.selectbox(
                            label="Año",
                            options=[""] + df_filtered['year'].drop_duplicates().sort_values(ascending=False).tolist(),
                            key="year_selected"
                        )
                        if selected_year:
                            df_filtered = df_filtered[df_filtered['year'] == selected_year]

                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)

                if selected_km_range and selected_year:
                    st.markdown('<div class="filter-title">Características Adicionales</div>', unsafe_allow_html=True)
                    selected_fuel_type = st.selectbox(
                        label="Combustible:",
                        options=[""] + df_filtered[['fuel_type']].drop_duplicates()['fuel_type'].tolist(),
                        key="fuel_type_selected"
                    )
                    if selected_fuel_type:
                        df_filtered = df_filtered[df_filtered['fuel_type'] == selected_fuel_type]

                st.markdown('</div>', unsafe_allow_html=True)


# button to clear all filters
if st.button(
    label="Limpiar Filtros",
    key="clear_filters_button",
    use_container_width=False,
):
    clear_filters()

if selected_make and selected_model:
    # Group by day and calculate average price
    df_avg = df_filtered.groupby('day', as_index=False)['price'].mean()
    df_avg['price'] = df_avg['price'].astype(int)
    min_price = df_avg['price'].min()
    max_price = df_avg['price'].max()
    price_range = max_price - min_price
    margin = price_range * 0.3
    chart = alt.Chart(df_avg).mark_line().encode(
        x=alt.X(
            'day:T', 
            axis=alt.Axis(
                title=None,
                format='%d/%m/%Y'
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
