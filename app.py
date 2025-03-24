import streamlit as st
import pandas as pd
from data_loader import load_dataset, process_dataset, process_entities, get_unique_locations
from visualization import (
    create_scorecard, 
    create_top_entities_chart, 
    create_timeline_chart,
    create_wordcloud,
    create_location_map,
    create_side_by_side_wordclouds
)

# Set page config
st.set_page_config(
    page_title="Dashboard Siaran Pers & Pemberitaan",
    page_icon="📊",
    layout="wide"
)

def get_common_entries(df1, col1, df2, col2):
    """
    Get common entries between two dataframes' columns
    """
    # Get unique values from both columns
    values1 = set()
    for val in df1[col1]:
        if not pd.isna(val):
            values1.add(str(val).strip())
    
    values2 = set()
    for val in df2[col2]:
        if not pd.isna(val):
            values2.add(str(val).strip())
    
    # Find intersection
    common = values1.intersection(values2)
    return len(common)

def main():
    # Title
    st.title("Dashboard Analisis Siaran Pers & Pemberitaan")
    
    # Load data
    with st.spinner("Memuat data..."):
        df_sp = load_dataset("DATASET SP")
        df_berita = load_dataset("DATASET BERITA")
    
    if df_sp.empty and df_berita.empty:
        st.error("Gagal memuat data")
        return
    
    # Process data - DATASET SP
    if not df_sp.empty:
        sp_title_col = df_sp.columns[0]  # Kolom A
        sp_content_col = df_sp.columns[1]  # Kolom B
        sp_sources_col = df_sp.columns[3]  # Kolom D
        sp_date_col = df_sp.columns[4]  # Kolom E
        sp_location_col = df_sp.columns[8]  # Kolom I
        
        # Process sources column to get entities
        _, source_counts = process_dataset(df_sp, sp_sources_col)
        
        # Get unique locations
        locations = get_unique_locations(df_sp, sp_location_col)
    
    # Process data - DATASET BERITA
    if not df_berita.empty:
        berita_sp_ref_col = df_berita.columns[1]  # Kolom B
        berita_media_col = df_berita.columns[3]  # Kolom D
        berita_content_col = df_berita.columns[4]  # Kolom E
        
        # Process media column to get entities
        _, media_counts = process_dataset(df_berita, berita_media_col)
    
    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["Siaran Pers", "Pemberitaan", "Analisis Gabungan"])
    
    # Tab 1: Siaran Pers
    with tab1:
        if df_sp.empty:
            st.warning("Data Siaran Pers tidak tersedia")
        else:
            # Create layout with columns
            col1, col2 = st.columns(2)
            
            # 1. Scorecard - Jumlah Siaran Pers
            with col1:
                create_scorecard("Jumlah Siaran Pers", len(df_sp))
            
            # 2. Bar Chart - Top 10 Narasumber
            with col2:
                create_top_entities_chart(source_counts, "Top 10 Narasumber", 10)
            
            # 3. Wordcloud dari Konten
            create_wordcloud(df_sp[sp_content_col], "Wordcloud Konten Siaran Pers")
            
            # 4. Timeline Series
            st.subheader("Timeline Publikasi Siaran Pers")
            create_timeline_chart(df_sp, sp_title_col, sp_date_col, "Publikasi Siaran Pers per Tanggal")
            
            # 5. Location Map
            st.subheader("Peta Lokasi Siaran Pers")
            create_location_map(locations)
    
    # Tab 2: Pemberitaan
    with tab2:
        if df_berita.empty:
            st.warning("Data Pemberitaan tidak tersedia")
        else:
            # Count unique SP references
            unique_sp_refs = 0
            if not df_sp.empty:
                unique_sp_refs = get_common_entries(df_berita, berita_sp_ref_col, df_sp, sp_title_col)
            
            # Create layout with columns
            col1, col2 = st.columns(2)
            
            # 1. Scorecard - Jumlah Pemberitaan
            with col1:
                create_scorecard(
                    "Jumlah Pemberitaan", 
                    len(df_berita), 
                    helptext=f"Termasuk {unique_sp_refs} pemberitaan yang mengacu pada Siaran Pers"
                )
                st.caption(f"Mengacu pada {unique_sp_refs} Siaran Pers")
            
            # 2. Bar Chart - Top 10 Media
            with col2:
                create_top_entities_chart(
                    media_counts, 
                    "Top 10 Media", 
                    10, 
                    color="#1E88E5"  # Blue color to differentiate from SP chart
                )
            
            # 3. Wordcloud dari Konten Berita
            create_wordcloud(df_berita[berita_content_col], "Wordcloud Konten Pemberitaan")
    
    # Tab 3: Analisis Gabungan
    with tab3:
        if df_sp.empty or df_berita.empty:
            st.warning("Data Siaran Pers atau Pemberitaan tidak tersedia")
        else:
            st.subheader("Perbandingan Wordcloud Siaran Pers vs Pemberitaan")
            create_side_by_side_wordclouds(
                df_sp[sp_content_col], 
                "Siaran Pers", 
                df_berita[berita_content_col], 
                "Pemberitaan"
            )
            
            # Comparison metrics
            st.subheader("Perbandingan Metrik")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                create_scorecard("Jumlah Siaran Pers", len(df_sp))
            
            with col2:
                create_scorecard("Jumlah Pemberitaan", len(df_berita))
            
            with col3:
                # Calculate ratio
                if len(df_sp) > 0:
                    ratio = round(len(df_berita) / len(df_sp), 2)
                    create_scorecard("Rasio Pemberitaan/Siaran Pers", ratio)
                else:
                    create_scorecard("Rasio Pemberitaan/Siaran Pers", "N/A")
    
    # Add data tables (hidden by default)
    with st.expander("Lihat Data Siaran Pers"):
        st.dataframe(df_sp)
    
    with st.expander("Lihat Data Berita"):
        st.dataframe(df_berita)

if __name__ == "__main__":
    main()
