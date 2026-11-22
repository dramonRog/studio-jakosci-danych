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


if __name__ == "__main__":
    demo_session = DataSession.from_csv(Path("data/raw/california_housing_dirty.csv"))
    out_dir = Path("output/figures")

    demos = [
        ("hist_median_income_raw.png", "histogram", {"column": "median_income"}),
        (
            "scatter_income_value_raw.png",
            "scatter",
            {"x": "median_income", "y": "median_house_value"},
        ),
        (
            "box_value_by_ocean_raw.png",
            "box",
            {"column": "median_house_value", "by": "ocean_proximity"},
        ),
        ("bar_ocean_proximity_raw.png", "bar", {"column": "ocean_proximity"}),
    ]

    for filename, chart_type, params in demos:
        fig = build_figure(demo_session, chart_type, **params)
        path = out_dir / filename
        save_figure(fig, path)
        print(f"Zapisano: {path}")
