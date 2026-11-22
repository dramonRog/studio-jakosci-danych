from pathlib import Path

from src.plots import (
    export_correlation_chart,
    export_standard_charts,
    write_correlation_notes,
)
from src.session import DataSession


def format_profile(profile) -> str:
    return profile.to_string()


def apply_cleaning(session: DataSession) -> None:
    """Pipeline czyszczenia na bieżącej sesji (modyfikuje current + audit_log)."""
    session.drop_exact_duplicates()

    session.handle_missing("total_bedrooms", strategy="median")
    session.handle_missing("ocean_proximity", strategy="mode")
    session.handle_missing("median_income", strategy="median")
    session.handle_missing("households", strategy="drop")

    session.apply_range_rule("longitude", -124.5, -114.0, action="report")
    session.apply_range_rule("longitude", -124.5, -114.0, action="remove")
    session.apply_range_rule("latitude", 32.0, 42.5, action="report")
    session.apply_range_rule("latitude", 32.0, 42.5, action="remove")
    session.apply_range_rule("housing_median_age", 0, 100, action="report")
    session.apply_range_rule("housing_median_age", 0, 100, action="remove")

    session.handle_outliers("median_house_value", factor=1.5, action="report")
    session.handle_outliers("median_house_value", factor=1.5, action="mark")


def run_cleaning_report(
    session: DataSession,
    input_path: Path,
    cleaned_path: Path,
    report_path: Path,
    before_summary: dict,
    before_profile,
) -> None:
    after_summary = session.summary()
    after_profile = session.profile().copy()

    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    session.current.to_csv(cleaned_path, index=False)

    report_lines = [
        "Raport before/after — czyszczenie danych",
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


def run_visualization(
    before_session: DataSession,
    after_session: DataSession,
    figures_dir: Path,
    notes_path: Path,
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    for path in export_standard_charts(before_session, figures_dir, stage="before"):
        print(f"Zapisano: {path}")
    for path in export_standard_charts(after_session, figures_dir, stage="after"):
        print(f"Zapisano: {path}")

    before_corr = export_correlation_chart(
        before_session, figures_dir, stage="before"
    )
    after_corr = export_correlation_chart(after_session, figures_dir, stage="after")
    print(f"Zapisano: {before_corr}")
    print(f"Zapisano: {after_corr}")

    write_correlation_notes(notes_path, before_session, after_session)
    print(f"Zapisano: {notes_path}")


def main() -> None:
    input_path = Path("data/raw/california_housing_dirty.csv")
    session = DataSession.from_csv(input_path)

    # Osobna sesja „before”: current == raw (bez czyszczenia)
    before_session = DataSession(session.raw.copy(deep=True))

    before_summary = session.summary()
    before_profile = session.profile().copy()

    apply_cleaning(session)
    run_cleaning_report(
        session=session,
        input_path=input_path,
        cleaned_path=Path("output/cleaned.csv"),
        report_path=Path("reports/report.txt"),
        before_summary=before_summary,
        before_profile=before_profile,
    )

    run_visualization(
        before_session=before_session,
        after_session=session,
        figures_dir=Path("output/figures"),
        notes_path=Path("reports/correlation_notes.txt"),
    )


if __name__ == "__main__":
    main()
