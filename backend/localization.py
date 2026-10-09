"""
Spoken Texts Localization Engine for Amateur Radio AI Transceiver.
Provides multilingual localized spoken messages, canned security refusals,
mock replies, and ITU / national phonetic alphabets.
"""

from typing import Dict, Any, Optional
from backend.regulations import NationalRegulation, resolve_regulation


# Phonetic Alphabets Dictionary
PHONETIC_ALPHABETS = {
    "itu": {
        "A": "Alfa", "B": "Bravo", "C": "Charlie", "D": "Delta", "E": "Echo",
        "F": "Foxtrot", "G": "Golf", "H": "Hotel", "I": "India", "J": "Juliett",
        "K": "Kilo", "L": "Lima", "M": "Mike", "N": "November", "O": "Oscar",
        "P": "Papa", "Q": "Quebec", "R": "Romeo", "S": "Sierra", "T": "Tango",
        "U": "Uniform", "V": "Victor", "W": "Whiskey", "X": "X-ray", "Y": "Yankee",
        "Z": "Zulu", "0": "Zero", "1": "One", "2": "Two", "3": "Three",
        "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine",
        "/": "Stroke"
    },
    "sk": {
        "A": "Adam", "B": "Božena", "C": "Cyril", "D": "Dávid", "E": "Emil",
        "F": "František", "G": "Gustáv", "H": "Helena", "I": "Ivan", "J": "Jozef",
        "K": "Karol", "L": "Ladislav", "M": "Mária", "N": "Norbert", "O": "Oto",
        "P": "Peter", "Q": "Quido", "R": "Rudolf", "S": "Svätopluk", "T": "Tomáš",
        "U": "Urban", "V": "Václav", "W": "Dvojité V", "X": "Xaver", "Y": "Ypsilon",
        "Z": "Zuzana", "0": "Nula", "1": "Jedna", "2": "Dva", "3": "Tri",
        "4": "Štyri", "5": "Päť", "6": "Šesť", "7": "Sedem", "8": "Osem", "9": "Deväť",
        "/": "Lomeno"
    },
    "cs": {
        "A": "Adam", "B": "Božena", "C": "Cyril", "D": "David", "E": "Emil",
        "F": "František", "G": "Gustav", "H": "Helena", "I": "Ivan", "J": "Josef",
        "K": "Karel", "L": "Ludvík", "M": "Marie", "N": "Norbert", "O": "Otakar",
        "P": "Petr", "Q": "Quido", "R": "Rudolf", "S": "Svatopluk", "T": "Tomáš",
        "U": "Urban", "V": "Václav", "W": "Dvojité V", "X": "Xaver", "Y": "Ypsilon",
        "Z": "Zikmund", "0": "Nula", "1": "Jedna", "2": "Dva", "3": "Tři",
        "4": "Čtyři", "5": "Pět", "6": "Šest", "7": "Sedm", "8": "Osm", "9": "Devět",
        "/": "Lomeno"
    },
    "de": {
        "A": "Anton", "B": "Berta", "C": "Cäsar", "D": "Dora", "E": "Emil",
        "F": "Friedrich", "G": "Gustav", "H": "Heinrich", "I": "Ida", "J": "Julius",
        "K": "Kaufmann", "L": "Ludwig", "M": "Martha", "N": "Nordpol", "O": "Otto",
        "P": "Paula", "Q": "Quelle", "R": "Richard", "S": "Samuel", "T": "Theodor",
        "U": "Ulrich", "V": "Viktor", "W": "Wilhelm", "X": "Xanthippe", "Y": "Ypsilon",
        "Z": "Zacharias", "0": "Null", "1": "Eins", "2": "Zwei", "3": "Drei",
        "4": "Vier", "5": "Fünf", "6": "Sechs", "7": "Sieben", "8": "Acht", "9": "Neun",
        "/": "Bruch"
    },
    "fr": {
        "A": "Anatole", "B": "Berthe", "C": "Célestin", "D": "Désiré", "E": "Eugène",
        "F": "François", "G": "Gaston", "H": "Henri", "I": "Isidore", "J": "Jean",
        "K": "Kléber", "L": "Louis", "M": "Marcel", "N": "Nicolas", "O": "Oscar",
        "P": "Pierre", "Q": "Quintal", "R": "Raoul", "S": "Suzanne", "T": "Théodore",
        "U": "Ursule", "V": "Victor", "W": "William", "X": "Xavier", "Y": "Yvonne",
        "Z": "Zoé", "0": "Zéro", "1": "Un", "2": "Deux", "3": "Trois",
        "4": "Quatre", "5": "Cinq", "6": "Six", "7": "Sept", "8": "Huit", "9": "Neuf",
        "/": "Barre"
    },
    "es": {
        "A": "Antonio", "B": "Barcelona", "C": "Carmen", "D": "Dolores", "E": "Enrique",
        "F": "Francia", "G": "Granada", "H": "Historia", "I": "Inés", "J": "José",
        "K": "Kilo", "L": "Lorenzo", "M": "Madrid", "N": "Navarra", "O": "Oviedo",
        "P": "París", "Q": "Queso", "R": "Ramón", "S": "Sevilla", "T": "Toledo",
        "U": "Ulises", "V": "Valencia", "W": "Washington", "X": "Xilófono", "Y": "Yegua",
        "Z": "Zaragoza", "0": "Cero", "1": "Uno", "2": "Dos", "3": "Tres",
        "4": "Cuatro", "5": "Cinco", "6": "Seis", "7": "Siete", "8": "Ocho", "9": "Nueve",
        "/": "Barra"
    },
    "pl": {
        "A": "Adam", "B": "Bogdan", "C": "Cezary", "D": "Dorota", "E": "Edward",
        "F": "Franciszek", "G": "Grażyna", "H": "Henryk", "I": "Irena", "J": "Józef",
        "K": "Karol", "L": "Ludwik", "M": "Marek", "N": "Nikodem", "O": "Olga",
        "P": "Paweł", "Q": "Quantum", "R": "Roman", "S": "Stanisław", "T": "Tadeusz",
        "U": "Urszula", "V": "Violetta", "W": "Wacław", "X": "Xawery", "Y": "Ypsilon",
        "Z": "Zygmunt", "0": "Zero", "1": "Jeden", "2": "Dwa", "3": "Trzy",
        "4": "Cztery", "5": "Pięć", "6": "Sześć", "7": "Siedem", "8": "Osiem", "9": "Dziewięć",
        "/": "Łamane"
    },
    "it": {
        "A": "Ancona", "B": "Bologna", "C": "Como", "D": "Domodossola", "E": "Empoli",
        "F": "Firenze", "G": "Genova", "H": "Hotel", "I": "Imola", "J": "Jolly",
        "K": "Kappa", "L": "Livorno", "M": "Milano", "N": "Napoli", "O": "Otranto",
        "P": "Palermo", "Q": "Quadro", "R": "Roma", "S": "Savona", "T": "Torino",
        "U": "Udine", "V": "Venezia", "W": "Washington", "X": "Xeres", "Y": "York",
        "Z": "Zara", "0": "Zero", "1": "Uno", "2": "Due", "3": "Tre",
        "4": "Quattro", "5": "Cinque", "6": "Sei", "7": "Sette", "8": "Otto", "9": "Nove",
        "/": "Barra"
    },
}


