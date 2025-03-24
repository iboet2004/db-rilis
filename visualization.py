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

def create_scorecard(title, value, delta=None, helptext=None):
    """Create a simple scorecard metric with optional help text"""
    st.metric(label=title, value=value, delta=delta, help=helptext)

def create_top_entities_chart(entity_counts, title, limit=10, color=None):
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
        height=400,
        color_discrete_sequence=[color] if color else None
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

def create_wordcloud(text_series, title="Wordcloud"):
    """Create wordcloud from text data"""
    if text_series.empty:
        st.warning(f"Tidak ada data untuk {title}")
        return
    
    # Prepare text
    text = prepare_text_for_wordcloud(text_series)
    
    if not text:
        st.warning(f"Tidak ada teks yang cukup untuk {title}")
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
    
    # Display wordcloud with title
    st.subheader(title)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout()
    
    st.pyplot(fig)

def create_location_map(locations):
    """Create map with markers for locations"""
    if not locations:
        st.warning("Tidak ada data lokasi")
        return
    
    # Placeholder map centered on Indonesia
    m = folium.Map(location=[-2.5489, 118.0149], zoom_start=5)
    
    # In a real application, you'd need to geocode these locations
    # For this example, we'll use random coordinates around Indonesia
    np.random.seed(42)
    for i, location in enumerate(locations):
        # Random coordinates around Indonesia
        lat = -6.0 + np.random.uniform(-3, 3)
        lon = 110.0 + np.random.uniform(-10, 10)
        
        folium.Marker(
            [lat, lon],
            popup=location,
            tooltip=location
        ).add_to(m)
    
    # Display map
    folium_static(m)

def create_side_by_side_wordclouds(text_series1, title1, text_series2, title2):
    """Create two wordclouds side by side"""
    if text_series1.empty and text_series2.empty:
        st.warning("Tidak ada data untuk wordcloud")
        return
    
    # Prepare text
    text1 = prepare_text_for_wordcloud(text_series1)
    text2 = prepare_text_for_wordcloud(text_series2)
    
    if not text1 and not text2:
        st.warning("Tidak ada teks yang cukup untuk wordcloud")
        return
    
    # Create layout with columns
    col1, col2 = st.columns(2)
    
    # First wordcloud
    if text1:
        wordcloud1 = WordCloud(
            width=600,
            height=300,
            background_color='white',
            max_words=100,
            contour_width=1,
            contour_color='steelblue'
        ).generate(text1)
        
        with col1:
            st.subheader(title1)
            fig1, ax1 = plt.subplots(figsize=(8, 4))
            ax1.imshow(wordcloud1, interpolation='bilinear')
            ax1.axis('off')
            plt.tight_layout()
            st.pyplot(fig1)
    else:
        with col1:
            st.warning(f"Tidak ada teks yang cukup untuk {title1}")
    
    # Second wordcloud
    if text2:
        wordcloud2 = WordCloud(
            width=600,
            height=300,
            background_color='white',
            max_words=100,
            contour_width=1,
            contour_color='steelblue'
        ).generate(text2)
        
        with col2:
            st.subheader(title2)
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            ax2.imshow(wordcloud2, interpolation='bilinear')
            ax2.axis('off')
            plt.tight_layout()
            st.pyplot(fig2)
    else:
        with col2:
            st.warning(f"Tidak ada teks yang cukup untuk {title2}")
