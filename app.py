import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

def count_media_per_sp(df_sp, df_berita, sp_title_col, berita_sp_ref_col):
    """
    Count number of media per press release
    """
    media_counts = {}
    
    for sp_title in df_sp[sp_title_col]:
        # Filter berita yang merujuk ke SP ini
        related_berita = df_berita[df_berita[berita_sp_ref_col] == sp_title]
        
        # Hitung jumlah media unik
        unique_media = related_berita[df_berita.columns[3]].nunique()
        media_counts[sp_title] = unique_media
    
    return media_counts

def create_sources_trend_analysis(df, entity_col, date_col, selected_sp=None):
    """
    Create scatter plot for sources mentioning trend with improved visualization
    """
    # Filter dataframe if a specific SP is selected
    if selected_sp is not None and selected_sp != "Semua Siaran Pers":
        df = df[df[df.columns[0]] == selected_sp]
    
    # Ensure dataframe is not empty
    if df.empty:
        st.warning("Tidak ada data untuk dianalisis")
        return
    
    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    # Prepare entity data
    all_entities_data = []
    
    for _, row in df.iterrows():
        date = row[date_col]
        # Split entities separated by semicolon
        entities = row[entity_col].split(';') if pd.notna(row[entity_col]) else []
        
        for entity in entities:
            entity = entity.strip()
            if entity:
                all_entities_data.append({
                    'Narasumber': entity,
                    'Tanggal': date
                })
    
    # Create DataFrame
    if not all_entities_data:
        st.warning("Tidak ada narasumber yang ditemukan")
        return
    
    entities_df = pd.DataFrame(all_entities_data)
    
    # Agregasi per minggu
    entities_df['Minggu'] = entities_df['Tanggal'].dt.to_period('W').apply(lambda r: r.start_time)
    weekly_counts = entities_df.groupby(['Narasumber', 'Minggu']).size().reset_index(name='Frekuensi')
    
    # Count total frequencies
    narasumber_counts = weekly_counts.groupby('Narasumber')['Frekuensi'].sum().sort_values(ascending=False)
    
    # Select top 10 sources for visualization
    top_sources = narasumber_counts.head(10)
    
    # Prepare data for top sources
    plot_data = weekly_counts[weekly_counts['Narasumber'].isin(top_sources.index)]
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Siaran Pers", len(df))
    with col2:
        st.metric("Total Narasumber", len(narasumber_counts))
    with col3:
        st.metric("Narasumber Tersering", top_sources.index[0])
    
    # Create scatter plot with Plotly
    fig = px.scatter(
        plot_data, 
        x='Minggu', 
        y='Narasumber',
        color='Narasumber',
        size='Frekuensi',
        size_min=5,
        size_max=20,
        title='Distribusi & Frekuensi Penyebutan Narasumber per Minggu',
        labels={'Narasumber': 'Narasumber', 'Minggu': 'Pekan'},
        height=400
    )
    
    # Customize layout
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="Pekan",
        yaxis_title="Narasumber",
        showlegend=False  # Menghilangkan legenda di samping
    )
    
    # Adjust marker properties
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='DarkSlateGrey'),
            opacity=0.7
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_media_sources_sankey(df_berita, sp_title_col, media_col):
    """
    Create Sankey diagram for sources in news
    """
    # Group by SP reference and media
    sankey_data = df_berita.groupby([sp_title_col, media_col]).size().reset_index(name='count')
    
    # Prepare data for Sankey diagram
    sources = sankey_data[sp_title_col].tolist()
    targets = sankey_data[media_col].tolist()
    values = sankey_data['count'].tolist()
    
    # Create color palette
    unique_sources = list(set(sources))
    unique_targets = list(set(targets))
    color_palette = px.colors.qualitative.Plotly
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = unique_sources + unique_targets,
          color = color_palette[:len(unique_sources)] + color_palette[:len(unique_targets)]
        ),
        link = dict(
          source = [unique_sources.index(s) for s in sources],
          target = [len(unique_sources) + unique_targets.index(t) for t in targets],
          value = values
      ))])

    fig.update_layout(title_text="Aliran Pemberitaan dari Siaran Pers ke Media", font_size=10)
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
        
        # 1. Total Siaran Pers
        st.metric("Total Siaran Pers", len(df_sp_filtered))
        
        # 2. Trend Penyebutan Narasumber
        st.subheader("Trend Penyebutan Narasumber")
        create_sources_trend_analysis(
            df_sp, 
            sp_sources_col, 
            sp_date_col, 
            selected_sp
        )
        
        # 3. Timeline Produksi Siaran Pers
        st.subheader("Timeline Produksi Siaran Pers")
        create_timeline_chart(
            df_sp_filtered, 
            sp_title_col, 
            sp_date_col, 
            "Publikasi Siaran Pers"
        )
    
    # Tab 2: Pemberitaan
    with tab2:
        # 1. Total Pemberitaan
        total_berita = len(df_berita)
        st.metric("Total Pemberitaan", total_berita)
        
        # 2. Top 10 Media
        st.subheader("Top 10 Media")
        media_counts = df_berita[berita_media_col].value_counts().head(10)
        create_top_entities_chart(media_counts, "Top 10 Media", 10)
        
        # 3. Rata-rata Media per Siaran Pers
        media_per_sp = count_media_per_sp(df_sp, df_berita, sp_title_col, berita_sp_ref_col)
        avg_media = np.mean(list(media_per_sp.values()))
        st.metric("Rata-rata Media per Siaran Pers", f"{avg_media:.2f}")
        
        # 4. Top 10 Siaran Pers dengan Pemberitaan Terbanyak
        st.subheader("Top 10 Siaran Pers dengan Pemberitaan Terbanyak")
        berita_per_sp = df_berita[berita_sp_ref_col].value_counts().head(10)
        create_top_entities_chart(berita_per_sp, "Top 10 Siaran Pers", 10)
        
        # 5. Wordcloud Konten Berita
        st.subheader("Wordcloud Konten Berita")
        create_wordcloud(df_berita[berita_content_col], "Wordcloud Pemberitaan")
        
        # 6. Sankey Diagram Narasumber di Berita
        st.subheader("Aliran Pemberitaan")
        create_media_sources_sankey(df_berita, berita_sp_ref_col, berita_media_col)
    
    # Tab 3: Analisis Mendalam
    with tab3:
        st.write("Analisis lanjutan akan ditambahkan")
    
    # Expanded Data Tables
    with st.expander("Detail Siaran Pers"):
        st.dataframe(df_sp)
    
    with st.expander("Detail Pemberitaan"):
        st.dataframe(df_berita)

if __name__ == "__main__":
    main()
