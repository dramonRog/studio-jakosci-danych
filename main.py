from pathlib import Path

from src.session import DataSession


def main() -> None:
    dirty = Path("data/raw/california_housing_dirty.csv")
    comma = Path("data/test/sample_comma.csv")
    semicolon = Path("data/test/sample_semicolon.csv")

    for path in (dirty, comma, semicolon):
        session = DataSession.from_csv(path)
        print("=" * 60)
        print(f"Plik: {path}")
        print(f"Wiersze={session.summary()['rows']}, "
              f"kolumny={session.summary()['columns']}, "
              f"duplikaty={session.summary()['duplicate_rows']}")
        print(session.profile())


if __name__ == "__main__":
    main()