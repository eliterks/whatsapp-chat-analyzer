import streamlit as st
import preprocessor,helper
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import export_helper
import datetime

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
        # Store analysis data for exports
        if 'export_data' not in st.session_state:
            st.session_state.export_data = {}
        
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
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

        # 😊 Emoji Usage Chart
        if selected_user == 'Overall':
            df = st.session_state.df
        if st.checkbox("Show Emoji Usage Chart"):
            helper.create_emoji_bar_chart(df)


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
        emoji_df= helper.emoji_helper(selected_user,df)
        st.dataframe(emoji_df)

        # Store all data for export
        st.session_state.export_data = {
            'stats': (num_messages, words, num_media_messages, num_links),
            'monthly_timeline': timeline,
            'daily_timeline': daily_timeline,
            'busy_day': busy_day,
            'busy_month': busy_month,
            'most_common_df': most_common_df,
            'emoji_df': emoji_df,
            'user_heatmap': user_heatmap,
            'top_users_data': (x, new_df) if selected_user == 'Overall' else None
        }

        # =========================
        # 📥 Export Section
        # =========================
        st.markdown("---")
        st.title("📥 Export Analysis Results")
        st.write("Download your chat analysis in PDF or Excel format")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Generate PDF
            try:
                pdf_buffer = export_helper.generate_pdf_report(
                    selected_user, df,
                    st.session_state.export_data['stats'],
                    st.session_state.export_data['monthly_timeline'],
                    st.session_state.export_data['daily_timeline'],
                    st.session_state.export_data['busy_day'],
                    st.session_state.export_data['busy_month'],
                    st.session_state.export_data['most_common_df'],
                    st.session_state.export_data['emoji_df'],
                    st.session_state.export_data['user_heatmap'],
                    st.session_state.export_data['top_users_data']
                )
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_pdf = f"whatsapp_analysis_{selected_user}_{timestamp}.pdf"
                
                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_buffer,
                    file_name=filename_pdf,
                    mime="application/pdf",
                    help="Download a comprehensive PDF report with all charts and statistics"
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
        
        with col2:
            # Generate Excel/CSV
            try:
                csv_buffer = export_helper.generate_csv_summary(
                    selected_user, df,
                    st.session_state.export_data['stats'],
                    st.session_state.export_data['monthly_timeline'],
                    st.session_state.export_data['daily_timeline'],
                    st.session_state.export_data['busy_day'],
                    st.session_state.export_data['busy_month'],
                    st.session_state.export_data['most_common_df'],
                    st.session_state.export_data['emoji_df'],
                    st.session_state.export_data['user_heatmap']
                )
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_excel = f"whatsapp_analysis_{selected_user}_{timestamp}.xlsx"
                
                st.download_button(
                    label="📊 Download Excel Report",
                    data=csv_buffer,
                    file_name=filename_excel,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download analysis data in Excel format with multiple sheets"
                )
            except Exception as e:
                st.error(f"Error generating Excel: {str(e)}")
        
        with col3:
            st.info("💡 **Tip**: PDF includes all visualizations, while Excel contains raw data for further analysis.")

