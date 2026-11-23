# Studio jakości i wizualizacji danych

Aplikacja do analizy jakości danych CSV: od wczytania pliku, przez diagnozę i czyszczenie, aż do wizualizacji i eksportu wyników. Użytkownik widzi, które operacje zmieniły zbiór (ślad zmian / audit log), a nie tylko końcowy „oczyszczony” plik.

Stack: **Python 3**, **pandas**, **Matplotlib**, **Seaborn**; planowane GUI w Tkinter/ttk.

## Opis projektu

Scenariusz pracy:

1. Wczytanie CSV (separator przecinek lub średnik).
2. Profil danych (rozmiar, typy, braki, duplikaty, unikalność, statystyki).
3. Reguły jakości (zakres wartości, outliery metodą IQR).
4. Czyszczenie z raportem liczby zmian i możliwością powrotu do danych surowych.
5. Wykresy before/after oraz analiza korelacji.
6. (planowane) Interaktywne GUI oraz eksport wykresów z poziomu okna aplikacji.

Zbiór referencyjny w repozytorium: zmodyfikowana, celowo „brudna” próbka w stylu California Housing  
(`data/raw/california_housing_dirty.csv`) - braki, duplikaty, wartości poza zakresem i obserwacje odstające.

## Co już jest zrobione

- Struktura projektu (`src/`, `data/`, `output/`, `reports/`).
- Klasa `DataSession` (`src/session.py`): dane surowe vs bieżące, profil, czyszczenie, audit log, `reset`.
- Wczytywanie CSV z autodetekcją separatora.
- Profil: liczba wierszy/kolumn, typy, braki (%), duplikaty, unikalność, `describe`.
- Czyszczenie:
  - usuwanie pełnych duplikatów,
  - co najmniej dwie strategie braków (imputacja median/mode oraz drop),
  - reguły zakresu (report → remove),
  - outliery IQR (report → oznaczenie flagą, bez ślepego usuwania).
- Moduł wykresów `src/plots.py`:
  - histogram, scatter, box, bar,
  - walidacja typów kolumn,
  - wspólna funkcja `build_figure(session, chart_type, **params)`,
  - heatmapa korelacji (Pearson).
- Pipeline w `main.py` zapisuje:
  - `output/cleaned.csv`,
  - `reports/report.txt`,
  - zestaw PNG before/after w `output/figures/`,
  - `reports/correlation_notes.txt`.
- Małe pliki testowe separatorów: `data/test/sample_comma.csv`, `data/test/sample_semicolon.csv`.

## Co jeszcze będzie zrobione

- GUI (Tkinter/ttk): wybór pliku, profil, parametry czyszczenia, podgląd wykresu.
- Osadzenie `Figure` w oknie oraz eksport PNG + PDF/SVG z GUI.
- Testy automatyczne logiki profilu/czyszczenia oraz dokumentacja scenariuszy GUI/eksportu.
- Dopięcie pod końcowe oddanie (historia pracy, obrona decyzji).

## Wykresy - jakie kolumny do jakiego typu

| Typ | Parametry | Przykład w pipeline |
|-----|-----------|---------------------|
| histogram | `column` (numeryczna) | `median_income` |
| scatter | `x`, `y` (numeryczne) | `median_income` vs `median_house_value` |
| box | `column` (+ opcjonalnie `by`) | `median_house_value` wg `ocean_proximity` |
| bar | `column` (kategorie) | `ocean_proximity` |
| correlation | kolumny liczbowe | heatmapa Pearsona |

Niepoprawny dobór kolumn (np. kategoria na histogram/scatter) kończy się `ValueError` z czytelnym komunikatem.

## Wymagania i uruchomienie

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Po uruchomieniu powstają m.in.:

- `output/cleaned.csv` - dane po czyszczeniu,
- `reports/report.txt` - before/after + audit log,
- `output/figures/*_before.png` oraz `*_after.png` - 4 typy wykresów,
- `output/figures/correlation_before.png` oraz `correlation_after.png`,
- `reports/correlation_notes.txt` - krótka interpretacja korelacji.

Szybki test samego buildera wykresów:

```powershell
python -m src.plots
```

## Wnioski

Pipeline czyszczenia wykrywa przygotowane problemy i raportuje wpływ każdej operacji. Wynik jest powtarzalny dla tego samego wejścia.

Wykresy before/after pokazują, jak zmienił się rozkład i zależności po czyszczeniu.  
Korelacja Pearsona opisuje siłę związku liniowego - **nie oznacza przyczynowości**. Nawet widoczna zależność `median_income`–`median_house_value` nie pozwala twierdzić, że dochód „powoduje” cenę domu; wpływają też lokalizacja, wiek zabudowy, podaż itd.
