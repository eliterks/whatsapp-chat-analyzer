import streamlit as st
import preprocessor, helper, sentiment_helper
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# =========================================
# 🌟 PAGE CONFIG
# =========================================
st.set_page_config(page_title="📱 WhatsApp Chat Analyzer", page_icon="💬", layout="wide")

# =========================================
# 🎨 SIDEBAR SETUP
st.sidebar.title("📱 WhatsApp Chat Analyser")

if st.sidebar.button("🧹 Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.sidebar.success("✅ Cache and session cleared! Please reload or upload a new file.")


# =========================================
# 📂 FILE UPLOAD
# =========================================
uploaded_file = st.sidebar.file_uploader("📁 Choose a WhatsApp chat file (.txt)")

# === Initialize session state ===
if "analysis_generated" not in st.session_state:
    st.session_state.analysis_generated = False
if "show_sentiment" not in st.session_state:
    st.session_state.show_sentiment = False

# =========================================
# 📂 IF FILE IS UPLOADED
# =========================================
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    st.sidebar.success("✅ File uploaded successfully!")

    # --- Robust decoding ---
    try:
        data = bytes_data.decode("utf-8")
    except UnicodeDecodeError:
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                data = bytes_data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            data = bytes_data.decode("utf-8", errors="replace")

    # --- Preprocess Data ---
    df = preprocessor.preprocess(data)
    st.session_state.df = df

    # --- Parsed Summary ---
    st.subheader("📊 Parsed Chat Summary")
    st.write(f"📋 **Total messages parsed:** {len(df)}")
    st.write(f"📅 **Date range:** {df['Date'].min().date()} → {df['Date'].max().date()}")
    st.dataframe(df.head(), use_container_width=True)

    # === User Selection ===
    user_list = df['Sender'].unique().tolist()
    user_list.sort()
    if "Meta AI" in user_list:
        user_list.remove("Meta AI")
    user_list.insert(0, "Overall")
    selected_user = st.sidebar.selectbox("👤 Show analysis for", user_list)

    # === Sidebar Buttons ===
    if st.sidebar.button("🚀 Generate Analysis"):
        st.session_state.analysis_generated = True
        st.session_state.show_sentiment = False

    if st.sidebar.button("🩵 Analyze Chat Sentiment"):
        st.session_state.show_sentiment = True
        st.session_state.analysis_generated = False

    # =========================================
    # 📊 MAIN CHAT ANALYSIS
    # =========================================
    if st.session_state.analysis_generated:
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        st.title("📈 Top Statistics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Messages", num_messages)
        col2.metric("Total Words", words)
        col3.metric("Media Shared", num_media_messages)
        col4.metric("Links Shared", num_links)

        # --- Monthly Timeline ---
        st.title("🗓️ Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['Message'], color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # --- Daily Timeline ---
        st.title("📆 Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['Message'], color='black')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # --- Emoji Chart ---
        if st.checkbox("📊 Show Emoji Usage Chart"):
            helper.create_emoji_bar_chart(df)

        # --- Activity Map ---
        st.title("🗺️ Activity Map")
        col1, col2 = st.columns(2)
        with col1:
            st.header("Most Active Days")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)
        with col2:
            st.header("Most Active Months")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='purple')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        # --- Heatmap ---
        st.title("🔥 Weekly Activity Heatmap")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        if user_heatmap.empty or user_heatmap.isnull().all().all():
            st.warning("⚠️ No activity data available to generate heatmap.")
        else:
            fig, ax = plt.subplots()
            sns.heatmap(user_heatmap, ax=ax)
            st.pyplot(fig)

        # --- Busy Users ---
        if selected_user == "Overall":
            st.title("🏆 Most Active Users")
            x, new_df = helper.most_busy_users(df)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top 5 Yappers")
                fig, ax = plt.subplots()
                ax.bar(x.index, x.values, color='green')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.subheader("Contribution (%)")
                st.dataframe(new_df)

        # --- WordCloud ---
        st.title("☁️ Word Cloud")
        df_wc = helper.create_wordcloud(selected_user, df)
        if df_wc is not None:
            fig, ax = plt.subplots()
            ax.imshow(df_wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.warning("⚠️ No words available to generate the Word Cloud.")

        # --- Most Common Words ---
        st.title("💬 Most Common Words")
        most_common_df = helper.most_common_words(selected_user, df)
        fig, ax = plt.subplots()
        ax.barh(most_common_df['Word'], most_common_df['Frequency'], color='teal')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # --- Emoji Analysis ---
        st.title("😀 Most Common Emojis")
        emoji_df = helper.emoji_helper(selected_user, df)
        st.dataframe(emoji_df)

    # =========================================
    # 🧠 SENTIMENT ANALYSIS VIEW
    # =========================================
    elif st.session_state.show_sentiment:
        st.title("🧠 Sentiment Analysis Dashboard")
        st.caption("Understand the emotional tone and polarity of each message.")

        sentiment_summary, sentiment_df = sentiment_helper.analyze_sentiments(selected_user, df)

        if sentiment_summary is not None:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("😊 Positive", sentiment_summary["positive"])
            col2.metric("😐 Neutral", sentiment_summary["neutral"])
            col3.metric("😡 Negative", sentiment_summary["negative"])
            col4.metric("📈 Avg Sentiment", round(sentiment_summary["avg_sentiment"], 3))

            st.markdown("---")

            # === Sentiment Distribution Bar Chart ===
            st.subheader("📊 Sentiment Distribution")
            fig, ax = plt.subplots()
            ax.bar(
                ["Positive", "Neutral", "Negative"],
                [sentiment_summary["positive"], sentiment_summary["neutral"], sentiment_summary["negative"]],
                color=["#2ecc71", "#f1c40f", "#e74c3c"]
            )
            ax.set_ylabel("Message Count")
            st.pyplot(fig)

            # === Sentiment Pie Chart ===
            st.subheader("🧩 Sentiment Composition")
            fig, ax = plt.subplots()
            ax.pie(
                [sentiment_summary["positive"], sentiment_summary["neutral"], sentiment_summary["negative"]],
                labels=["Positive", "Neutral", "Negative"],
                colors=["#2ecc71", "#f1c40f", "#e74c3c"],
                autopct='%1.1f%%',
                startangle=90
            )
            st.pyplot(fig)

            # === Sample Messages with Polarity ===
            st.subheader("💬 Sample Messages by Sentiment (with Scores)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**😊 Positive Messages**")
                st.dataframe(
                    sentiment_df[sentiment_df['Sentiment'] == 'Positive'][['Sender', 'Message', 'Polarity']].head(5)
                )
            with col2:
                st.markdown("**😐 Neutral Messages**")
                st.dataframe(
                    sentiment_df[sentiment_df['Sentiment'] == 'Neutral'][['Sender', 'Message', 'Polarity']].head(5)
                )
            with col3:
                st.markdown("**😡 Negative Messages**")
                st.dataframe(
                    sentiment_df[sentiment_df['Sentiment'] == 'Negative'][['Sender', 'Message', 'Polarity']].head(5)
                )

else:
    st.info("📂 Please upload your WhatsApp chat file to begin analysis.")
