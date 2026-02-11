"""
Database initialization script.
Creates all tables defined in the models.
"""
from app.db.database import engine, Base
from app.models import Document, ExtractedField, CompanyFact, FactHistory


def init_db():
    """
    Initialize database by creating all tables.
    
    This should be run once to set up the database schema.
    In production, use proper migration tools (Alembic).
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()

