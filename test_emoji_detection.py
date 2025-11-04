"""
Test script for emoji detection functionality.
Tests the robust emoji detection across different emoji package versions.
"""

import sys
import pandas as pd
from helper import is_emoji_robust, extract_emojis_from_text, emoji_helper

def test_emoji_detection():
    """Test basic emoji detection with common emojis"""
    print("=" * 60)
    print("Testing Emoji Detection")
    print("=" * 60)
    
    # Test cases with various emojis
    test_emojis = [
        '😀',  # Grinning Face
        '❤️',  # Red Heart
        '👍',  # Thumbs Up
        '🎉',  # Party Popper
        '🔥',  # Fire
        '💯',  # Hundred Points
        '😂',  # Face with Tears of Joy
        '🤔',  # Thinking Face
        '👀',  # Eyes
        '✅',  # Check Mark
    ]
    
    print("\n1. Testing individual emoji detection:")
    print("-" * 60)
    for emoji_char in test_emojis:
        result = is_emoji_robust(emoji_char)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - '{emoji_char}' detected: {result}")
    
    # Test non-emoji characters
    print("\n2. Testing non-emoji characters (should be False):")
    print("-" * 60)
    non_emojis = ['a', 'Z', '1', '!', ' ', '@']
    for char in non_emojis:
        result = is_emoji_robust(char)
        status = "✅ PASS" if not result else "❌ FAIL"
        print(f"{status} - '{char}' detected: {result}")
    
    # Test text extraction
    print("\n3. Testing emoji extraction from text:")
    print("-" * 60)
    test_texts = [
        "Hello 😀 world!",
        "I love this! ❤️👍",
        "Party time 🎉🎉🎉",
        "No emojis here",
        "Mixed: abc 😂 123 🔥 xyz",
        "Multiple: 😀😂🤣😊😍"
    ]
    
    for text in test_texts:
        emojis = extract_emojis_from_text(text)
        print(f"Text: {text}")
        print(f"  Emojis found: {emojis} (count: {len(emojis)})")
    
    print("\n4. Testing emoji_helper function with sample DataFrame:")
    print("-" * 60)
    
    # Create sample DataFrame
    sample_data = {
        'Sender': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob', 'Alice'],
        'Message': [
            'Hey! 😀 How are you?',
            'Great! 👍 Thanks for asking 😊',
            'Party tonight? 🎉🎉',
            'Sure! ❤️',
            'Awesome! 🔥🔥🔥',
            'See you there! 👀'
        ]
    }
    df = pd.DataFrame(sample_data)
    
    # Test for overall
    print("\nOverall emoji analysis:")
    result_df = emoji_helper('Overall', df)
    print(result_df.to_string(index=False))
    
    # Test for specific user
    print("\nEmoji analysis for Alice:")
    result_df = emoji_helper('Alice', df)
    print(result_df.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)

def test_emoji_package_info():
    """Display information about the emoji package"""
    import emoji
    print("\n" + "=" * 60)
    print("Emoji Package Information")
    print("=" * 60)
    
    print(f"Emoji package version: {emoji.__version__ if hasattr(emoji, '__version__') else 'Unknown'}")
    
    # Check available methods
    print("\nAvailable methods:")
    methods = ['is_emoji', 'EMOJI_DATA', 'UNICODE_EMOJI', 'emojize', 'demojize']
    for method in methods:
        has_method = hasattr(emoji, method)
        status = "✅" if has_method else "❌"
        print(f"  {status} emoji.{method}")
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    # Display package info first
    test_emoji_package_info()
    
    # Run tests
    try:
        test_emoji_detection()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
