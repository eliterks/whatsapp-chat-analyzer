import pandas as pd
import export_sentiment_helper

# Create test data similar to what causes the error
test_data = {
    'Sender': ['Alice', 'Bob', 'Charlie'],
    'Message': [
        'Hello world',
        'POLL: what is your dell scholarship status.. 😅 ? OPTION: After giving online interview , we got a email from the dell foundation team for offline interview. (11 votes) OPTION: Nope , can\'t got email for offline interview whether already given online interview... 😌 (5 votes) OPTION: neither got message for online interview nor for offline interview.. 😢 (22 votes) OPTION: can\'t fill for dell aspire program.. 🥲 (7 votes)',
        'Another message'
    ],
    'Polarity': [0.1, -0.2, 0.3],
    'Sentiment': ['Positive', 'Negative', 'Positive']
}

sentiment_df = pd.DataFrame(test_data)
sentiment_summary = {'positive': 2, 'neutral': 0, 'negative': 1, 'avg_sentiment': 0.067}

print('Testing Excel export with problematic data...')
try:
    excel_data = export_sentiment_helper.export_sentiment_excel(sentiment_summary, sentiment_df)
    print('✅ Excel export succeeded!')
except Exception as e:
    print(f'❌ Excel export failed: {e}')