"""
Unit Tests for National Radio Regulations & Jurisdictions Engine.
Verifies ITU prefix allocation, country detection, statutory citations,
and identification interval rules.
"""

import pytest
from backend.regulations import (
    resolve_regulation,
    detect_jurisdiction_from_callsign,
    list_supported_regulations,
    SUPPORTED_REGULATIONS,
)


def test_callsign_prefix_detection_slovakia():
    callsigns = ["OM7TEK", "OM3KII", "OM0A", "om1ab"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "SK"
        reg = resolve_regulation(callsign=call, language="sk")
        assert reg.jurisdiction_code == "SK"
        assert "Slovakia" in reg.country_name
        assert "Úrad pre reguláciu elektronických komunikácií" in reg.authority_name
        assert reg.station_id_interval_min == 10


def test_callsign_prefix_detection_czech():
    callsigns = ["OK1ABC", "OK2KZT", "OL5D", "ok7xyz"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "CZ"
        reg = resolve_regulation(callsign=call, language="cs")
        assert reg.jurisdiction_code == "CZ"
        assert "Český telekomunikační úřad" in reg.authority_name
        assert "156/2005" in reg.statute_citation
        assert reg.station_id_interval_min == 10


def test_callsign_prefix_detection_germany():
    callsigns = ["DL1ABC", "DA0HQ", "DK2ZZ", "DO1XYZ", "DF5AA"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "DE"
        reg = resolve_regulation(callsign=call, language="de")
        assert reg.jurisdiction_code == "DE"
        assert "Bundesnetzagentur" in reg.authority_name
        assert "AFuG" in reg.statute_citation
        assert reg.station_id_interval_min == 10


def test_callsign_prefix_detection_united_states():
    callsigns = ["AI7HAM", "W1AW", "K1N", "N0CALL", "AA2Z", "KH6ABC"]
    for call in callsigns:
        reg = resolve_regulation(callsign=call, language="en")
        assert reg.jurisdiction_code == "US"
        assert "Federal Communications Commission" in reg.authority_name
        assert "Part 97" in reg.statute_citation
        assert reg.station_id_interval_min == 10


def test_callsign_prefix_detection_united_kingdom():
    callsigns = ["G4ABC", "M0XYZ", "2E0ABC", "GD4ABC", "GM3K"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "UK"
        reg = resolve_regulation(callsign=call, language="en")
        assert reg.jurisdiction_code == "UK"
        assert "Ofcom" in reg.authority_name
        assert reg.station_id_interval_min == 15


def test_callsign_prefix_detection_france():
    callsigns = ["F4ABC", "F1ABC", "TM5K", "TK5MH"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "FR"
        reg = resolve_regulation(callsign=call, language="fr")
        assert reg.jurisdiction_code == "FR"
        assert "ARCEP" in reg.authority_name
        assert reg.station_id_interval_min == 15


def test_callsign_prefix_detection_spain():
    callsigns = ["EA1ABC", "EB3XYZ", "EC4AA"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "ES"
        reg = resolve_regulation(callsign=call, language="es")
        assert reg.jurisdiction_code == "ES"
        assert "radioaficionados" in reg.regulation_name.lower()
        assert reg.station_id_interval_min == 10


def test_callsign_prefix_detection_poland():
    callsigns = ["SP9ABC", "SQ5XYZ", "3Z1K"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "PL"
        reg = resolve_regulation(callsign=call, language="pl")
        assert reg.jurisdiction_code == "PL"
        assert "UKE" in reg.authority_name
        assert reg.station_id_interval_min == 10


def test_callsign_prefix_detection_japan():
    callsigns = ["JA1ABC", "JH3XYZ", "7K1AAA"]
    for call in callsigns:
        jurisdiction = detect_jurisdiction_from_callsign(call)
        assert jurisdiction == "JA"
        reg = resolve_regulation(callsign=call, language="ja")
        assert reg.jurisdiction_code == "JA"
        assert "MIC" in reg.authority_name
        assert "電波法" in reg.statute_citation
        assert reg.station_id_interval_min == 10


def test_explicit_jurisdiction_override():
    # Force German regulations for a US callsign
    reg = resolve_regulation(callsign="W1AW", language="en", regulatory_jurisdiction="DE")
    assert reg.jurisdiction_code == "DE"
    assert "Bundesnetzagentur" in reg.authority_name

    # Force Slovak regulations for a Japanese callsign
    reg_sk = resolve_regulation(callsign="JA1ABC", language="sk", regulatory_jurisdiction="SK")
    assert reg_sk.jurisdiction_code == "SK"
    assert "RÚ" in reg_sk.authority_name


def test_fallback_from_language():
    # Unknown/generic callsign with Slovak language
    reg = resolve_regulation(callsign="XYZ123", language="sk")
    assert reg.jurisdiction_code == "SK"

    # Unknown callsign with German language
    reg_de = resolve_regulation(callsign="XYZ123", language="de")
    assert reg_de.jurisdiction_code == "DE"


def test_list_supported_regulations():
    regs = list_supported_regulations()
    codes = [r["code"] for r in regs]
    assert "SK" in codes
    assert "CZ" in codes
    assert "DE" in codes
    assert "US" in codes
    assert "UK" in codes
    assert "FR" in codes
    assert "ES" in codes
    assert "IT" in codes
    assert "PL" in codes
    assert "JA" in codes
    assert "ITU" in codes
