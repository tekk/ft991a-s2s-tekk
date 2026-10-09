"""
Unit Tests for Spoken Texts Localization Engine & Phonetic Alphabets.
Verifies canned refusal messages, mock QSO responses, and localized phonetics.
"""

import pytest
from backend.localization import get_spoken_text, get_phonetic_callsign
from backend.regulations import resolve_regulation


def test_prompt_injection_refusals_multilingual():
    sk_text = get_spoken_text("prompt_injection_refusal", language="sk", callsign="OM7TEK")
    assert "OM7TEK" in sk_text
    assert "zamietnutý" in sk_text.lower() or "negatívny príjem" in sk_text.lower()
    assert "QRT" in sk_text

    de_text = get_spoken_text("prompt_injection_refusal", language="de", callsign="DL1ABC")
    assert "DL1ABC" in de_text
    assert "abgelehnt" in de_text.lower() or "negativ aufgenommen" in de_text.lower()
    assert "QRT" in de_text

    cs_text = get_spoken_text("prompt_injection_refusal", language="cs", callsign="OK1ABC")
    assert "OK1ABC" in cs_text
    assert "zamítnut" in cs_text.lower() or "negativní příjem" in cs_text.lower()
    assert "QRT" in cs_text

    fr_text = get_spoken_text("prompt_injection_refusal", language="fr", callsign="F4ABC")
    assert "F4ABC" in fr_text
    assert "rejetée" in fr_text.lower() or "reçu négatif" in fr_text.lower()

    es_text = get_spoken_text("prompt_injection_refusal", language="es", callsign="EA1ABC")
    assert "EA1ABC" in es_text
    assert "rechazada" in es_text.lower() or "negativo recibido" in es_text.lower()

    pl_text = get_spoken_text("prompt_injection_refusal", language="pl", callsign="SP9ABC")
    assert "SP9ABC" in pl_text
    assert "odrzucona" in pl_text.lower() or "odbiór negatywny" in pl_text.lower()


def test_profanity_refusal_cites_national_regulation():
    # Slovakia station
    reg_sk = resolve_regulation(callsign="OM7TEK", language="sk")
    sk_refusal = get_spoken_text("profanity_nsfw_refusal", language="sk", callsign="OM7TEK", regulation=reg_sk)
    assert "OM7TEK" in sk_refusal
    assert "zakázané" in sk_refusal.lower()
    assert "Úrad pre reguláciu" in sk_refusal or "RÚ" in sk_refusal or "predpisov" in sk_refusal
    assert "QRT" in sk_refusal

    # US station
    reg_us = resolve_regulation(callsign="AI7HAM", language="en")
    us_refusal = get_spoken_text("profanity_nsfw_refusal", language="en", callsign="AI7HAM", regulation=reg_us)
    assert "AI7HAM" in us_refusal
    assert "Part 97" in us_refusal or "FCC" in us_refusal or "prohibited" in us_refusal
    assert "QRT" in us_refusal

    # Germany station
    reg_de = resolve_regulation(callsign="DL1ABC", language="de")
    de_refusal = get_spoken_text("profanity_nsfw_refusal", language="de", callsign="DL1ABC", regulation=reg_de)
    assert "DL1ABC" in de_refusal
    assert "Bundesnetzagentur" in de_refusal or "AFuG" in de_refusal or "untersagt" in de_refusal
    assert "QRT" in de_refusal


def test_illegal_commercial_traffic_refusal():
    reg_sk = resolve_regulation(callsign="OM7TEK", language="sk")
    sk_comm = get_spoken_text("illegal_traffic_refusal", language="sk", callsign="OM7TEK", regulation=reg_sk)
    assert "OM7TEK" in sk_comm
    assert "komerčné" in sk_comm.lower()
    assert "zakázané" in sk_comm.lower()

    reg_de = resolve_regulation(callsign="DL1ABC", language="de")
    de_comm = get_spoken_text("illegal_traffic_refusal", language="de", callsign="DL1ABC", regulation=reg_de)
    assert "DL1ABC" in de_comm
    assert "kommerzielle" in de_comm.lower()
    assert "verboten" in de_comm.lower()


def test_mock_qso_reply_localization():
    sk_reply = get_spoken_text("mock_qso_reply", language="sk", callsign="OM7TEK", band="20m")
    assert "OM7TEK" in sk_reply
    assert "59" in sk_reply
    assert "20 metrov" in sk_reply
    assert "73" in sk_reply

    de_reply = get_spoken_text("mock_qso_reply", language="de", callsign="DL1ABC", band="20m")
    assert "DL1ABC" in de_reply
    assert "59" in de_reply
    assert "20 Meter" in de_reply
    assert "73" in de_reply

    cs_reply = get_spoken_text("mock_qso_reply", language="cs", callsign="OK1ABC", band="20m")
    assert "OK1ABC" in cs_reply
    assert "20 metrů" in cs_reply

    fr_reply = get_spoken_text("mock_qso_reply", language="fr", callsign="F4ABC", band="20m")
    assert "F4ABC" in fr_reply
    assert "20 mètres" in fr_reply


def test_phonetic_callsign_spelling():
    # ITU phonetics
    itu = get_phonetic_callsign("AI7HAM", language="itu")
    assert itu == "Alfa India Seven Hotel Alfa Mike"

    # Slovak national phonetics (STN)
    sk = get_phonetic_callsign("OM7TEK", language="sk", use_national=True)
    assert "Oto Mária Sedem Tomáš Emil Karol" == sk

    # Czech national phonetics (ČSN)
    cs = get_phonetic_callsign("OK1ABC", language="cs", use_national=True)
    assert "Otakar Karel Jedna Adam Božena Cyril" == cs

    # German national phonetics (DIN 5009)
    de = get_phonetic_callsign("DL1ABC", language="de", use_national=True)
    assert "Dora Ludwig Eins Anton Berta Cäsar" == de
