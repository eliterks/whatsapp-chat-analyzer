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
    """Parse date in dd/mm/yy or dd/mm/yyyy to ISO string; return None on failure."""
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _parse_times(time_part: str, ampm: str | None) -> tuple[str | None, str | None]:
    """
    Return (time_12hr_str, time_24hr_str) or (None, None) if parsing fails.
    - If AM/PM present, parse as 12h, also derive 24h.
    - If AM/PM absent, assume 24h, also derive 12h.
    """
    try:
        if ampm:
            full_12 = f"{time_part} {ampm.upper()}"
            dt = datetime.strptime(full_12, "%I:%M %p")
            return dt.strftime("%I:%M %p"), dt.strftime("%H:%M")
        else:
            dt = datetime.strptime(time_part, "%H:%M")
            return dt.strftime("%I:%M %p"), dt.strftime("%H:%M")
    except ValueError:
        return None, None


def preprocess(data: str) -> pd.DataFrame:
    # Find the start of each message/system entry by locating header occurrences
    starts = [m.start() for m in HEADER_RE.finditer(data)]
    if not starts:
        # Return an empty DataFrame with expected columns if nothing matches
        return pd.DataFrame(
            columns=[
                "Date", "Time (AM/PM)", "Time (24hr)", "Sender", "Message",
                "Year", "Month", "Day", "Hour", "Minute", "DayName",
                "Month_num", "only_date", "Period"
            ]
        )

    starts.append(len(data))  # sentinel for slicing the last chunk

    rows = []
    for s, e in zip(starts[:-1], starts[1:]):
        chunk = data[s:e].rstrip("\n")

        # Extract header fields from the chunk start
        m = HEADER_RE.match(chunk)
        if not m:
            continue  # safety

        date_str = m.group("date")
        time_str = m.group("time")
        ampm = m.group("ampm")

        # Remaining content (may be multiline)
        content = chunk[m.end():].strip()

        # Classify as user or system
        user_m = USER_LINE_RE.match(content)
        if user_m:
            sender = user_m.group("user").strip()
            message = user_m.group("message").strip()
        else:
            sender = "System"
            message = content

        # Parse date/time
        iso_date = _parse_date_iso(date_str)
        time_12, time_24 = _parse_times(time_str, ampm)

        if not iso_date or not time_24:
            # Skip rows with unparseable date/time
            continue

        rows.append(
            {
                "Date": iso_date,
                "Time (AM/PM)": time_12,
                "Time (24hr)": time_24,
                "Sender": sender,
                "Message": message,
            }
        )

    df = pd.DataFrame(rows)

    # Ensure consistent dtypes before string ops
    if "Message" in df.columns:
        df["Message"] = df["Message"].astype("string")
    if "Sender" in df.columns:
        df["Sender"] = df["Sender"].astype("string")

    # Parse dates/times safely
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Time (24hr)"] = pd.to_datetime(df["Time (24hr)"], format="%H:%M", errors="coerce")

    # Drop rows with invalid date/time
    df = df[df["Date"].notna() & df["Time (24hr)"].notna()]

    # Remove null/blank messages safely
    if not df.empty:
        df = df[df["Message"].str.strip().fillna("").ne("")]

    # Enrich fields
    if not df.empty:
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month_name()
        df["Day"] = df["Date"].dt.day
        df["Hour"] = df["Time (24hr)"].dt.hour
        df["Minute"] = df["Time (24hr)"].dt.minute
        df.loc[:, "DayName"] = df["Date"].dt.day_name()
        df.loc[:, "Month_num"] = df["Date"].dt.month
        df.loc[:, "only_date"] = df["Date"].dt.date

        # Domain-specific filters
        df = df[df["Message"] != "POLL:"]
        df = df[df["Message"] != "This message was deleted"]

        # Period label
        period = []
        for hour in df["Hour"]:
            if hour == 23:
                period.append(f"{hour}-00")
            elif hour == 0:
                period.append("00-1")
            else:
                period.append(f"{hour}-{hour+1}")
        df = df.copy()
        df.loc[:, "Period"] = period
    else:
        # If empty, make sure all expected columns exist
        df = pd.DataFrame(
            columns=[
                "Date", "Time (AM/PM)", "Time (24hr)", "Sender", "Message",
                "Year", "Month", "Day", "Hour", "Minute", "DayName",
                "Month_num", "only_date", "Period"
            ]
        ).astype(
            {
                "Message": "string",
                "Sender": "string",
                "Period": "string",
            }
        )

    return df