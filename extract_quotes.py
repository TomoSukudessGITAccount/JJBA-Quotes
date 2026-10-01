import csv
import html
import re
import requests

API = "https://jojowiki.com/api.php"
OUTPUT = "jojo quotes.csv"

# ============================================================
# CONFIGURAÇÃO
# Coloque aqui os personagens que você quer no Bonjourr.
# ============================================================

CHARACTERS = [
    "Jonathan Joestar",
    "Joseph Joestar",
    "Jotaro Kujo",
    "Josuke Higashikata",
    "Giorno Giovanna",
    "Jolyne Cujoh",

    "Dio Brando",
    "DIO",
    "Enrico Pucci",

    "Robert E. O. Speedwagon",
    "Caesar Anthonio Zeppeli",
    "Jean Pierre Polnareff",
    "Okuyasu Nijimura",
    "Bruno Bucciarati",
    "Pannacotta Fugo",
    "Ermes Costello",

    # Quando quiser entrar em SBR:
    # "Johnny Joestar",
    # "Gyro Zeppeli",
    # "Diego Brando",
]


def get_wikitext(page):
    """Obtém o código-fonte MediaWiki de uma página."""

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "titles": page,
    }

    response = requests.get(
        API,
        params=params,
        timeout=30,
        headers={
            "User-Agent": "TomoSuku-JoJoQuotes/1.0"
        },
    )

    response.raise_for_status()

    data = response.json()
    pages = data["query"]["pages"]

    if not pages or pages[0].get("missing"):
        print(f"⚠ Página não encontrada: {page}")
        return None

    return pages[0]["revisions"][0]["slots"]["main"]["content"]


def find_templates(text, template_names=("Q", "Quote")):
    """
    Procura templates MediaWiki respeitando templates aninhados.

    Exemplo:
    {{Q|{{Nihongo|Hello|こんにちは}}|{{Ch|Chapter 1}}}}
    """

    results = []
    lower = text.lower()

    i = 0

    while i < len(text):

        matched = None

        for name in template_names:
            marker = "{{" + name.lower()

            if lower.startswith(marker, i):
                after = i + len(marker)

                # Evita capturar coisas como {{QuoteBox}}
                if after < len(text) and text[after] not in "| \n}":
                    continue

                matched = name
                break

        if not matched:
            i += 1
            continue

        start = i
        depth = 0
        j = i

        while j < len(text) - 1:

            if text[j:j+2] == "{{":
                depth += 1
                j += 2
                continue

            if text[j:j+2] == "}}":
                depth -= 1
                j += 2

                if depth == 0:
                    results.append(text[start:j])
                    i = j
                    break

                continue

            j += 1

        else:
            i += 1

    return results


def split_template_parameters(template):
    """
    Divide parâmetros apenas quando | está no nível principal.

    Assim:
    {{Q|{{Nihongo|Hello|こんにちは}}|{{Ch|Chapter 1}}}}

    não quebra o Nihongo no meio.
    """

    inner = template[2:-2]

    first_pipe = inner.find("|")

    if first_pipe == -1:
        return []

    content = inner[first_pipe + 1:]

    parameters = []
    current = []
    depth = 0

    i = 0

    while i < len(content):

        if content[i:i+2] == "{{":
            depth += 1
            current.append("{{")
            i += 2
            continue

        if content[i:i+2] == "}}":
            depth -= 1
            current.append("}}")
            i += 2
            continue

        if content[i] == "|" and depth == 0:
            parameters.append("".join(current))
            current = []
        else:
            current.append(content[i])

        i += 1

    parameters.append("".join(current))

    return parameters


def clean_wikitext(text):
    """Transforma markup MediaWiki em texto normal."""

    # --------------------------------------------------------
    # Nihongo:
    # {{Nihongo|English text|Japanese|Romanization}}
    #
    # Mantemos apenas o primeiro parâmetro.
    # --------------------------------------------------------

    nihongo_pattern = re.compile(
        r"\{\{(?:Nihongo|nihongo|Nihongo2)"
        r"\|([^{}|]*(?:\{\{.*?\}\}[^{}|]*)?)"
        r"(?:\|.*?)?\}\}",
        flags=re.DOTALL,
    )

    previous = None

    while previous != text:
        previous = text
        text = nihongo_pattern.sub(r"\1", text)

    # --------------------------------------------------------
    # Links:
    #
    # [[Jotaro Kujo]]       -> Jotaro Kujo
    # [[DIO|Dio]]           -> Dio
    # --------------------------------------------------------

    text = re.sub(
        r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]",
        r"\1",
        text
    )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)

    # --------------------------------------------------------
    # Formatação Wiki
    # --------------------------------------------------------

    text = text.replace("'''", "")
    text = text.replace("''", "")

    # Remove templates restantes
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)

    # Decodifica &quot;, &amp;, etc.
    text = html.unescape(text)

    # Espaços
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_quotes(wikitext):
    quotes = []

    templates = find_templates(wikitext)

    for template in templates:

        params = split_template_parameters(template)

        if not params:
            continue

        quote = clean_wikitext(params[0])

        # Ignora lixo ou frases absurdamente pequenas
        if len(quote) < 4:
            continue

        quotes.append(quote)

    return quotes


def main():

    collected = []
    seen = set()

    print("=== JoJoWiki Quote Extractor ===\n")

    for character in CHARACTERS:

        print(f"🔎 {character}")

        try:
            text = get_wikitext(character)

            if not text:
                continue

            quotes = extract_quotes(text)

            print(f"   → {len(quotes)} quotes encontradas")

            for quote in quotes:

                # Normalização para detectar duplicatas
                key = (
                    character.lower(),
                    quote.lower()
                )

                if key in seen:
                    continue

                seen.add(key)

                collected.append(
                    (character, quote)
                )

        except Exception as error:
            print(f"   ❌ Erro: {error}")

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    with open(
        OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(
            file,
            quoting=csv.QUOTE_ALL
        )

        for author, quote in collected:
            writer.writerow([
                author,
                quote
            ])

    print()
    print("==============================")
    print(f"✨ {len(collected)} quotes salvas")
    print(f"📄 Arquivo: {OUTPUT}")
    print("==============================")


if __name__ == "__main__":
    main()