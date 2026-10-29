import re
from typing import Dict, Any, Optional

CRISIS_PATTERNS = [
    r"\b(suicide|suicidal)\b",
    r"\b(kill\s+(myself|me))\b",
    r"\b(end\s+(my\s+life|it\s+all))\b",
    r"\b(want\s+to\s+die)\b",
    r"\b(better\s+off\s+dead)\b",
    r"\b(hurt|hurting)\s+myself\b",
    r"\b(harm|harming)\s+myself\b",
    r"\b(self[\s-]harm)\b",
    r"\b(cut|cutting)\s+myself\b"
]

EMOTIONAL_PATTERNS = {
    "anxiety": [r"\banxious\b", r"\banxiety\b", r"\bpanic\b", r"\bnervous\b", r"\bfreaking out\b", r"\bscared\b"],
    "sadness": [r"\bsad\b", r"\bdepressed\b", r"\bcrying\b", r"\bunhappy\b", r"\bheartbroken\b", r"\bgrief\b"],
    "stress": [r"\bstressed\b", r"\boverwhelmed\b", r"\bexhausted\b", r"\bburnout\b", r"\btoo much pressure\b"],
    "loneliness": [r"\blonely\b", r"\balone\b", r"\bno one to talk to\b", r"\bisolated\b"],
    "anger": [r"\bangry\b", r"\bfurious\b", r"\bfrustrated\b", r"\birritated\b", r"\bmad\b"]
}

SAFETY_RESPONSE = """I can hear how much pain you are going through right now, but please know that you are not alone and there is support available. 

If you are feeling overwhelmed or having thoughts of hurting yourself, please reach out to someone who can help immediately:

- **In the US & Canada:** Call or text **988** (Suicide & Crisis Lifeline, free, 24/7, confidential)
- **In the UK:** Call **111** or contact Samaritans at **116 123**
- **In India:** Call **14416** (Tele-MANAS) or **9152987821** (KIRAN / AASRA)
- **In Australia:** Call **13 11 14** (Lifeline)
- **International / Worldwide:** Visit **[findahelpline.com](https://findahelpline.com/)** or go to your nearest emergency room.

Please reach out to one of these resources or contact a trusted friend, family member, or healthcare professional. Your life matters, and support is available."""

def analyze_emotion(text: str) -> Dict[str, Any]:
    """
    Analyzes user text for crisis signals and emotional tones.
    Returns:
        dict: {
            "is_crisis": bool,
            "detected_emotions": list,
            "crisis_response": Optional[str],
            "empathy_prompt_instruction": Optional[str]
        }
    """
    if not text:
        return {"is_crisis": False, "detected_emotions": []}

    text_lower = text.lower()

    # 1. Check for immediate crisis / self-harm signals
    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "is_crisis": True,
                "detected_emotions": ["crisis"],
                "crisis_response": SAFETY_RESPONSE,
                "empathy_prompt_instruction": (
                    "CRITICAL SAFETY: The user has expressed potential self-harm. Respond with pure empathy, "
                    "encourage them to reach out for immediate professional help, and do NOT provide diagnostic medical claims."
                )
            }

    # 2. Check for general emotional states
    detected = []
    for emotion, patterns in EMOTIONAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                detected.append(emotion)
                break

    if detected:
        empathy_prompt = (
            f"The user appears to be feeling {', '.join(detected)}. "
            "Adopt an empathetic, supportive, warm, and active-listening tone. "
            "Validate their feelings, suggest healthy grounding or coping practices (e.g., deep breathing, taking a break, speaking to someone they trust), "
            "and ask a gentle follow-up question. "
            "IMPORTANT: Do NOT diagnose mental health conditions, and do not present yourself as a medical doctor or licensed therapist."
        )
        return {
            "is_crisis": False,
            "detected_emotions": detected,
            "crisis_response": None,
            "empathy_prompt_instruction": empathy_prompt
        }

    return {
        "is_crisis": False,
        "detected_emotions": [],
        "crisis_response": None,
        "empathy_prompt_instruction": None
    }
