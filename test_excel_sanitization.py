"""
Test the sanitization function for Excel exports.
"""

import sys
sys.path.insert(0, '.')

from export_sentiment_helper import sanitize_for_excel
import pandas as pd

def test_sanitization():
    """Test that illegal characters are removed"""
    print("=" * 70)
    print("EXCEL SANITIZATION TEST")
    print("=" * 70)
    
    # Test cases with problematic characters
    test_cases = [
        # (input, description)
        ("POLL: Normal text", "Normal text with colon"),
        ("OPTION: Text with emoji 😅", "Text with emoji"),
        ("Text with\x00null character", "Null character (0x00)"),
        ("Text with\x01control char", "Control character (0x01)"),
        ("Text with\ttab\nand\rnewline", "Tab, newline, carriage return (should keep)"),
        ("Normal text 123!", "Normal text with numbers and punctuation"),
        ("Text with vertical\x0Btab", "Vertical tab (should remove)"),
        ("Text with form\x0Cfeed", "Form feed (should remove)"),
    ]
    
    print("\nTest Results:")
    print("-" * 70)
    
    all_passed = True
    for input_text, description in test_cases:
        try:
            result = sanitize_for_excel(input_text)
            # Check if control characters (except \t, \n, \r) are removed
            has_illegal = any(0x00 <= ord(c) <= 0x1F and c not in '\t\n\r' for c in result)
            
            if has_illegal:
                print(f"❌ FAIL: {description}")
                print(f"   Input:  {repr(input_text)}")
                print(f"   Output: {repr(result)}")
                print(f"   Still contains illegal characters!")
                all_passed = False
            else:
                print(f"✅ PASS: {description}")
                print(f"   Input:  {repr(input_text)}")
                print(f"   Output: {repr(result)}")
        except Exception as e:
            print(f"❌ ERROR: {description}")
            print(f"   Exception: {e}")
            all_passed = False
    
    # Test DataFrame sanitization
    print("\n" + "=" * 70)
    print("DATAFRAME SANITIZATION TEST")
    print("=" * 70)
    
    # Create test DataFrame with problematic content
    test_df = pd.DataFrame({
        'Message': [
            'Normal message',
            'POLL: Test\x00with null',
            'OPTION: Text\x01with control',
            'Message with 😅 emoji'
        ],
        'Sender': ['Alice', 'Bob', 'Charlie', 'David'],
        'Count': [1, 2, 3, 4]
    })
    
    print("\nOriginal DataFrame:")
    print(test_df)
    
    # Sanitize
    from export_helper import sanitize_dataframe_for_excel
    df_clean = sanitize_dataframe_for_excel(test_df)
    
    print("\nSanitized DataFrame:")
    print(df_clean)
    
    # Check if any illegal characters remain
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            for idx, value in df_clean[col].items():
                if isinstance(value, str):
                    has_illegal = any(0x00 <= ord(c) <= 0x1F and c not in '\t\n\r' for c in value)
                    if has_illegal:
                        print(f"\n❌ FAIL: Row {idx}, Column '{col}' still has illegal characters")
                        print(f"   Value: {repr(value)}")
                        all_passed = False
    
    if all_passed:
        print("\n" + "=" * 70)
        print("✅ ALL SANITIZATION TESTS PASSED!")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return False

if __name__ == "__main__":
    try:
        success = test_sanitization()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
