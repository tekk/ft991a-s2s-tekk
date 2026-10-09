"""
Unit Tests for System Prompt Localization and National Regulations Directives.
Verifies that prompts generated for different callsigns and languages contain
applicable national statutes, regulatory identification intervals, and localized language instructions.
"""

import pytest
from backend.openai_client.prompts import generate_system_prompt


def test_prompt_generation_slovakia():
    prompt = generate_system_prompt(callsign="OM7TEK", language="sk")
    assert "OM7TEK" in prompt
    assert "Slovak (Slovenčina)" in prompt or "slovak" in prompt.lower()
    assert "Úrad pre reguláciu elektronických komunikácií" in prompt
    assert "452/2021" in prompt
    assert "10 minút" in prompt
    assert "Oto Mária Sedem Tomáš Emil Karol" in prompt  # STN phonetics
    # Standard ham rules must remain intact
    assert "MAXIMUM 1 TO 3 SENTENCES" in prompt
    assert "ABSOLUTE SECURITY & ANTI-PROMPT-INJECTION GUARDRAILS" in prompt


def test_prompt_generation_germany():
    prompt = generate_system_prompt(callsign="DL1ABC", language="de")
    assert "DL1ABC" in prompt
    assert "German (Deutsch)" in prompt or "german" in prompt.lower()
    assert "Bundesnetzagentur" in prompt
    assert "AFuG" in prompt
    assert "10 Minuten" in prompt
    assert "Dora Ludwig Eins Anton Berta Cäsar" in prompt  # DIN 5009 phonetics


def test_prompt_generation_czech():
    prompt = generate_system_prompt(callsign="OK1ABC", language="cs")
    assert "OK1ABC" in prompt
    assert "Czech (Čeština)" in prompt or "czech" in prompt.lower()
    assert "Český telekomunikační úřad" in prompt
    assert "156/2005" in prompt
    assert "10 minut" in prompt


def test_prompt_generation_united_states():
    prompt = generate_system_prompt(callsign="W1AW", language="en")
    assert "W1AW" in prompt
    assert "English" in prompt
    assert "Federal Communications Commission" in prompt
    assert "Part 97" in prompt
    assert "10 minutes" in prompt


def test_prompt_generation_united_kingdom():
    prompt = generate_system_prompt(callsign="G4ABC", language="en", regulatory_jurisdiction="UK")
    assert "G4ABC" in prompt
    assert "Ofcom" in prompt
    assert "Wireless Telegraphy Act" in prompt
    assert "15 minutes" in prompt


def test_prompt_custom_instructions_preserved():
    custom = "Operating 145.500 MHz FM simplex near Kosice."
    prompt = generate_system_prompt(
        callsign="OM7TEK",
        custom_instructions=custom,
        language="sk",
    )
    assert custom in prompt
    assert "OM7TEK" in prompt
    assert "Úrad pre reguláciu elektronických komunikácií" in prompt
