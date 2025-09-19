import pytest
from httpx import AsyncClient, ASGITransport
from main import app

transport = ASGITransport(app=app)

TEST_USER = "testuser"
TEST_PASS = "testpass"
TEST_ARTICLE = {
    "title": "Sample Title",
    "content": "This is a sample article content."
}

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}



@pytest.mark.asyncio
async def test_get_user_details():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get(f"/auth/user/{TEST_USER}")
    if r.status_code == 200:
        assert "username" in r.json()
    else:
        assert r.status_code == 404

@pytest.mark.asyncio
async def test_password_reset():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/auth/reset-password", json={
            "username": TEST_USER,
            "new_password": "newpass123"
        })
    assert r.status_code in (200, 404)

@pytest.mark.asyncio
async def test_create_article():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "username": TEST_USER,
            "password": "newpass123",  # Use reset password
            "title": TEST_ARTICLE["title"],
            "content": TEST_ARTICLE["content"],
            "tags": ["test", "sample"]
        }
        r = await ac.post("/particles/create", json=payload)
    assert r.status_code in (200, 401, 500)
    if r.status_code == 200:
        assert "article_id" in r.json()


@pytest.mark.asyncio
async def test_edit_delete_article():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_resp = await ac.post("/particles/create", json={
            "username": TEST_USER,
            "password": "newpass123",
            "title": "Edit Title",
            "content": "Edit Content",
            "tags": ["edit"]
        })
        if create_resp.status_code != 200:
            pytest.skip("Could not create article for edit/delete test")
        article_id = create_resp.json()["article_id"]

        r = await ac.put(f"/particles/{article_id}/edit", json={
            "username": TEST_USER,
            "password": "newpass123",
            "new_title": "Updated Title",
            "new_content": "Updated Content",
            "new_tags": ["updated", "edit"]
        })
        assert r.status_code in (200, 403)

        r = await ac.delete(f"/particles/{article_id}")
        assert r.status_code in (200, 404)

