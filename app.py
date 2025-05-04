import streamlit as st
import altair as alt

from aux_functions.db_connect import DBConnect
from aux_functions.queries import Queries

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

# Initialize the bigquery client
try:
    db_connect = DBConnect()
    bigquery_client = db_connect.get_client()
except Exception as e:
    st.error(f"Error connecting to BigQuery: {e}")
    st.stop()

# Title
st.title("Histórico de Precios del Mercado de Coches de Segunda Mano en España", anchor=False)

# 1. Filter of make (empty by default)
makes_df = Queries.get_all_makes(bigquery_client)
make_options = [""] + makes_df['make'].tolist()
selected_make = st.selectbox("Selecciona la marca:", options=make_options, index=0)

if selected_make and selected_make != "":
    # Get selected make_id
    selected_make_id = int(makes_df[makes_df['make'] == selected_make]['make_id'].iloc[0])

    # 2. Filter of model (empty by default)
    models_df = Queries.get_models_for_make(bigquery_client, selected_make_id)
    model_options = [""] + models_df['model'].tolist()
    selected_model = st.selectbox("Selecciona el modelo:", options=model_options, index=0)

    if selected_model and selected_model != "":
        selected_model_id = int(models_df[models_df['model'] == selected_model]['model_id'].iloc[0])

        # 3. Get all data by attributes
        df = Queries.get_price_per_day(bigquery_client, selected_make_id, selected_model_id)

        if not df.empty:

            # Show hp filter
            hp_df = df[['hp_class_id', 'hp_range']].sort_values('hp_class_id')
            hp_options = [""] + hp_df['hp_range'].unique().tolist()
            selected_hp_range = st.selectbox("Selecciona el rango de caballos:", options=hp_options, index=0)

            # Show km filter
            km_df = df[['km_class_id', 'km_range']].sort_values('km_class_id')
            km_options = [""] + km_df['km_range'].unique().tolist()
            selected_km_range = st.selectbox("Selecciona el rango de kilometraje:", options=km_options, index=0)

            # Show transmission filter
            tt_df = df[['transmission_type']].sort_values('transmission_type')
            tt_options = [""] + tt_df['transmission_type'].unique().tolist()
            selected_transmission_type = st.selectbox("Selecciona el tipo de transmisión:", options=tt_options, index=0)

            # Show fuel filter
            ft_df = df[['fuel_type']].sort_values('fuel_type')
            ft_options = [""] + ft_df['fuel_type'].unique().tolist()
            selected_fuel_type = st.selectbox("Selecciona el tipo de combustible:", options=ft_options, index=0)

            # Show year filter
            year_df = df[['year']].sort_values('year')
            year_options = [""] + year_df['year'].unique().tolist()
            selected_year = st.selectbox("Selecciona el año de fabricación:", options=year_options, index=0)

            # Filter in memory if the user selects
            if (selected_km_range and selected_km_range != "" and
                selected_hp_range and selected_hp_range != "" and
                selected_transmission_type and selected_transmission_type != "" and
                selected_fuel_type and selected_fuel_type != "" and
                selected_year and selected_year != ""
            ):
                filtered_df = df[
                    (df['km_range'] == selected_km_range) &
                    (df['hp_range'] == selected_hp_range) &
                    (df['transmission_type'] == selected_transmission_type) &
                    (df['fuel_type'] == selected_fuel_type) &
                    (df['year'] == selected_year)
                ]
            else:
                filtered_df = (
                    df.groupby('day', as_index=False)
                    .agg(price=('price', 'mean'))
                )

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
                    title=f"Precio promedio para {selected_make} {selected_model})"
                )

                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("No hay datos disponibles para la selección actual.")
        else:
            st.warning("No hay datos disponibles para la selección actual.")
