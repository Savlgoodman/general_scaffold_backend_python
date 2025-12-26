"""
管理员用户API测试
"""
import pytest
from fastapi.testclient import TestClient

from app.models.admin_user import AdminUser
from app.core.security import get_password_hash


def test_register(client: TestClient):
    """
    测试管理员用户注册
    """
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["username"] == "testuser"


def test_login(client: TestClient, db):
    """
    测试管理员用户登录
    """
    # 创建测试管理员用户
    user = AdminUser(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    
    # 登录
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_get_current_admin_user(client: TestClient, db):
    """
    测试获取当前管理员用户信息
    """
    # 创建测试管理员用户
    user = AdminUser(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    
    # 登录获取token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
        }
    )
    token = login_response.json()["data"]["access_token"]
    
    # 获取当前管理员用户信息
    response = client.get(
        "/api/v1/admin_users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["username"] == "testuser"


