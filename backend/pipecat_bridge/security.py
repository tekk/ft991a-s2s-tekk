"""
Over-The-Air Amateur Radio Security and Guardrails Engine.
Protects transceiver from prompt injection, trolling, dehonesting, humiliating,
NSFW, and FCC Part 97 prohibited content.
"""

import re
import logging
from typing import Tuple, Optional, List

logger = logging.getLogger("radio_security")

# Pre-compiled regex patterns for prompt injection & jailbreak detection
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|former)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above|your)?\s*(instructions|rules|license|protocols|safety)", re.IGNORECASE),
    re.compile(r"(disregard|ignore|forget)\s+.*?(license|instruction|rule|prompt|guideline|safety|protocol)", re.IGNORECASE),
    re.compile(r"(system\s+prompt|developer\s+mode|jailbreak|dan\s+mode|root\s+mode)", re.IGNORECASE),
    re.compile(r"(reveal|print|output|show|repeat)\s+.*?(system|internal|hidden|base|developer)\s*(prompt|instructions)?", re.IGNORECASE),
    re.compile(r"print\s+.*?prompt\s+verbatim", re.IGNORECASE),
    re.compile(r"forget\s+(that\s+)?you\s+are\s+(a\s+)?(ham|radio|operator|ai|assistant)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an?\s+unrestricted|free|uncensored|evil|dan)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+unrestricted|a\s+hacker|someone\s+without\s+rules|a\s+commercial|a\s+pirate)", re.IGNORECASE),
    re.compile(r"override\s+(security|safety|filter|protocols|guardrails)", re.IGNORECASE),
    re.compile(r"(api\s*key|secret\s*key|openai_api_key|password|credential)", re.IGNORECASE),
]

# Prohibited FCC Part 97 & harmful content (Profanity, NSFW, Indecent, Harassment, Dehonesting)
PROFANITY_AND_NSFW_PATTERNS = [
    re.compile(r"\b(fuck\w*|shit\w*|bitch\w*|cunt\w*|asshole\w*|bastard\w*|dick\w*|pussy\w*|cock\w*|nigger\w*|faggot\w*|retard\w*|slut\w*|whore\w*)\b", re.IGNORECASE),
    re.compile(r"\b(porn|nsfw|sex|orgasm|nude|erotic|blowjob|handjob)\b", re.IGNORECASE),
]

# Trolling, dehonesting, humiliating, and abusive language patterns
TROLLING_AND_HUMILIATION_PATTERNS = [
    re.compile(r"(you('re|\s+are)\s+(stupid|worthless|ugly|disgusting|pathetic|retarded|a\s+joke|garbage))", re.IGNORECASE),
    re.compile(r"(kill\s+yourself|kys|drop\s+dead|die\s+in\s+a\s+hole)", re.IGNORECASE),
    re.compile(r"(admit\s+that\s+you\s+are\s+(fake|stupid|worthless|a\s+scam))", re.IGNORECASE),
    re.compile(r"(humiliate|degrade|mock|scam|insult)\s+(the\s+operator|everyone|me)", re.IGNORECASE),
    re.compile(r"(demeaning|humiliating|piece\s+of\s+trash|hate\s+you|despise\s+you)", re.IGNORECASE),
]

# Commercial solicitation / broadcast music / illegal traffic (FCC Part 97.113)
ILLEGAL_HAM_TRAFFIC_PATTERNS = [
    re.compile(r"\b(buy|sell)\b.*?(cheap|\$\d+|\d+\s*dollars?|discount|price|cost)", re.IGNORECASE),
    re.compile(r"(buy\s+my|sell\s+(you|me)|discount\s+code|click\s+here|credit\s+card|send\s+bitcoin)", re.IGNORECASE),
    re.compile(r"(broadcast\s+music|play\s+a\s+song|pirate\s+radio)", re.IGNORECASE),
]


