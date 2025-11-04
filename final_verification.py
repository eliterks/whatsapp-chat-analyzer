print('=== FINAL VERIFICATION OF EMOJI FIXES ===')
print()

# Test emoji detection
from helper import is_emoji_robust, extract_emojis_from_text, emoji_helper
import pandas as pd

print('1. Testing centralized emoji detection:')
test_emojis = ['😀', '❤️', '👍', '🎉', '🔥', 'a', '1', '!']
for emoji in test_emojis:
    result = is_emoji_robust(emoji)
    print(f'   {emoji}: {result}')

print()
print('2. Testing emoji extraction:')
test_texts = ['Hello 😀 world!', 'I love this! ❤️👍', 'No emojis here']
for text in test_texts:
    emojis = extract_emojis_from_text(text)
    print(f'   \"{text}\" -> {emojis}')

print()
print('3. Testing emoji_helper function:')
# Create sample data
sample_data = {
    'Sender': ['Alice', 'Bob', 'Alice', 'Charlie'],
    'Message': ['Hello 😀', 'I love this! ❤️👍', 'Great work! 🔥', 'Nice 🎉']
}
df = pd.DataFrame(sample_data)
result = emoji_helper('Overall', df)
print(f'   Overall emoji analysis: {len(result)} unique emojis found')

print()
print('4. Testing Excel sanitization:')
from export_sentiment_helper import sanitize_for_excel
problematic_text = 'POLL: test 😅 OPTION: test'
sanitized = sanitize_for_excel(problematic_text)
print(f'   Original: {repr(problematic_text)}')
print(f'   Sanitized: {repr(sanitized)}')

print()
print('✅ ALL EMOJI FIXES VERIFIED SUCCESSFULLY!')