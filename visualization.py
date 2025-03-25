import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def create_scorecard(value, label):
    """
    Create a simple scorecard metric
    """
    st.metric(label, value)

def create_top_entities_chart(data, title, top_n=10):
    """
    Create bar chart for top entities
    """
    fig = px.bar(
        x=data.index, 
        y=data.values, 
        title=title,
        labels={'x': 'Entitas', 'y': 'Jumlah'}
    )
    st.plotly_chart(fig, use_container_width=True)

def create_timeline_chart(df, title_col, date_col, chart_title):
    """
    Create timeline chart for dates
    """
    # Convert date column to datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Group by date and count
    timeline_data = df.groupby(df[date_col].dt.date).size().reset_index()
    timeline_data.columns = [date_col, 'Jumlah']
    
    fig = px.line(
        timeline_data, 
        x=date_col, 
        y='Jumlah', 
        title=chart_title
    )
    st.plotly_chart(fig, use_container_width=True)

def create_wordcloud(text_series, title):
    """
    Create word cloud from text series
    """
    # Combine all text
    text = ' '.join(text_series.dropna().astype(str))
    
    # Generate word cloud
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white'
    ).generate(text)
    
    # Display word cloud
    plt.figure(figsize=(10,5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title)
    st.pyplot(plt)

def create_side_by_side_wordclouds(series1, series2, title1, title2):
    """
    Create two word clouds side by side
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16,8))
    
    # Word cloud 1
    text1 = ' '.join(series1.dropna().astype(str))
    wordcloud1 = WordCloud(width=400, height=200, background_color='white').generate(text1)
    ax1.imshow(wordcloud1, interpolation='bilinear')
    ax1.set_title(title1)
    ax1.axis('off')
    
    # Word cloud 2
    text2 = ' '.join(series2.dropna().astype(str))
    wordcloud2 = WordCloud(width=400, height=200, background_color='white').generate(text2)
    ax2.imshow(wordcloud2, interpolation='bilinear')
    ax2.set_title(title2)
    ax2.axis('off')
    
    plt.tight_layout()
    st.pyplot(fig)
