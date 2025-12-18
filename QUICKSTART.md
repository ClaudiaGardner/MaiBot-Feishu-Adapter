# MaiBot 飞书适配器 - 快速开始

## 🎯 功能概览

MaiBot-Feishu-Adapter 是一个飞书机器人适配器，让 MaiBot 能够接入飞书平台，实现飞书群聊和私聊的智能对话。

## 📋 特性

- ✅ 支持飞书群聊和私聊
- ✅ 自动消息格式转换
- ✅ 实时消息推送
- ✅ 支持白名单/黑名单管理
- ✅ 与 MaiBot 无缝集成

## 🚀 快速启动

### 1. 配置飞书应用

参考 [DEPLOY.md](DEPLOY.md) 完成飞书应用配置。

### 2. 配置适配器

```bash
cd /home/cloud/maimai/MaiBot-Feishu-Adapter
cp template/template_config.toml config.toml
vim config.toml
```

填写以下必要信息：
- `app_id` - 飞书应用 ID
- `app_secret` - 飞书应用密钥
- `verification_token` - 事件验证 Token

### 3. 使用一键启动脚本

```bash
cd /home/cloud/maimai
./start_all.sh start
```

这将自动启动：
1. NapCat (QQ 协议)
2. QQ Adapter
3. 飞书 Adapter ⭐
4. MaiBot

### 4. 查看状态

```bash
./start_all.sh status
```

输出示例：
```
=== 服务状态 ===

NapCat:              运行中 (会话: napcat)
QQ Adapter:          运行中 (会话: adapter)
飞书 Adapter:        运行中 (会话: feishu-adapter) ⭐
MaiBot:              运行中 (会话: maibot)
```

### 5. 查看日志

```bash
# 进入飞书适配器会话
screen -r feishu-adapter

# 按 Ctrl+A 然后 D 退出（不停止程序）
```

## 🔧 单独管理飞书适配器

### 启动

```bash
cd /home/cloud/maimai/MaiBot-Feishu-Adapter
conda activate MaiBotEnv
python main.py
```

### 后台运行

```bash
screen -dmS feishu-adapter bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate MaiBotEnv && cd /home/cloud/maimai/MaiBot-Feishu-Adapter && python main.py; exec bash"
```

### 停止

```bash
screen -S feishu-adapter -X quit
```

## 📝 使用示例

### 私聊机器人

1. 在飞书中搜索你的机器人
2. 发送消息："你好"
3. 机器人会自动回复

### 群聊中使用

1. 将机器人添加到群聊
2. @机器人 发送消息："@凯西 今天天气怎么样"
3. 机器人会回复

## ⚙️ 配置说明

### 白名单模式（推荐）

```toml
[chat]
whitelist_mode = true
chat_whitelist = ["oc_xxx", "oc_yyy"]  # 允许的群聊 ID
user_whitelist = ["ou_xxx", "ou_yyy"]  # 允许的用户 open_id
```

### 黑名单模式

```toml
[chat]
whitelist_mode = false
chat_blacklist = ["oc_xxx"]  # 禁止的群聊 ID
user_blacklist = ["ou_xxx"]  # 禁止的用户 open_id
```

### 获取群聊 ID 和用户 ID

查看适配器日志，当收到消息时会显示：
```
📩 接收飞书消息: [group] ou_xxx: 你好
```

其中 `ou_xxx` 是用户的 open_id。群聊 ID 会在日志的详细信息中显示。

## 🐛 故障排除

### 问题：机器人不回复

**检查步骤：**
1. 确认适配器正在运行：`screen -r feishu-adapter`
2. 确认 MaiBot 正在运行：`screen -r maibot`
3. 检查白名单/黑名单配置
4. 查看日志是否有错误信息

### 问题：Webhook 验证失败

**解决方案：**
1. 确认 `verification_token` 配置正确
2. 检查 Webhook 地址是否可访问
3. 如果是内网，确认内网穿透正常

### 问题：发送消息失败

**检查步骤：**
1. 确认 `app_id` 和 `app_secret` 正确
2. 确认应用权限已配置
3. 查看飞书开放平台的审核状态

## 📚 更多信息

- 详细部署指南：[DEPLOY.md](DEPLOY.md)
- MaiBot 主项目：[../MaiBot/README.md](../MaiBot/README.md)
- 飞书开放平台：https://open.feishu.cn/

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
