import csv
import html
import re
from pathlib import Path


SOURCES_DIR = Path("sources")
ALL_QUOTES_FILE = Path("jojo-quotes-all.csv")


def find_q_templates(text):
    """Encontra templates {{Q|...}} respeitando templates aninhados."""

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
    Divide {{Q|QUOTE|AUTOR|FONTE}}
    sem quebrar templates e wikilinks internos.
    """

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

    text = text.replace("'''", "")
    text = text.replace("''", "")

    text = html.unescape(text)

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

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_author(author):

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

    for template in find_q_templates(text):

        parameters = split_template_parameters(
            template
        )

        if len(parameters) < 2:
            continue

        quote_text = clean_text(
            parameters[0]
        )

        author = normalize_author(
            parameters[1]
        )

        if not quote_text or not author:
            continue

        quotes.append(
            (author, quote_text)
        )

    return quotes


def load_all_quotes():

    all_quotes = []
    seen = set()

    files = sorted(
        SOURCES_DIR.rglob("*.txt")
    )

    for path in files:

        quotes = parse_source_file(path)

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

    return files, all_quotes


def write_csv(path, quotes):

    with path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(
            file,
            quoting=csv.QUOTE_ALL
        )

        writer.writerows(quotes)


def main():

    print()
    print("=== JoJo Quote Database Builder ===")
    print()

    if not SOURCES_DIR.exists():
        raise SystemExit(
            "❌ Pasta sources/ não encontrada."
        )

    files, quotes = load_all_quotes()

    print(
        f"📁 {len(files)} arquivos de personagens"
    )

    for path in files:

        amount = len(
            parse_source_file(path)
        )

        print(
            f"🔎 {path}: {amount} quotes"
        )

    if not quotes:
        raise SystemExit(
            "❌ Nenhuma quote encontrada."
        )

    write_csv(
        ALL_QUOTES_FILE,
        quotes
    )

    print()
    print(
        f"✨ {len(quotes)} quotes no acervo completo."
    )
    print(
        f"📄 {ALL_QUOTES_FILE}"
    )


if __name__ == "__main__":
    main()
