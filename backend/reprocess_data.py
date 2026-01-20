from backend.database import engine, Base
from backend.ingest_data import ingest_regina_maria
from backend.seed_credentials import seed

def reprocess():
    print("Dropping all tables to force schema update...")
    Base.metadata.drop_all(bind=engine)
    
    print("Seeding credentials...")
    # Using the credentials known from seed_credentials.py inspection
    seed("dragusinb@gmail.com", "Vl@dut123") 
    
    print("Starting fresh ingestion...")
    ingest_regina_maria()
    print("Reprocessing & Migration complete.")

if __name__ == "__main__":
    reprocess()
