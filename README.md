# Studio jakości i wizualizacji danych

Aplikacja do analizy jakości danych CSV: od wczytania pliku, przez diagnozę i czyszczenie, aż do wizualizacji i eksportu wyników. Użytkownik widzi, które operacje zmieniły zbiór (ślad zmian / audit log), a nie tylko końcowy „oczyszczony” plik.

Stack: **Python 3**, **pandas** (obecnie), później Matplotlib/Seaborn oraz GUI w Tkinter/ttk.

## Opis projektu

Scenariusz pracy:

1. Wczytanie CSV (separator przecinek lub średnik).
2. Profil danych (rozmiar, typy, braki, duplikaty, unikalność, statystyki).
3. Reguły jakości (zakres wartości, outliery metodą IQR).
4. Czyszczenie z raportem liczby zmian i możliwością powrotu do danych surowych.
5. (planowane) Interaktywne wykresy, GUI oraz eksport CSV/wykresów.

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
- Pipeline uruchamiany z `main.py`: zapis `output/cleaned.csv` oraz raport before/after w `reports/report.txt`.
- Małe pliki testowe separatorów: `data/test/sample_comma.csv`, `data/test/sample_semicolon.csv`.

## Co jeszcze będzie zrobione

- Wykresy: histogram, punktowy, pudełkowy, słupkowy + walidacja typów kolumn.
- Analiza korelacji z poprawną interpretacją.
- GUI (Tkinter/ttk): wybór pliku, profil, parametry czyszczenia, podgląd wykresu.
- Eksport wykresów (PNG oraz PDF lub SVG) i pełny przepływ w oknie aplikacji.
- Testy automatyczne logiki profilu/czyszczenia oraz dokumentacja scenariuszy GUI/eksportu.
- Uporządkowanie pod końcowe oddanie (zależności, historia pracy, obrona decyzji).

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

Po uruchomieniu powstają:

- `output/cleaned.csv` - dane po pipeline czyszczenia,
- `reports/report.txt` - porównanie before/after oraz pełny audit log.

## Wnioski (obecny etap)

Pipeline wykrywa przygotowane problemy w zbiorze próbnym i raportuje wpływ każdej operacji.  
Imputacja braków nie zmienia niepowiązanych kolumn; reguły zakresu usuwają tylko rekordy poza zadanym przedziałem.  
Outliery cen (`median_house_value`) są **oznaczane**, a nie automatycznie usuwane - ekstremalna wartość nie zawsze jest błędem i wymaga decyzji analityka.

Wynik jest powtarzalny: ten sam plik wejściowy i ten sam pipeline dają ten sam `cleaned.csv` oraz spójny raport.
