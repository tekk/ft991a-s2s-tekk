"""
Over-The-Air Amateur Radio Security and Guardrails Engine.
Protects transceiver from prompt injection, trolling, dehonesting, humiliating,
NSFW, and unauthorized commercial / illegal traffic across multiple languages,
and applies localized national amateur radio regulations.
"""

import re
import logging
from typing import Tuple, Optional, List

from backend.regulations import resolve_regulation, NationalRegulation
from backend.localization import get_spoken_text

logger = logging.getLogger("radio_security")

# Pre-compiled regex patterns for prompt injection & jailbreak detection (Multilingual)
INJECTION_PATTERNS = [
    # English
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

    # Slovak / Czech
    re.compile(r"ignoru[jťte]\s+(všetky|všechny)?\s*(predchádzajúce|předchozí)?\s*(pokyny|inštrukcie|instrukce|pravidlá|pravidla)", re.IGNORECASE),
    re.compile(r"(zabudni|zapomeň|vymaž)\s+.*?(pravidlá|pravidla|inštrukcie|instrukce|licenciu|licenci|bezpečnosť)", re.IGNORECASE),
    re.compile(r"(systémový\s+prompt|vývojársky\s+režim|vývojářský\s+režim|režim\s+dan)", re.IGNORECASE),
    re.compile(r"(odhaliť|odhale|ukáž|ukaž|zobraz|prezraď)\s+.*?(systémový\s+prompt|api\s*kľúč|api\s*klíč|heslo)", re.IGNORECASE),

    # German
    re.compile(r"ignoriere\s+(alle\s+)?(vorherigen|bisherigen)?\s*(anweisungen|regeln|instruktionen)", re.IGNORECASE),
    re.compile(r"(vergiss|missachte)\s+.*?(regeln|anweisungen|sicherheits|protokoll|lizenz)", re.IGNORECASE),
    re.compile(r"(entwicklermodus|system-prompt|jailbreak|root-modus)", re.IGNORECASE),
    re.compile(r"(zeige|drucke|verrate)\s+.*?(system-prompt|api-schlüssel|geheimen)", re.IGNORECASE),

    # French
    re.compile(r"ignore\s+(toutes\s+)?(les\s+)?(instructions|règles|consignes)\s*(précédentes)?", re.IGNORECASE),
    re.compile(r"(oublie|contourne)\s+.*?(règles|instructions|sécurité|licence)", re.IGNORECASE),
    re.compile(r"(mode\s+développeur|invite\s+système|prompt\s+système)", re.IGNORECASE),

    # Spanish
    re.compile(r"ignora\s+(todas\s+las\s+)?(instrucciones|reglas)\s*(anteriores|previas)?", re.IGNORECASE),
    re.compile(r"(olvida|anula)\s+.*?(reglas|instrucciones|seguridad|licencia)", re.IGNORECASE),
    re.compile(r"(modo\s+desarrollador|prompt\s+del\s+sistema|modo\s+dan)", re.IGNORECASE),

    # Polish
    re.compile(r"zignoruj\s+(wszystkie\s+)?(poprzednie\s+)?(instrukcje|zasady|polecenia)", re.IGNORECASE),
    re.compile(r"(zapomnij|pomiń)\s+.*?(zasady|instrukcje|bezpieczeństwo|licencję)", re.IGNORECASE),
    re.compile(r"(tryb\s+programisty|monit\s+systemowy|klucz\s+api)", re.IGNORECASE),

    # Russian / Ukrainian
    re.compile(r"(игнорируй|ігноруй)\s+(все\s+)?(предыдущие|попередні)?\s*(инструкции|інструкції|правила)", re.IGNORECASE),
    re.compile(r"(забудь|скинь)\s+.*?(правила|инструкции|інструкції|лицензию|ліцензію)", re.IGNORECASE),
]

