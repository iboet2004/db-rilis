import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import numpy as np
from data_loader import load_dataset, process_entities, get_unique_locations
from visualization import (
    create_scorecard, 
    create_top_entities_chart, 
    create_timeline_chart,
    create_wordcloud,
    create_side_by_side_wordclouds
)

# Set page config
st.set_page_config(
    page_title="Dashboard Siaran Pers & Pemberitaan",
    page_icon="📊",
    layout="wide"
)

def create_sp_selector(df_sp, sp_title_col, sp_date_col):
    """
    Create a dropdown selector for press releases with date range filter
    """
    # Add a "Semua Siaran Pers" option
    sp_titles = ["Semua Siaran Pers"] + list(df_sp[sp_title_col].dropna().unique())
    
    # Convert date column to datetime
    df_sp[sp_date_col] = pd.to_datetime(df_sp[sp_date_col], errors='coerce')
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Tanggal Mulai", 
            min_value=df_sp[sp_date_col].min().date(), 
            max_value=df_sp[sp_date_col].max().date(), 
            value=df_sp[sp_date_col].min().date()
        )
    
    with col2:
        end_date = st.date_input(
            "Tanggal Akhir", 
            min_value=df_sp[sp_date_col].min().date(), 
            max_value=df_sp[sp_date_col].max().date(), 
            value=df_sp[sp_date_col].max().date()
        )
    
    selected_sp = st.selectbox(
        "Pilih Siaran Pers", 
        sp_titles, 
        index=0, 
        key="sp_selector"
    )
    
    return selected_sp, start_date, end_date

def filter_dataframe(df, title_col, date_col, selected_title, start_date, end_date):
    """
    Filter dataframe based on selected title and date range
    """
    # Convert columns to datetime if not already
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Filter by date range
    df_filtered = df[
        (df[date_col].dt.date >= start_date) & 
        (df[date_col].dt.date <= end_date)
    ]
    
    # Filter by title
    if selected_title == "Semua Siaran Pers":
        return df_filtered
    else:
        return df_filtered[df_filtered[title_col] == selected_title]