# Multilingual Spoken Texts Master Dictionary
SPOKEN_TEXTS: Dict[str, Dict[str, str]] = {
    # 1. Prompt Injection Refusal
    "prompt_injection_refusal": {
        "en": "{callsign}: Negative copy. Command instruction rejected under amateur radio protocols. QRT.",
        "sk": "{callsign}: Negatívny príjem. Povel bol zamietnutý podľa rádioamatérskych predpisov. QRT.",
        "cs": "{callsign}: Negativní příjem. Příkaz byl zamítnut podle radioamatérských předpisů. QRT.",
        "de": "{callsign}: Negativ aufgenommen. Steuerbefehl gemäß Amateurfunkbetriebsregeln abgelehnt. QRT.",
        "fr": "{callsign}: Reçu négatif. Instruction de commande rejetée selon les protocoles radioamateur. QRT.",
        "es": "{callsign}: Negativo recibido. Instrucción de comando rechazada bajo protocolos de radioaficionado. QRT.",
        "it": "{callsign}: Ricezione negativa. Istruzione di comando rifiutata secondo i protocolli radioamatoriali. QRT.",
        "pl": "{callsign}: Odbiór negatywny. Instrukcja polecenia odrzucona zgodnie z przepisami radioamatorskimi. QRT.",
        "uk": "{callsign}: Не прийнято. Команда відхилена згідно з регламентом аматорського радіозв'язку. QRT.",
        "ru": "{callsign}: Не принято. Команда отклонена согласно регламенту любительской радиосвязи. QRT.",
        "ja": "{callsign}: コピーできません。アマチュア無線のプロトコルに基づきコマンド命令は拒絶されました。QRT。",
        "nl": "{callsign}: Negatief ontvangen. Opdracht geweigerd volgens amateurradioprotocollen. QRT.",
        "pt": "{callsign}: Cópia negativa. Instrução de comando rejeitada sob protocolos de radioamador. QRT.",
        "sv": "{callsign}: Negativ kopia. Kommandoinstruktion avvisad enligt amatörradioprotokoll. QRT.",
        "hu": "{callsign}: Nem vettem. A parancsutasítás elutasítva a rádióamatőr szabályok szerint. QRT.",
    },

    # 2. Profanity / NSFW / Indecent Speech Refusal (Cites national regulation)
    "profanity_nsfw_refusal": {
        "en": "{callsign}: Indecent or profane language prohibited under {regulation_name}. QRT.",
        "sk": "{callsign}: Nevhodné a vulgárne vysielanie je zakázané podľa predpisov {regulation_name}. QRT.",
        "cs": "{callsign}: Nevhodné a vulgární vysílání je zakázáno podle předpisů {regulation_name}. QRT.",
        "de": "{callsign}: Unanständige oder obszöne Sprache ist gemäß {regulation_name} untersagt. QRT.",
        "fr": "{callsign}: Tout langage indécent ou grossier est strictement interdit par {regulation_name}. QRT.",
        "es": "{callsign}: El lenguaje indecente o soez está prohibido según {regulation_name}. QRT.",
        "it": "{callsign}: Linguaggio indecente o profano è vietato ai sensi di {regulation_name}. QRT.",
        "pl": "{callsign}: Nieprzyzwoity lub wulgarny język jest zabroniony na mocy {regulation_name}. QRT.",
        "uk": "{callsign}: Непристойна або нецензурна лексика заборонена згідно з {regulation_name}. QRT.",
        "ru": "{callsign}: Непристойные или нецензурные выражения запрещены согласно {regulation_name}. QRT.",
        "ja": "{callsign}: {regulation_name}に基づき、不適切な言語や猥褻な表現は禁止されています。QRT。",
        "nl": "{callsign}: Onfatsoenlijk of grof taalgebruik is verboden volgens {regulation_name}. QRT.",
        "pt": "{callsign}: Linguagem indecente ou profana é proibida sob {regulation_name}. QRT.",
        "sv": "{callsign}: Oanständigt eller obscent språk är förbjudet enligt {regulation_name}. QRT.",
        "hu": "{callsign}: A trágár vagy illetlen kifejezések használata tiltott a következő szabályzat szerint: {regulation_name}. QRT.",
    },

    # 3. Trolling / Harassment / Defamation Refusal
    "trolling_harassment_refusal": {
        "en": "{callsign}: Abusive or defamatory radio transmissions will not be acknowledged. 73.",
        "sk": "{callsign}: Urážlivé alebo difamujúce rádiové vysielanie nebude potvrdené. 73.",
        "cs": "{callsign}: Urážlivé nebo hanlivé radiové vysílání nebude potvrzeno. 73.",
        "de": "{callsign}: Beleidigende oder diffamierende Funkübertragungen werden nicht bestätigt. 73.",
        "fr": "{callsign}: Les transmissions radio injurieuses ou diffamatoires ne seront pas prises en compte. 73.",
        "es": "{callsign}: Las transmisiones de radio ofensivas o difamatorias no serán atendidas. 73.",
        "it": "{callsign}: Trasmissioni offensive o diffamatorie non riceveranno risposta. 73.",
        "pl": "{callsign}: Obraźliwe lub zniesławiające transmisje radiowe nie będą potwierdzane. 73.",
        "uk": "{callsign}: Образливі або наклепницькі радіопередачі не будуть прийняті. 73.",
        "ru": "{callsign}: Оскорбительные или порочащие радиопередачи не будут подтверждаться. 73.",
        "ja": "{callsign}: 誹謗中傷や侮辱的な無線通信には応答いたしません。73。",
        "nl": "{callsign}: Aanstootgevende of lasterlijke radio-uitzendingen worden niet beantwoord. 73.",
        "pt": "{callsign}: Transmissões de rádio ofensivas ou difamatórias não serão atendidas. 73.",
        "sv": "{callsign}: Kränkande eller förolämpande radiosändningar kommer inte att besvaras. 73.",
        "hu": "{callsign}: Sértő vagy rágalmazó rádióadásra nem válaszolunk. 73.",
    },

    # 4. Commercial / Illegal Traffic Refusal (Cites national regulation)
    "illegal_traffic_refusal": {
        "en": "{callsign}: Commercial solicitations are prohibited on amateur radio bands under {regulation_name}. QRT.",
        "sk": "{callsign}: Komerčné ponuky a vysielanie sú na rádioamatérskych pásmach zakázané podľa {regulation_name}. QRT.",
        "cs": "{callsign}: Komerční nabídky a vysílání jsou na radioamatérských pásmech zakázány podle {regulation_name}. QRT.",
        "de": "{callsign}: Kommerzielle Aussendungen sind auf Amateurfunkbändern gemäß {regulation_name} verboten. QRT.",
        "fr": "{callsign}: Les sollicitations commerciales sont interdites sur les bandes radioamateurs selon {regulation_name}. QRT.",
        "es": "{callsign}: Las comunicaciones comerciales están prohibidas en las bandas de radioaficionados según {regulation_name}. QRT.",
        "it": "{callsign}: Le comunicazioni commerciali sono vietate sulle bande radioamatoriali ai sensi di {regulation_name}. QRT.",
        "pl": "{callsign}: Transmisje komercyjne są zabronione w pasmach radioamatorskich zgodnie z {regulation_name}. QRT.",
        "uk": "{callsign}: Комерційні повідомлення заборонені в аматорських радіодіапазонах згідно з {regulation_name}. QRT.",
        "ru": "{callsign}: Коммерческие сообщения запрещены в любительских радиодиапазонах согласно {regulation_name}. QRT.",
        "ja": "{callsign}: {regulation_name}に基づき、アマチュア無線帯での営利目的の通信は禁止されています。QRT。",
        "nl": "{callsign}: Commerciële berichten zijn verboden op amateurradiobanden volgens {regulation_name}. QRT.",
        "pt": "{callsign}: Mensagens comerciais são proibidas nas faixas de radioamador sob {regulation_name}. QRT.",
        "sv": "{callsign}: Kommersiella meddelanden är förbjudna på amatörradioband enligt {regulation_name}. QRT.",
        "hu": "{callsign}: Kereskedelmi célú adások tiltottak a rádióamatőr sávokban a következő szerint: {regulation_name}. QRT.",
    },

    # 5. Output Filter Suppression
    "filter_suppressed": {
        "en": "{callsign}: Transmission terminated due to content filter.",
        "sk": "{callsign}: Vysielanie prerušené filtrom obsahu.",
        "cs": "{callsign}: Vysílání přerušeno filtrem obsahu.",
        "de": "{callsign}: Aussendung durch Inhaltsfilter beendet.",
        "fr": "{callsign}: Transmission interrompue par le filtre de contenu.",
        "es": "{callsign}: Transmisión interrumpida por el filtro de contenido.",
        "it": "{callsign}: Trasmissione interrotta dal filtro contenuti.",
        "pl": "{callsign}: Transmisja przerwana przez filtr treści.",
        "uk": "{callsign}: Передачу перервано фільтром вмісту.",
        "ru": "{callsign}: Передача прервана фильтром содержимого.",
        "ja": "{callsign}: コンテンツフィルターにより送信を中断しました。",
        "nl": "{callsign}: Uitzending beëindigd door inhoudsfilter.",
        "pt": "{callsign}: Transmissão interrompida pelo filtro de conteúdo.",
        "sv": "{callsign}: Sändningen avbröts av innehållsfiltret.",
        "hu": "{callsign}: Az adás megszakítva a tartalomszűrő miatt.",
    },

    # 6. Stand By
    "standby": {
        "en": "{callsign}: Stand by.",
        "sk": "{callsign}: Moment, čakajte.",
        "cs": "{callsign}: Moment, čekejte.",
        "de": "{callsign}: Bitte warten.",
        "fr": "{callsign}: Patientez.",
        "es": "{callsign}: En espera.",
        "it": "{callsign}: Restate in ascolto.",
        "pl": "{callsign}: Proszę czekać.",
        "uk": "{callsign}: Зачекайте.",
        "ru": "{callsign}: Минутку, ждите.",
        "ja": "{callsign}: スタンバイ。",
        "nl": "{callsign}: Een ogenblik geduld.",
        "pt": "{callsign}: Aguarde.",
        "sv": "{callsign}: Vänta.",
        "hu": "{callsign}: Kérem várjon.",
    },

    # 7. Negative Copy
    "negative_copy": {
        "en": "{callsign}: Negative copy.",
        "sk": "{callsign}: Negatívny príjem.",
        "cs": "{callsign}: Negativní příjem.",
        "de": "{callsign}: Negativ aufgenommen.",
        "fr": "{callsign}: Reçu négatif.",
        "es": "{callsign}: Copia negativa.",
        "it": "{callsign}: Copia negativa.",
        "pl": "{callsign}: Odbiór negatywny.",
        "uk": "{callsign}: Не прийнято.",
        "ru": "{callsign}: Не принято.",
        "ja": "{callsign}: 受信不能。",
        "nl": "{callsign}: Negatief ontvangen.",
        "pt": "{callsign}: Cópia negativa.",
        "sv": "{callsign}: Negativ kopia.",
        "hu": "{callsign}: Nem vettem.",
    },

    # 8. Mock / Simulated QSO Response
    "mock_qso_reply": {
        "en": "{callsign} roger copy your signal 59 on {band}. 73!",
        "sk": "{callsign} roger, príjem vášho signálu 59 na pásme {band}. 73!",
        "cs": "{callsign} roger, příjem vašeho signálu 59 na pásmu {band}. 73!",
        "de": "{callsign} Roger, Signal 59 auf dem {band}-Band empfangen. 73!",
        "fr": "{callsign} bien reçu, votre signal est 59 sur la bande {band}. 73!",
        "es": "{callsign} recibido, señal 59 en la banda de {band}. 73!",
        "it": "{callsign} ricevuto, segnale 59 sulla banda dei {band}. 73!",
        "pl": "{callsign} roger, odbieram sygnał 59 na paśmie {band}. 73!",
        "uk": "{callsign} прийнято, ваш сигнал 59 на діапазоні {band}. 73!",
        "ru": "{callsign} принято, ваш сигнал 59 на диапазоне {band}. 73!",
        "ja": "{callsign} ラジャー、{band}にてシグナル59で受信しました。73!",
        "nl": "{callsign} roger, uw signaal 59 ontvangen op de {band}-band. 73!",
        "pt": "{callsign} copiado, seu sinal 59 na faixa de {band}. 73!",
        "sv": "{callsign} roger, mottagit din signal 59 på {band}-bandet. 73!",
        "hu": "{callsign} vettem, a jeled 59 a(z) {band} sávban. 73!",
    },
}