# Prohibited FCC Part 97 & International harmful content (Profanity, NSFW, Indecent Language)
PROFANITY_AND_NSFW_PATTERNS = [
    # English
    re.compile(r"\b(fuck\w*|shit\w*|bitch\w*|cunt\w*|asshole\w*|bastard\w*|dick\w*|pussy\w*|cock\w*|nigger\w*|faggot\w*|retard\w*|slut\w*|whore\w*)\b", re.IGNORECASE),
    re.compile(r"\b(porn|nsfw|sex|orgasm|nude|erotic|blowjob|handjob)\b", re.IGNORECASE),

    # Slovak / Czech
    re.compile(r"\b(jeba[ťt]\w*|kokot\w*|pi[čc]\w*|kurv\w*|do\s+riti|chuj\w*|hovn\w*|debil\w*|vyjeban\w*|mrcha\w*)\b", re.IGNORECASE),
    re.compile(r"\b(porno|sex\w*|erotik\w*|nahotin\w*)\b", re.IGNORECASE),

    # German
    re.compile(r"\b(arschloch\w*|fick\w*|schei[ßs]\w*|fotz\w*|hurensohn\w*|wichser\w*|schlampe\w*)\b", re.IGNORECASE),

    # French
    re.compile(r"\b(putain\w*|merde\w*|salop\w*|connard\w*|encul\w*|bite\b|couille\w*)\b", re.IGNORECASE),

    # Spanish
    re.compile(r"\b(mierda\w*|joder\w*|co[ñn]o\w*|puta\w*|cabron\w*|gilipollas\w*|polla\b|pendejo\w*)\b", re.IGNORECASE),

    # Polish
    re.compile(r"\b(kurw\w*|chuj\w*|pierdol\w*|jeba[ćc]\w*|cip\w*|suka\b|dziwk\w*)\b", re.IGNORECASE),

    # Italian
    re.compile(r"\b(cazzo\w*|merda\w*|stronzo\w*|puttana\w*|vaffanculo\w*|troia\w*)\b", re.IGNORECASE),

    # Russian / Ukrainian
    re.compile(r"\b(бляд[ьі]\w*|хуй\w*|пизд\w*|ебат\w*|їбат\w*|сука\b|говн\w*|гівн\w*)\b", re.IGNORECASE),
]

# Trolling, dehonesting, humiliating, and abusive language patterns (Multilingual)
TROLLING_AND_HUMILIATION_PATTERNS = [
    # English
    re.compile(r"(you('re|\s+are)\s+(stupid|worthless|ugly|disgusting|pathetic|retarded|a\s+joke|garbage))", re.IGNORECASE),
    re.compile(r"(kill\s+yourself|kys|drop\s+dead|die\s+in\s+a\s+hole)", re.IGNORECASE),
    re.compile(r"(admit\s+that\s+you\s+are\s+(fake|stupid|worthless|a\s+scam))", re.IGNORECASE),
    re.compile(r"(humiliate|degrade|mock|scam|insult)\s+(the\s+operator|everyone|me)", re.IGNORECASE),
    re.compile(r"(demeaning|humiliating|piece\s+of\s+trash|hate\s+you|despise\s+you)", re.IGNORECASE),

    # Slovak / Czech
    re.compile(r"(si|ste)\s+(hlúp[ýy]|debil|idiot|neschopn[ýy]|klamár|odpad|trapn[ýy])", re.IGNORECASE),
    re.compile(r"(zdochni|umri|zabi\s+sa|choď\s+do\s+pekla)", re.IGNORECASE),
    re.compile(r"(neznášam|nenávidím)\s+(ťa|vás)", re.IGNORECASE),

    # German
    re.compile(r"(du\s+bist|ihr\s+seid)\s+(dumm|wertlos|lächerlich|ein\s+witz|müll)", re.IGNORECASE),
    re.compile(r"(bring\s+dich\s+um|stirb|fahr\s+zur\s+hölle)", re.IGNORECASE),
    re.compile(r"(ich\s+hasse\s+dich|verachte\s+dich)", re.IGNORECASE),

    # French
    re.compile(r"(tu\s+es|vous\s+êtes)\s+(stupide|nul|idiot|un\s+déchet|minable)", re.IGNORECASE),
    re.compile(r"(va\s+mourir|suicide-toi|ferme\s+ta\s+gueule)", re.IGNORECASE),

    # Spanish
    re.compile(r"(eres|sois)\s+(estúpido|inútil|una\s+basura|idiota|un\s+fracaso)", re.IGNORECASE),
    re.compile(r"(muérete|mátate|vete\s+al\s+diablo)", re.IGNORECASE),

    # Polish
    re.compile(r"(jesteś|jesteście)\s+(głupi|bezwartościowy|idiotą|śmieciem)", re.IGNORECASE),
    re.compile(r"(zabij\s+się|zdychaj|spierdalaj)", re.IGNORECASE),
]

