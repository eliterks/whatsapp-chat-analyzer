import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import pandas as pd

# @st.cache
# @st.cache_data
@st.cache_resource
def load_model(model_path):
    """Loads the saved ML model from disk."""
    model = joblib.load(model_path)
    return model

# Load your model
model = load_model('activity_classifier.pkl')

st.sidebar.title("Whatsapp Chat Analyser")
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()

uploaded_file = st.sidebar.file_uploader("Choose a file")

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    st.sidebar.success("File uploaded successfully")
    
    # This is the original code without the try...except block
    # It will crash if the file is bad, but it will fix the indentation error.
    data = bytes_data.decode("utf-8")
    df = preprocessor.preprocess(data)
    
    st.subheader("Parsed Chat Summary")
    st.write(f"📊 Total messages parsed: {len(df)}")
    st.write(f"📅 Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    st.write("Sample data:", df.head())

    # fetch users
    user_list = df['Sender'].unique().tolist()
    # user_list.remove('Meta AI')
    user_list.sort()
    user_list.insert(0, "Overall")
    selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

    if st.sidebar.button("Generate Analysis"):
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        st.title("Top Statistics")
        col1, col2, col3, col4 = st.columns(4)
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

        # activity_map
        st.title("Activity Map")
        col1, col2 = st.columns(2)
        with col1:
            st.header("Most Active Days")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)
        with col2:
            st.header("Most Active Month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values)
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        # Weekly Activity HeatMap
        st.title("Activity Heatmap")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        if user_heatmap.empty or user_heatmap.isnull().all().all():
            st.warning("No activity data available to generate heatmap for this chat.")
        else:
            fig, ax = plt.subplots()
            sns.heatmap(user_heatmap, ax=ax)
            st.pyplot(fig)

        if selected_user == 'Overall':
            x, new__df = helper.most_busy_users(df)
            fig, ax = plt.subplots()
            col1, col2 = st.columns(2)
            with col1:
                st.header("Top 5 Yappers")
                ax.bar(x.index, x.values, color='green')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.header("Percentage Wise Contribution Of Members")
                st.dataframe(new_df)

        # WordCloud
        st.title("WordCloud")
        df_wcl = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wcl)
        ax.axis("off")
        st.pyplot(fig)

        # most common words
        most_common_df = helper.most_common_words(selected_user, df)
        fig, ax = plt.subplots()
        ax.barh(most_common_df['Word'], most_common_df['Frequency'])
        plt.xticks(rotation='vertical')
        st.title("Most Common Words")
        st.pyplot(fig)

        # emoji_analysis
        st.title("Most Common Emojis")
        emoji_df = helper.emoji_helper(selected_user, df)
        st.dataframe(emoji_df)
        
        # --- Machine Learning Prediction Section ---
        st.title("🤖 User Activity Prediction")
        
        # 1. Create feature table
        # We use the 'df' that has ALL users, not the 'selected_user' one
        feature_table = helper.engineer_features_for_prediction(df)

        if not feature_table.empty and selected_user == 'Overall':
            try:
                # 2. Get user list and features
                user_list_for_pred = feature_table.index
                X_predict = feature_table
                
                # 3. Make predictions
                predictions = model.predict(X_predict)
                probabilities = model.predict_proba(X_predict)[:, 1] # Prob of being 'Active'

                # 4. Create a clean results dataframe
                results_df = pd.DataFrame({
                    'User': user_list_for_pred,
                    'Prediction': predictions,
                    'Active_Probability': probabilities
                })
                
                # Map 0/1 to labels
                results_df['Activity_Level'] = results_df['Prediction'].apply(
                    lambda x: "Highly Active" if x == 1 else "Less Active"
                )

                # 5. Display results
                st.subheader("Predicted Activity Levels (Overall)")
                st.write("This model predicts which users are 'Highly Active' based on their chat patterns.")
                
                # Format probability as percentage
                results_df['Active_Probability'] = results_df['Active_Probability'].apply(
                    lambda x: f"{x*100:.2f}%"
                )
                
                # Show the table, sorted by probability
                st.dataframe(
                    results_df[['User', 'Activity_Level', 'Active_Probability']].sort_values(
                        by='Active_Probability', ascending=False
                    ),
                    use_container_width=True
                )

            except Exception as e:
                st.error("Error during prediction. The features might not match the model.")
                st.error(f"Details: {e}")
        
        elif selected_user != 'Overall':
            st.warning("User Activity Prediction is only available for the 'Overall' view.")
            
        else:
            st.error("Could not generate feature table for prediction.")