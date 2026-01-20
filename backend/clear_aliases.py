from backend.database import SessionLocal
from backend.models import BiomarkerAlias

def clear_aliases():
    session = SessionLocal()
    try:
        aliases = session.query(BiomarkerAlias).filter(BiomarkerAlias.alias.like("SPR%")).all()
        print(f"Found {len(aliases)} stale aliases.")
        for a in aliases:
            print(f"Deleting alias: {a.alias} (Standardized: {a.standardized_name})")
            session.delete(a)
        session.commit()
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clear_aliases()