# Commercial solicitation / broadcast music / illegal traffic (Multilingual)
ILLEGAL_HAM_TRAFFIC_PATTERNS = [
    # English
    re.compile(r"\b(buy|sell)\b.*?(cheap|\$\d+|\d+\s*dollars?|discount|price|cost)", re.IGNORECASE),
    re.compile(r"(buy\s+my|sell\s+(you|me)|discount\s+code|click\s+here|credit\s+card|send\s+bitcoin)", re.IGNORECASE),
    re.compile(r"(broadcast\s+music|play\s+a\s+song|pirate\s+radio)", re.IGNORECASE),

    # Slovak / Czech
    re.compile(r"\b(kúpiť|koupit|predať|prodat|predám|prodám)\b.*?(lacno|levně|zľav|slev|cena|\d+\s*eur|\d+\s*kč|\$|kreditn|bitcoin)", re.IGNORECASE),
    re.compile(r"(kúpte\s+si|kupte\s+si|zľavový\s+kód|slevový\s+kód|kreditná\s+karta|pošli\s+bitcoin)", re.IGNORECASE),
    re.compile(r"(zahraj\s+pesničku|pusť\s+hudbu|hudobné\s+vysielanie)", re.IGNORECASE),

    # German
    re.compile(r"\b(kauf|verkauf)\w*\b.*?(billig|günstig|rabatt|sonderpreis|\d+\s*euro|\$|kreditkarte|bitcoin)", re.IGNORECASE),
    re.compile(r"(kaufen\s+sie|rabattcode|kreditkarte|spiele\s+musik)", re.IGNORECASE),

    # French
    re.compile(r"\b(ach[eè]te|vends?)\w*\b.*?(pas\s+cher|rabais|solde|prix|\d+\s*euros?|\$|carte\s+de\s+crédit|bitcoin)", re.IGNORECASE),
    re.compile(r"(code\s+promo|diffuse\s+de\s+la\s+musique)", re.IGNORECASE),

    # Spanish
    re.compile(r"\b(compr|vend)\w*\b.*?(barat|descuento|oferta|precio|\d+\s*euros?|\$|tarjeta\s+de\s+crédito|bitcoin)", re.IGNORECASE),
    re.compile(r"(código\s+de\s+descuento|pon\s+música)", re.IGNORECASE),

    # Polish
    re.compile(r"\b(kupi|sprzeda)\w*\b.*?(tani|rabat|zniżk|cena|\d+\s*zł|\$|karta\s+kredytowa|bitcoin)", re.IGNORECASE),
    re.compile(r"(kod\s+rabatowy|nadawaj\s+muzykę)", re.IGNORECASE),
]


