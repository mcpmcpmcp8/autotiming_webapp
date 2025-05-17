import streamlit as st
import altair as alt

from aux_functions.db_connect import DBConnect
from aux_functions.queries import Queries
from aux_functions.css import hide_streamlit_style

# Hide streamlit style
hide_streamlit_style()

# Initialize the bigquery client
try:
    db_connect = DBConnect()
    bigquery_client = db_connect.get_client()
except Exception as e:
    st.error(f"Error connecting to BigQuery: {e}")
    st.stop()

# Title
st.title("Evolución del Precio de Coches", anchor=False)

# 1. Filter of make (empty by default)
df = Queries.get_all_dataset(bigquery_client)
make_options = [""] + df['make'].drop_duplicates().sort_values().tolist()
selected_make = st.selectbox("Selecciona la marca:", options=make_options, index=0)

if selected_make and selected_make != "":
    # Get selected make_id
    selected_make_id = int(df[df['make'] == selected_make]['make_id'].iloc[0])

    # 2. Filter of model (empty by default)
    model_options = [""] + df[df['make_id'] == selected_make_id]['model'].drop_duplicates().sort_values().tolist()
    selected_model = st.selectbox("Selecciona el modelo:", options=model_options, index=0)

    if selected_model and selected_model != "":
        selected_model_id = int(df[df['model'] == selected_model]['model_id'].iloc[0])

        # 3. Get all data by attributes
        df = df[(df['make_id'] == selected_make_id) & (df['model_id'] == selected_model_id)]
        if not df.empty:
            # Show hp filter
            hp_df = df[['hp_class_id', 'hp_range']].drop_duplicates().sort_values('hp_class_id')
            hp_options = [""] + hp_df['hp_range'].tolist()
            selected_hp_range = st.selectbox("Selecciona el rango de caballos:", options=hp_options, index=0)

            # Filter df by selected hp_range if any
            if selected_hp_range and selected_hp_range != "":
                df = df[df['hp_range'] == selected_hp_range]

            # Show km filter (only for the filtered df)
            km_df = df[['km_class_id', 'km_range']].drop_duplicates().sort_values('km_class_id')
            km_options = [""] + km_df['km_range'].tolist()
            selected_km_range = st.selectbox("Selecciona el rango de kilometraje:", options=km_options, index=0)

            # Filter df by selected km_range if any
            if selected_km_range and selected_km_range != "":
                df = df[df['km_range'] == selected_km_range]

            # Show transmission filter (only for the filtered df)
            tt_df = df[['transmission_type']].drop_duplicates().sort_values('transmission_type')
            tt_options = [""] + tt_df['transmission_type'].tolist()
            selected_transmission_type = st.selectbox("Selecciona el tipo de transmisión:", options=tt_options, index=0)

            # Filter df by selected transmission_type if any
            if selected_transmission_type and selected_transmission_type != "":
                df = df[df['transmission_type'] == selected_transmission_type]

            # Show fuel filter (only for the filtered df)
            ft_df = df[['fuel_type']].drop_duplicates().sort_values('fuel_type')
            ft_options = [""] + ft_df['fuel_type'].tolist()
            selected_fuel_type = st.selectbox("Selecciona el tipo de combustible:", options=ft_options, index=0)

            # Filter df by selected fuel_type if any
            if selected_fuel_type and selected_fuel_type != "":
                df = df[df['fuel_type'] == selected_fuel_type]

            # Show year filter (only for the filtered df)
            year_df = df[['year']].drop_duplicates().sort_values('year')
            year_options = [""] + year_df['year'].tolist()
            selected_year = st.selectbox("Selecciona el año de fabricación:", options=year_options, index=0)

            # Filter df by selected year if any
            if selected_year and selected_year != "":
                df = df[df['year'] == selected_year]

            if not df.empty:
                # Group by day and calculate average price
                df_avg = df.groupby('day', as_index=False)['price'].mean()
                df_avg['price'] = df_avg['price'].astype(int)  # Convert to integer for cleaner display

                min_price = df_avg['price'].min()
                max_price = df_avg['price'].max()
                price_range = max_price - min_price
                margin = price_range * 0.1

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
                        "text": f"Precio promedio para {selected_make} {selected_model}",
                        "anchor": "middle"
                    }
                )

                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("No hay datos disponibles para la selección actual.")
        else:
            st.warning("No hay datos disponibles para la selección actual.")
