# 快速部署指南

## 前提条件

1. MaiBot 已安装并运行
2. 拥有飞书企业自建应用权限

## 步骤 1: 安装依赖

```bash
cd /home/cloud/maimai/MaiBot-Feishu-Adapter
conda activate MaiBotEnv
pip install -r requirements.txt
```

## 步骤 2: 配置飞书应用

### 2.1 创建应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 点击"创建企业自建应用"
3. 填写应用名称和描述
4. 获取 **App ID** 和 **App Secret**

### 2.2 配置权限

在"权限管理"中添加以下权限：
- `im:message` - 获取消息
- `im:message:send_as_bot` - 以应用身份发消息
- `contact:user.base:readonly` - 获取用户基本信息（可选）

### 2.3 配置事件订阅（长连接模式）

1. 进入"事件订阅"
2. 选择 **"使用长连接接收事件"**
3. 订阅以下事件：
   - `im.message.receive_v1` - 接收消息
4. 无需配置回调地址（适配器会主动连接飞书服务器）
5. 无需 Verification Token 和 Encrypt Key（长连接模式不需要）

## 步骤 3: 配置 config.toml

复制模板并编辑：

```bash
cp template/template_config.toml config.toml
vim config.toml
```

填入飞书应用信息：

```toml
[feishu]
app_id = "cli_xxxxxxxxxx"           # 从飞书开放平台获取
app_secret = "your_app_secret"      # 从飞书开放平台获取

[maibot]
host = "localhost"
port = 8000
platform = "feishu"

[chat]
whitelist_mode = false              # 设为 false 允许所有聊天
chat_whitelist = []
user_whitelist = []
chat_blacklist = []
user_blacklist = []
```

**注意**: 长连接模式不需要配置 `verification_token` 和 `encrypt_key`，也不需要 `[adapter]` 配置段。

## 步骤 4: 启动适配器

### 方式 1: 直接启动

```bash
python main.py
```

### 方式 2: 使用 screen（推荐）

```bash
screen -dmS feishu-adapter bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate MaiBotEnv && cd /home/cloud/maimai/MaiBot-Feishu-Adapter && python main.py; exec bash"

# 查看日志
screen -r feishu-adapter

# 按 Ctrl+A 然后 D 退出 screen（不停止程序）
```

### 方式 3: 整合到 start_all.sh

编辑 `/home/cloud/maimai/start_all.sh`，添加飞书适配器的启动。

## 步骤 5: 测试

1. 在飞书中找到你的机器人应用
2. 添加到群聊或私聊
3. 发送消息 "@机器人名称 你好"
4. 应该能收到 MaiBot 的回复

## 故障排除

### 问题 1: 无法连接飞书长连接服务

**症状**: 日志显示"连接失败"

**解决方案**:
1. 确认网络可以访问 `open.feishu.cn`
2. 检查防火墙是否允许出站 WebSocket 连接
3. 查看日志中的详细错误信息

### 问题 2: 机器人不回复

**症状**: 发送消息后无回复

**解决方案**:
1. 检查适配器日志：`screen -r feishu-adapter`
2. 确认看到"飞书长连接已建立"消息
3. 检查 MaiBot 是否运行：`screen -r maibot`
4. 确认白名单/黑名单配置
5. 查看 MaiBot 日志是否收到消息

### 问题 3: Access Token 失败

**症状**: 日志显示"获取 access_token 失败"

**解决方案**:
1. 检查 `app_id` 和 `app_secret` 是否正确
2. 确认应用已发布且状态正常
3. 检查网络连接是否正常
## 监控和维护

### 查看日志
### 查看日志

```bash
# 适配器日志
screen -r feishu-adapter

# MaiBot 日志
screen -r maibot
```

### 重启服务

```bash
# 停止
screen -S feishu-adapter -X quit

# 启动
screen -dmS feishu-adapter bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate MaiBotEnv && cd /home/cloud/maimai/MaiBot-Feishu-Adapter && python main.py; exec bash"
```

### 健康检查

```bash
curl http://localhost:9000/feishu/health
```

应该返回：
```json
{
  "status": "healthy",
  "service": "MaiBot-Feishu-Adapter"
}
```
### 重启服务

```bash
# 停止
screen -S feishu-adapter -X quit

# 启动
screen -dmS feishu-adapter bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate MaiBotEnv && cd /home/cloud/maimai/MaiBot-Feishu-Adapter && python main.py; exec bash"
```
