import streamlit as st
import preprocessor,helper
import matplotlib.pyplot as plt
import seaborn as sns
# @st.cache
# @st.cache_data
# @st.cache_resource
st.sidebar.title("Whatsapp Chat Analyser")
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    st.sidebar.success("File uploaded successfully")
    data=bytes_data.decode("utf-8")
    df=preprocessor.preprocess(data)
    #st.title("DataFrame Of All Chats")
    #st.dataframe(df) #displays df

    st.subheader("Parsed Chat Summary")
    st.write(f"📊 Total messages parsed: {len(df)}")
    st.write(f"📅 Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    st.write("Sample data:", df.head())

    #fetch users
    user_list=df['Sender'].unique().tolist()
    #user_list.remove('Meta AI')
    user_list.sort()
    user_list.insert(0,"Overall")
    selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

    if st.sidebar.button("Generate Analysis"):
#these num_messages are just variables to carry the value fteched from fetch_stats func
# and jo upr variables ke naam ha wahi niche st.title mein ha
# and ye zaruri nhi ki jo variables ke naam idhar ha wahi same helper.py file mein bhi ho
        num_messages,words,num_media_messages,num_links= helper.fetch_stats(selected_user,df)
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



        # WordCloud
        st.title("WordCloud")
        df_wcl= helper.create_wordcloud(selected_user,df)
        fig, ax = plt.subplots()
        ax.imshow(df_wcl)
        ax.axis("off")
        st.pyplot(fig)

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




