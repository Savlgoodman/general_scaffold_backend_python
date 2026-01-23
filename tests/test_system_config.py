"""
系统配置功能测试
"""
import pytest
from app.models.admin_system_config import AdminSystemConfig
from app.services.system_info_service import SystemInfoService


def test_default_configs_exist():
    """测试默认配置存在"""
    assert "site_name" in SystemInfoService.DEFAULT_CONFIGS
    assert "version" in SystemInfoService.DEFAULT_CONFIGS
    assert "last_update_date" in SystemInfoService.DEFAULT_CONFIGS


def test_get_system_config_empty_db(db):
    """测试空数据库返回默认配置"""
    configs = SystemInfoService.get_system_config(db)
    
    assert configs == SystemInfoService.DEFAULT_CONFIGS
    assert "site_name" in configs
    assert "version" in configs
    assert "last_update_date" in configs


def test_update_system_config_create_new(db):
    """测试创建新配置项"""
    new_configs = [
        {
            "config_key": "test_key",
            "config_value": "test_value",
            "description": "测试配置"
        }
    ]
    
    result = SystemInfoService.update_system_config(db, new_configs)
    
    assert "test_key" in result
    assert result["test_key"] == "test_value"
    
    # 验证数据库中存在该配置
    config = db.query(AdminSystemConfig).filter(
        AdminSystemConfig.config_key == "test_key"
    ).first()
    assert config is not None
    assert config.config_value == "test_value"


def test_update_system_config_update_existing(db):
    """测试更新已存在的配置项"""
    # 先创建一个配置
    config = AdminSystemConfig(
        config_key="existing_key",
        config_value="old_value",
        description="旧描述"
    )
    db.add(config)
    db.commit()
    
    # 更新配置
    update_configs = [
        {
            "config_key": "existing_key",
            "config_value": "new_value",
            "description": "新描述"
        }
    ]
    
    result = SystemInfoService.update_system_config(db, update_configs)
    
    assert result["existing_key"] == "new_value"
    
    # 验证数据库中的值已更新
    updated_config = db.query(AdminSystemConfig).filter(
        AdminSystemConfig.config_key == "existing_key"
    ).first()
    assert updated_config.config_value == "new_value"
    assert updated_config.description == "新描述"


def test_update_system_config_batch(db):
    """测试批量更新多个配置项"""
    batch_configs = [
        {"config_key": "key1", "config_value": "value1", "description": "描述1"},
        {"config_key": "key2", "config_value": "value2", "description": "描述2"},
        {"config_key": "key3", "config_value": "value3", "description": "描述3"}
    ]
    
    result = SystemInfoService.update_system_config(db, batch_configs)
    
    assert "key1" in result
    assert "key2" in result
    assert "key3" in result
    assert result["key1"] == "value1"
    assert result["key2"] == "value2"
    assert result["key3"] == "value3"


def test_admin_system_config_model_fields(db):
    """测试模型字段存在性"""
    config = AdminSystemConfig(
        config_key="test",
        config_value="value",
        description="desc"
    )
    db.add(config)
    db.commit()
    
    # 验证所有字段
    assert hasattr(config, 'id')
    assert hasattr(config, 'config_key')
    assert hasattr(config, 'config_value')
    assert hasattr(config, 'description')
    assert hasattr(config, 'created_at')
    assert hasattr(config, 'updated_at')
    assert hasattr(config, 'is_deleted')


def test_config_key_unique_constraint(db):
    """测试 config_key 唯一约束"""
    config1 = AdminSystemConfig(
        config_key="unique_key",
        config_value="value1"
    )
    db.add(config1)
    db.commit()
    
    # 尝试插入相同的 config_key
    config2 = AdminSystemConfig(
        config_key="unique_key",
        config_value="value2"
    )
    db.add(config2)
    
    with pytest.raises(Exception):  # 应该抛出唯一约束异常
        db.commit()



def test_update_system_config_invalid_key(db):
    """测试更新非法配置键应该失败"""
    invalid_configs = [
        {
            "config_key": "invalid_key",
            "config_value": "some_value",
            "description": "非法配置"
        }
    ]
    
    with pytest.raises(ValueError) as exc_info:
        SystemInfoService.update_system_config(db, invalid_configs)
    
    assert "不允许的配置键" in str(exc_info.value)


def test_get_system_config_only_allowed_keys(db):
    """测试只返回允许的配置键"""
    # 创建一个允许的配置和一个不允许的配置
    allowed_config = AdminSystemConfig(
        config_key="site_name",
        config_value="测试站点"
    )
    # 直接插入一个不在白名单的配置（绕过 service 层验证）
    invalid_config = AdminSystemConfig(
        config_key="invalid_key",
        config_value="invalid_value"
    )
    db.add(allowed_config)
    db.add(invalid_config)
    db.commit()
    
    # 获取配置
    configs = SystemInfoService.get_system_config(db)
    
    # 应该只包含允许的键
    assert "site_name" in configs
    assert "invalid_key" not in configs
    # 应该包含所有默认配置键
    assert "version" in configs
    assert "last_update_date" in configs


def test_allowed_config_keys():
    """测试允许的配置键列表"""
    assert "site_name" in SystemInfoService.ALLOWED_CONFIG_KEYS
    assert "version" in SystemInfoService.ALLOWED_CONFIG_KEYS
    assert "last_update_date" in SystemInfoService.ALLOWED_CONFIG_KEYS
    assert len(SystemInfoService.ALLOWED_CONFIG_KEYS) == 3
