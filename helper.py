from urlextract import URLExtract
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re

extractor = URLExtract()  # Object for URL extraction
from pyvis.network import Network
import tempfile
import os


# =========================
# 😀 Centralized Emoji Detection
# =========================
def is_emoji_robust(character):
    """
    Robust emoji detection function that tries multiple methods
    to ensure compatibility across different emoji package versions.
    
    Args:
        character: Single character to check
        
    Returns:
        bool: True if character is an emoji, False otherwise
    """
    if not character:
        return False
    
    # Method 1: Try emoji.is_emoji() (available in emoji >= 2.0.0)
    try:
        if hasattr(emoji, 'is_emoji') and callable(emoji.is_emoji):
            if emoji.is_emoji(character):
                return True
    except Exception:
        pass
    
    # Method 2: Try checking in emoji.EMOJI_DATA (available in emoji >= 2.0.0)
    try:
        if hasattr(emoji, 'EMOJI_DATA') and character in emoji.EMOJI_DATA:
            return True
    except Exception:
        pass
    
    # Method 3: Try legacy emoji.UNICODE_EMOJI (for emoji < 2.0.0)
    try:
        if hasattr(emoji, 'UNICODE_EMOJI'):
            # UNICODE_EMOJI might be a dict with language keys
            if isinstance(emoji.UNICODE_EMOJI, dict):
                # Try common language keys
                for lang in ['en', 'es', 'pt', 'it', 'fr', 'de']:
                    if lang in emoji.UNICODE_EMOJI and character in emoji.UNICODE_EMOJI[lang]:
                        return True
            # Or it might be flat dict in older versions
            elif character in emoji.UNICODE_EMOJI:
                return True
    except Exception:
        pass
    
    # Method 4: Unicode range check as final fallback
    # Common emoji ranges in Unicode
    try:
        code_point = ord(character)
        # Basic Emoticons, Dingbats, Misc Symbols, Transport, etc.
        emoji_ranges = [
            (0x1F300, 0x1F9FF),  # Miscellaneous Symbols and Pictographs, Emoticons, etc.
            (0x2600, 0x26FF),    # Miscellaneous Symbols
            (0x2700, 0x27BF),    # Dingbats
            (0x1F600, 0x1F64F),  # Emoticons
            (0x1F680, 0x1F6FF),  # Transport and Map Symbols
            (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
            (0x1FA00, 0x1FA6F),  # Chess Symbols, etc.
            (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
            (0x2300, 0x23FF),    # Miscellaneous Technical
            (0x2B50, 0x2B50),    # Star
            (0x203C, 0x3299),    # Various symbols
        ]
        for start, end in emoji_ranges:
            if start <= code_point <= end:
                return True
    except Exception:
        pass
    
    return False


def extract_emojis_from_text(text):
    """
    Extract all emojis from a text string using robust detection.
    Filters out Unicode control characters that can cause display issues.
    
    Args:
        text: Text string to extract emojis from
        
    Returns:
        list: List of emoji characters found in the text
    """
    if not isinstance(text, str):
        return []
    
    # First, clean the text of problematic Unicode control characters
    # that can interfere with emoji display
    cleaned_text = re.sub(r'[\u200B-\u200D\uFEFF\uFE00-\uFE0F\u200E\u200F\u202A-\u202E\u2066-\u2069]', '', text)
    
    emojis = []
    for char in cleaned_text:
        if is_emoji_robust(char):
            emojis.append(char)
    
    return emojis

def create_interaction_graph(selected_user, df, dynamic=True):
    """
    Build an interactive PyVis network of user interactions.
    Each node = user; edge = frequency of interaction.
    Thicker edges mean stronger message connections.
    """
    if 'Sender' not in df.columns or len(df) < 5:
        return None

    if selected_user != "Overall":
        df = df[df['Sender'] == selected_user]

    df = df.reset_index(drop=True)

    # 🧮 Count consecutive sender pairs
    interactions = {}
    for i in range(1, len(df)):
        s1, s2 = df.loc[i - 1, "Sender"], df.loc[i, "Sender"]
        if s1 != s2:
            key = tuple(sorted([s1, s2]))
            interactions[key] = interactions.get(key, 0) + 1

    if not interactions:
        return None

    # 🎨 Create PyVis network
    net = Network(height="700px", width="100%", bgcolor="#0a0a0a", font_color="white", directed=False, notebook=False)

    # ✨ Physics (controls movement and layout)
    physics_options = """
    const options = {
      "physics": {
        "enabled": %s,
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.008,
          "springLength": 180,
          "springConstant": 0.06,
          "avoidOverlap": 0.5
        },
        "maxVelocity": 30,
        "solver": "forceAtlas2Based",
        "timestep": 0.3
      },
      "edges": {
        "smooth": {"type": "dynamic"},
        "color": {"inherit": false},
        "width": 1
      },
      "interaction": {
        "hover": true,
        "zoomView": true,
        "dragNodes": true,
        "navigationButtons": true
      }
    }
    """ % ("true" if dynamic else "false")

    net.set_options(physics_options)

    # 🧩 Add user nodes
    unique_users = df["Sender"].unique().tolist()
    msg_counts = {u: df[df["Sender"] == u].shape[0] for u in unique_users}
    for user in unique_users:
        color = f"hsl({hash(user) % 360}, 70%, 60%)"
        size = 15 + (msg_counts[user] ** 0.5) * 3
        net.add_node(
            user,
            label=user,
            color=color,
            size=size,
            title=f"{user}: {msg_counts[user]} messages"
        )

    # 🔗 Add edges (based on frequency)
    max_count = max(interactions.values())
    for (u1, u2), count in interactions.items():
        width = 1 + (count / max_count) * 8
        hue = int(360 * (count / max_count))
        edge_color = f"hsl({hue}, 90%, 60%)"
        net.add_edge(
            u1, u2,
            value=count,
            title=f"{u1} ↔ {u2}: {count} messages",
            color=edge_color,
            width=width
        )

    # ⚙️ Do NOT use show_buttons (it’s bugged in latest pyvis)
    # net.show_buttons(filter_=["physics"])  # ❌ removed

    # ✅ Generate HTML output safely
    try:
        html_content = net.generate_html()
    except Exception:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.write_html(tmp.name)
            tmp_path = tmp.name
        with open(tmp_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        os.remove(tmp_path)

    # Add optional smooth rotation if dynamic=True
        if dynamic:
            html_content += """
            <script type="text/javascript">
                const container = document.querySelector('#mynetwork');
                const options = {
                    interaction: { zoomView: false, dragView: false },
                    physics: false
                };
                const network = new vis.Network(container, {nodes: nodes, edges: edges}, options);

                // --- Lock initial view ---
                network.moveTo({
                scale: 1.0,
                position: {x: 0, y: 0},
                animation: {duration: 0}
                });

                // --- Create smooth 3D-like rotation effect ---
                let angle = 0;
                const radius = 600;
                setInterval(() => {
                    angle += 0.0025;
                    const x = Math.cos(angle) * radius;
                    const y = Math.sin(angle) * radius;
                    network.moveTo({
                        position: {x: x, y: y},
                        scale: 1.0,
                        animation: {duration: 80, easingFunction: 'linear'}
                    });
                }, 80);

                // Prevent user scroll or zoom events completely
                container.addEventListener('wheel', e => e.preventDefault(), { passive: false });
            </script>
            """


    return html_content


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

    # Stop word removal
    def remove_stop_words(message):
        words = []
        for word in str(message).lower().split():
            if word not in stop_words:
                words.append(word)
        return " ".join(words)

    temp['Message'] = temp['Message'].apply(remove_stop_words)

    # Combine all messages
    final_text = temp['Message'].str.cat(sep=" ").strip()
    # Keep only English letters, numbers, and spaces
    final_text = re.sub(r'[^A-Za-z0-9\s]', '', final_text)


    if not final_text:
        print("⚠️ No valid words found to generate WordCloud.")
        return None

    # Generate WordCloud with default font (no boxes, cross-platform)
    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white'
        ).generate(final_text)
    except Exception as e:
        print(f"⚠️ Error generating WordCloud: {e}")
        return None

    return wordcloud


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
    """
    Extract and count emojis from messages using robust detection.
    Returns a DataFrame with top 10 most used emojis.
    """
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    emojis = []
    for message in df['Message']:
        # Use robust emoji extraction
        emojis.extend(extract_emojis_from_text(str(message)))

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

# =========================
# 😊 Emoji Usage Bar Chart
# =========================
def create_emoji_bar_chart(selected_user, df):
    """
    Create and display emoji bar chart in Streamlit using robust emoji detection.
    """
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    import streamlit as st
    from collections import Counter
    import matplotlib.font_manager as fm
    import os
    import platform

    # Filter by user if not Overall
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    # Extract emojis using robust detection
    all_emojis = []
    for msg in df['Message']:
        all_emojis.extend(extract_emojis_from_text(msg))

    if not all_emojis:
        st.warning("No emojis detected 😅")
        return

    emoji_counts = Counter(all_emojis).most_common(10)
    emoji_df = pd.DataFrame(emoji_counts, columns=['emoji', 'count'])

    # --- Setup emoji-compatible font ---
    emoji_font = None
    try:
        system = platform.system()
        if system == 'Windows':
            # Try multiple Windows emoji fonts
            font_paths = [
                "C:\\Windows\\Fonts\\seguiemj.ttf",  # Segoe UI Emoji
                "C:\\Windows\\Fonts\\seguisym.ttf",  # Segoe UI Symbol
            ]
        elif system == 'Darwin':  # macOS
            font_paths = [
                "/System/Library/Fonts/Apple Color Emoji.ttc",
                "/System/Library/Fonts/Apple Symbols.ttf",
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                emoji_font = fm.FontProperties(fname=font_path)
                break
    except Exception:
        pass

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Use a style that works well with emojis
    plt.style.use('default')
    
    sns.barplot(data=emoji_df, x='emoji', y='count', palette='viridis', ax=ax)

    # Configure emoji display on x-axis
    if emoji_font is not None:
        # Use the emoji font for x-axis labels
        ax.set_xticklabels(emoji_df['emoji'], fontproperties=emoji_font, fontsize=24)
    else:
        # Fallback: try to use a font that might support emojis
        try:
            # Try to find any font that might support emojis
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            emoji_friendly_fonts = ['DejaVu Sans', 'Arial Unicode MS', 'Segoe UI', 'Apple Color Emoji']
            for font_name in emoji_friendly_fonts:
                if font_name in available_fonts:
                    ax.set_xticklabels(emoji_df['emoji'], fontname=font_name, fontsize=24)
                    break
            else:
                # Last resort: use default but larger
                ax.set_xticklabels(emoji_df['emoji'], fontsize=24)
        except:
            ax.set_xticklabels(emoji_df['emoji'], fontsize=24)
    
    ax.set_title("Top 10 Emojis Used", fontsize=14, weight='bold')
    ax.set_xlabel("Emoji", fontsize=12)
    ax.set_ylabel("Count", fontsize=12)
    
    # Remove tick marks (the small lines on axes)
    ax.tick_params(axis='x', which='both', length=0)  # Remove x-axis ticks
    ax.tick_params(axis='y', which='both', length=3)  # Keep y-axis ticks small
    
    plt.tight_layout()
    st.pyplot(fig)


# =========================
# 😊 Generate Emoji Bar Chart Figure (for PDF export)
# =========================
def generate_emoji_bar_chart_figure(selected_user, df):
    """
    Generate emoji bar chart figure without displaying it (for PDF export).
    Uses robust emoji detection for compatibility.
    """
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    from collections import Counter
    import matplotlib.font_manager as fm
    import os
    import platform

    # Filter by user if not Overall
    if selected_user != 'Overall':
        df = df[df['Sender'] == selected_user]

    # Extract emojis using robust detection
    all_emojis = []
    for msg in df['Message']:
        all_emojis.extend(extract_emojis_from_text(msg))

    if not all_emojis:
        return None  # No emojis found

    emoji_counts = Counter(all_emojis).most_common(10)
    emoji_df = pd.DataFrame(emoji_counts, columns=['emoji', 'count'])

    # --- Setup emoji-compatible font ---
    emoji_font = None
    try:
        system = platform.system()
        if system == 'Windows':
            # Try multiple Windows emoji fonts
            font_paths = [
                "C:\\Windows\\Fonts\\seguiemj.ttf",  # Segoe UI Emoji
                "C:\\Windows\\Fonts\\seguisym.ttf",  # Segoe UI Symbol
            ]
        elif system == 'Darwin':  # macOS
            font_paths = [
                "/System/Library/Fonts/Apple Color Emoji.ttc",
                "/System/Library/Fonts/Apple Symbols.ttf",
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                emoji_font = fm.FontProperties(fname=font_path)
                break
    except Exception:
        pass

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Use a style that works well with emojis
    plt.style.use('default')
    
    sns.barplot(data=emoji_df, x='emoji', y='count', palette='viridis', ax=ax)

    # Configure emoji display on x-axis
    if emoji_font is not None:
        # Use the emoji font for x-axis labels
        ax.set_xticklabels(emoji_df['emoji'], fontproperties=emoji_font, fontsize=24)
    else:
        # Fallback: try to use a font that might support emojis
        try:
            # Try to find any font that might support emojis
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            emoji_friendly_fonts = ['DejaVu Sans', 'Arial Unicode MS', 'Segoe UI', 'Apple Color Emoji']
            for font_name in emoji_friendly_fonts:
                if font_name in available_fonts:
                    ax.set_xticklabels(emoji_df['emoji'], fontname=font_name, fontsize=24)
                    break
            else:
                # Last resort: use default but larger
                ax.set_xticklabels(emoji_df['emoji'], fontsize=24)
        except:
            ax.set_xticklabels(emoji_df['emoji'], fontsize=24)
    
    ax.set_title("Top 10 Emojis Used", fontsize=14, weight='bold')
    ax.set_xlabel("Emoji", fontsize=12)
    ax.set_ylabel("Count", fontsize=12)
    
    # Remove tick marks (the small lines on axes)
    ax.tick_params(axis='x', which='both', length=0)  # Remove x-axis ticks
    ax.tick_params(axis='y', which='both', length=3)  # Keep y-axis ticks small
    
    plt.tight_layout()
    return fig