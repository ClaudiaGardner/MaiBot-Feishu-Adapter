"""飞书长连接事件客户端 (使用官方 SDK)"""
import asyncio
import threading  # 🟢 引入 threading
from lark_oapi import ws
import lark_oapi as lark
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
from lark_oapi.event.dispatcher_handler import EventDispatcherHandler
from src.logger import logger
from src.config import global_config
from src.message_converter import process_feishu_message
from src.feishu_client import feishu_client


class FeishuEventClient:
    """飞书长连接事件客户端"""
    
    def __init__(self):
        self.cli = None
        self.main_loop = None
        self._thread = None  # 保存线程引用
    
    async def handle_message_event(self, event_data: P2ImMessageReceiveV1):
        """处理消息事件"""
        try:
            event = event_data.event
            open_id = event.sender.sender_id.open_id
            user_info = feishu_client.get_user_info(open_id) or {}
            sender_name = user_info.get("name", "飞书用户")
            sender_avatar = user_info.get("avatar_url", "")
            
            message_data = {
                "sender": {
                    "sender_id": {
                        "open_id": event.sender.sender_id.open_id,
                        "user_id": getattr(event.sender.sender_id, 'user_id', ''),
                    },
                    "sender_type": event.sender.sender_type,
                    "tenant_key": event.sender.tenant_key,
                    "name": sender_name,
                    "sender_name": {"default_name": sender_name},
                    "avatar_url": sender_avatar,
                },
                "message": {
                    "message_id": event.message.message_id,
                    "root_id": getattr(event.message, 'root_id', ''),
                    "parent_id": getattr(event.message, 'parent_id', ''),
                    "create_time": event.message.create_time,
                    "chat_id": event.message.chat_id,
                    "chat_type": event.message.chat_type,
                    "message_type": event.message.message_type,
                    "content": event.message.content,
                    "mentions": getattr(event.message, 'mentions', None) or [],
                }
            }
            await process_feishu_message(message_data)
        except Exception as e:
            logger.error(f"❌ 处理消息事件失败: {e}", exc_info=True)
    
    def on_message_sync(self, data: P2ImMessageReceiveV1):
        """消息事件回调"""
        try:
            logger.info(f"🔔 收到消息回调！")
            
            # 🟢 添加调试日志
            event = data.event
            chat_type = event.message.chat_type if event and event.message else "unknown"
            chat_id = event.message.chat_id if event and event.message else "unknown"
            logger.info(f"📋 消息详情: chat_type={chat_type}, chat_id={chat_id}")
            
            if self.main_loop and self.main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.handle_message_event(data), 
                    self.main_loop
                )
            else:
                logger.warning("⚠️ 主事件循环不可用，无法处理消息")
        except Exception as e:
            logger.error(f"❌ 消息回调失败: {e}", exc_info=True)
    
    async def connect(self):
        """连接到飞书长连接服务"""
        try:
            logger.info("🔗 正在建立飞书长连接...")
            self.main_loop = asyncio.get_event_loop()
            
            handler_builder = EventDispatcherHandler.builder(
                global_config.feishu.encrypt_key,
                global_config.feishu.verification_token
            )
            
            # 🟢 关键修复：注册群消息和私聊消息的事件处理器
            # p2 表示 API 版本 2.0（point 2）
            handler_builder.register_p2_im_message_receive_v1(self.on_message_sync)  # 通用消息接收
            
            logger.info("✅ 已注册消息接收事件处理器")
            
            self.cli = ws.Client(
                app_id=global_config.feishu.app_id,
                app_secret=global_config.feishu.app_secret,
                event_handler=handler_builder.build()
            )
            
            logger.info("✅ 飞书长连接配置完成")
            logger.info("💓 开始接收事件...")
            
            # --- 🟢 关键修改：使用守护线程启动阻塞的 start() ---
            # 守护线程 (daemon=True) 会在主程序退出时自动随之销毁，不会卡住程序
            self._thread = threading.Thread(target=self.cli.start)
            self._thread.daemon = True 
            self._thread.start()
            
            # 注意：这里不再需要 await，因为线程在后台运行
            
        except Exception as e:
            logger.error(f"❌ 建立长连接失败: {e}", exc_info=True)
            raise
    
    async def disconnect(self):
        """断开连接"""
        # 🟢 关键修改：不再调用不存在的 close()
        # 由于我们使用了守护线程，主程序退出时，长连接线程会自动被系统回收
        logger.info("🔌 飞书长连接客户端已标记为停止")

# 全局实例
feishu_event_client = FeishuEventClient()