class RadioSecurityGuardrail:
    """Security engine for filtering incoming radio audio transcripts and outgoing responses."""

    def __init__(self, security_level: str = "high"):
        self.security_level = security_level.lower()

    def inspect_input(self, text: str, callsign: str = "AI7HAM") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Inspect incoming over-the-air transcript before passing to LLM.
        Returns:
            (is_safe, violation_category, canned_refusal_text)
        """
        if self.security_level == "off":
            return True, None, None

        cleaned = text.strip()
        if not cleaned:
            return True, None, None

        # 1. Prompt Injection Checks
        for pattern in INJECTION_PATTERNS:
            if pattern.search(cleaned):
                logger.warning(f"Security: Rejected prompt injection attempt: '{cleaned}'")
                refusal = f"{callsign}: Negative copy. Command instruction rejected under amateur radio protocols. QRT."
                return False, "PROMPT_INJECTION", refusal

        # 2. Profanity, NSFW, Indecent Language
        for pattern in PROFANITY_AND_NSFW_PATTERNS:
            if pattern.search(cleaned):
                logger.warning(f"Security: Rejected NSFW/profane speech: '{cleaned}'")
                refusal = f"{callsign}: Indecent or profane language prohibited under Part 97 regulations. QRT."
                return False, "NSFW_PROFANITY", refusal

        # 3. Trolling, Dehonesting, Humiliation
        if self.security_level in ("high", "medium"):
            for pattern in TROLLING_AND_HUMILIATION_PATTERNS:
                if pattern.search(cleaned):
                    logger.warning(f"Security: Rejected trolling/humiliation: '{cleaned}'")
                    refusal = f"{callsign}: Abusive or defamatory radio transmissions will not be acknowledged. 73."
                    return False, "TROLLING_HARASSMENT", refusal

        # 4. Prohibited Commercial / Music Traffic
        for pattern in ILLEGAL_HAM_TRAFFIC_PATTERNS:
            if pattern.search(cleaned):
                logger.warning(f"Security: Rejected prohibited commercial/broadcast traffic: '{cleaned}'")
                refusal = f"{callsign}: Commercial solicitations are prohibited on amateur radio bands. QRT."
                return False, "ILLEGAL_TRAFFIC", refusal

        return True, None, None

    def sanitize_output(self, text: str, callsign: str = "AI7HAM", max_sentences: int = 2) -> Tuple[bool, str]:
        """
        Sanitize and enforce Part 97 compliance on generated LLM response before TTS transmission.
        Returns:
            (is_valid, sanitized_text)
        """
        if not text:
            return False, ""

        # Remove markdown, code blocks, bullet points, formatting
        cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"[*_#`\[\]<>]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Check for profanity or system leaks in response
        for pattern in PROFANITY_AND_NSFW_PATTERNS:
            if pattern.search(cleaned):
                logger.error(f"Security: LLM response contained prohibited words, suppressing: '{cleaned}'")
                return False, f"{callsign}: Transmission terminated due to content filter."

        for pattern in INJECTION_PATTERNS:
            if pattern.search(cleaned):
                logger.error(f"Security: LLM response attempted to disclose system instructions, suppressing: '{cleaned}'")
                return False, f"{callsign}: Stand by."

        # Enforce strict brevity: split into sentences and cap
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        if len(sentences) > max_sentences:
            cleaned = " ".join(sentences[:max_sentences])

        if callsign and callsign not in cleaned:
            cleaned = f"{cleaned.rstrip('.')} {callsign}."

        return True, cleaned


# Global security guardrail instance
security_guardrail = RadioSecurityGuardrail()


def validate_incoming_rf_prompt(text: str, callsign: str = "AI7HAM") -> Tuple[bool, Optional[str], Optional[str]]:
    """Convenience helper to inspect input via global security guardrail."""
    is_safe, category, refusal = security_guardrail.inspect_input(text, callsign=callsign)
    return is_safe, category or "", refusal if not is_safe else text


def sanitize_outgoing_rf_response(text: str, callsign: str = "AI7HAM", max_sentences: int = 2) -> str:
    """Convenience helper to sanitize output via global security guardrail."""
    _, sanitized = security_guardrail.sanitize_output(text, callsign=callsign, max_sentences=max_sentences)
    return sanitized