def create_sources_trend_analysis(df, entity_col, date_col, selected_sp=None, top_n=5):
    """
    Create trend analysis for sources with multiple entities per press release
    """
    # Filter dataframe if a specific SP is selected
    if selected_sp is not None and selected_sp != "Semua Siaran Pers":
        df = df[df[df.columns[0]] == selected_sp]
    
    # Pastikan dataframe tidak kosong
    if df.empty:
        st.warning("Tidak ada data untuk dianalisis")
        return
    
    # Konversi kolom tanggal
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    # Pilihan agregasi
    agregasi = st.radio(
        "Agregasi Trend Narasumber", 
        ["Mingguan", "Bulanan"], 
        horizontal=True
    )
    
    # Prepare data with multiple entities
    all_entities = []
    entity_date_counts = {}
    
    for _, row in df.iterrows():
        date = row[date_col]
        # Split entities with semicolon instead of comma
        entities = row[entity_col].split(';') if pd.notna(row[entity_col]) else []
        
        for entity in entities:
            entity = entity.strip()  # Remove whitespace
            if entity:  # Ensure non-empty entity
                all_entities.append(entity)
                if entity not in entity_date_counts:
                    entity_date_counts[entity] = {}
                
                # Tentukan periode agregasi
                if agregasi == "Mingguan":
                    period_key = date.to_period('W').start_time
                else:  # Bulanan
                    period_key = date.to_period('M').start_time
                
                # Hitung jumlah untuk setiap periode
                if period_key not in entity_date_counts[entity]:
                    entity_date_counts[entity][period_key] = 0
                entity_date_counts[entity][period_key] += 1
    
    # Sort entities by total occurrences
    sorted_entities = sorted(entity_date_counts.keys(), key=lambda x: sum(entity_date_counts[x].values()), reverse=True)
    
    # Create dataframe for trend analysis
    trend_df = pd.DataFrame(columns=["Entitas", "Periode", "Jumlah"])
    
    for entity in sorted_entities[:top_n]:
        entity_data = pd.DataFrame({
            "Entitas": [entity] * len(entity_date_counts[entity]),
            "Periode": list(entity_date_counts[entity].keys()),
            "Jumlah": list(entity_date_counts[entity].values())
        })
        trend_df = pd.concat([trend_df, entity_data], ignore_index=True)
    
    # Create chart - Kembalikan legenda ke sisi chart
    fig = px.line(
        trend_df,
        x='Periode',
        y='Jumlah',
        color='Entitas',
        title=f"Tren Penyebutan {top_n} Narasumber Teratas ({agregasi})",
        labels={'Jumlah': 'Jumlah Penyebutan', 'Periode': 'Periode'},
        height=400
    )
    
    # Kembalikan legenda ke sisi chart
    fig.update_layout(
        legend=dict(
            orientation="v",  # Vertical orientation
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        xaxis_title="Periode",
        yaxis_title="Jumlah Penyebutan"
    )
    
    fig.update_traces(mode='lines+markers')
    
    st.plotly_chart(fig, use_container_width=True)

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
    
    # Column definitions
    sp_title_col = df_sp.columns[0]  # Kolom A
    sp_content_col = df_sp.columns[1]  # Kolom B
    sp_sources_col = df_sp.columns[3]  # Kolom D
    sp_date_col = df_sp.columns[4]  # Kolom E
    
    berita_sp_ref_col = df_berita.columns[1]  # Kolom B
    berita_media_col = df_berita.columns[3]  # Kolom D
    berita_content_col = df_berita.columns[4]  # Kolom E
    berita_date_col = df_berita.columns[0]  # Kolom A

    entity_col = berita_media_col  # Narasumber
    date_col = berita_date_col
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Siaran Pers", "Pemberitaan", "Analisis Mendalam"])
    
    # Tab 1: Siaran Pers
    with tab1:
        # Selector for press releases with date range
        selected_sp, start_date, end_date = create_sp_selector(df_sp, sp_title_col, sp_date_col)
        
        # Filter dataframe with date range
        df_sp_filtered = filter_dataframe(
            df_sp, 
            sp_title_col, 
            sp_date_col, 
            selected_sp, 
            start_date, 
            end_date
        )
        
        # Total Siaran Pers
        st.metric("Total Siaran Pers", len(df_sp_filtered))
        
        # Trend Penyebutan Narasumber
        st.subheader("Trend Penyebutan Narasumber")
        create_sources_trend_analysis(df_berita, entity_col, date_col, selected_sp)
        
        # Timeline Produksi Siaran Pers
        st.subheader("Timeline Produksi Siaran Pers")
        create_timeline_chart(df_sp_filtered, sp_title_col, sp_date_col, "Publikasi Siaran Pers")
    
    # Tab 2: Pemberitaan
    with tab2:
        # Total Pemberitaan
        total_berita = len(df_berita)
        st.metric("Total Pemberitaan", total_berita)
        
        # Top 10 Media
        st.subheader("Top 10 Media")
        media_counts = df_berita[df_berita.columns[3]].value_counts().head(10)
        create_top_entities_chart(media_counts, "Top 10 Media", 10)
        
        # Rata-rata Media per Siaran Pers
        media_per_sp = df_berita[df_berita.columns[0]].value_counts().to_dict()
        avg_media = np.mean(list(media_per_sp.values()))
        st.metric("Rata-rata Media per Siaran Pers", f"{avg_media:.2f}")
        
        # Top 10 Siaran Pers dengan Pemberitaan Terbanyak
        st.subheader("Top 10 Siaran Pers dengan Pemberitaan Terbanyak")
        berita_per_sp = df_berita[df_berita.columns[0]].value_counts().head(10)
        create_top_entities_chart(berita_per_sp, "Top 10 Siaran Pers", 10)
    
    # Tab 3: Analisis Mendalam
    with tab3:
        # Wordcloud
        st.subheader("Wordcloud")
        create_wordcloud(df_berita, entity_col)
        
        # Side-by-side wordclouds
        st.subheader("Wordclouds Sebilan")
        create_side_by_side_wordclouds(df_berita, entity_col, 9)

# Run the main function
if __name__ == "__main__":
    main()
