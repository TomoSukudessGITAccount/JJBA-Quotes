import csv
import html
import re
from pathlib import Path


SOURCES_DIR = Path("sources")
OUTPUT_FILE = Path("jojo quotes.csv")


def find_q_templates(text):
    """
    Encontra todos os templates {{Q|...}}
    respeitando templates aninhados.
    """

    templates = []
    i = 0

    while i < len(text) - 1:

        if not text.startswith("{{Q|", i):
            i += 1
            continue

        start = i
        depth = 0
        j = i

        while j < len(text) - 1:

            if text.startswith("{{", j):
                depth += 1
                j += 2
                continue

            if text.startswith("}}", j):
                depth -= 1
                j += 2

                if depth == 0:
                    templates.append(text[start:j])
                    i = j
                    break

                continue

            j += 1

        else:
            i += 1

    return templates


def split_template_parameters(template):
    """
    Divide:

    {{Q|QUOTE|AUTOR|FONTE}}

    sem quebrar coisas internas como:

    {{Ch|Chapter 456}}
    [[Giorno Giovanna|GioGio]]
    """

    # Remove "{{Q|" do começo e "}}" do final
    content = template[4:-2]

    parts = []
    current = []

    template_depth = 0
    link_depth = 0

    i = 0

    while i < len(content):

        if content.startswith("{{", i):
            template_depth += 1
            current.append("{{")
            i += 2
            continue

        if content.startswith("}}", i):
            template_depth -= 1
            current.append("}}")
            i += 2
            continue

        if content.startswith("[[", i):
            link_depth += 1
            current.append("[[")
            i += 2
            continue

        if content.startswith("]]", i):
            link_depth -= 1
            current.append("]]")
            i += 2
            continue

        if (
            content[i] == "|"
            and template_depth == 0
            and link_depth == 0
        ):
            parts.append("".join(current))
            current = []
            i += 1
            continue

        current.append(content[i])
        i += 1

    parts.append("".join(current))

    return parts


def clean_wikilinks(text):
    """
    Converte:

    [[Giorno Giovanna|GioGio]]
        ↓
    GioGio

    [[Purple Haze]]
        ↓
    Purple Haze
    """

    def replace_link(match):

        content = match.group(1)

        if "|" in content:
            return content.split("|")[-1]

        return content

    return re.sub(
        r"\[\[([^\]]+)\]\]",
        replace_link,
        text
    )


def clean_templates(text):
    """
    Remove templates restantes que eventualmente
    apareçam dentro da própria frase.
    """

    previous = None

    while previous != text:

        previous = text

        text = re.sub(
            r"\{\{[^{}]*\}\}",
            "",
            text
        )

    return text


def clean_text(text):

    text = clean_wikilinks(text)
    text = clean_templates(text)

    # Formatação wiki
    text = text.replace("'''", "")
    text = text.replace("''", "")

    # HTML entities
    text = html.unescape(text)

    # HTML simples
    text = re.sub(
        r"<br\s*/?>",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    # Normaliza espaços
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_author(author):
    """
    Remove descrições editoriais simples do campo autor.

    Exemplo real:
    'Pannacotta Fugo seething'
        ↓
    'Pannacotta Fugo'

    Podemos expandir esta lista depois.
    """

    author = clean_text(author)

    suffixes = [
        " seething",
        " yelling",
        " shouting",
        " thinking",
        " screaming",
        " crying",
    ]

    lower = author.lower()

    for suffix in suffixes:

        if lower.endswith(suffix):

            author = author[
                :len(author) - len(suffix)
            ]

            break

    return author.strip()


def parse_source_file(path):

    text = path.read_text(
        encoding="utf-8"
    )

    quotes = []

    templates = find_q_templates(text)

    for template in templates:

        parameters = split_template_parameters(
            template
        )

        # Precisamos pelo menos:
        # quote + autor
        if len(parameters) < 2:
            continue

        quote_text = clean_text(
            parameters[0]
        )

        author = normalize_author(
            parameters[1]
        )

        if not quote_text:
            continue

        if not author:
            continue

        quotes.append(
            (author, quote_text)
        )

    return quotes


def main():

    print()
    print("=== JoJo Quote Converter ===")
    print()

    if not SOURCES_DIR.exists():

        print(
            "❌ Pasta 'sources' não encontrada."
        )

        return

    all_quotes = []
    seen = set()

    files = sorted(
        SOURCES_DIR.rglob("*.txt")
    )

    print(
        f"📁 {len(files)} arquivos encontrados."
    )
    print()

    for path in files:

        quotes = parse_source_file(path)

        print(
            f"🔎 {path}: "
            f"{len(quotes)} quotes"
        )

        for author, quote_text in quotes:

            key = (
                author.casefold(),
                quote_text.casefold()
            )

            if key in seen:
                continue

            seen.add(key)

            all_quotes.append(
                (author, quote_text)
            )

    if not all_quotes:

        print()
        print(
            "❌ Nenhuma quote encontrada."
        )

        return

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(
            file,
            quoting=csv.QUOTE_ALL
        )

        for author, quote_text in all_quotes:

            writer.writerow(
                [author, quote_text]
            )

    print()
    print("==============================")
    print(
        f"✨ {len(all_quotes)} quotes salvas"
    )
    print(
        f"📄 {OUTPUT_FILE}"
    )
    print("==============================")


if __name__ == "__main__":
    main()
