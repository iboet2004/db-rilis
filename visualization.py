import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from datetime import datetime
import numpy as np
from utils import prepare_text_for_wordcloud

def create_scorecard(title, value, delta=None):
    """Create a simple scorecard metric"""
    st.metric(label=title, value=value, delta=delta)

def create_top_entities_chart(entity_counts, title, limit=5):
    """Create bar chart for top entities"""
    if entity_counts.empty:
        st.warning(f"Tidak ada data untuk {title}")
        return
    
    # Get top entities
    top_entities = entity_counts.head(limit)
    
    # Create plotly bar chart
    fig = px.bar(
        x=top_entities.values,
        y=top_entities.index,
        orientation='h',
        title=title,
        labels={'x': 'Jumlah', 'y': ''},
        height=400
    )
    
    # Customize chart
    fig.update_layout(
        xaxis_title="Jumlah",
        yaxis_title="",
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_timeline_chart(df, title_col, date_col, chart_title):
    """Create timeline series chart"""
    if df.empty or title_col not in df.columns or date_col not in df.columns:
        st.warning(f"Tidak ada data untuk timeline chart")
        return
    
    # Copy dataframe to avoid warnings
    timeline_df = df.copy()
    
    # Convert date column to datetime
    timeline_df[date_col] = pd.to_datetime(timeline_df[date_col], errors='coerce')
    
    # Drop rows with invalid dates
    timeline_df = timeline_df.dropna(subset=[date_col])
    
    if timeline_df.empty:
        st.warning("Tidak ada data tanggal yang valid")
        return
    
    # Group by date and count titles
    date_counts = timeline_df.groupby(timeline_df[date_col].dt.date).size().reset_index()
    date_counts.columns = ['Date', 'Count']
    
    # Create plotly line chart
    fig = px.line(
        date_counts,
        x='Date',
        y='Count',
        title=chart_title,
        labels={'Count': 'Jumlah Publikasi', 'Date': 'Tanggal'},
        height=400
    )
    
    # Add markers
    fig.update_traces(mode='lines+markers')
    
    # Customize chart
    fig.update_layout(
        xaxis_title="Tanggal",
        yaxis_title="Jumlah Publikasi"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_wordcloud(text_series):
    """Create wordcloud from text data"""
    if text_series.empty:
        st.warning("Tidak ada data untuk wordcloud")
        return
    
    # Prepare text
    text = prepare_text_for_wordcloud(text_series)
    
    if not text:
        st.warning("Tidak ada teks yang cukup untuk wordcloud")
        return
    
    # Create wordcloud
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        max_words=100,
        contour_width=1,
        contour_color='steelblue'
    ).generate(text)
    
    # Display wordcloud
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout()
    
    st.pyplot(fig)
