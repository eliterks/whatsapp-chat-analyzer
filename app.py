import streamlit as st
import preprocessor,helper
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

if "analysis_generated" not in st.session_state:
    st.session_state.analysis_generated = False

st.sidebar.title("Whatsapp Chat Analyser")
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
uploaded_file = st.file_uploader("Choose a WhatsApp chat file")

if uploaded_file is not None:
    # =========================
    # 📂 File Upload & Decoding
    # =========================
    bytes_data = uploaded_file.getvalue()
    # Decode WhatsApp chat in UTF-8 to preserve emojis
    data = bytes_data.decode("utf-8", errors="ignore")
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


    st.subheader("Parsed Chat Summary")
    st.write(f"📊 Total messages parsed: {len(df)}")
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # convert invalids to NaT
    df = df.dropna(subset=['Date'])  # drop rows with no valid date
    st.write(f"📅 Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

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
        
        # 😊 Emoji Usage Bar Chart (Optional)
        
        if selected_user == 'Overall':
            df = st.session_state.df  # use stored dataframe
        if st.checkbox("📊 Show Emoji Usage Bar Chart", value=False):
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

# =========================
# ⏱️ Average Response Time Visualization
# =========================
import seaborn as sns
import matplotlib.pyplot as plt

st.title("Average Response Time ⏱️")
avg_response_df = helper.average_response_time(df)

if avg_response_df.empty:
    st.warning("Not enough data to calculate response times.")
else:
    fig, ax = plt.subplots()
    sns.barplot(data=avg_response_df, x='Sender', y='Avg_Response_Time (min)', palette='mako', ax=ax)
    ax.set_title("Average Response Time per User (in minutes)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
