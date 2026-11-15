from pathlib import Path

from src.session import DataSession


def format_profile(profile) -> str:
    return profile.to_string()


def run_lab6_pipeline(
    input_path: Path,
    cleaned_path: Path,
    report_path: Path,
) -> None:
    session = DataSession.from_csv(input_path)

    before_summary = session.summary()
    before_profile = session.profile().copy()

    # 1) Duplikaty
    session.drop_exact_duplicates()

    # 2) Braki — dwie strategie: imputacja + drop
    session.handle_missing("total_bedrooms", strategy="median")
    session.handle_missing("ocean_proximity", strategy="mode")
    session.handle_missing("median_income", strategy="median")
    session.handle_missing("households", strategy="drop")

    # 3) Reguły zakresu: najpierw report, potem decyzja (remove)
    session.apply_range_rule("longitude", -124.5, -114.0, action="report")
    session.apply_range_rule("longitude", -124.5, -114.0, action="remove")
    session.apply_range_rule("latitude", 32.0, 42.5, action="report")
    session.apply_range_rule("latitude", 32.0, 42.5, action="remove")
    session.apply_range_rule("housing_median_age", 0, 100, action="report")
    session.apply_range_rule("housing_median_age", 0, 100, action="remove")

    # 4) Outliery IQR: najpierw report, potem oznaczenie (bez ślepego usuwania)
    session.handle_outliers("median_house_value", factor=1.5, action="report")
    session.handle_outliers("median_house_value", factor=1.5, action="mark")

    after_summary = session.summary()
    after_profile = session.profile().copy()

    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    session.current.to_csv(cleaned_path, index=False)

    report_lines = [
        "LAB 6 — raport before/after",
        f"Wejście: {input_path}",
        f"Wyjście: {cleaned_path}",
        "",
        "=== BEFORE ===",
        f"Wiersze={before_summary['rows']}, kolumny={before_summary['columns']}, "
        f"duplikaty={before_summary['duplicate_rows']}",
        format_profile(before_profile),
        "",
        "=== AFTER ===",
        f"Wiersze={after_summary['rows']}, kolumny={after_summary['columns']}, "
        f"duplikaty={after_summary['duplicate_rows']}",
        format_profile(after_profile),
        "",
        "=== AUDIT LOG ===",
        *[f"- {line}" for line in session.audit_log],
        "",
        "=== DECYZJE ===",
        "- Braki: median/mode dla wybranych kolumn; drop dla households",
        "- Zakres: usuwanie rekordów poza sensownym zakresem geograficznym/wieku",
        "- Outliery median_house_value: oznaczenie kolumną flagi (nie usuwanie),",
        "  bo ekstremalne ceny mogą być prawdziwe i wymagają decyzji analityka",
    ]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Zapisano: {cleaned_path}")
    print(f"Zapisano: {report_path}")
    print(f"Wiersze po czyszczeniu: {after_summary['rows']}")


def main() -> None:
    run_lab6_pipeline(
        input_path=Path("data/raw/california_housing_dirty.csv"),
        cleaned_path=Path("output/cleaned.csv"),
        report_path=Path("reports/report.txt"),
    )


if __name__ == "__main__":
    main()