import streamlit as st
import altair as alt

from aux_functions.db_connect import DBConnect
from aux_functions.queries import Queries
from aux_functions.css import hide_streamlit_style
from aux_functions.filters import apply_filter_style, create_make_model_filters, create_attribute_filters

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

# Title
st.title("Evolución del Precio de Coches", anchor=False)

# Get initial dataset
df = Queries.get_all_dataset(bigquery_client)

# Create make and model filters
selected_make, selected_make_id, selected_model = create_make_model_filters(df)

if selected_make and selected_make != "" and selected_model and selected_model != "":
    # Get selected model_id
    selected_model_id = int(df[df['model'] == selected_model]['model_id'].iloc[0])
    
    # Filter initial dataset by make and model
    df = df[(df['make_id'] == selected_make_id) & (df['model_id'] == selected_model_id)]
    
    if not df.empty:
        # Create attribute filters in a horizontal layout
        filters = create_attribute_filters(df)
        
        # Apply filters sequentially
        filtered_df = df.copy()
        for filter_name, filter_value in filters.items():
            if filter_value and filter_value != "":
                filtered_df = filtered_df[filtered_df[filter_name] == filter_value]
        
        if not filtered_df.empty:
            # Group by day and calculate average price
            df_avg = filtered_df.groupby('day', as_index=False)['price'].mean()
            df_avg['price'] = df_avg['price'].astype(int)  # Convert to integer for cleaner display

            min_price = df_avg['price'].min()
            max_price = df_avg['price'].max()
            price_range = max_price - min_price
            margin = price_range * 0.1

            # Create chart
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

            # Display chart in a container for better styling
            with st.container():
                st.markdown('<div class="filter-container">', unsafe_allow_html=True)
                st.altair_chart(chart, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No hay datos disponibles para la selección actual.")
    else:
        st.warning("No hay datos disponibles para la selección actual.")
