"""Budowa wykresów Matplotlib na podstawie DataSession."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from src.session import DataSession


def _require_column(session: DataSession, column: str) -> None:
    if column not in session.current.columns:
        raise ValueError(f"Brak kolumny: {column}")


def _numeric_series(session: DataSession, column: str) -> pd.Series:
    _require_column(session, column)
    values = pd.to_numeric(session.current[column], errors="coerce").dropna()
    if values.empty:
        raise ValueError(f"Kolumna '{column}' nie zawiera danych liczbowych")
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


def save_figure(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")


if __name__ == "__main__":
    # Szybki test pierwszego wykresu (surowy zbiór).
    demo_session = DataSession.from_csv(Path("data/raw/california_housing_dirty.csv"))
    figure = histogram_figure(demo_session, "median_income")
    out = Path("output/figures/hist_median_income_raw.png")
    save_figure(figure, out)
    print(f"Zapisano: {out}")
