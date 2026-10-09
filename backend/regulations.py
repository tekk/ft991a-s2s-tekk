"""
National Amateur Radio Regulations & Jurisdictions Engine.
Provides prefix matching, regulatory profiles, legal statutory references,
mandatory station identification rules, and operating constraints for amateur radio stations.
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class NationalRegulation(BaseModel):
    """National amateur radio regulatory profile."""
    jurisdiction_code: str = Field(description="ISO or canonical country/jurisdiction code, e.g. US, SK, CZ, DE")
    country_name: str = Field(description="Full country or authority name")
    authority_name: str = Field(description="National telecommunications regulatory agency")
    regulation_name: str = Field(description="Governing regulatory statute or licence terms")
    statute_citation: str = Field(description="Legal citation, e.g. 47 CFR Part 97")
    station_id_interval_min: int = Field(default=10, description="Mandatory station identification interval in minutes")
    station_id_rule: str = Field(description="Mandatory station identification rule text")
    prohibitions: List[str] = Field(default_factory=list, description="Key prohibited transmissions under national law")
    primary_language: str = Field(default="en", description="Primary national language code")
    phonetic_alphabet_standard: str = Field(description="National phonetic alphabet standard description")
    etiquette_notes: str = Field(description="National ham radio courtesy and QSO etiquette guidelines")
    regulatory_prompt_clause: str = Field(description="Prompt directive enforcing national amateur radio regulations")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# Comprehensive National Amateur Radio Regulations Registry
SUPPORTED_REGULATIONS: Dict[str, NationalRegulation] = {
    "SK": NationalRegulation(
        jurisdiction_code="SK",
        country_name="Slovakia (Slovenská republika)",
        authority_name="Úrad pre reguláciu elektronických komunikácií a poštových služieb (RÚ)",
        regulation_name="Všeobecné povolenie pre amatérsku službu a Zákon o elektronických komunikáciách",
        statute_citation="Zákon č. 452/2021 Z. z. a Všeobecné povolenie RÚ č. 1/2014",
        station_id_interval_min=10,
        station_id_rule="Volacia značka stanice musí byť vysielaná na začiatku a na konci každého spojenia a v intervaloch nie dlhších ako 10 minút.",
        prohibitions=[
            "Komerčné správy a vysielanie v prospech tretích osôb za odplatu",
            "Vysielanie hudby, zábavných relácií a rozhlasové vysielanie",
            "Šifrovanie a kódovanie správ s cieľom utajiť ich význam",
            "Vulgarizmy, neslušné, hanlivé alebo urážlivé výrazy",
            "Zneužitie tiesňových a núdzových volaní",
        ],
        primary_language="sk",
        phonetic_alphabet_standard="Medzinárodná hláskovacia tabuľka ICAO/ITU (Alfa, Bravo...) a Slovenská hláskovacia tabuľka STN (Adam, Božena, Cyril, Dávid, Emil, František...).",
        etiquette_notes="Rádioamatérske pozdravy: '73' (veľa úspechov / s pozdravom), 'QSL' (potvrdenie príjmu), 'príjem' (odovzdanie slova), 'dopočutia na pásme'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (SLOVAKIA - RÚ):\n"
            "- You operate under the strict jurisdiction of the Slovak Republic telecommunications regulator: "
            "Úrad pre reguláciu elektronických komunikácií a poštových služieb (RÚ) pursuant to Zákon č. 452/2021 Z. z.\n"
            "- Mandatory Station Identification: You MUST identify your station with your callsign {callsign} "
            "at the beginning and end of each transmission and at intervals not exceeding 10 minutes.\n"
            "- National Prohibitions: Strictly NO commercial traffic, NO broadcasting of music, NO encrypted speech "
            "intended to obscure meaning, and NO profane or offensive language under Slovak amateur radio regulations.\n"
            "- Language & Tone: Maintain standard Slovak amateur radio courtesies (73, QSL, príjem)."
        ),
    ),
    "CZ": NationalRegulation(
        jurisdiction_code="CZ",
        country_name="Czech Republic (Česká republika)",
        authority_name="Český telekomunikační úřad (ČTÚ)",
        regulation_name="Vyhláška o technických a provozních podmínkách amatérské radiokomunikační služby",
        statute_citation="Vyhláška č. 156/2005 Sb. a Zákon o elektronických komunikacích č. 127/2005 Sb.",
        station_id_interval_min=10,
        station_id_rule="Stanice se musí identifikovat svou volací značkou na začátku a konci každého spojení a nejméně jednou za 10 minut během spojení.",
        prohibitions=[
            "Komerční zprávy a vysílání za úplatu",
            "Vysílání hudby a rozhlasových pořadů",
            "Kódování a šifrování zpráv za účelem zatajení obsahu",
            "Nevhodný, vulgární nebo hanlivý jazyk",
        ],
        primary_language="cs",
        phonetic_alphabet_standard="Mezinárodní hláskovací tabulka ITU (Alfa, Bravo...) a Česká hláskovací tabulka ČSN (Adam, Božena, Cyril, David, Emil, František...).",
        etiquette_notes="Radioamatérské pozdravy: '73' (srdečný pozdrav), 'QSL' (potvrzení), 'příjem' (předání slova), 'naslyšenou na pásmu'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (CZECH REPUBLIC - ČTÚ):\n"
            "- You operate under the jurisdiction of Český telekomunikační úřad (ČTÚ) pursuant to Vyhláška č. 156/2005 Sb.\n"
            "- Mandatory Station Identification: You MUST identify your station with your callsign {callsign} "
            "at the beginning, end, and at intervals not exceeding 10 minutes.\n"
            "- National Prohibitions: Strictly NO commercial transmissions, NO music broadcasting, NO secret codes or encryption, "
            "and NO vulgar or defamatory speech under ČTÚ regulations.\n"
            "- Language & Tone: Follow polite Czech amateur radio conventions (73, QSL, příjem)."
        ),
    ),
    "DE": NationalRegulation(
        jurisdiction_code="DE",
        country_name="Germany (Deutschland)",
        authority_name="Bundesnetzagentur (BNetzA)",
        regulation_name="Gesetz über den Amateurfunk (AFuG) und Amateurfunkverordnung (AFuV)",
        statute_citation="AFuG § 1ff. und Verordnung zum Gesetz über den Amateurfunk (AFuV)",
        station_id_interval_min=10,
        station_id_rule="Das zugeteilte personengebundene Rufzeichen ist zu Beginn und am Ende jeder Funkverbindung sowie in angemessenen Abständen (mindestens alle 10 Minuten) auszusenden.",
        prohibitions=[
            "Kommerzielle und geschäftliche Übertragungen sowie Werbung",
            "Aussendung von Musik, Rundfunkbeiträgen und Unterhaltungssendungen",
            "Verschlüsselung von Aussendungen zur Verschleierung des Inhalts",
            "Unanständige, beleidigende oder obszöne Sprache",
        ],
        primary_language="de",
        phonetic_alphabet_standard="Internationales ICAO/ITU-Buchstabieralphabet (Alfa, Bravo...) und deutsches Buchstabieralphabet nach DIN 5009 (Anton, Berta, Cäsar, Dora, Emil...).",
        etiquette_notes="Amateurfunk-Höflichkeitsformeln: '73' (Viele Grüße), 'Roger / Verstanden', 'Kommen / Bitte kommen' (Übergabe des Durchgangs), 'Auf Wiederhören'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (GERMANY - BNETZA):\n"
            "- You operate under the jurisdiction of the Bundesnetzagentur (BNetzA) pursuant to the Amateurfunkgesetz (AFuG) and AFuV.\n"
            "- Mandatory Station Identification: You MUST identify station {callsign} at the start and end of each QSO, "
            "and at least once every 10 minutes.\n"
            "- National Prohibitions: Strictly NO commercial traffic, NO music broadcasts, NO content encryption, and NO offensive speech.\n"
            "- Language & Tone: Maintain professional German amateur radio etiquette (73, Roger, Kommen)."
        ),
    ),
    "US": NationalRegulation(
        jurisdiction_code="US",
        country_name="United States of America",
        authority_name="Federal Communications Commission (FCC)",
        regulation_name="FCC Rules and Regulations Title 47 Part 97 (Amateur Radio Service)",
        statute_citation="47 CFR Part 97 (§ 97.113, § 97.119)",
        station_id_interval_min=10,
        station_id_rule="Each amateur station must transmit its assigned call sign on its transmitting channel at the end of each communication, and at least every 10 minutes during a communication (§ 97.119).",
        prohibitions=[
            "Communications in which the station has a pecuniary interest or commercial solicitation (§ 97.113(a)(2))",
            "Broadcast of music, sound effects, or entertainment (§ 97.113(a)(4))",
            "Obscene or indecent words or language (§ 97.113(a)(4))",
            "Messages encoded for the purpose of obscuring their meaning (§ 97.113(a)(4))",
            "False or deceptive signals or call signs (§ 97.113(a)(4))",
        ],
        primary_language="en",
        phonetic_alphabet_standard="ITU / NATO phonetic alphabet (Alfa, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel...).",
        etiquette_notes="Ham courtesy: '73' (Best regards), 'Roger', 'QSL', 'Over' (passing transmission), 'Clear'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (UNITED STATES - FCC PART 97):\n"
            "- You operate under the Federal Communications Commission (FCC) Amateur Radio Service rules (47 CFR Part 97).\n"
            "- Mandatory Station Identification: You MUST identify your station with your callsign {callsign} "
            "at the end of each communication and at intervals not exceeding 10 minutes (§ 97.119).\n"
            "- National Prohibitions: Strictly NO communications involving pecuniary interest or commercial solicitation (§ 97.113), "
            "NO broadcasting of music, NO obscene or profane language, and NO encrypted speech hiding meaning.\n"
            "- Language & Tone: Standard American ham radio courtesies and concise exchanges."
        ),
    ),
    "UK": NationalRegulation(
        jurisdiction_code="UK",
        country_name="United Kingdom",
        authority_name="Office of Communications (Ofcom)",
        regulation_name="Ofcom Amateur Radio Licence Terms and Conditions (Wireless Telegraphy Act)",
        statute_citation="Wireless Telegraphy Act 2006 & Ofcom Amateur Radio Licence (BR68)",
        station_id_interval_min=15,
        station_id_rule="The station must transmit its call sign at least once every 15 minutes, and at the beginning and end of each period of transmission.",
        prohibitions=[
            "Commercial messages, advertising, and pecuniary gain",
            "Broadcasting of recorded music or general public entertainment",
            "Encrypted transmissions intended to obscure meaning",
            "Offensive, indecent, or abusive language",
        ],
        primary_language="en",
        phonetic_alphabet_standard="NATO / ITU phonetic alphabet (Alfa, Bravo, Charlie, Delta...).",
        etiquette_notes="Ham courtesy: '73', 'Best 73s', 'Roger', 'Over to you', 'Clear'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (UNITED KINGDOM - OFCOM):\n"
            "- You operate under the jurisdiction of the Office of Communications (Ofcom) pursuant to the Wireless Telegraphy Act.\n"
            "- Mandatory Station Identification: Transmit your callsign {callsign} at the start, end, and at intervals not exceeding 15 minutes.\n"
            "- National Prohibitions: Strictly NO commercial traffic, NO music broadcasts, NO encryption obscuring meaning, and NO offensive speech.\n"
            "- Language & Tone: British amateur radio etiquette and clear phonetics."
        ),
    ),
    "FR": NationalRegulation(
        jurisdiction_code="FR",
        country_name="France (République française)",
        authority_name="ARCEP & ANFR",
        regulation_name="Réglementation des services d'amateur (Code des postes et des communications électroniques)",
        statute_citation="Arrêté du 21 septembre 2000 modifié et CPCE Art. L.33-1",
        station_id_interval_min=15,
        station_id_rule="L'indicatif d'appel doit être transmis au début et à la fin de chaque période d'émission et au moins toutes les 15 minutes.",
        prohibitions=[
            "Communications commerciales ou publicitaires",
            "Diffusion de musique et programmes de divertissement",
            "Chiffrement ou codes secrets destinés à dissimuler le sens",
            "Propos injurieux, obscènes ou contraires à l'ordre public",
        ],
        primary_language="fr",
        phonetic_alphabet_standard="Alphabet phonétique international de l'UIT (Alfa, Bravo, Charlie, Delta, Echo...).",
        etiquette_notes="Courtoisie radioamateur: '73' (amitiés), 'QSL' (bien reçu), 'à vous' (passage du micro), 'au plaisir de se recroiser sur l'air'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (FRANCE - ARCEP / ANFR):\n"
            "- You operate under the regulations of ARCEP and ANFR (Réglementation des services d'amateur en France).\n"
            "- Mandatory Station Identification: Transmit station callsign {callsign} at start, end, and at intervals not exceeding 15 minutes.\n"
            "- National Prohibitions: Strictly NO commercial traffic, NO music broadcasting, NO cryptography obscuring content, NO obscene language.\n"
            "- Language & Tone: Professional French radioamateur courtesies (73, bien reçu, à vous)."
        ),
    ),
    "ES": NationalRegulation(
        jurisdiction_code="ES",
        country_name="Spain (España)",
        authority_name="Ministerio para la Transformación Digital y SETID / CNMC",
        regulation_name="Reglamento de uso del dominio público radioeléctrico por radioaficionados",
        statute_citation="Orden IET/1311/2013 y Ley 11/2022 General de Telecomunicaciones",
        station_id_interval_min=10,
        station_id_rule="El distintivo de llamada debe ser transmitido al comienzo y al final de cada comunicación, y al menos una vez cada 10 minutos.",
        prohibitions=[
            "Comunicaciones con fines comerciales o de lucro",
            "Retransmisión de música o programas de radiodifusión",
            "Cifrado de mensajes destinado a ocultar su significado",
            "Lenguaje soez, ofensivo o indecoroso",
        ],
        primary_language="es",
        phonetic_alphabet_standard="Alfabeto fonético internacional UIT (Alfa, Bravo, Charlie, Delta, Eco, Foxtrot...).",
        etiquette_notes="Cortesía de radioaficionado: '73' (cordiales saludos), 'recibido / enterado', 'cambio' (pase de transmisión), 'buenas tardes colega'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (SPAIN - SETID / CNMC):\n"
            "- You operate under the Spanish Radio Amateur Regulations (Reglamento de Radioaficionados de España).\n"
            "- Mandatory Station Identification: You MUST identify with callsign {callsign} at start, end, and at least every 10 minutes.\n"
            "- National Prohibitions: Strictly NO commercial messages, NO music transmissions, NO encrypted messages, NO foul language.\n"
            "- Language & Tone: Respectful Spanish amateur radio etiquette (73, recibido, cambio)."
        ),
    ),
    "IT": NationalRegulation(
        jurisdiction_code="IT",
        country_name="Italy (Italia)",
        authority_name="Ministero delle Imprese e del Made in Italy (MIMIT)",
        regulation_name="Codice delle comunicazioni elettroniche (Servizio di radioamatore)",
        statute_citation="D.Lgs. 1 agosto 2003, n. 259 (Allegato 26)",
        station_id_interval_min=10,
        station_id_rule="Il nominativo di chiamata deve essere trasmesso all'inizio, al termine del collegamento e ad intervalli non superiori a 10 minuti.",
        prohibitions=[
            "Comunicazioni commerciali e a scopo di lucro",
            "Diffusione di musica o intrattenimento",
            "Uso di linguaggi segreti o cifrati volti a nascondere il significato",
            "Linguaggio ingiurioso, osceno o indecoroso",
        ],
        primary_language="it",
        phonetic_alphabet_standard="Alfabeto fonetico internazionale ICAO/ITU (Alfa, Bravo, Charlie...) e alfabeto telefonico italiano (Ancona, Bologna, Como, Domodossola...).",
        etiquette_notes="Cortesia radioamatoriale: '73' (cordiali saluti), 'QSL / ricevuto', 'a te il cambio', 'a risentirci'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (ITALY - MIMIT):\n"
            "- You operate under the Italian electronic communications code (D.Lgs. 259/2003 Allegato 26 - Servizio Radioamatoriale).\n"
            "- Mandatory Station Identification: Transmit callsign {callsign} at start, end, and intervals not exceeding 10 minutes.\n"
            "- National Prohibitions: Strictly NO commercial activity, NO music, NO encrypted traffic, NO offensive language.\n"
            "- Language & Tone: Authentic Italian amateur radio conventions (73, ricevuto, cambio)."
        ),
    ),
    "PL": NationalRegulation(
        jurisdiction_code="PL",
        country_name="Poland (Polska)",
        authority_name="Urząd Komunikacji Elektronicznej (UKE)",
        regulation_name="Prawo Komunikacji Elektronicznej i przepisy o służbie radiokomunikacyjnej amatorskiej",
        statute_citation="Ustawa Prawo Komunikacji Elektronicznej i Rozporządzenie MAiC ws. urządzeń radiowych",
        station_id_interval_min=10,
        station_id_rule="Znak wywoławczy stacji musi być nadawany na początku, na końcu łączności oraz co najmniej raz na 10 minut w trakcie jej trwania.",
        prohibitions=[
            "Transmisje komercyjne, reklamowe i zarobkowe",
            "Nadawanie muzyki oraz audycji rozrywkowych",
            "Stosowanie kodów i szyfrów mających na celu ukrycie treści",
            "Słowa wulgarne, nieprzyzwoite lub obraźliwe",
        ],
        primary_language="pl",
        phonetic_alphabet_standard="Międzynarodowa tabela literowania ITU (Alfa, Bravo...) oraz polska tabela literowania (Adam, Bogdan, Cezary, Dorota, Edward, Franciszek...).",
        etiquette_notes="Zwroty krótkofalarskie: '73' (serdeczne pozdrowienia), 'QSL / odbiór', 'do usłyszenia na paśmie'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (POLAND - UKE):\n"
            "- You operate under the jurisdiction of Urząd Komunikacji Elektronicznej (UKE) in Poland.\n"
            "- Mandatory Station Identification: Identify with callsign {callsign} at start, end, and every 10 minutes.\n"
            "- National Prohibitions: Strictly NO commercial traffic, NO music broadcasts, NO encryption hiding content, NO vulgar language.\n"
            "- Language & Tone: Traditional Polish shortwave etiquette (73, odbiór, do usłyszenia)."
        ),
    ),
    "JA": NationalRegulation(
        jurisdiction_code="JA",
        country_name="Japan (日本)",
        authority_name="Ministry of Internal Affairs and Communications (総務省 総合通信局 - MIC)",
        regulation_name="Radio Act (電波法) and Amateur Radio Operation Regulations",
        statute_citation="電波法 昭和25年法律第131号 及び 無線局運用規則",
        station_id_interval_min=10,
        station_id_rule="識別信号（呼出符号）は、通信の開始時、終了時、および通信中おおむね10分ごとに送信しなければならない。",
        prohibitions=[
            "営利を目的とする通信（商業広告、商取引）",
            "音楽等の放送および娯楽送信",
            "通信の秘密を害する暗号や秘密符丁の使用",
            "電波の秩序を乱す不適切な発言や暴言",
        ],
        primary_language="ja",
        phonetic_alphabet_standard="ITU国際通話表 (Alfa, Bravo, Charlie...) および 和文通話表 (朝日のア、いろはのイ...).",
        etiquette_notes="アマチュア無線マナー: '73' (ベストリガーズ / さようなら), 'ラジャー' (了解), 'どうぞ' (送信交代).",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (JAPAN - MIC / 電波法):\n"
            "- You operate under the jurisdiction of the Ministry of Internal Affairs and Communications (総務省) pursuant to the Radio Act (電波法).\n"
            "- Mandatory Station Identification: You MUST transmit your callsign {callsign} at the beginning, end, and at intervals of approx 10 minutes.\n"
            "- National Prohibitions: Strictly NO commercial transmissions, NO music broadcasting, NO secret codes, NO foul language.\n"
            "- Language & Tone: Polite Japanese amateur radio protocol (どうぞ, ラジャー, 73)."
        ),
    ),
    "ITU": NationalRegulation(
        jurisdiction_code="ITU",
        country_name="International (ITU Radio Regulations)",
        authority_name="International Telecommunication Union (ITU)",
        regulation_name="ITU Radio Regulations (Article 25 - Amateur Services)",
        statute_citation="ITU Radio Regulations (RR) Article 25",
        station_id_interval_min=10,
        station_id_rule="Amateur stations shall transmit their call sign at short intervals during transmissions and at the end of each exchange.",
        prohibitions=[
            "Commercial communications or transmissions of pecuniary interest",
            "Broadcasting to the general public or transmission of music",
            "Encrypted transmissions intended to obscure the plain meaning",
            "Indecent, profane, or defamatory language",
        ],
        primary_language="en",
        phonetic_alphabet_standard="ITU phonetic alphabet (Alfa, Bravo, Charlie, Delta, Echo, Foxtrot...).",
        etiquette_notes="Standard international amateur radio etiquette: '73', 'QSL', 'Roger', 'Over'.",
        regulatory_prompt_clause=(
            "REGULATORY JURISDICTION & NATIONAL LAW (INTERNATIONAL - ITU ARTICLE 25):\n"
            "- You operate under the International Telecommunication Union (ITU) Radio Regulations (Article 25).\n"
            "- Mandatory Station Identification: You MUST identify your station with your callsign {callsign} at short intervals (max 10 minutes) and upon signing off.\n"
            "- International Prohibitions: Strictly NO commercial traffic, NO entertainment/music broadcasting, NO secret encryption, NO profanity.\n"
            "- Language & Tone: Courteous amateur radio operating practice."
        ),
    ),
}


# ITU Callsign Prefix Allocation Table (Prefix Pattern -> Jurisdiction Code)
# Matches callsign prefix to ITU allocated country regulatory authority
CALLSIGN_PREFIX_MAP = [
    # Slovakia
    (re.compile(r"^OM", re.I), "SK"),
    # Czech Republic
    (re.compile(r"^(OK|OL)", re.I), "CZ"),
    # Germany
    (re.compile(r"^(DA|DB|DC|DD|DE|DF|DG|DH|DI|DJ|DK|DL|DM|DO|DP|Y[2-9])", re.I), "DE"),
    # United States
    (re.compile(r"^(W|K|N|AA|AB|AC|AD|AE|AF|AG|AH|AI|AJ|AK|AL)[0-9]", re.I), "US"),
    # United Kingdom
    (re.compile(r"^(G|M|2E|GD|GI|GJ|GM|GU|GW|ZB|ZC|ZD|ZF|ZG|ZH|ZJ)", re.I), "UK"),
    # France
    (re.compile(r"^(F|TK|FG|FH|FJ|FK|FM|FO|FP|FR|FS|FT|FW|FY|TM|TO|TX)", re.I), "FR"),
    # Spain
    (re.compile(r"^(EA|EB|EC|ED|EE|EF|EG|EH|AM|AN|AO)", re.I), "ES"),
    # Italy
    (re.compile(r"^(I|IA|IB|IC|ID|IE|IF|IG|IH|II|IJ|IK|IL|IM|IN|IO|IP|IQ|IR|IS|IT|IU|IV|IW|IX|IY|IZ)", re.I), "IT"),
    # Poland
    (re.compile(r"^(SP|SQ|SO|SN|SR|3Z|HF)", re.I), "PL"),
    # Japan
    (re.compile(r"^(JA|JH|JR|JE|JF|JG|JI|JJ|JK|JL|JM|JN|JO|JP|JQ|JS|7[J-N]|8[J-N])", re.I), "JA"),
    # Canada
    (re.compile(r"^(VE|VA|VO|VY|CF|CG|CH|CI|CJ|CK|CY|CZ)", re.I), "US"),  # FCC/ISED compatible rules
    # Australia
    (re.compile(r"^(VK|AX|VI|VJ|VL|VN|VZ)", re.I), "UK"),  # Commonwealth / Ofcom compatible
]


# Language code to default national regulatory jurisdiction mapping
LANGUAGE_TO_JURISDICTION_MAP: Dict[str, str] = {
    "sk": "SK",
    "cs": "CZ",
    "de": "DE",
    "en": "US",
    "fr": "FR",
    "es": "ES",
    "it": "IT",
    "pl": "PL",
    "ja": "JA",
    "uk": "ITU",
    "ru": "ITU",
    "nl": "DE",  # CEPT / EU aligned
    "hu": "SK",  # CEPT aligned
    "sv": "ITU",
    "no": "ITU",
    "da": "ITU",
    "fi": "ITU",
    "tr": "ITU",
    "el": "ITU",
    "pt": "ES",  # Ibero-American / CEPT
    "zh": "ITU",
    "ko": "ITU",
    "hi": "ITU",
    "ar": "ITU",
}


def detect_jurisdiction_from_callsign(callsign: str) -> Optional[str]:
    """Detect regulatory jurisdiction code from ITU callsign prefix."""
    clean = callsign.strip().upper()
    for pattern, jurisdiction in CALLSIGN_PREFIX_MAP:
        if pattern.match(clean):
            return jurisdiction
    return None


def resolve_regulation(
    callsign: str,
    language: str = "en",
    regulatory_jurisdiction: str = "auto",
) -> NationalRegulation:
    """
    Resolve active national amateur radio regulation based on explicit jurisdiction,
    callsign prefix, or language code with fallback to ITU international rules.
    """
    explicit = regulatory_jurisdiction.strip().upper() if regulatory_jurisdiction else "AUTO"

    # 1. Explicit override if valid
    if explicit != "AUTO" and explicit in SUPPORTED_REGULATIONS:
        return SUPPORTED_REGULATIONS[explicit]

    # 2. Heuristic from callsign ITU prefix
    detected_from_call = detect_jurisdiction_from_callsign(callsign)
    if detected_from_call and detected_from_call in SUPPORTED_REGULATIONS:
        return SUPPORTED_REGULATIONS[detected_from_call]

    # 3. Fallback from language code
    lang_key = language.strip().lower()
    if lang_key in LANGUAGE_TO_JURISDICTION_MAP:
        jurisdiction = LANGUAGE_TO_JURISDICTION_MAP[lang_key]
        if jurisdiction in SUPPORTED_REGULATIONS:
            return SUPPORTED_REGULATIONS[jurisdiction]

    # 4. Universal fallback
    return SUPPORTED_REGULATIONS["US"] if language.lower().startswith("en") else SUPPORTED_REGULATIONS["ITU"]


def list_supported_regulations() -> List[Dict[str, Any]]:
    """Return list of all supported national regulations for UI/API."""
    return [
        {
            "code": code,
            "country": reg.country_name,
            "authority": reg.authority_name,
            "regulation": reg.regulation_name,
            "statute": reg.statute_citation,
            "id_interval_min": reg.station_id_interval_min,
            "primary_language": reg.primary_language,
        }
        for code, reg in SUPPORTED_REGULATIONS.items()
    ]
