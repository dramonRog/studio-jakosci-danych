"""Budowa wykresów Matplotlib/Seaborn na podstawie DataSession."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from src.session import DataSession

SUPPORTED_CHARTS = ("histogram", "scatter", "box", "bar")


def _require_column(session: DataSession, column: str) -> None:
    if column not in session.current.columns:
        raise ValueError(f"Brak kolumny: {column}")


def _numeric_series(session: DataSession, column: str) -> pd.Series:
    _require_column(session, column)
    values = pd.to_numeric(session.current[column], errors="coerce").dropna()
    if values.empty:
        raise ValueError(f"Kolumna '{column}' nie zawiera danych liczbowych")
    return values


def _is_numeric_column(session: DataSession, column: str) -> bool:
    _require_column(session, column)
    values = pd.to_numeric(session.current[column], errors="coerce")
    return bool(values.notna().any())


def _categorical_series(session: DataSession, column: str) -> pd.Series:
    _require_column(session, column)
    values = session.current[column].dropna().astype(str)
    if values.empty:
        raise ValueError(f"Kolumna '{column}' nie zawiera danych kategorycznych")
    return values


def histogram_figure(session: DataSession, column: str) -> Figure:
    """Histogram rozkładu kolumny liczbowej. Zwraca Figure (do pliku lub GUI)."""
    data = _numeric_series(session, column)

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot()
    ax.hist(data, bins="auto", edgecolor="white")
    ax.set(
        title=f"Rozkład: {column}",
        xlabel=column,
        ylabel="Liczba rekordów",
    )
    fig.tight_layout()
    return fig


def scatter_figure(session: DataSession, x: str, y: str) -> Figure:
    """Wykres punktowy dwóch kolumn liczbowych."""
    if not _is_numeric_column(session, x):
        raise ValueError(f"Kolumna X '{x}' musi być numeryczna")
    if not _is_numeric_column(session, y):
        raise ValueError(f"Kolumna Y '{y}' musi być numeryczna")

    frame = session.current[[x, y]].copy()
    frame[x] = pd.to_numeric(frame[x], errors="coerce")
    frame[y] = pd.to_numeric(frame[y], errors="coerce")
    frame = frame.dropna()
    if frame.empty:
        raise ValueError(f"Brak wspólnych danych liczbowych dla '{x}' i '{y}'")

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot()
    sns.scatterplot(data=frame, x=x, y=y, ax=ax, alpha=0.75)
    ax.set(
        title=f"Zależność: {y} vs {x}",
        xlabel=x,
        ylabel=y,
    )
    fig.tight_layout()
    return fig


def box_figure(session: DataSession, column: str, by: str | None = None) -> Figure:
    """
    Wykres pudełkowy kolumny liczbowej.
    Opcjonalnie grupowanie po kolumnie kategorycznej (`by`).
    """
    if not _is_numeric_column(session, column):
        raise ValueError(f"Kolumna '{column}' musi być numeryczna")

    if by is None:
        data = _numeric_series(session, column)
        frame = pd.DataFrame({column: data})
        fig = Figure(figsize=(7, 4), dpi=100)
        ax = fig.add_subplot()
        sns.boxplot(data=frame, y=column, ax=ax)
        ax.set(title=f"Box plot: {column}", xlabel="", ylabel=column)
    else:
        _require_column(session, by)
        frame = session.current[[column, by]].copy()
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame[by] = frame[by].astype(str)
        frame = frame.dropna()
        if frame.empty:
            raise ValueError(
                f"Brak danych do box plot dla '{column}' grupowanych po '{by}'"
            )
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot()
        sns.boxplot(data=frame, x=by, y=column, ax=ax)
        ax.set(
            title=f"Box plot: {column} wg {by}",
            xlabel=by,
            ylabel=column,
        )
        ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    return fig


def bar_figure(session: DataSession, column: str) -> Figure:
    """Wykres słupkowy liczby wystąpień kategorii."""
    values = _categorical_series(session, column)
    counts = values.value_counts().sort_index()

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot()
    sns.barplot(x=counts.index.astype(str), y=counts.values, ax=ax)
    ax.set(
        title=f"Liczebność kategorii: {column}",
        xlabel=column,
        ylabel="Liczba rekordów",
    )
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    return fig


def build_figure(session: DataSession, chart_type: str, **params) -> Figure:
    """
    Buduje wykres na podstawie parametrów.

    chart_type: histogram | scatter | box | bar
    params zależą od typu, np.:
      - histogram: column=
      - scatter: x=, y=
      - box: column=, by= (opcjonalnie)
      - bar: column=
    """
    kind = chart_type.strip().lower()
    if kind not in SUPPORTED_CHARTS:
        raise ValueError(
            f"Nieobsługiwany typ wykresu: {chart_type!r}. "
            f"Dozwolone: {', '.join(SUPPORTED_CHARTS)}"
        )

    if kind == "histogram":
        column = params.get("column")
        if not column:
            raise ValueError("histogram wymaga parametru column=")
        return histogram_figure(session, column)

    if kind == "scatter":
        x = params.get("x")
        y = params.get("y")
        if not x or not y:
            raise ValueError("scatter wymaga parametrów x= oraz y=")
        return scatter_figure(session, x, y)

    if kind == "box":
        column = params.get("column")
        if not column:
            raise ValueError("box wymaga parametru column=")
        return box_figure(session, column, by=params.get("by"))

    # bar
    column = params.get("column")
    if not column:
        raise ValueError("bar wymaga parametru column=")
    return bar_figure(session, column)


def save_figure(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")


def _numeric_frame(session: DataSession) -> pd.DataFrame:
    """Ramka tylko z kolumn liczbowych (bez flag outlierów)."""
    frame = session.current.copy()
    drop_cols = [c for c in frame.columns if str(c).startswith("is_outlier_")]
    frame = frame.drop(columns=drop_cols, errors="ignore")
    numeric = frame.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        raise ValueError("Do korelacji potrzebne są co najmniej 2 kolumny liczbowe")
    return numeric


def correlation_figure(session: DataSession, title_suffix: str = "") -> Figure:
    """Heatmapa korelacji Pearsona dla kolumn liczbowych."""
    numeric = _numeric_frame(session)
    corr = numeric.corr(numeric_only=True)

    fig = Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot()
    sns.heatmap(
        corr,
        ax=ax,
        cmap="coolwarm",
        center=0,
        annot=True,
        fmt=".2f",
        square=True,
        cbar_kws={"shrink": 0.8},
    )
    title = "Macierz korelacji (Pearson)"
    if title_suffix:
        title = f"{title} ({title_suffix})"
    ax.set_title(title)
    fig.tight_layout()
    return fig


STANDARD_CHART_SPECS: list[tuple[str, str, dict]] = [
    ("hist_median_income", "histogram", {"column": "median_income"}),
    (
        "scatter_income_value",
        "scatter",
        {"x": "median_income", "y": "median_house_value"},
    ),
    (
        "box_value_by_ocean",
        "box",
        {"column": "median_house_value", "by": "ocean_proximity"},
    ),
    ("bar_ocean_proximity", "bar", {"column": "ocean_proximity"}),
]


def export_standard_charts(
    session: DataSession,
    out_dir: Path,
    stage: str,
) -> list[Path]:
    """
    Zapisuje zestaw 4 wykresów dla wskazanego etapu (before/after).
    stage trafia do nazwy pliku i tytułu.
    """
    saved: list[Path] = []
    for stem, chart_type, params in STANDARD_CHART_SPECS:
        fig = build_figure(session, chart_type, **params)
        if fig.axes:
            base_title = fig.axes[0].get_title()
            fig.axes[0].set_title(f"{base_title} ({stage})")
        path = out_dir / f"{stem}_{stage}.png"
        save_figure(fig, path)
        saved.append(path)
    return saved


def export_correlation_chart(
    session: DataSession,
    out_dir: Path,
    stage: str,
) -> Path:
    fig = correlation_figure(session, title_suffix=stage)
    path = out_dir / f"correlation_{stage}.png"
    save_figure(fig, path)
    return path


def write_correlation_notes(
    path: Path,
    before_session: DataSession,
    after_session: DataSession,
) -> None:
    """Krótka interpretacja korelacji — bez mylenia z przyczynowością."""
    before_corr = _numeric_frame(before_session).corr(numeric_only=True)
    after_corr = _numeric_frame(after_session).corr(numeric_only=True)

    pair = ("median_income", "median_house_value")
    before_val = (
        float(before_corr.loc[pair[0], pair[1]])
        if pair[0] in before_corr.columns and pair[1] in before_corr.columns
        else float("nan")
    )
    after_val = (
        float(after_corr.loc[pair[0], pair[1]])
        if pair[0] in after_corr.columns and pair[1] in after_corr.columns
        else float("nan")
    )

    lines = [
        "Notatki korelacji (Pearson)",
        "",
        f"Para podsumowana: {pair[0]} vs {pair[1]}",
        f"- before: {before_val:.3f}",
        f"- after:  {after_val:.3f}",
        "",
        "Interpretacja:",
        "- Współczynnik korelacji opisuje siłę i kierunek związku liniowego",
        "  między zmiennymi, a nie to, że jedna zmienna powoduje drugą.",
        "- Nawet wysoka korelacja income–house_value nie oznacza przyczynowości:",
        "  na cenę wpływają też lokalizacja, wiek zabudowy, podaż itd.",
        "- Porównanie before/after pokazuje, jak czyszczenie danych zmienia",
        "  obraz zależności (np. po usunięciu błędnych zakresów), ale nadal",
        "  nie uprawnia do wniosków przyczynowo-skutkowych.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    demo_session = DataSession.from_csv(Path("data/raw/california_housing_dirty.csv"))
    out_dir = Path("output/figures")
    for path in export_standard_charts(demo_session, out_dir, stage="before"):
        print(f"Zapisano: {path}")
    corr_path = export_correlation_chart(demo_session, out_dir, stage="before")
    print(f"Zapisano: {corr_path}")
