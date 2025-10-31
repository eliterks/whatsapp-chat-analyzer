"""
===========================================================
📊 sentiment_helper.py — WhatsApp Chat Sentiment Analyzer
===========================================================

Author: Saikat Munshib
Description:
    Adds sentiment analysis capabilities with detailed insights:
        - Sentiment distribution (bar & pie)
        - Most positive & negative messages
        - Sentiment polarity scores (-1 to +1)
===========================================================
"""

from textblob import TextBlob
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st


# ==============================
# 🧩 Helper Function
# ==============================
def _get_sentiment(message: str) -> str:
    """Classifies a message into Positive, Negative, or Neutral."""
    try:
        message = str(message).strip()
        if not message or message == "<Media omitted>":
            return "Neutral"

        polarity = TextBlob(message).sentiment.polarity
        if polarity > 0.1:
            return "Positive"
        elif polarity < -0.1:
            return "Negative"
        else:
            return "Neutral"
    except Exception:
        return "Neutral"


# ==============================
# 🔍 Core Analysis
# ==============================
def analyze_sentiment(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    """Returns DataFrame with Sender, Message, Polarity, Sentiment."""
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    df = df[df['Message'] != '<Media omitted>'].copy()
    if df.empty:
        st.warning("⚠️ No valid messages available for sentiment analysis.")
        return pd.DataFrame(columns=['Sender', 'Message', 'Polarity', 'Sentiment'])

    df['Polarity'] = df['Message'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
    df['Sentiment'] = df['Polarity'].apply(
        lambda p: 'Positive' if p > 0.1 else ('Negative' if p < -0.1 else 'Neutral')
    )
    return df[['Sender', 'Message', 'Polarity', 'Sentiment']]


# ==============================
# 📊 Sentiment Distribution
# ==============================
def sentiment_distribution(selected_user: str, df: pd.DataFrame) -> pd.Series:
    """Returns a Series showing sentiment distribution counts."""
    sentiment_df = analyze_sentiment(selected_user, df)
    if sentiment_df.empty:
        return pd.Series(dtype='int64')

    return sentiment_df['Sentiment'].value_counts()


def plot_sentiment_charts(selected_user: str, df: pd.DataFrame):
    """Displays both bar chart and pie chart for sentiment distribution."""
    sentiment_counts = sentiment_distribution(selected_user, df)

    if sentiment_counts.empty:
        st.warning("⚠️ No sentiment data available for visualization.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Sentiment Bar Chart")
        fig, ax = plt.subplots(figsize=(5, 4))
        sns.barplot(
            x=sentiment_counts.index,
            y=sentiment_counts.values,
            palette=["#2ecc71", "#f1c40f", "#e74c3c"],
            ax=ax
        )
        ax.set_xlabel("Sentiment Type")
        ax.set_ylabel("Number of Messages")
        st.pyplot(fig)

    with col2:
        st.subheader("🥧 Sentiment Pie Chart")
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(
            sentiment_counts.values,
            labels=sentiment_counts.index,
            autopct="%1.1f%%",
            colors=["#2ecc71", "#f1c40f", "#e74c3c"],
            startangle=90
        )
        ax.axis("equal")
        st.pyplot(fig)


# ==============================
# 💬 Top Positive / Negative Messages
# ==============================
def top_positive_messages(selected_user: str, df: pd.DataFrame, n=10):
    """Returns top 'n' most positive messages with sender and polarity score."""
    sentiment_df = analyze_sentiment(selected_user, df)
    if sentiment_df.empty:
        return pd.DataFrame(columns=['Sender', 'Message', 'Polarity', 'Sentiment'])

    top_pos = sentiment_df.sort_values(by='Polarity', ascending=False).head(n)
    top_pos['Polarity'] = top_pos['Polarity'].round(3)
    return top_pos[['Sender', 'Message', 'Polarity', 'Sentiment']]


def top_negative_messages(selected_user: str, df: pd.DataFrame, n=10):
    """Returns top 'n' most negative messages with sender and polarity score."""
    sentiment_df = analyze_sentiment(selected_user, df)
    if sentiment_df.empty:
        return pd.DataFrame(columns=['Sender', 'Message', 'Polarity', 'Sentiment'])

    top_neg = sentiment_df.sort_values(by='Polarity', ascending=True).head(n)
    top_neg['Polarity'] = top_neg['Polarity'].round(3)
    return top_neg[['Sender', 'Message', 'Polarity', 'Sentiment']]


# ==============================
# 🧠 Summary for Streamlit Integration
# ==============================
def sentiment_summary(selected_user: str, df: pd.DataFrame):
    """Displays sentiment distribution and top messages with scores."""
    st.title("💡 Sentiment Analysis Summary")
    st.caption("Understand the emotional tone and sentiment strength of each message.")

    # Charts
    plot_sentiment_charts(selected_user, df)

    # Top Messages
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("😊 Most Positive Messages")
        pos_df = top_positive_messages(selected_user, df)
        if pos_df.empty:
            st.info("No positive messages found.")
        else:
            st.dataframe(pos_df, use_container_width=True)

    with col2:
        st.subheader("😞 Most Negative Messages")
        neg_df = top_negative_messages(selected_user, df)
        if neg_df.empty:
            st.info("No negative messages found.")
        else:
            st.dataframe(neg_df, use_container_width=True)


# ==============================
# 🔄 For app.py integration
# ==============================
def analyze_sentiments(selected_user, df):
    """
    Extracts sentiment summary stats + detailed dataframe.
    Returns (summary_dict, sentiment_df)
    """
    sentiment_df = analyze_sentiment(selected_user, df)
    if sentiment_df.empty:
        return None, pd.DataFrame()

    sentiment_counts = sentiment_df['Sentiment'].value_counts().to_dict()

    summary = {
        'positive': sentiment_counts.get('Positive', 0),
        'neutral': sentiment_counts.get('Neutral', 0),
        'negative': sentiment_counts.get('Negative', 0),
        'avg_sentiment': sentiment_df['Polarity'].mean().round(3)
    }

    return summary, sentiment_df
