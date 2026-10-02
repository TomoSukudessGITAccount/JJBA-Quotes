import random
from collections import defaultdict
from pathlib import Path

from extract_quotes import (
    load_all_quotes,
    write_csv,
)


MONTHLY_FILE = Path("jojo quotes.csv")
MONTHLY_LIMIT = 30


def create_balanced_selection(quotes, limit=30):

    if len(quotes) <= limit:
        shuffled = quotes.copy()
        random.SystemRandom().shuffle(shuffled)
        return shuffled

    rng = random.SystemRandom()

    by_author = defaultdict(list)

    for author, quote_text in quotes:
        by_author[author].append(
            (author, quote_text)
        )

    authors = list(
        by_author.keys()
    )

    rng.shuffle(authors)

    selected = []
    selected_set = set()

    # Primeiro tentamos colocar 1 quote por personagem.
    for author in authors:

        if len(selected) >= limit:
            break

        chosen = rng.choice(
            by_author[author]
        )

        selected.append(chosen)
        selected_set.add(chosen)

    # Se há menos personagens do que vagas,
    # completamos com outras quotes aleatórias.
    if len(selected) < limit:

        remaining = [
            quote
            for quote in quotes
            if quote not in selected_set
        ]

        rng.shuffle(remaining)

        needed = (
            limit - len(selected)
        )

        selected.extend(
            remaining[:needed]
        )

    # Mistura a ordem final.
    rng.shuffle(selected)

    return selected


def main():

    print()
    print("=== Monthly JoJo Quote Rotation ===")
    print()

    files, all_quotes = load_all_quotes()

    if not all_quotes:
        raise SystemExit(
            "❌ Nenhuma quote disponível."
        )

    monthly_quotes = (
        create_balanced_selection(
            all_quotes,
            MONTHLY_LIMIT
        )
    )

    write_csv(
        MONTHLY_FILE,
        monthly_quotes
    )

    characters = {
        author
        for author, _ in monthly_quotes
    }

    print(
        f"📚 Acervo: {len(all_quotes)} quotes"
    )

    print(
        f"👥 Personagens disponíveis: "
        f"{len(set(a for a, _ in all_quotes))}"
    )

    print(
        f"🎲 Seleção mensal: "
        f"{len(monthly_quotes)} quotes"
    )

    print(
        f"🎭 Personagens no mês: "
        f"{len(characters)}"
    )

    print()
    print(
        f"📄 Arquivo: {MONTHLY_FILE}"
    )


if __name__ == "__main__":
    main()
