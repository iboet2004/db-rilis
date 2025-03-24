import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from data_loader import load_dataset, process_dataset, process_entities, get_unique_locations
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

def create_trend_analysis(df, entity_col, date_col, top_n=5, days=30):
    """
    Create trend analysis for top entities over time
    """
    if entity_col not in df.columns or date_col not in df.columns:
        st.warning("Data tidak tersedia untuk analisis tren")
        return
    
    # Convert date to datetime
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
    
    # Drop rows with invalid dates
    df_copy = df_copy.dropna(subset=[date_col])
    
    if df_copy.empty:
        st.warning("Tidak ada data tanggal yang valid untuk analisis tren")
        return
    
    # Process entities
    all_entities = []
    entity_dates = {}
    
    for _, row in df_copy.iterrows():
        date = row[date_col].date()
        entities = process_entities(row[entity_col])
        
        for entity in entities:
            all_entities.append(entity)
            if entity not in entity_dates:
                entity_dates[entity] = []
            entity_dates[entity].append(date)
    
    # Count total occurrences
    entity_counts = pd.Series(all_entities).value_counts()
    
    # Get top N entities
    top_entities = entity_counts.head(top_n).index.tolist()
    
    if not top_entities:
        st.warning("Tidak ada data entitas yang cukup untuk analisis tren")
        return
    
    # Determine date range
    all_dates = [date for dates in entity_dates.values() for date in dates]
    if not all_dates:
        return
    
    min_date = min(all_dates)
    max_date = max(all_dates)
    
    # Create date range from min to max date
    date_range = pd.date_range(min_date, max_date)
    
    # Create dataframe for trend analysis
    trend_data = []
    
    for entity in top_entities:
        if entity not in entity_dates:
            continue
            
        for date in date_range:
            date_key = date.date()
            count = entity_dates[entity].count(date_key)
            trend_data.append({
                'Entitas': entity,
                'Tanggal': date,
                'Jumlah': count
            })
    
    # Create dataframe
    trend_df = pd.DataFrame(trend_data)
    
    # Create line chart for trend analysis
    fig = px.line(
        trend_df,
        x='Tanggal',
        y='Jumlah',
        color='Entitas',
        title=f"Tren Penyebutan {top_n} Entitas Teratas",
        labels={'Jumlah': 'Jumlah Penyebutan', 'Tanggal': 'Tanggal'},
        height=400
    )
    
    # Add markers
    fig.update_traces(mode='lines+markers')
    
    # Customize chart
    fig.update_layout(
        xaxis_title="Tanggal",
        yaxis_title="Jumlah Penyebutan",
        legend_title="Entitas"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_effectiveness_chart(df_sp, sp_title_col, df_berita, berita_sp_ref_col, berita_date_col, top_n=10):
    """
    Create chart showing most effective press releases (most news coverage)
    """
    if df_sp.empty or df_berita.empty:
        st.warning("Data tidak tersedia untuk analisis efektivitas")
        return
    
    if sp_title_col not in df_sp.columns or berita_sp_ref_col not in df_berita.columns:
        st.warning("Kolom yang diperlukan tidak ditemukan")
        return
    
    # Get unique SP titles
    sp_titles = {}
    for idx, title in enumerate(df_sp[sp_title_col]):
        if not pd.isna(title):
            sp_titles[str(title).strip()] = idx
    
    # Count references in news
    sp_refs_count = {}
    
    for _, row in df_berita.iterrows():
        ref = row[berita_sp_ref_col]
        if pd.isna(ref):
            continue
            
        ref_str = str(ref).strip()
        if ref_str in sp_titles:
            if ref_str not in sp_refs_count:
                sp_refs_count[ref_str] = 0
            sp_refs_count[ref_str] += 1
    
    # Create dataframe for visualization
    effectiveness_data = []
    
    for title, count in sp_refs_count.items():
        effectiveness_data.append({
            'Judul Siaran Pers': title[:50] + '...' if len(title) > 50 else title,
            'Jumlah Pemberitaan': count
        })
    
    # Sort and get top N
    effectiveness_df = pd.DataFrame(effectiveness_data)
    effectiveness_df = effectiveness_df.sort_values('Jumlah Pemberitaan', ascending=False).head(top_n)
    
    if effectiveness_df.empty:
        st.warning("Tidak ada data yang cukup untuk analisis efektivitas")
        return
    
    # Create horizontal bar chart
    fig = px.bar(
        effectiveness_df,
        x='Jumlah Pemberitaan',
        y='Judul Siaran Pers',
        orientation='h',
        title=f"Top {top_n} Siaran Pers dengan Pemberitaan Terbanyak",
        labels={'Jumlah Pemberitaan': 'Jumlah Pemberitaan', 'Judul Siaran Pers': ''},
        height=400,
        color='Jumlah Pemberitaan',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Customize chart
    fig.update_layout(
        xaxis_title="Jumlah Pemberitaan",
        yaxis_title="",
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
def create_media_response_time(df_sp, sp_title_col, sp_date_col, df_berita, berita_sp_ref_col, berita_date_col):
    """
    Analyze media response time after press release
    """
    if df_sp.empty or df_berita.empty:
        st.warning("Data tidak tersedia untuk analisis waktu respon")
        return
    
    # Check required columns
    req_cols = [sp_title_col, sp_date_col, berita_sp_ref_col, berita_date_col]
    if not all(col in df_sp.columns if i < 2 else col in df_berita.columns for i, col in enumerate(req_cols)):
        st.warning("Kolom yang diperlukan tidak ditemukan")
        return
    
    # Convert date columns to datetime
    df_sp_copy = df_sp.copy()
    df_berita_copy = df_berita.copy()
    
    df_sp_copy[sp_date_col] = pd.to_datetime(df_sp_copy[sp_date_col], errors='coerce')
    df_berita_copy[berita_date_col] = pd.to_datetime(df_berita_copy[berita_date_col], errors='coerce')
    
    # Drop rows with invalid dates
    df_sp_copy = df_sp_copy.dropna(subset=[sp_date_col])
    df_berita_copy = df_berita_copy.dropna(subset=[berita_date_col])
    
    if df_sp_copy.empty or df_berita_copy.empty:
        st.warning("Tidak ada data tanggal yang valid untuk analisis waktu respon")
        return
    
    # Create dictionary of SP titles and their dates
    sp_dates = {}
    for _, row in df_sp_copy.iterrows():
        title = row[sp_title_col]
        date = row[sp_date_col]
        
        if not pd.isna(title) and not pd.isna(date):
            sp_dates[str(title).strip()] = date
    
    # Calculate response times
    response_times = []
    
    for _, row in df_berita_copy.iterrows():
        ref = row[berita_sp_ref_col]
        news_date = row[berita_date_col]
        
        if pd.isna(ref) or pd.isna(news_date):
            continue
            
        ref_str = str(ref).strip()
        if ref_str in sp_dates:
            sp_date = sp_dates[ref_str]
            
            # Calculate days difference
            days_diff = (news_date - sp_date).days
            
            # Only consider positive differences (news after SP)
            # and reasonable time frame (within 30 days)
            if 0 <= days_diff <= 30:
                response_times.append(days_diff)
    
    if not response_times:
        st.warning("Tidak cukup data untuk analisis waktu respon")
        return
    
    # Create histogram of response times
    fig = px.histogram(
        response_times,
        nbins=15,
        title="Waktu Respon Media Setelah Siaran Pers (dalam Hari)",
        labels={'value': 'Hari', 'count': 'Jumlah Pemberitaan'},
        height=300
    )
    
    # Calculate average response time
    avg_response = sum(response_times) / len(response_times)
    
    # Add a vertical line for average
    fig.add_vline(
        x=avg_response,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Rata-rata: {avg_response:.1f} hari",
        annotation_position="top right"
    )
    
    # Customize chart
    fig.update_layout(
        xaxis_title="Hari",
        yaxis_title="Jumlah Pemberitaan",
        bargap=0.1
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
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
        
        # Process sources column to get entities (separasi dengan ';' bukan ',')
        df_sp[sp_sources_col] = df_sp[sp_sources_col].astype(str).apply(lambda x: x.split(';') if pd.notna(x) else [])
        _, source_counts = process_dataset(df_sp, sp_sources_col)
    
    # Process data - DATASET BERITA
    if not df_berita.empty:
        berita_date_col = df_berita.columns[0]  # Kolom A sebagai tanggal
        berita_sp_ref_col = df_berita.columns[1]  # Kolom B
        berita_media_col = df_berita.columns[3]  # Kolom D
        berita_content_col = df_berita.columns[4]  # Kolom E
        
        # Convert date column to datetime (same treatment as Dataset SP)
        df_berita[berita_date_col] = pd.to_datetime(df_berita[berita_date_col], errors='coerce')
        df_berita = df_berita.dropna(subset=[berita_date_col])
        
        # Process media column to get entities
        _, media_counts = process_dataset(df_berita, berita_media_col)
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4 = st.tabs(["Siaran Pers", "Pemberitaan", "Analisis Gabungan", "Insight Mendalam"])
    
    # Tab 1: Siaran Pers
    with tab1:
        if df_sp.empty:
            st.warning("Data Siaran Pers tidak tersedia")
        else:
            st.subheader("Timeline Publikasi Siaran Pers")
            create_timeline_chart(df_sp, sp_title_col, sp_date_col, "Publikasi Siaran Pers per Tanggal")
            
            st.subheader("Tren Penyebutan Narasumber Teratas")
            create_trend_analysis(df_sp, sp_sources_col, sp_date_col, top_n=5)
    
    # Tab 2: Pemberitaan
    with tab2:
        if df_berita.empty:
            st.warning("Data Pemberitaan tidak tersedia")
        else:
            st.subheader("Timeline Pemberitaan")
            create_timeline_chart(df_berita, berita_content_col, berita_date_col, "Pemberitaan per Tanggal")
    
    # Tab 3: Analisis Gabungan
    with tab3:
        if df_sp.empty or df_berita.empty:
            st.warning("Data Siaran Pers atau Pemberitaan tidak tersedia")
        else:
            st.subheader("Efektivitas Siaran Pers")
            create_effectiveness_chart(df_sp, sp_title_col, df_berita, berita_sp_ref_col, berita_date_col)
    
    # Tab 4: Deep Insights
    with tab4:
        if df_sp.empty or df_berita.empty:
            st.warning("Data Siaran Pers atau Pemberitaan tidak tersedia")
        else:
            st.subheader("Analisis Waktu Respon Media")
            create_media_response_time(df_sp, sp_title_col, sp_date_col, df_berita, berita_sp_ref_col, berita_date_col)
    
    # Add data tables (hidden by default)
    with st.expander("Lihat Data Siaran Pers"):
        st.dataframe(df_sp)
    
    with st.expander("Lihat Data Berita"):
        st.dataframe(df_berita)

if __name__ == "__main__":
    main()

