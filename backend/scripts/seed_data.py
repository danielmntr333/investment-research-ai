"""Seed database with sample data for testing."""
import asyncio
from uuid import uuid4


async def seed_database():
    """Seed database with test data."""
    print("Seeding database with sample data...")
    
    # To be implemented:
    # 1. Create test user
    # 2. Upload sample documents
    # 3. Process and chunk documents
    # 4. Create sample conversations
    
    print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
