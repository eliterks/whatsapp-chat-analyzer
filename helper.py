from urlextract import URLExtract
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji

extractor = URLExtract()  # Object for URL extraction


# =========================
# 📊 Basic Chat Statistics
# =========================
def fetch_stats(selected_user, df):
    df.columns = df.columns.str.strip()

    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    # Total messages
    num_messages = df.shape[0]

    # Total words
    words = []
    for message in df['Message']:
        words.extend(str(message).split())

    # Media messages
    num_media_messages = df[df['Message'] == '<Media omitted>'].shape[0]

    # Links shared
    links = []
    for message in df['Message']:
        links.extend(extractor.find_urls(str(message)))

    return num_messages, len(words), num_media_messages, len(links)


# =========================
# 👥 Most Busy Users
# =========================
def most_busy_users(df):
    x = df['Sender'].value_counts().head()

    percentage_df = (
        round(df['Sender'].value_counts() / df.shape[0] * 100, 2)
        .reset_index()
    )
    percentage_df.columns = ['Sender', 'Percentage']

    return x, percentage_df


# =========================
# ☁️ Word Cloud Generation
# =========================
def create_wordcloud(selected_user, df):
    import re

    # Load stop words safely
    try:
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = f.read().split()
    except FileNotFoundError:
        print("⚠️ Warning: stop_hinglish.txt not found. Proceeding without stop words.")
        stop_words = []

    # Filter by user
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    # Remove media messages
    temp = df[df['Message'] != '<Media omitted>'].copy()

    if temp.empty:
        print("⚠️ No messages available for WordCloud generation.")
        return None

    # Stop word removal function
    def remove_stop_words(message):
        y = []
        message_str = str(message)
        for word in message_str.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)

    temp.loc[:, 'Message'] = temp['Message'].apply(remove_stop_words)

    # Combine messages
    final_text = temp['Message'].str.cat(sep=" ").strip()
    final_text = re.sub(r'[^\u0000-\uFFFF]', '', final_text)  # remove unsupported chars

    if not final_text:
        print("⚠️ No valid words found to generate WordCloud.")
        return None

    # Generate WordCloud safely
    try:
        wcl = WordCloud(
            width=1200,
            height=800,
            background_color='white',
            font_path="D:/Whatsapp/NotoSansBengali-VariableFont_wdth,wght.ttf",  # ✅ Unicode font
            collocations=False,
            min_font_size=10
        )
        return wcl.generate(final_text)
    except ValueError:
        print("⚠️ WordCloud failed: no valid words found even after filtering.")
        return None


# =========================
# 🧾 Most Common Words
# =========================
def most_common_words(selected_user, df):
    try:
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = f.read()
    except FileNotFoundError:
        print("⚠️ stop_hinglish.txt not found. Proceeding without stop words.")
        stop_words = []

    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    temp = df[df['Message'] != '<Media omitted>']

    if temp.empty:
        return pd.DataFrame(columns=['Word', 'Frequency'])

    words = []
    for message in temp['Message']:
        message_str = str(message)
        for word in message_str.lower().split():
            if word not in stop_words:
                words.append(word)

    if not words:
        return pd.DataFrame(columns=['Word', 'Frequency'])

    most_common_df = pd.DataFrame(Counter(words).most_common(20), columns=['Word', 'Frequency'])
    return most_common_df


# =========================
# 😀 Emoji Analysis
# =========================
def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    emojis = []
    for message in df['Message']:
        for char in str(message):
            if emoji.is_emoji(char):
                emojis.append(char)

    if not emojis:
        return pd.DataFrame(columns=['Emoji', 'Count'])

    emoji_counts = Counter(emojis)
    emoji_df = pd.DataFrame(emoji_counts.most_common(10), columns=['Emoji', 'Count'])
    return emoji_df


# =========================
# 📆 Monthly Timeline
# =========================
def monthly_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    if df.empty:
        return pd.DataFrame(columns=['Year', 'Month_num', 'Month', 'Message', 'time'])

    timeline = df.groupby(['Year', 'Month_num', 'Month']).count()['Message'].reset_index()
    timeline['time'] = [f"{m}-{y}" for m, y in zip(timeline['Month'], timeline['Year'])]
    return timeline


# =========================
# 🗓️ Daily Timeline
# =========================
def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    if df.empty:
        return pd.DataFrame(columns=['only_date', 'Message'])

    return df.groupby('only_date').count()['Message'].reset_index()


# =========================
# 🗺️ Activity Maps
# =========================
def week_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    if df.empty:
        return pd.Series(dtype='int64')

    return df['DayName'].value_counts()


def month_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    if df.empty:
        return pd.Series(dtype='int64')

    return df['Month'].value_counts()


# =========================
# 🔥 Activity Heatmap
# =========================
def activity_heatmap(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    if df.empty or 'Period' not in df.columns:
        print("⚠️ Warning: 'Period' column not found for heatmap.")
        return pd.DataFrame()

    period_order = [
        "00-1", "1-2", "2-3", "3-4", "4-5", "5-6", "6-7", "7-8", "8-9", "9-10",
        "10-11", "11-12", "12-13", "13-14", "14-15", "15-16", "16-17",
        "17-18", "18-19", "19-20", "20-21", "21-22", "22-23", "23-00"
    ]

    try:
        pivot_table = (
            df.pivot_table(index='DayName', columns='Period', values='Message', aggfunc='count')
            .fillna(0)
            .reindex(columns=period_order, fill_value=0)
        )
        return pivot_table
    except Exception as e:
        print(f"⚠️ Error occurred while generating heatmap: {e}")
        return pd.DataFrame()
