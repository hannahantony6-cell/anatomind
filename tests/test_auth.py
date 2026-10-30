from conftest import PASSWORD, make_user


def test_signup_login_me_and_no_hash_leak(client):
    user = make_user(client)
    assert "password" not in str(user).lower()
    r = client.get("/api/auth/me")
    assert r.status_code == 200 and r.json()["email"] == "alice@example.com"
    assert "password_hash" not in r.text


def test_duplicate_email_rejected(client):
    make_user(client)
    r = client.post("/api/auth/signup", json={"full_name": "Other Person", "email": "ALICE@example.com",
                                              "password": PASSWORD, "confirm_password": PASSWORD})
    assert r.status_code == 409 and r.json()["error"]["code"] == "email_taken"


def test_password_policy_and_mismatch(client):
    base = {"full_name": "Weak Pw", "email": "w@example.com"}
    r = client.post("/api/auth/signup", json={**base, "password": "alllowercase1", "confirm_password": "alllowercase1"})
    assert r.status_code == 422
    r = client.post("/api/auth/signup", json={**base, "password": PASSWORD, "confirm_password": PASSWORD + "x"})
    assert r.status_code == 422 and "match" in r.json()["error"]["message"].lower()
    r = client.post("/api/auth/signup", json={**base, "email": "not-an-email", "password": PASSWORD, "confirm_password": PASSWORD})
    assert r.status_code == 422


def test_passwords_are_hashed_with_argon2(client):
    make_user(client)
    from app.database import SessionLocal
    from app.models import User
    with SessionLocal() as db:
        h = db.query(User).one().password_hash
    assert h.startswith("$argon2") and PASSWORD not in h


def test_invalid_credentials(client):
    make_user(client)
    r = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "Wrong1234"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"
    r = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "Wrong1234"})
    assert r.status_code == 401


def test_protected_routes_require_auth(client):
    for method, url in [("get", "/api/topics/tree"), ("get", "/api/progress/summary"), ("get", "/api/quizzes/1"),
                        ("get", "/api/progress/history"), ("get", "/api/remediation/ch1-s1-c1"),
                        ("post", "/api/learning/notes"), ("post", "/api/learning/quiz"), ("get", "/api/auth/me")]:
        r = getattr(client, method)(url, **({"json": {}} if method == "post" else {}))
        assert r.status_code == 401, (url, r.status_code)


def test_logout_revokes_token(client):
    make_user(client)
    token = client.cookies.get("anatomind_session")
    assert client.post("/api/auth/logout").status_code == 204
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})   # replay the old token
    assert r.status_code == 401 and r.json()["error"]["code"] == "session_revoked"


def test_tampered_token_rejected(client):
    make_user(client)
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401
