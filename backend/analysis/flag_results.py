from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import TestResult
from backend.analysis.parser import RangeEvaluator

def flag_all_results():
    session = SessionLocal()
    try:
        results = session.query(TestResult).all()
        print(f"Analyzing {len(results)} test results...")
        
        count_high = 0
        count_low = 0
        count_normal = 0
        count_unknown = 0
        
        for res in results:
            # Skip if no reference range or value
            if not res.reference_range or not res.value:
                res.flags = "UNKNOWN"
                count_unknown += 1
                continue
                
            flag = RangeEvaluator.evaluate(res.value, res.reference_range)
            res.flags = flag
            
            if flag == "HIGH": count_high += 1
            elif flag == "LOW": count_low += 1
            elif flag == "NORMAL": count_normal += 1
            else: count_unknown += 1
            
        session.commit()
        print("Analysis Complete.")
        print(f"HIGH: {count_high}")
        print(f"LOW: {count_low}")
        print(f"NORMAL: {count_normal}")
        print(f"UNKNOWN: {count_unknown}")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    flag_all_results()
