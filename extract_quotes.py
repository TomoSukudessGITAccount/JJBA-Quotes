import csv
import re
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

OUTPUT = "jojo quotes.csv"

# (Nome que aparecerá no CSV, página da JoJoWiki)
CHARACTERS = [
    ("Jonathan Joestar", "Jonathan Joestar"),
    ("Joseph Joestar", "Joseph Joestar"),
    ("Jotaro Kujo", "Jotaro Cujoh"),
    ("Josuke Higashikata", "Josuke Higashikata"),
    ("Giorno Giovanna", "Giorno Giovanna"),
    ("Jolyne Cujoh", "Jolyne Cujoh"),

    ("Dio Brando", "Dio Brando"),
    ("DIO", "DIO"),
    ("Enrico Pucci", "Enrico Pucci"),

    ("Robert E. O. Speedwagon", "Robert E. O. Speedwagon"),
    ("Caesar Anthonio Zeppeli", "Caesar Anthonio Zeppeli"),
    ("Jean Pierre Polnareff", "Jean Pierre Polnareff"),
    ("Okuyasu Nijimura", "Okuyasu Nijimura"),
    ("Bruno Bucciarati", "Bruno Bucciarati"),
    ("Pannacotta Fugo", "Pannacotta Fugo"),
    ("Ermes Costello", "Ermes Costello"),

    # Steel Ball Run, quando quiser:
    # ("Johnny Joestar", "Johnny Joestar"),
    # ("Gyro Zeppeli", "Gyro Zeppeli"),
    # ("Diego Brando", "Diego Brando"),
]

HEADERS = {
    "User-Agent": (
        "TomoSuku-JoJoQuotes/2.0 "
        "(personal Bonjourr quote dataset)"
    )
}


def get_soup(page):
    """Baixa a página renderizada da JoJoWiki."""

    page_url = page.replace(" ", "_")

    url = (
        "https://jojowiki.com/"
        + quote(page_url, safe="_()'-")
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def find_quotes_section(soup):
    """
    Procura o H2 da seção Quotes.

    Também aceita 'Frases', caso futuramente seja usada
    uma página em português.
    """

    for heading in soup.find_all(["h2", "h3"]):

        text = heading.get_text(
            " ",
            strip=True
        ).lower()

        # Remove coisas como [edit]
        text = re.sub(
            r"\[.*?\]",
            "",
            text
        ).strip()

        if text in {
            "quotes",
            "frases",
            "citations",
            "zitate"
        }:
            return heading

    return None


def clean_quote(text):
    """Limpa espaços e alguns caracteres estranhos."""

    text = text.replace("\xa0", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip(
        " \n\t“”\""
    )


def extract_quotes(soup):
    """Extrai os blockquotes da seção Quotes."""

    heading = find_quotes_section(soup)

    if not heading:
        return []

    quotes = []
    seen_blocks = set()

    # Anda pelo HTML depois do título Quotes.
    for element in heading.find_all_next():

        # Chegamos à próxima seção principal.
        if (
            element.name == "h2"
            and element is not heading
        ):
            break

        if element.name != "blockquote":
            continue

        # Evita processar o mesmo bloco mais de uma vez.
        block_id = id(element)

        if block_id in seen_blocks:
            continue

        seen_blocks.add(block_id)

        # Normalmente a frase está dentro do primeiro <p>.
        paragraph = element.find("p")

        if paragraph:
            text = paragraph.get_text(
                " ",
                strip=True
            )
        else:
            # Fallback
            text = element.get_text(
                " ",
                strip=True
            )

        text = clean_quote(text)

        # Ignora blocos vazios ou quase vazios.
        if len(text) < 4:
            continue

        quotes.append(text)

    return quotes


def main():

    collected = []
    seen = set()

    print()
    print("=== JoJoWiki Quote Extractor v2 ===")
    print()

    for author, page in CHARACTERS:

        print(f"🔎 {author}")

        try:

            soup = get_soup(page)

            quotes = extract_quotes(soup)

            print(
                f"   → {len(quotes)} quotes encontradas"
            )

            for quote_text in quotes:

                key = quote_text.casefold()

                # Remove duplicatas globais.
                if key in seen:
                    continue

                seen.add(key)

                collected.append(
                    (author, quote_text)
                )

        except Exception as error:

            print(
                f"   ❌ Erro: {error}"
            )

    print()

    # MUITO IMPORTANTE:
    # se algo quebrar novamente, NÃO apaga seu CSV.
    if not collected:

        print("❌ Nenhuma quote foi encontrada.")
        print(
            "O CSV antigo NÃO será sobrescrito."
        )

        sys.exit(1)

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

        for author, quote_text in collected:

            writer.writerow([
                author,
                quote_text
            ])

    print("==============================")
    print(
        f"✨ {len(collected)} quotes salvas"
    )
    print(
        f"📄 {OUTPUT}"
    )
    print("==============================")


if __name__ == "__main__":
    main()
