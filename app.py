import streamlit as st
import preprocessor,helper
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import export_helper
from datetime import datetime

if "analysis_generated" not in st.session_state:
    st.session_state.analysis_generated = False

st.sidebar.title("Whatsapp Chat Analyser")
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
uploaded_file = st.file_uploader("Choose a WhatsApp chat file")

if uploaded_file is not None:
    # -------------------------
    # Handle new uploads & session
    # -------------------------
    uploaded_filename = uploaded_file.name
    # If the filename changed, reset analysis state to avoid stale data
    if st.session_state.get("last_uploaded") != uploaded_filename:
        st.session_state.analysis_generated = False
        st.session_state.last_uploaded = uploaded_filename
        # clear previously stored df if present
        st.session_state.df = None

    # =========================
    # 📂 File Upload & Decoding
    # =========================
    bytes_data = uploaded_file.getvalue()
    # Decode WhatsApp chat in UTF-8 to preserve emojis
    try:
        data = bytes_data.decode("utf-8")
    except Exception:
        # fallback to ignore errors if strict decode fails
        data = bytes_data.decode("utf-8", errors="ignore")

    # Basic extension hint: most WhatsApp exports are .txt
    if not uploaded_filename.lower().endswith((".txt",)):
        st.warning("Uploaded file does not have a .txt extension. The app will validate the content format below.")

    # Validate content looks like WhatsApp export using the preprocessor's header regex
    try:
        header_ok = bool(preprocessor.HEADER_RE.search(data))
    except Exception:
        header_ok = False

    if not header_ok:
        st.error(
            "Uploaded file doesn't look like a WhatsApp chat export.\n"
            "Expected lines like 'dd/mm/yy, hh:mm - Sender: message'.\n"
            "Please upload a valid WhatsApp chat export (usually a .txt file)."
        )
        # Stop further execution in Streamlit to avoid crashes on wrong formats
        st.stop()

    # =========================
    # 🧹 Preprocess and Store
    # =========================
    df = preprocessor.preprocess(data)
    st.session_state.df = df  # optional, if you want to persist between runs

    # =========================
    # 📊 Basic Chat Info
    # =========================
    st.subheader("Parsed Chat Summary")
    st.write(f"📊 Total messages parsed: {len(df)}")

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    st.write(f"📅 Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    st.write("Sample data:", df.head())

    #fetch users
    user_list=df['Sender'].unique().tolist()
    #user_list.remove('Meta AI')
    user_list.sort()
    user_list.insert(0,"Overall")
    selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

    if st.sidebar.button("Generate Analysis"):
        st.session_state.analysis_generated = True
    
    if st.session_state.analysis_generated:
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        
        # Store statistics in session state for export
        st.session_state.stats = {
            'messages': num_messages,
            'words': words,
            'media': num_media_messages,
            'links': num_links
        }
        
        st.title("Top Statistics")
        col1,col2,col3,col4=st.columns(4)
        with col1:
            st.header("Total Messages")
            st.title(num_messages)
        with col2:
            st.header("Total Words")
            st.title(words)
        with col3:
            st.header("Total No Of Media Shared")
            st.title(num_media_messages)
        with col4:
            st.header("Total No Of Links Shared")
            st.title(num_links)
        
        # === Export Options ===
        st.markdown("---")
        st.subheader("📥 Export Analysis Results")
        
        # Get date range for export
        date_range = f"{df['Date'].min().date()} to {df['Date'].max().date()}"
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # Export basic statistics to CSV
            csv_stats = export_helper.export_statistics_csv(
                num_messages, words, num_media_messages, num_links
            )
            st.download_button(
                label="📊 Download Statistics (CSV)",
                data=csv_stats,
                file_name=f"whatsapp_stats_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download basic statistics as CSV file"
            )
        
        with col_export2:
            # Export basic statistics to PDF
            pdf_stats = export_helper.export_statistics_pdf(
                selected_user, num_messages, words, 
                num_media_messages, num_links, date_range
            )
            st.download_button(
                label="📄 Download Statistics (PDF)",
                data=pdf_stats,
                file_name=f"whatsapp_stats_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                help="Download basic statistics as PDF file"
            )
        
        st.markdown("---")

        # monthly timeline
        st.title("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['Message'], color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # daily timeline
        st.title("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['Message'], color='black')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        #activity_map
        st.title("Activity Map")
        col1,col2=st.columns(2)
        with col1:
            st.header("Most Active Days")
            busy_day=helper.week_activity_map(selected_user,df)
            fig,ax=plt.subplots()
            ax.bar(busy_day.index,busy_day.values,color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)
        with col2:
            st.header("Most Active Month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values)
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        #Weekly Activity HeatMap
        st.title("Activity Heatmap")
        user_heatmap= helper.activity_heatmap(selected_user,df)
        if user_heatmap.empty or user_heatmap.isnull().all().all():
            st.warning("No activity data available to generate heatmap for this chat.")
        else:
            fig, ax = plt.subplots()
            sns.heatmap(user_heatmap, ax=ax)
            st.pyplot(fig)

        if selected_user=='Overall':
            x,new_df= helper.most_busy_users(df)
            fig, ax = plt.subplots()
            col1,col2=st.columns(2)
            with col1:
                st.header("Top 5 Yappers")
                ax.bar(x.index, x.values,color='green')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.header("Percentage Wise Contribution Of Members")
                st.dataframe(new_df)
                




        # === WordCloud ===
        st.title("WordCloud")
        df_wcl = helper.create_wordcloud(selected_user, df)

        if df_wcl is not None:
            fig, ax = plt.subplots()
            ax.imshow(df_wcl, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.warning("No words available to generate the WordCloud for this user.")



        # most common words
        most_common_df= helper.most_common_words(selected_user,df)

        fig,ax=plt.subplots()

        ax.barh(most_common_df['Word'],most_common_df['Frequency'])
        plt.xticks(rotation='vertical')
        st.title("Most Common Words")
        st.pyplot(fig)

        #emoji_analysis
        
        st.title("Most Common Emojis")
        emoji_df = helper.emoji_helper(selected_user, df)
        st.dataframe(emoji_df)
        
        st.markdown("---")
        
                # =========================
        # ⏱️ Average Response Time per User
        # =========================
        st.markdown("---")
        st.title("⏱️ Average Response Time per User")

        try:
            avg_response_df = helper.average_response_time(df)

            if avg_response_df is not None and not avg_response_df.empty:
                st.dataframe(avg_response_df)

                fig, ax = plt.subplots(figsize=(8, 5))
                sns.barplot(
                    data=avg_response_df,
                    x='Sender',
                    y='Avg Response Time (seconds)',
                    palette='crest',
                    ax=ax
                )
                plt.xticks(rotation=45)
                ax.set_title("Average Response Time (seconds)")
                st.pyplot(fig)
            else:
                st.info("No sufficient data to calculate response times.")
        except Exception as e:
            st.error(f"⚠️ Error calculating response time: {e}")


        # 😊 Emoji Usage Bar Chart (Optional)
        
        if st.checkbox("📊 Show Emoji Usage Bar Chart", value=False):
average-response-time-feature
helper.create_emoji_bar_chart(df)



import streamlit as st

# Initialize dark mode state
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# --- Button beside Deploy (top-right) ---
st.markdown("""
    <style>
        /* Position theme toggle beside the "Deploy" button */
        #theme-toggle {
            position: fixed;
            top: 10px;
            right: 100px; /* Adjust spacing to sit beside Deploy */
            z-index: 9999;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 20px;
        }
        #theme-toggle:hover {
            transform: scale(1.2);
        }
    </style>

    <script>
        // Reload page after click to apply CSS instantly
        const toggleBtn = document.getElementById("theme-toggle");
        if (toggleBtn) {
            toggleBtn.addEventListener("click", () => location.reload());
        }
    </script>
""", unsafe_allow_html=True)

# Button itself
if st.button("🌙" if st.session_state.dark_mode else "☀️", key="deploy_theme_button"):
    st.session_state.dark_mode = not st.session_state.dark_mode

# Inject positioning for Streamlit-generated button (since we can't edit toolbar DOM)
st.markdown("""
    <style>
        div[data-testid="stButton"] button[kind="primary"] {
            position: fixed !important;
            top: 10px !important;
            right: 100px !important;
            z-index: 9999 !important;
            background: transparent !important;
            border: none !important;
            font-size: 20px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Global Theme Inversion ---
if st.session_state.dark_mode:
    st.markdown("""
        <style>
            html {
                filter: invert(1) hue-rotate(180deg);
            }
            img, video {
                filter: invert(1) hue-rotate(180deg);
            }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("<style>html { filter: none; }</style>", unsafe_allow_html=True)

            helper.create_emoji_bar_chart(selected_user, df)        
        # === Comprehensive Export Section ===
        st.markdown("---")
        st.subheader("📦 Export Complete Analysis")
        st.write("Download all analysis results including statistics, timelines, word frequency, and emoji analysis.")
        
        col_full1, col_full2 = st.columns(2)
        
        with col_full1:
            # Prepare data for Excel export
            timeline_df = helper.monthly_timeline(selected_user, df)
            daily_timeline_df = helper.daily_timeline(selected_user, df)
            busy_users_df = None
            
            if selected_user == 'Overall':
                _, busy_users_df = helper.most_busy_users(df)
            
            # Export complete analysis to Excel
            try:
                excel_data = export_helper.export_complete_analysis_csv(
                    selected_user, df, st.session_state.stats,
                    timeline_df=timeline_df,
                    daily_timeline_df=daily_timeline_df,
                    common_words_df=most_common_df,
                    emoji_df=emoji_df,
                    busy_users_df=busy_users_df
                )
                st.download_button(
                    label="📊 Download Complete Analysis (Excel)",
                    data=excel_data,
                    file_name=f"whatsapp_complete_analysis_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download all analysis data in Excel format with multiple sheets"
                )
            except Exception as e:
                st.error(f"Error preparing Excel export: {e}")
        
        with col_full2:
            # Export complete analysis to PDF with charts
            try:
                # Generate all charts for PDF export
                charts_dict = {}
                
                # Monthly Timeline Chart
                fig_monthly, ax_monthly = plt.subplots(figsize=(10, 4))
                ax_monthly.plot(timeline_df['time'], timeline_df['Message'], color='green', linewidth=2)
                ax_monthly.set_xlabel('Time Period')
                ax_monthly.set_ylabel('Messages')
                ax_monthly.set_title('Monthly Timeline')
                plt.xticks(rotation=45)
                plt.tight_layout()
                charts_dict['Monthly Timeline'] = fig_monthly
                
                # Daily Timeline Chart
                fig_daily, ax_daily = plt.subplots(figsize=(10, 4))
                ax_daily.plot(daily_timeline_df['only_date'], daily_timeline_df['Message'], color='black', linewidth=2)
                ax_daily.set_xlabel('Date')
                ax_daily.set_ylabel('Messages')
                ax_daily.set_title('Daily Timeline')
                plt.xticks(rotation=45)
                plt.tight_layout()
                charts_dict['Daily Timeline'] = fig_daily
                
                # Most Active Days Chart
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
                
                # Most Active Month Chart
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
                
                # Activity Heatmap
                user_heatmap = helper.activity_heatmap(selected_user, df)
                if not user_heatmap.empty and not user_heatmap.isnull().all().all():
                    fig_heatmap, ax_heatmap = plt.subplots(figsize=(12, 6))
                    sns.heatmap(user_heatmap, ax=ax_heatmap, cmap='YlOrRd')
                    ax_heatmap.set_title('Activity Heatmap')
                    plt.tight_layout()
                    charts_dict['Activity Heatmap'] = fig_heatmap
                
                # WordCloud
                df_wcl = helper.create_wordcloud(selected_user, df)
                if df_wcl is not None:
                    fig_wc, ax_wc = plt.subplots(figsize=(10, 6))
                    ax_wc.imshow(df_wcl, interpolation="bilinear")
                    ax_wc.axis("off")
                    ax_wc.set_title('Word Cloud')
                    plt.tight_layout()
                    charts_dict['Word Cloud'] = fig_wc
                
                # Most Common Words Chart
                fig_words, ax_words = plt.subplots(figsize=(10, 6))
                ax_words.barh(most_common_df['Word'], most_common_df['Frequency'], color='teal')
                ax_words.set_xlabel('Frequency')
                ax_words.set_ylabel('Words')
                ax_words.set_title('Most Common Words')
                plt.tight_layout()
                charts_dict['Most Common Words'] = fig_words
                
                # Emoji Bar Chart
                fig_emoji_bar = helper.generate_emoji_bar_chart_figure(selected_user, df)
                if fig_emoji_bar is not None:
                    charts_dict['Emoji Usage Bar Chart'] = fig_emoji_bar
                
                # Top Users Chart (if Overall)
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
                
                # Generate PDF with charts
                pdf_complete = export_helper.export_complete_analysis_pdf(
                    selected_user, st.session_state.stats, date_range,
                    common_words_df=most_common_df,
                    emoji_df=emoji_df,
                    busy_users_df=busy_users_df if selected_user == 'Overall' else None,
                    charts=charts_dict
                )
                
                # Close all figures to free memory
                for fig in charts_dict.values():
                    plt.close(fig)
                
                st.download_button(
                    label="📄 Download Complete Analysis (PDF)",
                    data=pdf_complete,
                    file_name=f"whatsapp_complete_analysis_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    help="Download comprehensive analysis report in PDF format with all visualizations"
                )
            except Exception as e:
                st.error(f"Error preparing PDF export: {e}")
                import traceback
                st.error(traceback.format_exc())
        
        st.success("✅ Analysis complete! Use the export buttons above to save your results.")
main
