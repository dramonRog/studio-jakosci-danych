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

    def _log(self, message: str, before: int, after: int) -> None:
        affected = abs(before - after)
        self.audit_log.append(
            f"{message} | przed={before}, po={after}, zmieniono={affected}"
        )

    def drop_exact_duplicates(self) -> int:
        before = len(self.current)
        self.current = self.current.drop_duplicates().copy()
        removed = before - len(self.current)
        self._log(f"Usunięto pełne duplikaty: {removed}", before, len(self.current))
        return removed

    def handle_missing(
        self,
        column: str,
        strategy: str = "drop",
    ) -> int:
        """
        Strategie braków:
        - drop: usuń wiersze z brakiem w kolumnie
        - mean / median / mode: imputacja (tylko wskazana kolumna)
        """
        if column not in self.current.columns:
            raise ValueError(f"Brak kolumny: {column}")

        before = len(self.current)
        missing_before = int(self.current[column].isna().sum())

        if strategy == "drop":
            self.current = self.current.dropna(subset=[column]).copy()
        elif strategy == "mean":
            value = pd.to_numeric(self.current[column], errors="coerce").mean()
            self.current[column] = self.current[column].fillna(value)
        elif strategy == "median":
            value = pd.to_numeric(self.current[column], errors="coerce").median()
            self.current[column] = self.current[column].fillna(value)
        elif strategy == "mode":
            modes = self.current[column].mode(dropna=True)
            if modes.empty:
                raise ValueError(f"Nie można wyliczyć mode dla kolumny: {column}")
            self.current[column] = self.current[column].fillna(modes.iloc[0])
        else:
            raise ValueError("strategy musi być: drop, mean, median albo mode")

        after = len(self.current)
        self._log(
            f"Braki w '{column}' strategią '{strategy}' "
            f"(braków przed={missing_before})",
            before,
            after,
        )
        return missing_before

    def apply_range_rule(
        self,
        column: str,
        min_value: float,
        max_value: float,
        action: str = "report",
    ) -> int:
        """
        Reguła zakresu dla jednej kolumny.
        action:
        - report: tylko zlicz (nie zmienia danych)
        - remove: usuń wiersze poza zakresem
        - clip: przytnij wartości do [min, max]
        """
        if column not in self.current.columns:
            raise ValueError(f"Brak kolumny: {column}")

        values = pd.to_numeric(self.current[column], errors="coerce")
        mask = (values < min_value) | (values > max_value)
        # NaN nie traktujemy tu jako naruszenie zakresu
        mask = mask.fillna(False)
        count = int(mask.sum())
        before = len(self.current)

        if action == "report":
            self.audit_log.append(
                f"Reguła zakresu '{column}' [{min_value}, {max_value}]: "
                f"wykryto={count} (bez zmian danych)"
            )
            return count

        if action == "remove":
            self.current = self.current.loc[~mask].copy()
            self._log(
                f"Usunięto rekordy poza zakresem '{column}' "
                f"[{min_value}, {max_value}]: {count}",
                before,
                len(self.current),
            )
            return count

        if action == "clip":
            self.current[column] = values.clip(min_value, max_value)
            self._log(
                f"Przycięto wartości '{column}' do [{min_value}, {max_value}]: {count}",
                before,
                len(self.current),
            )
            return count

        raise ValueError("action musi być: report, remove albo clip")

    def iqr_mask(self, column: str, factor: float = 1.5) -> pd.Series:
        values = pd.to_numeric(self.current[column], errors="coerce")
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            return pd.Series(False, index=self.current.index)
        return (values < q1 - factor * iqr) | (values > q3 + factor * iqr)

    def handle_outliers(
        self,
        column: str,
        factor: float = 1.5,
        action: str = "report",
    ) -> int:
        """
        Outliery metodą IQR.
        action: report | remove | mark
        mark dodaje kolumnę is_outlier_<column> (True/False).
        """
        if column not in self.current.columns:
            raise ValueError(f"Brak kolumny: {column}")

        mask = self.iqr_mask(column, factor=factor).fillna(False)
        count = int(mask.sum())
        before = len(self.current)

        if action == "report":
            self.audit_log.append(
                f"IQR outliery '{column}' (factor={factor}): "
                f"wykryto={count} (bez zmian danych)"
            )
            return count

        if action == "remove":
            self.current = self.current.loc[~mask].copy()
            self._log(
                f"Usunięto IQR outliery '{column}' (factor={factor}): {count}",
                before,
                len(self.current),
            )
            return count

        if action == "mark":
            flag_col = f"is_outlier_{column}"
            self.current[flag_col] = mask.astype(bool)
            self.audit_log.append(
                f"Oznaczono IQR outliery '{column}' kolumną '{flag_col}': {count}"
            )
            return count

        raise ValueError("action musi być: report, remove albo mark")

    def reset(self) -> None:
        self.current = self.raw.copy(deep=True)
        self.audit_log.append("Przywrócono dane surowe")