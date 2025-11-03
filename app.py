# app.py (Unified: Analysis + Sentiment + Exports)
import streamlit as st
import preprocessor, helper, sentiment_helper, export_helper
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
import export_sentiment_helper


# =========================================
# Page config
# =========================================
st.set_page_config(page_title="📱 WhatsApp Chat Analyzer", page_icon="💬", layout="wide")

# =========================================
# Sidebar - Clear cache + upload + actions
# =========================================
st.sidebar.title("📱 WhatsApp Chat Analyser")

if st.sidebar.button("🧹 Clear Cache"):
    # Clear streamlit caches and session state
    try:
        st.cache_data.clear()
    except Exception:
        pass
    try:
        st.cache_resource.clear()
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.sidebar.success("✅ Cache and session cleared! Please reload or upload a new file.")

uploaded_file = st.sidebar.file_uploader("📁 Choose a WhatsApp chat file (.txt)")

# ensure flags exist in session
if "analysis_generated" not in st.session_state:
    st.session_state.analysis_generated = False
if "show_sentiment" not in st.session_state:
    st.session_state.show_sentiment = False
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None
if "df" not in st.session_state:
    st.session_state.df = None
if "stats" not in st.session_state:
    st.session_state.stats = None

# =========================================
# File upload handling
# =========================================
if uploaded_file is not None:
    uploaded_filename = uploaded_file.name

    # reset state when a different file is uploaded
    if st.session_state.get("last_uploaded") != uploaded_filename:
        st.session_state.analysis_generated = False
        st.session_state.show_sentiment = False
        st.session_state.last_uploaded = uploaded_filename
        st.session_state.df = None
        st.session_state.stats = None

    bytes_data = uploaded_file.getvalue()
    # robust decoding
    try:
        data = bytes_data.decode("utf-8")
    except Exception:
        # fallback encodings; final fallback ignore errors
        decoded = None
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                decoded = bytes_data.decode(enc)
                break
            except Exception:
                continue
        if decoded is None:
            data = bytes_data.decode("utf-8", errors="ignore")
        else:
            data = decoded

    # basic extension hint
    if not uploaded_filename.lower().endswith((".txt",)):
        st.sidebar.warning("Uploaded file does not have .txt extension. The app will still try to parse it.")

    # validate content roughly using preprocessor HEADER_RE if available
    header_ok = True
    try:
        header_ok = bool(preprocessor.HEADER_RE.search(data))
    except Exception:
        header_ok = True  # if preprocessor doesn't expose HEADER_RE, skip strict check

    if not header_ok:
        st.error(
            "Uploaded file doesn't look like a WhatsApp chat export.\n"
            "Expected lines like 'dd/mm/yy, hh:mm - Sender: message'.\n"
            "Please upload a valid WhatsApp chat export (usually .txt)."
        )
        st.stop()

    # preprocess once and cache in session
    try:
        df = preprocessor.preprocess(data)
    except Exception as e:
        st.error(f"Preprocessing failed: {e}")
        st.stop()

    # make sure Date exists and is parsed
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
    except Exception:
        # if Date column absent or invalid, continue but warn
        st.warning("Warning: 'Date' column couldn't be parsed fully. Some timeline charts may be empty.")

    st.session_state.df = df

    # show basic parsed summary
    st.subheader("📊 Parsed Chat Summary")
    st.write(f"📋 **Total messages parsed:** {len(df)}")
    if 'Date' in df.columns and len(df) > 0:
        st.write(f"📅 **Date range:** {df['Date'].min().date()} → {df['Date'].max().date()}")
    st.dataframe(df.head(), use_container_width=True)

    # user selection
    user_list = df['Sender'].unique().tolist()
    user_list.sort()
    if "Meta AI" in user_list:
        user_list.remove("Meta AI")
    user_list.insert(0, "Overall")
    selected_user = st.sidebar.selectbox("👤 Show analysis for", user_list)

    # === Sidebar Buttons (Modes) ===
    if st.sidebar.button("🚀 Generate Analysis", key="generate_analysis"):
        st.session_state.analysis_generated = True
        st.session_state.show_sentiment = False
        st.session_state.show_interaction = False

    if st.sidebar.button("🩵 Analyze Chat Sentiment", key="sentiment_analysis"):
        st.session_state.show_sentiment = True
        st.session_state.analysis_generated = False
        st.session_state.show_interaction = False

    if st.sidebar.button("👥 Show Interaction Graph", key="interaction_graph"):
        st.session_state.show_interaction = True
        st.session_state.analysis_generated = False
        st.session_state.show_sentiment = False


    # =========================================
    # MAIN ANALYSIS VIEW
    # =========================================
    if st.session_state.analysis_generated:
        df = st.session_state.df  # fresh reference

        # top stats
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        # store stats for export
        st.session_state.stats = {
            'messages': num_messages,
            'words': words,
            'media': num_media_messages,
            'links': num_links
        }

        st.title("📈 Top Statistics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Messages", num_messages)
        col2.metric("Total Words", words)
        col3.metric("Media Shared", num_media_messages)
        col4.metric("Links Shared", num_links)

        # Export quick stats (CSV / PDF)
        st.markdown("---")
        st.subheader("📥 Export Analysis Results")
        date_range = f"{df['Date'].min().date()} to {df['Date'].max().date()}" if 'Date' in df.columns else "N/A"

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            try:
                csv_stats = export_helper.export_statistics_csv(num_messages, words, num_media_messages, num_links)
                st.download_button(
                    "📊 Download Statistics (CSV)",
                    data=csv_stats,
                    file_name=f"whatsapp_stats_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Unable to prepare CSV stats: {e}")

        with col_e2:
            try:
                pdf_stats = export_helper.export_statistics_pdf(selected_user, num_messages, words, num_media_messages, num_links, date_range)
                st.download_button(
                    "📄 Download Statistics (PDF)",
                    data=pdf_stats,
                    file_name=f"whatsapp_stats_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Unable to prepare PDF stats: {e}")

        st.markdown("---")

        # monthly timeline
        st.title("🗓️ Monthly Timeline")
        try:
            timeline = helper.monthly_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(timeline['time'], timeline['Message'], color='green')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Monthly timeline failed: {e}")

        # daily timeline
        st.title("📆 Daily Timeline")
        try:
            daily_timeline = helper.daily_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(daily_timeline['only_date'], daily_timeline['Message'], color='black')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Daily timeline failed: {e}")

        # Emoji usage chart toggle
        if selected_user == "Overall":
            df_for_emoji = st.session_state.df
        else:
            df_for_emoji = df

        if st.checkbox("📊 Show Emoji Usage Chart"):
            try:
                # helper should produce a figure or do plotting inside
                helper.create_emoji_bar_chart(df_for_emoji)  # earlier you had create_emoji_bar_chart; adapt if signature differs
            except Exception as e:
                st.warning(f"Emoji chart failed: {e}")

        # activity map
        st.title("🗺️ Activity Map")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.header("Most Active Days")
            busy_day = helper.week_activity_map(selected_user, df)
            try:
                fig, ax = plt.subplots()
                ax.bar(busy_day.index, busy_day.values, color='orange')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Most Active Days chart failed: {e}")

        with col_d2:
            st.header("Most Active Months")
            busy_month = helper.month_activity_map(selected_user, df)
            try:
                fig, ax = plt.subplots()
                ax.bar(busy_month.index, busy_month.values, color='purple')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Most Active Months chart failed: {e}")

        # weekly heatmap
        st.title("🔥 Weekly Activity Heatmap")
        try:
            user_heatmap = helper.activity_heatmap(selected_user, df)
            if user_heatmap.empty or user_heatmap.isnull().all().all():
                st.warning("No activity data available to generate heatmap for this chat.")
            else:
                fig, ax = plt.subplots(figsize=(12, 5))
                sns.heatmap(user_heatmap, ax=ax)
                st.pyplot(fig)
        except Exception as e:
            st.warning(f"Heatmap generation failed: {e}")

        # most busy users (overall)
        if selected_user == "Overall":
            st.title("🏆 Most Active Users")
            x, new_df = helper.most_busy_users(df)
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                st.subheader("Top 5 Yappers")
                fig, ax = plt.subplots()
                ax.bar(x.index, x.values, color='green')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col_u2:
                st.subheader("Contribution (%)")
                st.dataframe(new_df)

        # wordcloud
        st.title("☁️ Word Cloud")
        try:
            df_wcl = helper.create_wordcloud(selected_user, df)
            if df_wcl is not None:
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.imshow(df_wcl, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)
            else:
                st.warning("No words available to generate the Word Cloud for this user.")
        except Exception as e:
            st.warning(f"WordCloud generation failed: {e}")

        # most common words
        st.title("💬 Most Common Words")
        try:
            most_common_df = helper.most_common_words(selected_user, df)
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.barh(most_common_df['Word'], most_common_df['Frequency'], color='teal')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Most common words chart failed: {e}")

        # emoji list
        st.title("😀 Most Common Emojis")
        try:
            emoji_df = helper.emoji_helper(selected_user, df)
            st.dataframe(emoji_df)
        except Exception as e:
            st.warning(f"Emoji extraction failed: {e}")

        # Export complete analysis (Excel / PDF)
        st.markdown("---")
        st.subheader("📦 Export Complete Analysis")
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            try:
                timeline_df = helper.monthly_timeline(selected_user, df)
                daily_timeline_df = helper.daily_timeline(selected_user, df)
                busy_users_df = None
                if selected_user == 'Overall':
                    _, busy_users_df = helper.most_busy_users(df)
                excel_data = export_helper.export_complete_analysis_csv(
                    selected_user, df, st.session_state.stats,
                    timeline_df=timeline_df,
                    daily_timeline_df=daily_timeline_df,
                    common_words_df=most_common_df if 'most_common_df' in locals() else pd.DataFrame(),
                    emoji_df=emoji_df if 'emoji_df' in locals() else pd.DataFrame(),
                    busy_users_df=busy_users_df
                )
                st.download_button(
                    "📊 Download Complete Analysis (Excel)",
                    data=excel_data,
                    file_name=f"whatsapp_complete_analysis_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error preparing Excel export: {e}")

        with col_ex2:
            try:
                # prepare charts dictionary (figures) for PDF export
                charts_dict = {}

                # monthly timeline fig
                try:
                    fig_monthly, ax_monthly = plt.subplots(figsize=(10, 4))
                    ax_monthly.plot(timeline['time'], timeline['Message'], color='green', linewidth=2)
                    ax_monthly.set_xlabel('Time Period')
                    ax_monthly.set_ylabel('Messages')
                    ax_monthly.set_title('Monthly Timeline')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    charts_dict['Monthly Timeline'] = fig_monthly
                except Exception:
                    pass

                # daily timeline fig
                try:
                    fig_daily, ax_daily = plt.subplots(figsize=(10, 4))
                    ax_daily.plot(daily_timeline_df['only_date'], daily_timeline_df['Message'], color='black', linewidth=2)
                    ax_daily.set_xlabel('Date')
                    ax_daily.set_ylabel('Messages')
                    ax_daily.set_title('Daily Timeline')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    charts_dict['Daily Timeline'] = fig_daily
                except Exception:
                    pass

                # most active days fig
                try:
                    busy_day = helper.week_activity_map(selected_user, df)
                    if not busy_day.empty:
                        fig_days, ax_days = plt.subplots(figsize=(10, 4))
                        ax_days.bar(busy_day.index, busy_day.values, color='orange')
                        ax_days.set_xlabel('Day of Week')
                        ax_days.set_ylabel('Messages')
                        ax_days.set_title('Most Active Days')
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        charts_dict['Most Active Days'] = fig_days
                except Exception:
                    pass

                # most active months fig
                try:
                    busy_month = helper.month_activity_map(selected_user, df)
                    if not busy_month.empty:
                        fig_months, ax_months = plt.subplots(figsize=(10, 4))
                        ax_months.bar(busy_month.index, busy_month.values, color='purple')
                        ax_months.set_xlabel('Month')
                        ax_months.set_ylabel('Messages')
                        ax_months.set_title('Most Active Months')
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        charts_dict['Most Active Months'] = fig_months
                except Exception:
                    pass

                # heatmap
                try:
                    user_heatmap = helper.activity_heatmap(selected_user, df)
                    if not user_heatmap.empty and not user_heatmap.isnull().all().all():
                        fig_heatmap, ax_heatmap = plt.subplots(figsize=(12, 6))
                        sns.heatmap(user_heatmap, ax=ax_heatmap, cmap='YlOrRd')
                        ax_heatmap.set_title('Activity Heatmap')
                        plt.tight_layout()
                        charts_dict['Activity Heatmap'] = fig_heatmap
                except Exception:
                    pass

                # wordcloud fig
                try:
                    df_wcl = helper.create_wordcloud(selected_user, df)
                    if df_wcl is not None:
                        fig_wc, ax_wc = plt.subplots(figsize=(10, 6))
                        ax_wc.imshow(df_wcl, interpolation="bilinear")
                        ax_wc.axis("off")
                        ax_wc.set_title('Word Cloud')
                        plt.tight_layout()
                        charts_dict['Word Cloud'] = fig_wc
                except Exception:
                    pass

                # most common words fig
                try:
                    fig_words, ax_words = plt.subplots(figsize=(10, 6))
                    ax_words.barh(most_common_df['Word'], most_common_df['Frequency'], color='teal')
                    ax_words.set_xlabel('Frequency')
                    ax_words.set_ylabel('Words')
                    ax_words.set_title('Most Common Words')
                    plt.tight_layout()
                    charts_dict['Most Common Words'] = fig_words
                except Exception:
                    pass

                # emoji bar chart (helper returns a fig or None)
                try:
                    fig_emoji_bar = helper.generate_emoji_bar_chart_figure(selected_user, df)
                    if fig_emoji_bar is not None:
                        charts_dict['Emoji Usage Bar Chart'] = fig_emoji_bar
                except Exception:
                    pass

                # top contributors fig
                try:
                    if selected_user == 'Overall':
                        x, _ = helper.most_busy_users(df)
                        fig_users, ax_users = plt.subplots(figsize=(10, 4))
                        ax_users.bar(x.index, x.values, color='green')
                        ax_users.set_xlabel('User')
                        ax_users.set_ylabel('Messages')
                        ax_users.set_title('Top 5 Contributors')
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        charts_dict['Top Contributors'] = fig_users
                except Exception:
                    pass

                # call export helper to create PDF from charts + data
                pdf_complete = export_helper.export_complete_analysis_pdf(
                    selected_user, st.session_state.stats, date_range,
                    common_words_df=(most_common_df if 'most_common_df' in locals() else pd.DataFrame()),
                    emoji_df=(emoji_df if 'emoji_df' in locals() else pd.DataFrame()),
                    busy_users_df=(busy_users_df if 'busy_users_df' in locals() else None),
                    charts=charts_dict
                )

                # close figures to free memory
                for fig in charts_dict.values():
                    try:
                        plt.close(fig)
                    except Exception:
                        pass

                st.download_button(
                    "📄 Download Complete Analysis (PDF)",
                    data=pdf_complete,
                    file_name=f"whatsapp_complete_analysis_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error preparing PDF export: {e}")

        st.success("✅ Analysis complete! Use the export buttons above to save your results.")

    # =========================================
    # SENTIMENT VIEW
    # =========================================
    elif st.session_state.show_sentiment:
        df = st.session_state.df
        st.title("🧠 Sentiment Analysis Dashboard")
        st.caption("Understand the emotional tone and polarity of each message.")

        # returns a (summary_dict, sentiment_df)
        try:
            sentiment_summary, sentiment_df = sentiment_helper.analyze_sentiments(selected_user, df)
        except Exception as e:
            st.error(f"Sentiment analysis failed: {e}")
            sentiment_summary, sentiment_df = None, pd.DataFrame()

        if sentiment_summary is not None:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("😊 Positive", sentiment_summary["positive"])
            col2.metric("😐 Neutral", sentiment_summary["neutral"])
            col3.metric("😡 Negative", sentiment_summary["negative"])
            col4.metric("📈 Avg Sentiment", round(sentiment_summary["avg_sentiment"], 3))

            st.markdown("---")

            # bar chart
            st.subheader("📊 Sentiment Distribution")
            try:
                fig, ax = plt.subplots()
                ax.bar(
                    ["Positive", "Neutral", "Negative"],
                    [sentiment_summary["positive"], sentiment_summary["neutral"], sentiment_summary["negative"]],
                    color=["#2ecc71", "#f1c40f", "#e74c3c"]
                )
                ax.set_ylabel("Message Count")
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Sentiment bar chart failed: {e}")

            # pie chart
            st.subheader("🧩 Sentiment Composition")
            try:
                fig, ax = plt.subplots()
                ax.pie(
                    [sentiment_summary["positive"], sentiment_summary["neutral"], sentiment_summary["negative"]],
                    labels=["Positive", "Neutral", "Negative"],
                    colors=["#2ecc71", "#f1c40f", "#e74c3c"],
                    autopct='%1.1f%%',
                    startangle=90
                )
                ax.axis('equal')
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Sentiment pie chart failed: {e}")

            # sample messages with polarity and sender
            st.subheader("💬 Sample Messages by Sentiment (with Scores)")
            try:
                col_p, col_n, col_u = st.columns(3)
                with col_p:
                    st.markdown("**😊 Positive Messages**")
                    st.dataframe(sentiment_df[sentiment_df['Sentiment'] == 'Positive'][['Sender', 'Message', 'Polarity']].head(5))
                with col_n:
                    st.markdown("**😐 Neutral Messages**")
                    st.dataframe(sentiment_df[sentiment_df['Sentiment'] == 'Neutral'][['Sender', 'Message', 'Polarity']].head(5))
                with col_u:
                    st.markdown("**😡 Negative Messages**")
                    st.dataframe(sentiment_df[sentiment_df['Sentiment'] == 'Negative'][['Sender', 'Message', 'Polarity']].head(5))
            except Exception as e:
                st.warning(f"Failed to render sample messages: {e}")


            # =============================
