import pandas as pd
from export_sentiment_helper import sanitize_for_excel

# Create test DataFrame similar to sentiment_df
test_data = {
    'Sender': ['Alice', 'Bob'],
    'Message': [
        'Hello',
        'POLL:\nwhat is your dell scholarship status.. 😅 ?\nOPTION: After giving  online interview , we got a email from the dell foundation team for offline interview. (11 votes)\nOPTION: Nope , can\'t got email for  offline interview whether already given online interview... 😌 (5 votes)\nOPTION: neither got message for online interview nor for offline interview.. 😢 (22 votes)\nOPTION: can\'t fill for dell aspire program.. 🥲 (7 votes)'
    ],
    'Polarity': [0.1, -0.2],
    'Sentiment': ['Positive', 'Negative']
}

df = pd.DataFrame(test_data)
print('Original DataFrame:')
print(df)
print()

# Apply sanitization like the export function does
df_clean = df.copy()
for col in df_clean.columns:
    if df_clean[col].dtype == 'object':
        df_clean[col] = df_clean[col].apply(lambda x: sanitize_for_excel(x) if isinstance(x, str) else x)

print('Sanitized DataFrame:')
print(df_clean)
print()

# Try to save to Excel
try:
    with pd.ExcelWriter('test.xlsx', engine='openpyxl') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Messages')
    print('Excel export successful!')
except Exception as e:
    print(f'Excel export failed: {e}')