# 飞书文档导出工具

## 📖 说明

这是一个**完全独立**的工具，用于将飞书 Wiki 文档导出为 MaiBot LPMM 知识库可用的格式。

**特点**：
- ✅ 不修改 MaiBot Core 代码
- ✅ 独立运行，不需要启动 MaiBot
- ✅ 自动保存配置，方便重复使用

## 🚀 使用方法

### 1. 安装依赖

```bash
pip install requests
```

### 2. 运行工具

```bash
cd /home/cloud/maimai/MaiBot-Feishu-Adapter/tools
python export_feishu_wiki.py
```

### 3. 按提示输入信息

- 飞书 App ID
- 飞书 App Secret
- Wiki 空间 ID
- 输出目录（MaiBot 的 `data/lpmm_raw_data`）

### 4. 处理导出的数据

```bash
cd /home/cloud/maimai/MaiBot
bash scripts/run_lpmm.sh
```

### 5. 重启 MaiBot

```bash
cd ~/maimai
./start_all.sh restart
```

## 📁 配置文件

首次运行后，工具会在当前目录生成 `feishu_wiki_config.json`：

```json
{
  "app_id": "cli_xxxxxxxxxx",
  "app_secret": "xxxxxxxxxxxxx"
}
```

下次运行会自动读取，无需重复输入。

## ⚙️ 飞书权限要求

确保你的飞书应用有以下权限：
- `wiki:wiki:readonly` - 读取知识库
- `docx:document:readonly` - 读取文档

## 📝 输出格式

导出的文件格式：
```
# 文档标题1

文档内容...

================================================================================

# 文档标题2

文档内容...

================================================================================
```

## 🔍 常见问题

**Q: 支持哪些文档类型？**
A: 目前支持新版飞书文档（docx）。旧版文档、表格等暂不支持。

**Q: 如何获取 Wiki 空间 ID？**
A: 打开 Wiki 页面，URL 中的 `wiki/xxxxx` 部分就是空间 ID。

**Q: 导出很慢怎么办？**
A: 文档较多时会比较慢，请耐心等待。飞书 API 有频率限制。

## 💡 提示

- 定期运行此工具可以保持知识库更新
- 可以配合 cron 定时任务自动更新
- 建议先用小范围测试，确认效果后再大批量导入

---

**工具位置**: `MaiBot-Feishu-Adapter/tools/export_feishu_wiki.py`
