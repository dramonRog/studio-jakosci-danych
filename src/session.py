from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class DataSession:
    raw: pd.DataFrame
    current: pd.DataFrame = field(init=False)
    audit_log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current = self.raw.copy(deep=True)

    @classmethod
    def from_csv(cls, path: Path) -> "DataSession":
        # sep=None korzysta z mechanizmu wykrywania separatora silnika Python.
        frame = pd.read_csv(path, sep=None, engine="python")
        if frame.empty:
            raise ValueError("Plik nie zawiera rekordów")
        return cls(frame)

    def profile(self) -> pd.DataFrame:
        return pd.DataFrame({
            "dtype": self.current.dtypes.astype(str),
            "missing": self.current.isna().sum(),
            "missing_pct": self.current.isna().mean().mul(100).round(2),
            "unique": self.current.nunique(dropna=True),
        })

    def summary(self) -> dict:
        """Krótki przegląd zbioru: rozmiar, duplikaty, statystyki opisowe."""
        return {
            "rows": int(self.current.shape[0]),
            "columns": int(self.current.shape[1]),
            "duplicate_rows": int(self.current.duplicated().sum()),
            "dtypes": self.current.dtypes.astype(str).to_dict(),
            "describe": self.current.describe(include="all").to_string(),
        }

    def reset(self) -> None:
        self.current = self.raw.copy(deep=True)
        self.audit_log.append("Przywrócono dane surowe")