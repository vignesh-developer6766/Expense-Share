import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def csrf_app():
    """Create test application with CSRF protection enabled."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_SSL_STRICT"] = True
    app.config["TRUSTED_HOSTS"] = [
        "expenseshare-ai.onrender.com",
        "expenseshare-ai-vignesh.netlify.app",
        "localhost",
        "127.0.0.1",
        "testserver",
    ]

    with app.app_context():
        db.create_all()
        # Seed test user
        if not User.query.filter_by(email="csrf_test@example.com").first():
            user = User(name="CSRF Tester", email="csrf_test@example.com")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


def test_login_via_netlify_proxy_success(csrf_client):
    """Verify login through Netlify proxy headers with matching referrer succeeds."""
    # 1. GET login page with Netlify proxy headers to obtain CSRF token
    res = csrf_client.get(
        "/auth/login",
        base_url="https://expenseshare-ai-vignesh.netlify.app",
        headers={
            "X-Forwarded-Host": "expenseshare-ai-vignesh.netlify.app",
            "X-Forwarded-Proto": "https",
        },
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'name="csrf_token"' in html

    # Extract CSRF token
    import re
    token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert token_match is not None
    token = token_match.group(1)

    # 2. POST login through Netlify proxy
    post_res = csrf_client.post(
        "/auth/login",
        base_url="https://expenseshare-ai-vignesh.netlify.app",
        headers={
            "X-Forwarded-Host": "expenseshare-ai-vignesh.netlify.app",
            "X-Forwarded-Proto": "https",
            "Referer": "https://expenseshare-ai-vignesh.netlify.app/auth/login",
        },
        data={
            "csrf_token": token,
            "email": "csrf_test@example.com",
            "password": "password123",
        },
    )
    # Successful login redirects to dashboard
    assert post_res.status_code == 302
    assert "/dashboard" in post_res.headers.get("Location")


def test_login_render_backend_with_netlify_referrer(csrf_client):
    """Verify Netlify referrer is accepted on Render backend for trusted hosts."""
    res = csrf_client.get(
        "/auth/login",
        base_url="https://expenseshare-ai.onrender.com",
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    import re
    token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert token_match is not None
    token = token_match.group(1)

    # POST with Netlify referrer to Render backend
    post_res = csrf_client.post(
        "/auth/login",
        base_url="https://expenseshare-ai.onrender.com",
        headers={
            "Referer": "https://expenseshare-ai-vignesh.netlify.app/auth/login",
        },
        data={
            "csrf_token": token,
            "email": "csrf_test@example.com",
            "password": "password123",
        },
    )
    assert post_res.status_code == 302
    assert "/dashboard" in post_res.headers.get("Location")


def test_malicious_referrer_blocked(csrf_client):
    """Verify that an untrusted external referrer is rejected with 400 Bad Request."""
    res = csrf_client.get(
        "/auth/login",
        base_url="https://expenseshare-ai-vignesh.netlify.app",
    )
    import re
    token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html := res.get_data(as_text=True))
    token = token_match.group(1)

    post_res = csrf_client.post(
        "/auth/login",
        base_url="https://expenseshare-ai-vignesh.netlify.app",
        headers={
            "Referer": "https://malicious-attacker-site.com/phishing",
        },
        data={
            "csrf_token": token,
            "email": "csrf_test@example.com",
            "password": "password123",
        },
    )
    assert post_res.status_code == 400
    assert "The referrer does not match the host" in post_res.get_data(as_text=True)


def test_missing_csrf_token_blocked(csrf_client):
    """Verify requests without CSRF token are blocked with 400 Bad Request."""
    post_res = csrf_client.post(
        "/auth/login",
        base_url="https://expenseshare-ai-vignesh.netlify.app",
        headers={
            "Referer": "https://expenseshare-ai-vignesh.netlify.app/auth/login",
        },
        data={
            "email": "csrf_test@example.com",
            "password": "password123",
        },
    )
    assert post_res.status_code == 400


def test_invalid_csrf_token_blocked(csrf_client):
    """Verify requests with tampered/invalid CSRF token are blocked."""
    post_res = csrf_client.post(
        "/auth/login",
        base_url="https://expenseshare-ai-vignesh.netlify.app",
        headers={
            "Referer": "https://expenseshare-ai-vignesh.netlify.app/auth/login",
        },
        data={
            "csrf_token": "tampered_invalid_token_12345",
            "email": "csrf_test@example.com",
            "password": "password123",
        },
    )
    assert post_res.status_code == 400


def test_untrusted_forwarded_host_ignored(csrf_app, csrf_client):
    """Verify spoofed X-Forwarded-Host is not adopted into request.host."""
    res = csrf_client.get(
        "/health",
        base_url="https://expenseshare-ai.onrender.com",
        headers={
            "X-Forwarded-Host": "attacker.spoofed.domain.com",
            "X-Forwarded-Proto": "https",
        },
    )
    assert res.status_code == 200
