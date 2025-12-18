"""MaiBot 通信客户端"""
import json
import asyncio
import base64
from maim_message import Router, RouteConfig, TargetConfig
from src.logger import logger, custom_logger
from src.config import global_config
from src.feishu_client import feishu_client

class MaiBotClient:
    def __init__(self):
        route_config = RouteConfig(
            route_config={
                global_config.maibot.platform: TargetConfig(
                    url=f"ws://{global_config.maibot.host}:{global_config.maibot.port}/ws",
                    token=None,
                )
            }
        )
        self.router = Router(route_config, custom_logger)
    
    async def connect(self):
        logger.info(f"正在连接到 MaiBot: ws://{global_config.maibot.host}:{global_config.maibot.port}/ws")
        self.router.register_class_handler(self.handle_maibot_response)
        await self.router.run()
    
    async def send_message(self, message_base):
        """发送消息到 MaiBot (接收 MessageBase 对象)"""
        try:
            await self.router.send_message(message_base)
        except Exception as e:
            logger.error(f"发送消息到 MaiBot 失败: {e}")

    async def handle_maibot_response(self, message: dict):
        """处理 MaiBot 的回复/指令"""
        try:
            # 🟢 关键修改：MaiBot 的回复是以 MessageBase 字典格式发送的
            # 检查是否是 MessageBase 格式（包含 message_info 和 message_segment）
            if "message_info" in message and "message_segment" in message:
                await self.handle_message_base_reply(message)
                return
            
            # 否则按旧逻辑处理（主动发送指令）
            msg_type = message.get("type")
            action = message.get("action")
            
            if not action and ("status" in message or "retcode" in message):
                return
            
            if action in ["send_msg", "send_private_msg", "send_group_msg"]:
                params = message.get("params", {})
                
                # 获取目标 ID
                user_id = params.get("user_id")
                group_id = params.get("group_id")
                receive_id = ""
                receive_id_type = ""
                
                if group_id:
                    receive_id = str(group_id); receive_id_type = "chat_id"
                elif user_id:
                    receive_id = str(user_id); receive_id_type = "open_id"
                else:
                    target_id = params.get("target_id")
                    if target_id:
                        receive_id = str(target_id)
                        receive_id_type = "chat_id" if receive_id.startswith("oc_") else "open_id"
                    else:
                        return

                # 解析消息内容
                raw_content = params.get("message", "")
                
                # 如果是字符串，转为单元素列表
                segments = raw_content if isinstance(raw_content, list) else [{"type": "text", "data": {"text": str(raw_content)}}]
                
                # 获取当前 loop
                try: loop = asyncio.get_running_loop()
                except RuntimeError: loop = asyncio.get_event_loop()

                # 遍历消息段，逐个发送
                for seg in segments:
                    if not isinstance(seg, dict): continue
                    
                    seg_type = seg.get("type")
                    data = seg.get("data", {})
                    
                    # 1. 处理文本
                    if seg_type == "text":
                        text = data.get("text", "")
                        if text.strip():
                            content_payload = json.dumps({"text": text}, ensure_ascii=False)
                            await loop.run_in_executor(None, lambda: feishu_client.send_message(
                                receive_id, receive_id_type, "text", content_payload
                            ))
                            
                    # 2. 处理图片
                    elif seg_type == "image":
                        file_content = data.get("file", "")
                        
                        # 检查是否为 Base64
                        base64_str = ""
                        if file_content.startswith("base64://"):
                            base64_str = file_content.replace("base64://", "")
                        elif "base64" in file_content: 
                            base64_str = file_content
                        
                        if base64_str:
                            try:
                                logger.info("🖼️ 检测到图片，正在解码上传...")
                                # 解码 Base64
                                image_data = base64.b64decode(base64_str)
                                
                                # 定义内部函数以便在 executor 中运行
                                def upload_and_send():
                                    image_key = feishu_client.upload_image(image_data)
                                    if image_key:
                                        feishu_client.send_image_message(receive_id, receive_id_type, image_key)
                                
                                await loop.run_in_executor(None, upload_and_send)
                                
                            except Exception as e:
                                logger.error(f"❌ 图片处理失败: {e}")
                        else:
                            logger.warning(f"⚠️ 暂不支持发送网络图片链接: {file_content[:30]}...")

                    # 3. 处理表情
                    elif seg_type == "emoji" or seg_type == "face":
                        pass 

                return 

        except Exception as e:
            logger.error(f"处理 MaiBot 回复异常: {e}", exc_info=True)

    async def handle_message_base_reply(self, message_base_dict: dict):
        """处理 MessageBase 格式的回复消息"""
        from maim_message import MessageBase, Seg
        
        try:
            # 将字典转换为 MessageBase 对象
            message_base = MessageBase.from_dict(message_base_dict)
            
            # 提取信息
            message_info = message_base.message_info
            message_segment = message_base.message_segment
            
            # 确定发送目标
            user_info = message_info.user_info
            group_info = message_info.group_info
            
            receive_id = ""
            receive_id_type = ""
            
            if group_info:
                # 群聊
                receive_id = str(group_info.group_id)
                receive_id_type = "chat_id"
            elif user_info:
                # 私聊
                receive_id = str(user_info.user_id)
                receive_id_type = "open_id"
            else:
                logger.warning("无法确定消息接收者")
                return
            
            # 解析 Seg 消息段
            segments = self.parse_seg_to_list(message_segment)
            
            # 获取原始消息 ID（用于回复）
            additional_config = getattr(message_info, 'additional_config', {}) or {}
            feishu_info = additional_config.get('feishu', {})
            original_message_id = feishu_info.get('message_id')
            
            # 发送消息
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            for seg in segments:
                seg_type = seg.get("type")
                data = seg.get("data", "")
                
                if seg_type == "text":
                    if data.strip():
                        content_payload = json.dumps({"text": data}, ensure_ascii=False)
                        
                        # 如果有原始消息 ID，使用 reply；否则 send
                        if original_message_id:
                            await loop.run_in_executor(None, lambda: feishu_client.reply_message(
                                original_message_id, "text", content_payload
                            ))
                        else:
                            await loop.run_in_executor(None, lambda: feishu_client.send_message(
                                receive_id, receive_id_type, "text", content_payload
                            ))
                        
                elif seg_type == "image":
                    if data.startswith("base64://"):
                        base64_str = data.replace("base64://", "")
                    else:
                        base64_str = data
                    
                    try:
                        image_data = base64.b64decode(base64_str)
                        def upload_and_send():
                            image_key = feishu_client.upload_image(image_data)
                            if image_key:
                                feishu_client.send_image_message(receive_id, receive_id_type, image_key)
                        await loop.run_in_executor(None, upload_and_send)
                    except Exception as e:
                        logger.error(f"图片发送失败: {e}")
            
            logger.info(f"✅ 消息已发送到飞书")
                        
        except Exception as e:
            logger.error(f"处理 MessageBase 回复失败: {e}", exc_info=True)

    def parse_seg_to_list(self, seg: 'Seg') -> list:
        """将 Seg 对象解析为简单的列表格式"""
        result = []
        
        if seg.type == "seglist":
            for sub_seg in seg.data:
                result.extend(self.parse_seg_to_list(sub_seg))
        elif seg.type == "text":
            result.append({"type": "text", "data": seg.data})
        elif seg.type == "image":
            result.append({"type": "image", "data": seg.data})
        elif seg.type == "emoji":
            result.append({"type": "emoji", "data": seg.data})
        # 忽略其他类型（如 reply 等）
        
        return result

    async def disconnect(self):
        try:
            await self.router.stop()
        except asyncio.CancelledError:
            pass  # 忽略取消错误，这是正常的关闭行为
        except Exception as e:
            logger.error(f"断开连接失败: {e}")

maibot_client = MaiBotClient()