def test_signup_creates_user_and_returns_token(client):
    response = client.post(
        "/auth/signup", json={"email": "new@example.com", "password": "supersecret"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_signup_duplicate_email_rejected(client):
    client.post("/auth/signup", json={"email": "dup@example.com", "password": "supersecret"})
    response = client.post("/auth/signup", json={"email": "dup@example.com", "password": "different"})
    assert response.status_code == 400


def test_login_with_correct_credentials(client):
    client.post("/auth/signup", json={"email": "login@example.com", "password": "supersecret"})
    response = client.post("/auth/login", data={"username": "login@example.com", "password": "supersecret"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_rejected(client):
    client.post("/auth/signup", json={"email": "login2@example.com", "password": "supersecret"})
    response = client.post("/auth/login", data={"username": "login2@example.com", "password": "wrongpass"})
    assert response.status_code == 401


def test_login_with_unknown_email_rejected(client):
    response = client.post("/auth/login", data={"username": "nobody@example.com", "password": "whatever"})
    assert response.status_code == 401


def test_password_is_stored_hashed_not_plaintext(client, db):
    client.post("/auth/signup", json={"email": "hashcheck@example.com", "password": "supersecret"})

    from app.models.user import User

    user = db.query(User).filter(User.email == "hashcheck@example.com").first()
    assert user is not None
    assert user.password_hash != "supersecret"
