from pathlib import Path

from src.session import DataSession


def main() -> None:
    path = Path("data/raw/california_housing_dirty.csv")
    session = DataSession.from_csv(path)

    print("BEFORE")
    print(session.summary())
    print(session.profile())
    print()

    session.drop_exact_duplicates()
    session.handle_missing("total_bedrooms", strategy="median")
    session.handle_missing("ocean_proximity", strategy="mode")
    session.apply_range_rule("longitude", -124.5, -114.0, action="report")
    session.apply_range_rule("longitude", -124.5, -114.0, action="remove")
    session.apply_range_rule("latitude", 32.0, 42.5, action="remove")
    session.apply_range_rule("housing_median_age", 0, 100, action="remove")
    session.handle_outliers("median_house_value", factor=1.5, action="report")
    session.handle_outliers("median_house_value", factor=1.5, action="mark")

    print("AFTER")
    print(session.summary())
    print(session.profile())
    print()
    print("AUDIT LOG")
    for line in session.audit_log:
        print("-", line)

    session.reset()
    print()
    print("AFTER RESET")
    print(session.summary())
    print(session.audit_log[-1])


if __name__ == "__main__":
    main()