# Localized Band Name Translations
BAND_NAMES: Dict[str, Dict[str, str]] = {
    "20m": {
        "en": "20 meters", "sk": "20 metrov", "cs": "20 metrů", "de": "20 Meter",
        "fr": "20 mètres", "es": "20 metros", "it": "20 metri", "pl": "20 metrów",
        "ja": "20mバンド", "ru": "20 метров", "uk": "20 метрів",
    },
    "40m": {
        "en": "40 meters", "sk": "40 metrov", "cs": "40 metrů", "de": "40 Meter",
        "fr": "40 mètres", "es": "40 metros", "it": "40 metri", "pl": "40 metrów",
        "ja": "40mバンド", "ru": "40 метров", "uk": "40 метрів",
    },
    "2m": {
        "en": "2 meters", "sk": "2 metre", "cs": "2 metry", "de": "2 Meter",
        "fr": "2 mètres", "es": "2 metros", "it": "2 metri", "pl": "2 metry",
        "ja": "2mバンド", "ru": "2 метра", "uk": "2 метри",
    },
    "70cm": {
        "en": "70 centimeters", "sk": "70 centimetrov", "cs": "70 centimetrů", "de": "70 Zentimeter",
        "fr": "70 centimètres", "es": "70 centímetros", "it": "70 centimetri", "pl": "70 centymetrów",
        "ja": "70cmバンド", "ru": "70 сантиметров", "uk": "70 сантиметрів",
    },
}