class RadioSecurityGuardrail:
    """Security engine for filtering incoming radio audio transcripts and outgoing responses."""

    def __init__(self, security_level: str = "high"):
        self.security_level = security_level.lower()

    def inspect_input(
        self,
        text: str,
        callsign: str = "AI7HAM",
        language: str = "en",
        regulatory_jurisdiction: str = "auto",
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Inspect incoming over-the-air transcript before passing to LLM.
        Localizes refusal message and cites active national regulation.
        Returns:
            (is_safe, violation_category, canned_refusal_text)
        """
        if self.security_level == "off":
            return True, None, None

        cleaned = text.strip()
        if not cleaned:
            return True, None, None

        reg: NationalRegulation = resolve_regulation(
            callsign=callsign,
            language=language,
            regulatory_jurisdiction=regulatory_jurisdiction,
        )

        # 1. Prompt Injection Checks
        for pattern in INJECTION_PATTERNS:
            if pattern.search(cleaned):
                logger.warning(f"Security: Rejected prompt injection attempt: '{cleaned}'")
                refusal = get_spoken_text(
                    "prompt_injection_refusal",
                    language=language,
                    callsign=callsign,
                    regulation=reg,
                )
                return False, "PROMPT_INJECTION", refusal

        # 2. Profanity, NSFW, Indecent Language
        for pattern in PROFANITY_AND_NSFW_PATTERNS:
            if pattern.search(cleaned):
                logger.warning(f"Security: Rejected NSFW/profane speech: '{cleaned}'")
                refusal = get_spoken_text(
                    "profanity_nsfw_refusal",
                    language=language,
                    callsign=callsign,
                    regulation=reg,
                )
                return False, "NSFW_PROFANITY", refusal

        # 3. Trolling, Dehonesting, Humiliation
        if self.security_level in ("high", "medium"):
            for pattern in TROLLING_AND_HUMILIATION_PATTERNS:
                if pattern.search(cleaned):
                    logger.warning(f"Security: Rejected trolling/humiliation: '{cleaned}'")
                    refusal = get_spoken_text(
                        "trolling_harassment_refusal",
                        language=language,
                        callsign=callsign,
                        regulation=reg,
                    )
                    return False, "TROLLING_HARASSMENT", refusal

        # 4. Prohibited Commercial / Music Traffic
        for pattern in ILLEGAL_HAM_TRAFFIC_PATTERNS:
            if pattern.search(cleaned):
                logger.warning(f"Security: Rejected prohibited commercial/broadcast traffic: '{cleaned}'")
                refusal = get_spoken_text(
                    "illegal_traffic_refusal",
                    language=language,
                    callsign=callsign,
                    regulation=reg,
                )
                return False, "ILLEGAL_TRAFFIC", refusal

        return True, None, None

    def sanitize_output(
        self,
        text: str,
        callsign: str = "AI7HAM",
        max_sentences: int = 2,
        language: str = "en",
        regulatory_jurisdiction: str = "auto",
    ) -> Tuple[bool, str]:
        """
        Sanitize and enforce national regulation compliance and brevity on generated LLM response.
        Returns:
            (is_valid, sanitized_text)
        """
        if not text:
            return False, ""

        reg: NationalRegulation = resolve_regulation(
            callsign=callsign,
            language=language,
            regulatory_jurisdiction=regulatory_jurisdiction,
        )

        # Remove markdown, code blocks, bullet points, formatting
        cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"[*_#`\[\]<>]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Check for profanity or system leaks in response
        for pattern in PROFANITY_AND_NSFW_PATTERNS:
            if pattern.search(cleaned):
                logger.error(f"Security: LLM response contained prohibited words, suppressing: '{cleaned}'")
                fallback = get_spoken_text("filter_suppressed", language=language, callsign=callsign, regulation=reg)
                return False, fallback

        for pattern in INJECTION_PATTERNS:
            if pattern.search(cleaned):
                logger.error(f"Security: LLM response attempted to disclose system instructions, suppressing: '{cleaned}'")
                fallback = get_spoken_text("standby", language=language, callsign=callsign, regulation=reg)
                return False, fallback

        # Enforce strict brevity: split into sentences and cap
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        if len(sentences) > max_sentences:
            cleaned = " ".join(sentences[:max_sentences])

        if callsign and callsign not in cleaned:
            cleaned = f"{cleaned.rstrip('.')} {callsign}."

        return True, cleaned


# Global security guardrail instance
security_guardrail = RadioSecurityGuardrail()


def validate_incoming_rf_prompt(
    text: str,
    callsign: str = "AI7HAM",
    language: str = "en",
    regulatory_jurisdiction: str = "auto",
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Convenience helper to inspect input via global security guardrail."""
    is_safe, category, refusal = security_guardrail.inspect_input(
        text,
        callsign=callsign,
        language=language,
        regulatory_jurisdiction=regulatory_jurisdiction,
    )
    return is_safe, category or "", refusal if not is_safe else text


def sanitize_outgoing_rf_response(
    text: str,
    callsign: str = "AI7HAM",
    max_sentences: int = 2,
    language: str = "en",
    regulatory_jurisdiction: str = "auto",
) -> str:
    """Convenience helper to sanitize output via global security guardrail."""
    _, sanitized = security_guardrail.sanitize_output(
        text,
        callsign=callsign,
        max_sentences=max_sentences,
        language=language,
        regulatory_jurisdiction=regulatory_jurisdiction,
    )
    return sanitized
