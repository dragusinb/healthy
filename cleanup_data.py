from backend_v2.database import SessionLocal
from backend_v2.models import User, Document, TestResult

def cleanup_demo_data():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "dragusinb@gmail.com").first()
    
    if not user:
        print("User not found!")
        return

    # Find demo documents by filename
    demo_filenames = ["Analize_Synevo_Demo.pdf", "Analize_Synevo_Old.pdf"]
    
    docs_to_delete = db.query(Document).filter(
        Document.user_id == user.id,
        Document.filename.in_(demo_filenames)
    ).all()
    
    print(f"Found {len(docs_to_delete)} demo documents to delete.")
    
    for doc in docs_to_delete:
        print(f"Deleting document: {doc.filename} and its results...")
        # Delete results first (though cascade might handle it, being explicit is safer)
        db.query(TestResult).filter(TestResult.document_id == doc.id).delete()
        db.delete(doc)
        
    db.commit()
    print("Cleanup complete!")

if __name__ == "__main__":
    cleanup_demo_data()
