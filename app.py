import streamlit as st
import pandas as pd
from data_loader import load_dataset, process_dataset, get_unique_locations
from visualization import (
    create_scorecard, 
    create_top_entities_chart, 
    create_timeline_chart,
    create_wordcloud,
    create_location_map
)

# Set page config
st.set_page_config(
    page_title="Dashboard Siaran Pers",
    page_icon="📊",
    layout="wide"
)

def main():
    # Title
    st.title("Dashboard Analisis Siaran Pers")
    
    # Load data
    with st.spinner("Memuat data..."):
        df_sp = load_dataset("DATASET SP")
        df_berita = load_dataset("DATASET BERITA")
    
    if df_sp.empty:
        st.error("Gagal memuat data Siaran Pers")
        return
    
    # Process data
    sp_title_col = df_sp.columns[0]  # Kolom A
    sp_content_col = df_sp.columns[1]  # Kolom B
    sp_sources_col = df_sp.columns[3]  # Kolom D
    sp_date_col = df_sp.columns[4]  # Kolom E
    sp_location_col = df_sp.columns[8]  # Kolom I
    
    # Process sources column to get entities
    _, source_counts = process_dataset(df_sp, sp_sources_col)
    
    # Get unique locations
    locations = get_unique_locations(df_sp, sp_location_col)
    
    # Create layout with columns
    col1, col2 = st.columns(2)
    
    # 1. Scorecard - Jumlah Siaran Pers
    with col1:
        create_scorecard("Jumlah Siaran Pers", len(df_sp))
    
    # 2. Bar Chart - Top 10 Narasumber
    with col2:
        create_top_entities_chart(source_counts, "Top 10 Narasumber", 10)
    
    # 3. Wordcloud dari Konten
    st.subheader("Wordcloud Konten Siaran Pers")
    create_wordcloud(df_sp[sp_content_col])
    
    # 4. Timeline Series
    st.subheader("Timeline Publikasi Siaran Pers")
    create_timeline_chart(df_sp, sp_title_col, sp_date_col, "Publikasi Siaran Pers per Tanggal")
    
    # 5. Location Map
    st.subheader("Peta Lokasi Siaran Pers")
    create_location_map(locations)
    
    # Add data tables (hidden by default)
    with st.expander("Lihat Data Siaran Pers"):
        st.dataframe(df_sp)
    
    with st.expander("Lihat Data Berita"):
        st.dataframe(df_berita)

if __name__ == "__main__":
    main()
