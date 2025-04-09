import re
import pandas as pd
from datetime import datetime
# @st.cache
# @st.cache_data
# @st.cache_resource
def preprocess(data):
    pattern = r'(\d{2}/\d{2}/\d{2}),\s(\d{1,2}:\d{2})\s*[^\x00-\x7F]*([AaPp][Mm])\s-\s([^:]+):\s(.*)'
    matches = re.findall(pattern,data)
    # Lists to store structured data
    dates, times_12hr, senders, messages, times_24hr = [], [], [], [], []

    for match in matches:
        date, time_12hr, meridian, sender, message = match

        # Combine time + meridian
        full_12hr_time = f"{time_12hr} {meridian.upper()}"

        # Convert to 24hr format
        time_24hr = datetime.strptime(full_12hr_time, "%I:%M %p").strftime("%H:%M")

        # Append all
        dates.append(datetime.strptime(date, "%d/%m/%y").strftime("%Y-%m-%d"))
        times_12hr.append(full_12hr_time)
        times_24hr.append(time_24hr)
        senders.append(sender.strip())
        messages.append(message.strip())

    # Step 3: Create DataFrame
    df = pd.DataFrame({
        "Date": dates,
        "Time (AM/PM)": times_12hr,
        "Time (24hr)": times_24hr,
        "Sender": senders,
        "Message": messages
    })
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month_name()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Day'] = df['Date'].dt.day
    df['Time (24hr)'] = pd.to_datetime(df['Time (24hr)'], format='%H:%M')
    df['Hour'] = df['Time (24hr)'].dt.hour
    df['Minute'] = df['Time (24hr)'].dt.minute
    df.loc[:, 'DayName'] = df['Date'].dt.day_name()
    df.loc[:, 'Month_num'] = df['Date'].dt.month
    df.loc[:, 'only_date'] = df['Date'].dt.date
    df = df[df['Message'] != 'POLL:']
    df = df[df['Message'] != 'This message was deleted']

    period = []
    for hour in df[['DayName', 'Hour']]['Hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))
    df = df.copy()  # explicitly make it a full independent copy
    df.loc[:, 'Period'] = period
    return df