# 📤 EXPORT SENTIMENT ANALYSIS
# =============================

            st.markdown("---")
            st.subheader("📤 Export Sentiment Analysis Results")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                csv_data = export_sentiment_helper.export_sentiment_csv(sentiment_df)
                st.download_button(
                    label="⬇️  📄 Download CSV",
                    data=csv_data,
                    file_name=f"sentiment_analysis_{selected_user}.csv",
                    mime="text/csv"
                    )

            with col2:
                excel_data = export_sentiment_helper.export_sentiment_excel(sentiment_summary, sentiment_df)
                st.download_button(
                    label="⬇️  📘 Download Excel",
                    data=excel_data,
                    file_name=f"sentiment_analysis_{selected_user}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            with col3:
                pdf_data = export_sentiment_helper.export_sentiment_pdf(selected_user, sentiment_summary, sentiment_df)
                st.download_button(
                    label="⬇️  🧾 Download PDF",
                    data=pdf_data,
                    file_name=f"sentiment_analysis_{selected_user}.pdf",
                    mime="application/pdf"
                    )
 
            with col4:
                word_data = export_sentiment_helper.export_sentiment_word(selected_user, sentiment_summary, sentiment_df)
                st.download_button(
                    label="⬇️  📝 Download Word",
                    data=word_data,
                    file_name=f"sentiment_analysis_{selected_user}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )


        else:
            st.warning("No sentiment data available for this chat or the chat contains no valid text messages.")

        # ======================================================
# 👥 INTERACTION GRAPH SECTION (Stylish Visualization)
# ======================================================
    elif st.session_state.get("show_interaction", False):
        st.title("👥 User Relationship Graph")
        st.caption("Each circle represents a user. Line thickness = frequency of interaction.")
        dynamic_mode = st.checkbox("🌀 Enable 3D Motion", value=True)

        html = helper.create_interaction_graph(selected_user, st.session_state.df, dynamic=dynamic_mode)
        if html:
            st.components.v1.html(html, height=750, scrolling=False)
            # 🧭 Add legend/info section
            st.markdown("""
            ### 🔍 Graph Legend  
            - 🟢 **Node (Circle)** → Represents a chat participant.  
            - 🌈 **Node Color** → Randomly assigned; used to visually separate users.  
            - 🔵 **Line (Edge)** → Represents messages exchanged between two users.  
            - 📏 **Line Thickness** → Shows interaction strength — thicker = more messages.  
            - 🎨 **Line Color Intensity** → Warmer (red/yellow) = higher message frequency, cooler (blue/purple) = fewer messages.  
            - ⚙️ **Motion Mode** → When ON, the graph slowly rotates like a 3D web.  
            - 🔒 **Stable Mode** → When OFF, the graph stays still; zoom and drag freely.  
            """)
        else:
            st.warning("⚠️ No sufficient interaction data available to build a network graph.")



else:
    st.info("📂 Please upload your WhatsApp chat file to begin analysis.")

