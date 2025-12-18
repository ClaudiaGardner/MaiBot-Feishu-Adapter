"""消息格式转换器 - 使用 maim_message 标准格式"""
import json
import time
import base64
from typing import Dict, Any
from src.logger import logger
from src.config import global_config

# 🟢 引入 maim_message 标准对象
from maim_message import (
    UserInfo,
    GroupInfo,
    Seg,
    BaseMessageInfo,
    MessageBase,
    FormatInfo,
)


async def download_feishu_image(image_key: str, message_id: str) -> str:
    """下载飞书图片并转换为base64
    
    Args:
        image_key: 飞书图片的image_key
        message_id: 消息ID
        
    Returns:
        base64编码的图片字符串，失败返回空字符串
    """
    from src.feishu_client import feishu_client
    import requests
    
    try:
        # 获取 access token
        token = feishu_client._get_tenant_access_token()
        if not token:
            logger.error("无法获取 access token")
            return ""
        
        # 🟢 使用正确的API：获取消息中的资源文件
        # 文档: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message-resource/get
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{image_key}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 指定返回类型为文件流
        params = {
            "type": "image"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            # 图片内容在响应体中
            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            logger.info(f"✅ 图片下载成功: {image_key}")
            return image_base64
        else:
            # 🟢 详细错误日志
            try:
                error_data = response.json()
                logger.error(f"图片下载失败: HTTP {response.status_code}")
                logger.error(f"错误详情: {error_data}")
                logger.error(f"URL: {url}")
            except:
                logger.error(f"图片下载失败: HTTP {response.status_code}, Response: {response.text[:200]}")
            return ""
            
    except Exception as e:
        logger.error(f"下载图片异常: {e}", exc_info=True)
        return ""





async def process_feishu_message(event_data: Dict[str, Any]):
    """处理飞书原始数据 -> 转换为 MaiBot 标准格式 -> 发送"""
    
    # 1. 提取基础信息
    sender = event_data.get("sender", {})
    message = event_data.get("message", {})
    
    # 防止自言自语
    if sender.get("sender_type") == "app":
        return

    # 2. 构造用户信息 (UserInfo 对象)
    open_id = sender.get("sender_id", {}).get("open_id")
    user_id = open_id or sender.get("sender_id", {}).get("user_id", "")
    nickname = sender.get("name") or sender.get("sender_name", {}).get("default_name", "飞书用户")
    
    platform_name = global_config.maibot.platform
    
    user_info = UserInfo(
        platform=platform_name,
        user_id=str(user_id),
        user_nickname=nickname,
        user_cardname=nickname,
    )

    # 3. 构造群组信息 (GroupInfo 对象，私聊时为 None)
    chat_type = message.get("chat_type", "")
    chat_id = message.get("chat_id", "")
    
    group_info = None
    if chat_type == "group":
        group_info = GroupInfo(
            platform=platform_name,
            group_id=str(chat_id),
            group_name="飞书群组"
        )

    # 4. 时间戳处理
    create_time_ms = message.get("create_time", "0")
    try:
        msg_time = float(int(create_time_ms) / 1000.0)
    except:
        msg_time = time.time()

    # 5. 消息内容解析为 Seg 列表
    content_raw = message.get("content", "{}")
    message_type = message.get("message_type", "")
    message_id = message.get("message_id", "")  # 🟢 获取消息ID
    
    seg_list = []
    text_content = ""
    
    try:
        content_json = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
        
        if message_type == "text":
            text_content = content_json.get("text", "")
        elif message_type == "image":
            # 🟢 处理图片消息
            image_key = content_json.get("image_key", "")
            if image_key and message_id:
                # 下载图片并转换为base64
                image_base64 = await download_feishu_image(image_key, message_id)
                if image_base64:
                    seg_list.append(Seg(type="image", data=image_base64))
                    text_content = "[图片]"
                else:
                    text_content = "[图片下载失败]"
            else:
                text_content = "[图片]"
        else:
            text_content = f"[{message_type}]"
    except Exception as e:
        logger.error(f"解析消息内容失败: {e}")
        text_content = str(content_raw)
    
    # 🟢 处理 @ 提及：将 @_user_1 替换为 @<昵称:user_id>
    mentions = message.get("mentions", [])
    bot_mentioned = False  # 标记机器人是否被 @
    bot_user_id = None
    
    if mentions and text_content:
        for mention in mentions:
            # mention 是 MentionEvent 对象，需要用属性访问
            try:
                key = getattr(mention, "key", "")
                mention_id_obj = getattr(mention, "id", None)
                mention_name = getattr(mention, "name", "")
                
                # id 也是一个对象，需要获取 open_id
                mention_id = ""
                if mention_id_obj:
                    mention_id = getattr(mention_id_obj, "open_id", "")
                    # 检查是否 mention 的是机器人（tenant_key）
                    mention_tenant_key = getattr(mention, "tenant_key", "")
                    if mention_tenant_key:
                        bot_mentioned = True
                        bot_user_id = mention_id  # 记录机器人的 user_id
                
                if key and mention_id:
                    # 替换为 @<昵称:user_id> 格式（参考 Napcat）
                    replacement = f"@<{mention_name}:{mention_id}>"
                    text_content = text_content.replace(key, replacement)
            except Exception as e:
                logger.debug(f"处理 mention 失败: {e}")

    # 构造最终的 Seg 列表
    if not seg_list:  # 如果没有图片，添加文本
        seg_list.append(Seg(type="text", data=text_content))
    
    # 包装为 seglist
    submit_seg = Seg(type="seglist", data=seg_list)

    # 6. 构造 FormatInfo
    format_info = FormatInfo(
        content_format=["text", "image"],
        accept_format=["text", "image", "json"]
    )

    # 7. 构造 BaseMessageInfo
    message_info = BaseMessageInfo(
        platform=platform_name,
        message_id=str(message.get("message_id", "")),
        time=msg_time,
        user_info=user_info,
        group_info=group_info,
        template_info=None,
        format_info=format_info,
        additional_config={
            "feishu": {
                "chat_id": chat_id,
                "chat_type": chat_type,
                "message_id": message.get("message_id", "")  # 🟢 保存消息ID用于回复引用
            },
            "bot_mentioned": bot_mentioned,  # 🟢 标记机器人是否被 @
            "bot_user_id": bot_user_id,      # 🟢 机器人的 user_id
        }
    )

    # 8. 构造 MessageBase
    message_base = MessageBase(
        message_info=message_info,
        message_segment=submit_seg,
        raw_message=text_content
    )

    logger.info(f"📩 转换消息: {nickname}: {text_content[:30]}")
    
    # 9. 发送到 MaiBot
    from src.maibot_client import maibot_client
    import asyncio
    
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
            
        loop.create_task(maibot_client.send_message(message_base))
        
    except Exception as e:
        logger.error(f"❌ 投递消息到 Maibot 失败: {e}", exc_info=True)