import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.db.models import Base, UserModel, DeviceModel, VectorMemoryModel
from app.memory.vector_store import generate_free_embedding, MemoryVectorStore

TEST_SQLITE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_free_embedding_generator():
    vec1 = generate_free_embedding("User prefers dark theme")
    vec2 = generate_free_embedding("User prefers dark theme")
    vec3 = generate_free_embedding("User likes bright light")

    assert len(vec1) == 384
    assert vec1 == vec2  # Deterministic
    assert vec1 != vec3  # Different embeddings for different text

@pytest.mark.asyncio
async def test_database_models_creation():
    engine = create_async_engine(TEST_SQLITE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create user
        user = UserModel(email="ev_test@example.com", hashed_password="hashed_pass_123")
        session.add(user)
        
        # Create device
        device = DeviceModel(
            device_id="laptop-macbook-test",
            device_name="MacBook Pro",
            device_type="laptop",
            capabilities_json={"terminal": True, "gui": True}
        )
        session.add(device)
        await session.commit()

        # Query user & device
        assert user.id is not None
        assert device.id is not None
        assert device.device_name == "MacBook Pro"

    await engine.dispose()
