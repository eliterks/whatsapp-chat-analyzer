from helper import extract_emojis_from_text

# Test with the problematic POLL text
problematic_text = 'POLL: what is your dell scholarship status.. 😅 ? OPTION: After giving online interview , we got a email from the dell foundation team for offline interview. (11 votes) OPTION: Nope , can\'t got email for offline interview whether already given online interview... 😌 (5 votes) OPTION: neither got message for online interview nor for offline interview.. 😢 (22 votes) OPTION: can\'t fill for dell aspire program.. 🥲 (7 votes)'

print('Original text contains characters with ord > 127:')
for i, char in enumerate(problematic_text):
    if ord(char) > 127:
        print(f'  {i}: {repr(char)} (U+{ord(char):04X})')

print()
print('Extracted emojis:')
emojis = extract_emojis_from_text(problematic_text)
print(f'Found {len(emojis)} emojis: {emojis}')

print()
print('Testing sanitization:')
from export_sentiment_helper import sanitize_for_excel
sanitized = sanitize_for_excel(problematic_text)
print(f'Original length: {len(problematic_text)}')
print(f'Sanitized length: {len(sanitized)}')
print(f'Sanitized text: {repr(sanitized)}')