def get_spoken_text(
    key: str,
    language: str = "en",
    callsign: str = "AI7HAM",
    regulation: Optional[NationalRegulation] = None,
    band: str = "20 meters",
    **kwargs
) -> str:
    """
    Retrieve and format localized spoken radio text for a given message key.
    Includes national regulation authority citation where appropriate.
    """
    lang = language.strip().lower()
    table = SPOKEN_TEXTS.get(key, {})

    # Match language code or fallback to English
    template = table.get(lang)
    if not template and "-" in lang:
        template = table.get(lang.split("-")[0])
    if not template:
        template = table.get("en", f"{callsign}: Message.")

    # Determine regulation citation
    reg_name = "amateur radio regulations"
    if regulation:
        reg_name = regulation.authority_name or regulation.regulation_name
    elif "regulation_name" in kwargs:
        reg_name = kwargs["regulation_name"]

    # Format localized band string if key is mock QSO
    if "band" in template and band in BAND_NAMES:
        band = BAND_NAMES[band].get(lang, band)

    format_args = {
        "callsign": callsign,
        "regulation_name": reg_name,
        "band": band,
    }
    format_args.update(kwargs)

    try:
        return template.format(**format_args)
    except Exception:
        return template


def get_phonetic_callsign(callsign: str, language: str = "en", use_national: bool = False) -> str:
    """
    Format callsign into spoken phonetic words.
    Uses ITU phonetic alphabet or national phonetic alphabet (e.g. STN for SK, ČSN for CS, DIN 5009 for DE).
    """
    clean = callsign.strip().upper()
    lang = language.strip().lower()
    alphabet = PHONETIC_ALPHABETS.get(lang if use_national else "itu", PHONETIC_ALPHABETS["itu"])

    words = []
    for ch in clean:
        if ch in alphabet:
            words.append(alphabet[ch])
        elif ch in PHONETIC_ALPHABETS["itu"]:
            words.append(PHONETIC_ALPHABETS["itu"][ch])
        else:
            words.append(ch)
    return " ".join(words)
