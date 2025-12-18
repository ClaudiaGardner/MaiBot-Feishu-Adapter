# MaiBot-Feishu-Adapter

> 飞书（Lark/Feishu）适配器，用于连接 [MaiBot](https://github.com/Moemu/MaiBot) 与飞书平台。

## 📌 功能特性

- ✅ **消息双向通信**：接收飞书消息并转发给 MaiBot，将 MaiBot 的回复发送回飞书
- ✅ **群组 & 私聊支持**：同时支持飞书群组和私聊消息
- ✅ **@ 提及识别**：正确处理飞书中的 @ 提及，MaiBot 能识别被 @ 并响应
- ✅ **图片处理**：
  - 接收飞书图片，下载并转换为 base64 供 MaiBot 多模态模型处理
  - 发送图片到飞书（上传 base64 图片）
- ✅ **机器人自动注册**：启动时自动向 MaiBot 注册机器人信息
- ✅ **长连接模式**：使用飞书 WebSocket 长连接，实时接收消息
- ✅ **独立记忆**：群组和私聊的记忆、上下文完全独立

## 📋 前提条件

### 1. MaiBot Core
- 已安装并配置 [MaiBot](https://github.com/Moemu/MaiBot)
- MaiBot 正在运行并监听 `localhost:8000`

### 2. 飞书应用
1. 在 [飞书开放平台](https://open.feishu.cn/) 创建应用
2. 开启**机器人能力**
3. 配置**权限**：
   - `im:message` - 获取与发送单聊、群组消息
   - `im:message.p2p_msg` - 获取用户发给机器人的单聊消息
   - `im:message.group_msg` - 获取群组中所有消息（敏感权限）
   - `im:message.group_at_msg` - 获取用户在群组中@机器人的消息
   - `im:resource` - 获取与上传图片或文件资源
4. 配置**事件订阅**：
   - 订阅 `im.message.receive_v1` 事件
   - 使用**长连接模式**（无需配置回调 URL）

### 3. Python 环境
- Python 3.10+
- Conda（推荐）或虚拟环境

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/MaiBot-Feishu-Adapter.git
cd MaiBot-Feishu-Adapter
```

### 2. 安装依赖

```bash
# 使用 conda（推荐）
conda create -n MaiBotEnv python=3.12
conda activate MaiBotEnv
pip install -r requirements.txt

# 或使用 venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置

复制配置模板并填写你的飞书应用信息：

```bash
cp config.toml.example config.toml
```

编辑 `config.toml`：

```toml
[feishu]
app_id = "cli_xxxxxxxxxx"           # 飞书应用 App ID
app_secret = "xxxxxxxxxxxxx"         # 飞书应用 App Secret
encrypt_key = ""                     # 可选：加密 Key
verification_token = ""              # 可选：验证 Token

[maibot]
platform = "feishu"                  # 平台标识
host = "localhost"                   # MaiBot 地址
port = 8000                          # MaiBot WebSocket 端口
```

### 4. 运行

```bash
python main.py
```

或使用 screen 后台运行：

```bash
screen -dmS feishu-adapter bash -c "conda activate MaiBotEnv && python main.py; exec bash"
screen -r feishu-adapter  # 查看日志
```

## 📁 项目结构

```
MaiBot-Feishu-Adapter/
├── main.py                 # 主程序入口
├── config.toml            # 配置文件（需自行创建）
├── config.toml.example    # 配置模板
├── requirements.txt       # Python 依赖
├── src/
│   ├── logger.py         # 日志配置
│   ├── config.py         # 配置加载
│   ├── feishu_client.py  # 飞书 API 客户端
│   ├── event_client.py   # 飞书事件监听（长连接）
│   ├── message_converter.py  # 消息格式转换
│   └── maibot_client.py  # MaiBot 客户端
└── README.md
```

## 🔧 工作原理

```
飞书用户消息
    ↓
飞书 WebSocket 长连接推送
    ↓
event_client.py 接收事件
    ↓
message_converter.py 转换为 MessageBase 格式
    ↓
maibot_client.py 发送到 MaiBot Core (ws://localhost:8000)
    ↓
MaiBot 处理并生成回复
    ↓
maibot_client.py 接收回复（MessageBase 格式）
    ↓
解析消息段（文本、图片等）
    ↓
feishu_client.py 发送到飞书
    ↓
飞书用户收到回复
```

## 🎯 使用说明

### 群组使用
1. 在飞书群组中添加你的机器人应用
2. 确保应用有 `im:message.group_msg` 权限并已发布
3. 在群里 @ 机器人或直接发送消息（取决于权限配置）

### 私聊使用
1. 直接与机器人应用私聊即可
2. 无需特殊配置

### 图片功能
- **接收图片**：用户发送的图片会自动下载并转换为 base64，供 MaiBot 的多模态模型（如 `qwen3-vl-30`）识别
- **发送图片**：MaiBot 回复的图片（base64 格式）会自动上传到飞书并发送

## ⚙️ 配置选项

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `feishu.app_id` | 飞书应用 ID | ✅ |
| `feishu.app_secret` | 飞书应用密钥 | ✅ |
| `feishu.encrypt_key` | 消息加密 Key | ❌ |
| `feishu.verification_token` | 事件验证 Token | ❌ |
| `maibot.platform` | 平台标识 | ✅ |
| `maibot.host` | MaiBot 地址 | ✅ |
| `maibot.port` | MaiBot 端口 | ✅ |

## 🐛 常见问题

### 1. 无法连接到 MaiBot
**错误**：`Cannot connect to host localhost:8000`

**解决**：
- 确保 MaiBot Core 已启动并监听 8000 端口
- 检查防火墙设置
- 先启动 MaiBot Core，再启动 Adapter

### 2. 群组消息收不到
**可能原因**：
- 未开启 `im:message.group_msg` 权限
- 权限修改后未重新发布应用版本
- 机器人未添加到群组

**解决**：
1. 在开放平台检查权限配置
2. 创建新版本并发布
3. 确认机器人在群组成员列表中

### 3. 图片下载失败
**错误**：`HTTP 400` 或 `图片下载失败`

**解决**：
- 确保有 `im:resource` 权限
- 检查 `tenant_access_token` 是否有效
- 查看详细错误日志

### 4. @ 提及不生效
**现象**：@ 机器人后没有响应

**检查**：
- 机器人是否已成功注册（查看启动日志）
- MaiBot Core 是否正确识别机器人 ID
- 查看 MaiBot Core 日志确认是否收到消息

## 📝 开发说明

### 消息格式
本适配器使用 [maim_message](https://pypi.org/project/maim-message/) 标准格式与 MaiBot Core 通信：

```python
MessageBase(
    message_info=BaseMessageInfo(
        platform="feishu",
        user_info=UserInfo(...),
        group_info=GroupInfo(...),  # 私聊时为 None
        ...
    ),
    message_segment=Seg(type="seglist", data=[
        Seg(type="text", data="消息内容"),
        Seg(type="image", data="base64_image_data"),
        ...
    ])
)
```

### 添加新功能
1. 在 `message_converter.py` 中处理新的消息类型
2. 在 `maibot_client.py` 中处理 MaiBot 的新回复类型
3. 在 `feishu_client.py` 中添加新的飞书 API 调用

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [MaiBot](https://github.com/Moemu/MaiBot) - AI聊天机器人核心
- [飞书开放平台](https://open.feishu.cn/) - 飞书 API 文档
- [maim_message](https://pypi.org/project/maim-message/) - 消息标准格式库

## 💬 联系方式

如有问题，欢迎提交 [Issue](https://github.com/YOUR_USERNAME/MaiBot-Feishu-Adapter/issues)

---

⭐ 如果这个项目对你有帮助，请给个 Star！
