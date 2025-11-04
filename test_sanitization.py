# Test the sanitization function
from export_sentiment_helper import sanitize_for_excel

problematic_text = 'POLL: what is your dell scholarship status.. 😅 ? OPTION: After giving online interview , we got a email from the dell foundation team for offline interview. (11 votes) OPTION: Nope , can\'t got email for offline interview whether already given online interview... 😌 (5 votes) OPTION: neither got message for online interview nor for offline interview.. 😢 (22 votes) OPTION: can\'t fill for dell aspire program.. 🥲 (7 votes)'

print('Original text:')
print(repr(problematic_text))
print()

sanitized = sanitize_for_excel(problematic_text)
print('Sanitized text:')
print(repr(sanitized))
print()

print('Are they the same?', problematic_text == sanitized)

# Check for invisible characters
print('Invisible/problematic characters in original:')
for i, char in enumerate(problematic_text):
    code = ord(char)
    if code < 32 or (code >= 127 and code < 160) or code in [8206, 8207, 8234, 8235, 8236, 8237, 8238, 8296, 8297, 65279, 65520, 65521, 65522, 65523, 65524, 65525, 65526, 65527, 65528, 65529]:
        print(f'  Position {i}: {repr(char)} (U+{code:04X})')