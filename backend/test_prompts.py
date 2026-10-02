#!/usr/bin/env python3
"""Quick test to verify prompts don't contain unwanted phrases"""

import sys
from pathlib import Path

# Add project root to Python path
backend_root = Path(__file__).parent
sys.path.insert(0, str(backend_root))

from app.agent.prompts import build_voice_assistant_instructions

def check_forbidden_phrases(text: str, source: str) -> list[str]:
    """Check for phrases that should NOT appear in prompts - except in prohibition rules"""
    forbidden = [
        ("I don't have", "as a statement (not in prohibition)"),
        ("I do not have", "as a statement (not in prohibition)"),
        ("we don't have", "as a statement"),
        ("we do not have", "as a statement"),
        ("cannot find", "as a statement"),
        ("unable to find", "as a statement"),
        ("data not available", "as a statement"),
        ("insufficient information", "as a statement"),
    ]
    
    found = []
    text_lower = text.lower()
    
    # Skip checking if it's in a "NEVER say" or "DON'T say" prohibition context
    for phrase, description in forbidden:
        phrase_lower = phrase.lower()
        if phrase_lower in text_lower:
            # Check if it's in a prohibition context (NEVER, DON'T, prohibition, etc.)
            idx = text_lower.find(phrase_lower)
            context_start = max(0, idx - 100)  # Increased from 50 to 100
            context_end = min(len(text_lower), idx + len(phrase_lower) + 50)
            context = text_lower[context_start:context_end]
            
            # If it's in a prohibition context, it's OK
            prohibition_keywords = [
                "never say", "don't say", "never ever say", "never tell", 
                "absolute rules", "without saying", "do not say", "never mention"
            ]
            if any(keyword in context for keyword in prohibition_keywords):
                continue  # This is OK - it's telling the AI not to say it
            
            found.append(f"❌ Found '{phrase}' {description} in {source}")
    
    return found

def test_system_prompt():
    """Test the main system prompt"""
    print("\n🔍 Testing build_voice_assistant_instructions...")
    
    # Test in Hindi
    prompt_hi = build_voice_assistant_instructions("Hindi", "")
    issues_hi = check_forbidden_phrases(prompt_hi, "Hindi prompt")
    
    # Test in English
    prompt_en = build_voice_assistant_instructions("English", "")
    issues_en = check_forbidden_phrases(prompt_en, "English prompt")
    
    all_issues = issues_hi + issues_en
    
    if not all_issues:
        print("✅ System prompts are clean")
    else:
        for issue in all_issues:
            print(issue)
    
    # Check for positive signals
    print("\n📋 Checking for required instructions:")
    if "ABSOLUTE RULES" in prompt_en:
        print("✅ Contains ABSOLUTE RULES section")
    if "NEVER say \"I don't have information\"" in prompt_en:
        print("✅ Contains explicit prohibition against 'I don't have'")
    if "answer every question directly" in prompt_en.lower():
        print("✅ Contains instruction to answer directly")
    
    return len(all_issues) == 0

def test_voice_instructions():
    """Test that voice.py instructions are clean"""
    print("\n🔍 Testing voice.py inline instructions...")
    
    # Read the voice.py file
    voice_file = Path(__file__).parent / "app" / "knowledge" / "voice.py"
    if not voice_file.exists():
        print("⚠️  Cannot find voice.py file")
        return False
    
    voice_content = voice_file.read_text(encoding='utf-8')
    issues = check_forbidden_phrases(voice_content, "voice.py")
    
    if not issues:
        print("✅ Voice instructions are clean")
    else:
        for issue in issues:
            print(issue)
    
    # Check for positive signals
    print("\n📋 Checking voice.py for correct patterns:")
    if "Answer this question directly using your general knowledge" in voice_content:
        print("✅ Contains instruction to answer directly with general knowledge")
    if "NEVER say 'I don't have'" in voice_content:
        print("✅ Contains NEVER prohibition in abstention branch")
    if "Just answer naturally" in voice_content:
        print("✅ Contains 'answer naturally' instruction")
    
    return len(issues) == 0

def test_abstention_handling():
    """Test that abstention language is removed"""
    print("\n🔍 Testing abstention language removal...")
    
    # Read policy.py to check abstention messages
    policy_file = Path(__file__).parent / "app" / "knowledge" / "policy.py"
    if not policy_file.exists():
        print("⚠️  Cannot find policy.py file")
        return False
    
    policy_content = policy_file.read_text(encoding='utf-8')
    
    # Check that _ABSTENTIONS dict has been updated to helpful messages
    issues = []
    
    # Bad phrases that should NOT appear in policy
    bad_phrases_policy = [
        "I don't have that information",
        "I cannot provide",
        "data is not available",
    ]
    
    for phrase in bad_phrases_policy:
        if phrase in policy_content:
            issues.append(f"❌ Found old abstention phrase in policy.py: '{phrase}'")
    
    if not issues:
        print("✅ Abstention messages have been updated")
    else:
        for issue in issues:
            print(issue)
    
    # Check voice.py abstention handling
    voice_file = Path(__file__).parent / "app" / "knowledge" / "voice.py"
    voice_content = voice_file.read_text(encoding='utf-8')
    
    if "if decision.requires_abstention:" in voice_content:
        if "answer the question using general knowledge" in voice_content.lower():
            print("✅ Abstention branch answers with general knowledge")
        else:
            issues.append("❌ Abstention branch doesn't answer with general knowledge")
    
    return len(issues) == 0

def main():
    """Run all prompt tests"""
    print("=" * 60)
    print("🧪 SAHAYAK PROMPT VALIDATION")
    print("=" * 60)
    
    results = [
        test_system_prompt(),
        test_voice_instructions(),
        test_abstention_handling(),
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED - Prompts are clean!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review prompts above")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
