from urlextract import URLExtract
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
extractor = URLExtract() #creating object of URLExtract
def fetch_stats(selected_user,df):
    df.columns = df.columns.str.strip()
    #fetch total no of messages
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]
    num_messages = df.shape[0]
    #fetch total no of words
    words = []
    for message in df['Message']:
        words.extend(message.split())
    #fetch no of media sent
    num_media_messages= df[df['Message'] == '<Media omitted>'].shape[0]
    # no of links shared
    links = []
    for message in df['Message']:
        links.extend(extractor.find_urls(message))

    return num_messages,len(words),num_media_messages,len(links)
def most_busy_users(df):
    x = df['Sender'].value_counts().head()
    df= round(df['Sender'].value_counts()/df.shape[0] *100,2).reset_index().rename(columns={'count':'Percentage'})
    return x,df
#WordCloud
def create_wordcloud(selected_user,df):
    f = open('stop_hinglish.txt', 'r')
    stop_words = f.read()
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]
    #remove media messages only for wordcloud
    temp = df[df['Message'] != '<Media omitted>'] #isse media omitted sirf delete wordcloud ke liye hoga
    def remove_stop_words(message):
        y=[]
        for word in message.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)
    wcl = WordCloud(width = 500, height = 500,
                    background_color ='white',
                    min_font_size = 10)
    temp['Message']=temp['Message'].apply(remove_stop_words)
    df_wcl=wcl.generate(temp['Message'].str.cat(sep=" "))
    return df_wcl

def most_common_words(selected_user,df):

    f=open('stop_hinglish.txt','r')
    stop_words=f.read()
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]
    temp = df[df['Message'] != '<Media omitted>']
    words=[]
    for message in temp['Message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)

    most_common_df= pd.DataFrame(Counter(words).most_common(20),columns=['Word','Frequency'])
    return most_common_df

#emoji analysis
def emoji_helper(selected_user,df):
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]

    emojis = []

    for message in df['Message']:
        for char in message:
            if emoji.is_emoji(char):
                emojis.append(char)

    emoji_counts = Counter(emojis)
    emoji_df = pd.DataFrame(emoji_counts.most_common(10), columns=['Emoji', 'Count'])

    return emoji_df

#monthly_timeline
def monthly_timeline(selected_user,df):
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]
    timeline = df.groupby(['Year', 'Month_num', 'Month']).count()['Message'].reset_index()
    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['Month'][i] + "-" + str(timeline['Year'][i]))

    timeline['time'] = time
    return timeline

#daily_timeline
def daily_timeline(selected_user,df):
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]

    daily_timeline = df.groupby('only_date').count()['Message'].reset_index()

    return daily_timeline

def week_activity_map(selected_user,df):
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]

    return df['DayName'].value_counts()

def month_activity_map(selected_user,df):
    if selected_user!='Overall':
        df= df[df['Sender']== selected_user]
    return df['Month'].value_counts()

def activity_heatmap(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]
    period_order = [
        "00-1", "1-2", "2-3", "3-4", "4-5", "5-6", "6-7", "7-8", "8-9", "9-10",
        "10-11", "11-12", "12-13", "13-14", "14-15", "15-16", "16-17", "17-18", "18-19", "19-20",
        "20-21", "21-22", "22-23", "23-00"
    ]
    pivot_table = df.pivot_table(index='DayName', columns='Period', values='Message', aggfunc='count').fillna(0)
    # Add missing columns with 0s
    for period in period_order:
        if period not in pivot_table.columns:
            pivot_table[period] = 0
    pivot_table = pivot_table[period_order]
    return pivot_table



