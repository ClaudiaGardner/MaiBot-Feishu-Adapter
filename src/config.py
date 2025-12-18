"""配置管理模块"""
import toml
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import shutil


@dataclass
class FeishuConfig:
    """飞书配置"""
    app_id: str = ""
    app_secret: str = ""
    encrypt_key: str = ""
    verification_token: str = ""

@dataclass
class MaiBotConfig:
    """MaiBot 配置"""
    host: str = "localhost"
    port: int = 8000
    platform: str = "feishu"


@dataclass
class ChatConfig:
    """聊天配置"""
    whitelist_mode: bool = True
    chat_whitelist: List[str] = field(default_factory=list)
    user_whitelist: List[str] = field(default_factory=list)
    chat_blacklist: List[str] = field(default_factory=list)
    user_blacklist: List[str] = field(default_factory=list)


@dataclass
class DebugConfig:
    """调试配置"""
    level: str = "INFO"


@dataclass
class GlobalConfig:
    """全局配置"""
    feishu: FeishuConfig
    maibot: MaiBotConfig
    chat: ChatConfig
    debug: DebugConfig


def load_config() -> GlobalConfig:
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.toml"
    template_path = Path(__file__).parent.parent / "template" / "template_config.toml"
    
    # 如果配置文件不存在，从模板复制
    if not config_path.exists():
        if template_path.exists():
            shutil.copy(template_path, config_path)
            print(f"✅ 已从模板创建配置文件: {config_path}")
        else:
            raise FileNotFoundError(f"配置文件和模板都不存在: {config_path}")
    
    # 加载配置
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = toml.load(f)
    
    # 解析配置
    return GlobalConfig(
        feishu=FeishuConfig(**config_data.get("feishu", {})),
        maibot=MaiBotConfig(**config_data.get("maibot", {})),
        chat=ChatConfig(**config_data.get("chat", {})),
        debug=DebugConfig(**config_data.get("debug", {}))
    )


# 全局配置实例
global_config = load_config()
