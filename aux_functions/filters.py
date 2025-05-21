import streamlit as st
import pandas as pd

def apply_filter_style():
    """Apply custom styling to filters"""
    st.markdown("""
        <style>
        .filter-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .filter-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #262730;
        }
        .stSelectbox {
            background-color: white;
        }
        </style>
    """, unsafe_allow_html=True)

def create_make_model_filters(df: pd.DataFrame) -> tuple:
    """Create make and model filters in a vertical layout"""
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">Selección de Vehículo</div>', unsafe_allow_html=True)
        
        # Make filter
        make_options = [""] + df['make'].drop_duplicates().sort_values().tolist()
        selected_make = st.selectbox("Marca:", options=make_options, index=0)
        
        # Model filter (only if make is selected)
        if selected_make and selected_make != "":
            selected_make_id = int(df[df['make'] == selected_make]['make_id'].iloc[0])
            model_options = [""] + df[df['make_id'] == selected_make_id]['model'].drop_duplicates().sort_values().tolist()
            selected_model = st.selectbox("Modelo:", options=model_options, index=0)
        else:
            selected_model = ""
            selected_make_id = None
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        return selected_make, selected_make_id, selected_model

def create_attribute_filters(df: pd.DataFrame) -> dict:
    """Create all other filters in a horizontal layout"""
    if df.empty:
        return {}
    
    # Create three columns for the filters
    col1, col2, col3 = st.columns(3)
    
    filters = {}
    
    with col1:
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">Características Técnicas</div>', unsafe_allow_html=True)
        
        # HP filter
        hp_df = df[['hp_class_id', 'hp_range']].drop_duplicates().sort_values('hp_class_id')
        hp_options = [""] + hp_df['hp_range'].tolist()
        filters['hp_range'] = st.selectbox("Potencia (CV):", options=hp_options, index=0)
        
        # Transmission filter
        tt_df = df[['transmission_type']].drop_duplicates().sort_values('transmission_type')
        tt_options = [""] + tt_df['transmission_type'].tolist()
        filters['transmission_type'] = st.selectbox("Transmisión:", options=tt_options, index=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">Estado del Vehículo</div>', unsafe_allow_html=True)
        
        # KM filter
        km_df = df[['km_class_id', 'km_range']].drop_duplicates().sort_values('km_class_id')
        km_options = [""] + km_df['km_range'].tolist()
        filters['km_range'] = st.selectbox("Kilometraje:", options=km_options, index=0)
        
        # Year filter
        year_df = df[['year']].drop_duplicates().sort_values('year', ascending=False)
        year_options = [""] + year_df['year'].tolist()
        filters['year'] = st.selectbox("Año:", options=year_options, index=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">Características Adicionales</div>', unsafe_allow_html=True)
        
        # Fuel filter
        ft_df = df[['fuel_type']].drop_duplicates().sort_values('fuel_type')
        ft_options = [""] + ft_df['fuel_type'].tolist()
        filters['fuel_type'] = st.selectbox("Combustible:", options=ft_options, index=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return filters
