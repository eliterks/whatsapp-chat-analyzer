"""
Integration test to verify emoji functionality in the full app context.
Tests that all emoji-related functions work together correctly.
"""

import pandas as pd
import matplotlib.pyplot as plt
from helper import (
    is_emoji_robust, 
    extract_emojis_from_text, 
    emoji_helper,
    generate_emoji_bar_chart_figure
)

def test_integration():
    """Test the complete emoji workflow"""
    print("=" * 70)
    print("EMOJI FUNCTIONALITY INTEGRATION TEST")
    print("=" * 70)
    
    # Create realistic test data
    test_data = {
        'Sender': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob', 'Alice', 'Charlie', 'Bob'],
        'Message': [
            'Good morning! ☀️😀',
            'Hey! How are you? 👋',
            'I\'m great! Thanks for asking! 😊❤️',
            'Anyone up for pizza tonight? 🍕🍕',
            'Count me in! 🎉👍',
            'Yay! This will be fun! 🔥🔥🔥',
            'See you at 7pm! ⏰',
            'Can\'t wait! 😋🍕'
        ]
    }
    df = pd.DataFrame(test_data)
    
    print("\n1. Testing emoji_helper() function")
    print("-" * 70)
    
    # Test Overall analysis
    print("\n   a) Overall emoji analysis:")
    emoji_df = emoji_helper('Overall', df)
    if emoji_df.empty:
        print("      ❌ FAIL: No emojis detected")
        return False
    else:
        print(f"      ✅ PASS: {len(emoji_df)} unique emojis detected")
        print(f"         Top 3: {emoji_df.head(3)['Emoji'].tolist()}")
    
    # Test per-user analysis
    print("\n   b) Per-user emoji analysis (Alice):")
    alice_df = emoji_helper('Alice', df)
    if alice_df.empty:
        print("      ❌ FAIL: No emojis detected for Alice")
        return False
    else:
        print(f"      ✅ PASS: {len(alice_df)} unique emojis for Alice")
        print(f"         Emojis: {alice_df['Emoji'].tolist()}")
    
    print("\n2. Testing generate_emoji_bar_chart_figure() for PDF export")
    print("-" * 70)
    
    # Test figure generation
    fig = generate_emoji_bar_chart_figure('Overall', df)
    if fig is None:
        print("   ❌ FAIL: Figure generation returned None")
        return False
    else:
        print("   ✅ PASS: Figure generated successfully")
        print(f"      Figure size: {fig.get_size_inches()}")
        plt.close(fig)  # Clean up
    
    print("\n3. Testing edge cases")
    print("-" * 70)
    
    # Test with no emojis
    print("\n   a) DataFrame with no emojis:")
    no_emoji_data = {
        'Sender': ['User1', 'User2'],
        'Message': ['Hello', 'How are you']
    }
    no_emoji_df = pd.DataFrame(no_emoji_data)
    result = emoji_helper('Overall', no_emoji_df)
    if result.empty:
        print("      ✅ PASS: Correctly returns empty DataFrame")
    else:
        print("      ❌ FAIL: Should return empty DataFrame")
        return False
    
    # Test figure with no emojis
    fig = generate_emoji_bar_chart_figure('Overall', no_emoji_df)
    if fig is None:
        print("      ✅ PASS: Correctly returns None for empty data")
    else:
        print("      ❌ FAIL: Should return None for no emojis")
        plt.close(fig)
        return False
    
    # Test with user filter
    print("\n   b) Non-existent user:")
    result = emoji_helper('NonExistentUser', df)
    if result.empty:
        print("      ✅ PASS: Correctly returns empty DataFrame")
    else:
        print("      ❌ FAIL: Should return empty for non-existent user")
        return False
    
    print("\n4. Testing emoji extraction accuracy")
    print("-" * 70)
    
    # Test specific messages
    test_messages = [
        ("Hello 😀", ['😀'], 1),
        ("Multiple 😀😂🔥", ['😀', '😂', '🔥'], 3),
        ("No emojis here", [], 0),
        ("Mixed: abc 🎉 123", ['🎉'], 1),
    ]
    
    all_passed = True
    for text, expected_emojis, expected_count in test_messages:
        extracted = extract_emojis_from_text(text)
        if extracted == expected_emojis:
            print(f"   ✅ PASS: '{text}' -> {extracted}")
        else:
            print(f"   ❌ FAIL: '{text}'")
            print(f"      Expected: {expected_emojis}, Got: {extracted}")
            all_passed = False
    
    if not all_passed:
        return False
    
    print("\n5. Testing data consistency")
    print("-" * 70)
    
    # Verify DataFrame structure
    emoji_df = emoji_helper('Overall', df)
    required_columns = ['Emoji', 'Count']
    
    if list(emoji_df.columns) == required_columns:
        print(f"   ✅ PASS: DataFrame has correct columns: {required_columns}")
    else:
        print(f"   ❌ FAIL: Expected columns {required_columns}, got {list(emoji_df.columns)}")
        return False
    
    # Verify data types
    if emoji_df['Count'].dtype in ['int64', 'int32']:
        print("   ✅ PASS: Count column has correct data type")
    else:
        print(f"   ❌ FAIL: Count should be int, got {emoji_df['Count'].dtype}")
        return False
    
    # Verify sorting (should be by count descending)
    if len(emoji_df) > 1:
        is_sorted = all(emoji_df['Count'].iloc[i] >= emoji_df['Count'].iloc[i+1] 
                       for i in range(len(emoji_df)-1))
        if is_sorted:
            print("   ✅ PASS: Emojis are sorted by count (descending)")
        else:
            print("   ❌ FAIL: Emojis should be sorted by count")
            return False
    
    print("\n" + "=" * 70)
    print("INTEGRATION TEST COMPLETE - ALL TESTS PASSED ✅")
    print("=" * 70)
    return True

def test_special_emojis():
    """Test with special and compound emojis"""
    print("\n" + "=" * 70)
    print("SPECIAL EMOJI TEST")
    print("=" * 70)
    
    special_emojis = [
        ('👨‍👩‍👧‍👦', 'Family emoji'),  # Compound emoji with ZWJ
        ('🏳️‍🌈', 'Rainbow flag'),  # Flag with variation selector
        ('❤️', 'Red heart with variation selector'),
        ('⭐', 'Star'),
        ('✨', 'Sparkles'),
    ]
    
    print("\nTesting special emojis:")
    print("-" * 70)
    
    for emoji_char, description in special_emojis:
        detected = any(is_emoji_robust(c) for c in emoji_char)
        status = "✅" if detected else "⚠️"
        print(f"{status} {emoji_char} - {description}: {'Detected' if detected else 'Not detected'}")
    
    print("\nNote: Compound emojis may be detected as multiple separate emojis.")
    print("This is expected behavior for the current implementation.")
    print("=" * 70)

if __name__ == "__main__":
    try:
        # Run main integration test
        success = test_integration()
        
        # Run special emoji test (informational)
        test_special_emojis()
        
        if success:
            print("\n✅ ALL INTEGRATION TESTS PASSED!")
            exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR DURING TESTING: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
