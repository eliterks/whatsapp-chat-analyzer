import streamlit as st  # <-- Includes import
# Python
import re
from datetime import datetime
import pandas as pd


# Shared header (date, time, optional AM/PM, dash or en-dash)
HEADER_PATTERN = r"""
^
(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s
(?P<time>\d{1,2}:\d{2})
(?:\s*[^\x00-\x7F]*?(?P<ampm>[AaPp][Mm]))?   # tolerate Unicode spaces/marks; AM/PM optional
\s[-–]\s
"""

HEADER_RE = re.compile(HEADER_PATTERN, re.VERBOSE | re.MULTILINE)
USER_LINE_RE = re.compile(r"^(?P<user>[^:]+):\s(?P<message>.*)", re.DOTALL)


def _parse_date_iso(date_str: str) -> str | None:
    """Parse date in dd/mm/yy or mm/dd/yy to ISO string; return None on failure."""

    # --- BUG FIX IS HERE: Checks for both date formats ---
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%m/%d/%y", "%m/%d/%Y"):
    # --- END OF BUG FIX ---
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _parse_times(time_part: str, ampm: str | None) -> tuple[str | None, str | None]:
    """
    Return (time_12hr_str, time_24hr_dt)
    """
    if ampm:  # 12-hour format
        try:
            time_12hr = f"{time_part} {ampm.upper()}"
            # Use datetime.strptime to parse time, then get the time part
            time_24hr_dt = datetime.strptime(time_12hr, "%I:%M %p")
            time_24hr_str = time_24hr_dt.strftime("%H:%M") # Store as string H:M
            return time_12hr, time_24hr_str # Return string H:M
        except ValueError:
            return None, None  # Invalid 12-hr time
    else:  # 24-hour format
        try:
            # Use datetime.strptime to parse time, then get the time part
            time_24hr_dt = datetime.strptime(time_part, "%H:%M")
            # Generate 12hr format string if needed, or return None
            time_12hr_str = time_24hr_dt.strftime("%I:%M %p")
            time_24hr_str = time_24hr_dt.strftime("%H:%M") # Store as string H:M
            return time_12hr_str, time_24hr_str # Return string H:M
        except ValueError:
            return None, None  # Invalid 24-hr time


@st.cache_data  # <-- Includes cache fix
def preprocess(data: str) -> pd.DataFrame:
    """
    Parse a WhatsApp chat export file into a Pandas DataFrame.
    """
    parsed_lines = []

    # Split the file into messages
    messages = HEADER_RE.split(data)

    if not messages or len(messages) < 2:
        # If no messages, return an empty DataFrame
        return pd.DataFrame()

    # The first split part is just header, ignore it
    for i in range(1, len(messages), 5):
        try:
            # We get 5 groups: date, time, ampm, (header), message_block
            date_str = messages[i]
            time_str = messages[i+1]
            ampm_str = messages[i+2]
            message_block = messages[i+4]

            # Parse date and time
            iso_date = _parse_date_iso(date_str)
            time_12hr, time_24hr = _parse_times(time_str, ampm_str)

            if iso_date is None or time_24hr is None:
                continue # Skip bad date/time

            # Split message block into user and message
            user_line_match = USER_LINE_RE.match(message_block)

            if user_line_match:
                # It's a user message
                user = user_line_match.group("user").strip()
                message = user_line_match.group("message").strip()
            else:
                # It's a system message
                user = "System"
                message = message_block.strip()

            parsed_lines.append(
                {
                    "Date": iso_date,
                    "Time (AM/PM)": time_12hr,
                    "Time (24hr)": time_24hr, # Keep as string H:M
                    "Sender": user,
                    "Message": message,
                }
            )
        except IndexError:
            # Reached end of messages list
            continue
        except Exception as e:
            # Other parsing error
            print(f"Error parsing block: {e}")
            continue

    # Create DataFrame
    df = pd.DataFrame(parsed_lines)

    if df.empty:
        # If no lines were parsed, return empty
        return pd.DataFrame()

    # Clean up empty messages
    df = df[df["Message"].str.strip().fillna("").ne("")]

    # Enrich fields
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month_name()
        df["Day"] = df["Date"].dt.day
        # Convert time string to datetime.time before accessing dt properties
        # Handle potential errors during conversion
        time_as_datetime = pd.to_datetime(df['Time (24hr)'], format='%H:%M', errors='coerce')

        # Drop rows where time conversion failed (NaN in time_as_datetime)
        df = df[time_as_datetime.notna()]
        time_as_datetime = time_as_datetime.dropna() # Remove NaT for safe dt access

        # Safely access dt properties now using the valid datetime objects
        df['Hour'] = time_as_datetime.dt.hour
        df['Minute'] = time_as_datetime.dt.minute

        df.loc[:, "DayName"] = df["Date"].dt.day_name()
        df.loc[:, "Month_num"] = df["Date"].dt.month
        df.loc[:, "only_date"] = df["Date"].dt.date

        # Domain-specific filters
        df = df[df["Message"] != "POLL:"]
        df = df[df["Message"] != "This message was deleted"]

        # Period label
        period = []
        # Use .loc to iterate safely after potential row drops
        for hour in df.loc[time_as_datetime.index, "Hour"]:
            if hour == 23:
                period.append(f"{hour}-00")
            elif hour == 0:
                period.append("00-1")
            else:
                period.append(f"{hour}-{hour+1}")
        df = df.copy()
        # Use .loc to assign safely after potential row drops
        df.loc[time_as_datetime.index, "Period"] = period
    else:
        # If empty, make sure all expected columns exist
        df = pd.DataFrame(
            columns=[
                "Date", "Time (AM/PM)", "Time (24hr)", "Sender", "Message",
                "Year", "Month", "Day", "Hour", "Minute", "DayName",
                "Month_num", "only_date", "Period"
            ]
        )
    return df
