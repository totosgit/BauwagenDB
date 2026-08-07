"""Schema-Anpassungen, die create_all() nicht erledigen kann.

create_all() legt nur *neue Tabellen* an. Neue Spalten in bestehenden
Tabellen und das Entfernen alter Tabellen muss von Hand passieren -- genau
daran ist das Schema hier schon einmal auseinandergelaufen (die Spalte
items.location_id ist ein Ueberbleibsel davon).

Alle Schritte sind idempotent: mehrfaches Ausfuehren aendert nichts.
"""
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _columns(inspector, table: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table)}


def run_migrations(engine: Engine) -> list[str]:
    """Bringt ein bestehendes Schema auf den aktuellen Stand.

    Gibt zurueck, was tatsaechlich geaendert wurde -- fuer das Log beim Start.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    done: list[str] = []

    with engine.begin() as conn:
        # Die Strichliste haengt jetzt an Benutzerkonten statt an einer
        # eigenen Gruppenleiter-Tabelle. Alte Striche werden verworfen
        # (so entschieden -- es war ein Testbestand).
        if "tallies" in tables and "group_leader_id" in _columns(inspector, "tallies"):
            conn.execute(text("DROP TABLE tallies"))
            done.append("tallies verworfen (hing noch an group_leaders)")

        if "group_leaders" in tables:
            conn.execute(text("DROP TABLE group_leaders"))
            done.append("group_leaders entfernt")

        # Ersetzt durch access_tokens (fastapi-users)
        if "sessions" in tables:
            conn.execute(text("DROP TABLE sessions"))
            done.append("alte sessions-Tabelle entfernt")

        # Notizen und Einkaufsliste tragen jetzt den Urheber aus dem Konto.
        # Bestandsdaten bleiben ohne Verweis: bei Notizen zeigen wir weiter
        # den getippten Namen, bei Einkaufszetteln "unbekannt".
        # Gespeichert wird beides: der Verweis aufs Konto und der Name als
        # Momentaufnahme. Letzterer ueberlebt das Loeschen eines Kontos und
        # erfuellt zugleich die alte NOT NULL-Regel auf notes.author, die
        # SQLite nicht per ALTER lockern kann.
        for tabelle in ("notes", "shopping_items"):
            if tabelle not in tables:
                continue
            spalten = _columns(inspector, tabelle)
            if "created_by" not in spalten:
                conn.execute(text(f"ALTER TABLE {tabelle} ADD COLUMN created_by CHAR(36)"))
                done.append(f"{tabelle}.created_by ergaenzt")
            if "author" not in spalten:
                conn.execute(text(f"ALTER TABLE {tabelle} ADD COLUMN author VARCHAR(100)"))
                done.append(f"{tabelle}.author ergaenzt")

        # Lagerorte koennen unter dem Jahr woanders stehen
        if "locations" in tables and "parent_jahr_id" not in _columns(inspector, "locations"):
            conn.execute(text("ALTER TABLE locations ADD COLUMN parent_jahr_id INTEGER"))
            done.append("locations.parent_jahr_id ergaenzt")

    return done
