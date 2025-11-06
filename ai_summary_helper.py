# ==========================================
# ai_summary_helper.py
# ==========================================
import streamlit as st
import pandas as pd
import re
from collections import Counter
from wordcloud import WordCloud
from textblob import TextBlob
from io import BytesIO
import matplotlib.pyplot as plt

# Try importing transformers (T5 summarizer)
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model="t5-small")
except Exception:
    summarizer = None


# ------------------------------------------
# Utility: Clean and preprocess chat text
# ------------------------------------------
def clean_text(text):
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ------------------------------------------
# Fallback Extractive Summarizer (Sumy LexRank)
# ------------------------------------------
def fallback_summarize(text, sentence_count=5):
    try:
        from sumy.summarizers.lex_rank import LexRankSummarizer
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary_sentences = summarizer(parser.document, sentence_count)
        return " ".join(str(s) for s in summary_sentences)
    except Exception as e:
        return f"⚠️ Unable to summarize text (Sumy fallback failed): {e}"


# ------------------------------------------
# Main AI Summary Generator
# ------------------------------------------
def generate_chat_summary(selected_user, df):
    if df is None or df.empty:
        st.warning("⚠️ No chat data found.")
        return

    # Filter user if not Overall
    if selected_user != "Overall":
        df = df[df['Sender'] == selected_user]

    messages = df['Message'].dropna().tolist()
    if not messages:
        st.warning("⚠️ No valid text messages found for summarization.")
        return

    full_text = " ".join(clean_text(msg) for msg in messages if isinstance(msg, str))

    # Limit input length
    if len(full_text.split()) > 3000:
        full_text = " ".join(full_text.split()[:3000])

    # Try AI summarization first
    st.info("🤖 Generating AI-based summary... please wait.")
    ai_summary = None
    if summarizer:
        try:
            ai_summary = summarizer(full_text[:1000], max_length=150, min_length=40, do_sample=False)[0]['summary_text']
        except Exception:
            ai_summary = None

    # Fallback to Sumy LexRank
    if not ai_summary:
        st.warning("⚙️ AI model unavailable — using extractive summarization.")
        ai_summary = fallback_summarize(full_text, sentence_count=5)

    # Display summary
    st.subheader("🧠 AI Chat Summary")
    st.success(ai_summary)

    # --------------------------------------
    # Sentiment & Topics Analysis
    # --------------------------------------
    sentiments = [TextBlob(msg).sentiment.polarity for msg in messages if isinstance(msg, str)]
    if sentiments:
        avg_sentiment = sum(sentiments) / len(sentiments)
        mood = "😊 Positive" if avg_sentiment > 0.1 else "😐 Neutral" if avg_sentiment >= -0.1 else "😡 Negative"
        st.markdown(f"### 💬 Overall Mood: {mood} (avg polarity: `{avg_sentiment:.3f}`)")
    else:
        avg_sentiment, mood = 0, "😐 Neutral"
        st.info("No sentiment data available.")

    # Top words
    all_words = clean_text(" ".join(messages)).split()
    common_words = [word.lower() for word in all_words if len(word) > 3]
    freq = Counter(common_words)
    top_10 = freq.most_common(10)

    st.markdown("### 🔑 Top Discussion Topics")
    for word, count in top_10:
        st.markdown(f"- **{word}** — {count} mentions")

    # WordCloud
    try:
        wc = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(freq)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)
    except Exception:
        st.info("WordCloud generation skipped.")

    # --------------------------------------
    # User Activity Breakdown
    # --------------------------------------
    st.markdown("### 👥 User Contribution Summary")
    if 'Sender' in df.columns:
        user_stats = df['Sender'].value_counts(normalize=True).reset_index()
        user_stats.columns = ['User', 'Contribution']
        user_stats['Contribution'] = (user_stats['Contribution'] * 100).round(2)
        st.dataframe(user_stats)
    else:
        st.info("No sender data available.")

    # --------------------------------------
    # ✅ Export AI Summary Results
    # --------------------------------------
    try:
        import export_ai_summary_helper
        export_ai_summary_helper.show_download_buttons(
            ai_summary,
            avg_sentiment,
            mood,
            top_10
        )
    except Exception as e:
        st.error(f"Error generating download files: {e}")


# ------------------------------------------
# Streamlit Display Wrapper
# ------------------------------------------
def display_chat_summary(selected_user, df):
    st.title("🧠 AI Chat Summarizer")
    st.caption("Automatically understand your chat's purpose, emotion, and key discussion points.")
    generate_chat_summary(selected_user, df)
