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

def create_sp_selector(df_sp, sp_title_col):
    """
    Create a dropdown selector for press releases
    """
    # Add a "Semua Siaran Pers" option
    sp_titles = ["Semua Siaran Pers"] + list(df_sp[sp_title_col].dropna().unique())
    
    selected_sp = st.selectbox(
        "Pilih Siaran Pers", 
        sp_titles, 
        index=0, 
        key="sp_selector"
    )
    
    return selected_sp

def filter_dataframe(df, title_col, selected_title):
    """
    Filter dataframe based on selected title
    """
    if selected_title == "Semua Siaran Pers":
        return df
    else:
        return df[df[title_col] == selected_title]

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

def create_sources_trend_analysis(df, entity_col, date_col, selected_sp=None, top_n=5):
    """
    Create trend analysis for sources with improved visualization
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
    
    # Prepare data
    all_entities = []
    entity_date_counts = {}
    
    for _, row in df.iterrows():
        date = row[date_col]
        entities = process_entities(row[entity_col], separator=';')
        
        for entity in entities:
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
    
    # Jika tidak ada entitas sama sekali
    if not all_entities:
        st.warning("Tidak ada narasumber yang ditemukan")
        return
    
    # Count total occurrences
    entity_counts = pd.Series(all_entities).value_counts()
    
    # Get top N entities
    top_entities = entity_counts.head(top_n).index.tolist()
    
    # Jika tidak ada top entities
    if not top_entities:
        st.warning("Tidak ada narasumber yang cukup untuk dianalisis")
        return
    
    # Prepare trend data
    trend_data = []
    
    # Gunakan periode dari dataframe
    if agregasi == "Mingguan":
        date_range = pd.period_range(
            start=df[date_col].min().to_period('W').start_time, 
            end=df[date_col].max().to_period('W').start_time, 
            freq='W'
        )
    else:  # Bulanan
        date_range = pd.period_range(
            start=df[date_col].min().to_period('M').start_time, 
            end=df[date_col].max().to_period('M').start_time, 
            freq='M'
        )
    
    for entity in top_entities:
        for date in date_range:
            count = entity_date_counts.get(entity, {}).get(date.start_time, 0)
            trend_data.append({
                'Entitas': entity,
                'Periode': date.start_time,
                'Jumlah': count
            })
    
    # Create dataframe
    trend_df = pd.DataFrame(trend_data)
    
    # Pastikan ada data untuk divisualisasikan
    if trend_df.empty:
        st.warning("Tidak ada data trend untuk divisualisasikan")
        return
    
    # Tambahan analisis sumber siaran pers
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Jumlah Total Narasumber", len(set(all_entities)))
    
    with col2:
        # Hitung jumlah siaran pers per narasumber
        narasumber_sp_count = {}
        for _, row in df.iterrows():
            entities = process_entities(row[entity_col], separator=';')
            for entity in entities:
                if entity not in narasumber_sp_count:
                    narasumber_sp_count[entity] = 0
                narasumber_sp_count[entity] += 1
        
        top_narasumber = max(narasumber_sp_count, key=narasumber_sp_count.get)
        st.metric("Narasumber Tersering", f"{top_narasumber} ({narasumber_sp_count[top_narasumber]} kali)")
    
    # Create chart
    fig = px.line(
        trend_df,
        x='Periode',
        y='Jumlah',
        color='Entitas',
        title=f"Tren Penyebutan {top_n} Narasumber Teratas ({agregasi})",
        labels={'Jumlah': 'Jumlah Penyebutan', 'Periode': 'Periode'},
        height=400
    )
    
    # Pindahkan legenda ke bawah
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        xaxis_title="Periode",
        yaxis_title="Jumlah Penyebutan"
    )
    
    fig.update_traces(mode='lines+markers')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tambahan: Distribusi Narasumber
    st.subheader("Distribusi Narasumber")
    fig_pie = px.pie(
        values=list(entity_counts.head(top_n)),
        names=entity_counts.head(top_n).index,
        title="Proporsi Penyebutan Narasumber Top",
        height=400
    )
    st.plotly_chart(fig_pie, use_container_width=True)

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
        # Selector for press releases
        selected_sp = create_sp_selector(df_sp, sp_title_col)
        
        # Filter dataframe if a specific SP is selected
        df_sp_filtered = filter_dataframe(df_sp, sp_title_col, selected_sp)
        
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
