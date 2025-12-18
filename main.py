"""
MaiBot 飞书适配器 - 主程序入口
"""
import asyncio
import signal
import sys
from src.logger import logger
from src.config import global_config
from src.maibot_client import maibot_client
from src.feishu_client import feishu_client
from src.event_client import feishu_event_client
import logging
import lark_oapi
from maim_message import UserInfo, BaseMessageInfo, Seg, MessageBase, FormatInfo

# 全局变量用于优雅关闭
shutdown_event = asyncio.Event()
shutdown_count = 0


def signal_handler(signum, frame):
    """信号处理器"""
    global shutdown_count
    shutdown_count += 1
    
    if shutdown_count == 1:
        logger.warning(f"收到信号 {signum}，正在优雅关闭... (再次按 Ctrl+C 强制退出)")
        shutdown_event.set()
    else:
        logger.error("收到第二次中断信号，强制退出！")
        import sys
        sys.exit(0)


async def run_maibot_client():
    """运行 MaiBot 客户端"""
    try:
        await maibot_client.connect()
        # router.run() 会一直运行，直到被取消
    except Exception as e:
        logger.error(f"❌ MaiBot 客户端错误: {e}")
        shutdown_event.set()


async def run_feishu_event_client():
    """运行飞书长连接客户端"""
    try:
        await feishu_event_client.connect()
    except Exception as e:
        logger.error(f"飞书事件客户端错误: {e}")
        shutdown_event.set()


async def async_main():
    """异步主函数"""
    global should_exit
    
    # 创建任务列表
    tasks = []
    
    try:
        # 1. 先启动 MaiBot 客户端连接
        logger.info("正在启动 MaiBot 客户端...")
        maibot_task = asyncio.create_task(maibot_client.connect())
        tasks.append(maibot_task)
        
        # 等待 MaiBot 连接成功（最多 2 秒）
        await asyncio.sleep(2)
        
        # 2. 注册机器人自己
        await register_bot_self()
        
        # 3. 启动飞书事件监听
        logger.info("正在启动飞书事件监听...")
        feishu_task = asyncio.create_task(feishu_event_client.connect())
        tasks.append(feishu_task)
        
        # 4. 创建 shutdown 监听任务
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        tasks.append(shutdown_task)
        
        # 5. 等待任一任务完成
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # 如果 shutdown_event 被触发，取消所有任务
        if shutdown_task in done:
            logger.info("收到关闭信号，正在取消所有任务...")
            for task in pending:
                task.cancel()
        
        # 等待所有任务完成
        await asyncio.gather(*pending, return_exceptions=True)
                
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
    except Exception as e:
        logger.error(f"主循环异常: {e}", exc_info=True)
    finally:
        # 清理资源
        logger.info("正在清理资源...")
        
        # 取消所有未完成的任务
        for task in tasks:
            if not task.done():
                task.cancel()
        
        try:
            await feishu_event_client.disconnect()
        except Exception as e:
            logger.debug(f"关闭飞书连接时出错: {e}")
        
        try:
            await maibot_client.disconnect()
        except Exception as e:
            logger.debug(f"关闭 MaiBot 客户端时出错: {e}")


async def register_bot_self():
    """注册机器人自己到 MaiBot"""
    from src.feishu_client import feishu_client
    import time
    
    try:
        # 获取机器人自己的信息
        # 飞书 app 的 user_id 通常就是 app_id 对应的 open_id (ou_xxx)
        # 我们需要调用 API 获取
        token = feishu_client._get_tenant_access_token()
        if not token:
            logger.warning("无法获取 token，跳过机器人注册")
            return
        
        import requests
        url = "https://open.feishu.cn/open-apis/bot/v3/info"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("code") == 0:
            bot_info = data.get("bot", {})
            bot_open_id = bot_info.get("open_id", "")
            bot_name = bot_info.get("app_name", "Kaisy")
            
            logger.info(f"🤖 机器人信息: {bot_name} ({bot_open_id})")
            
            # 构造注册消息发送给 MaiBot
            platform_name = global_config.maibot.platform
            
            user_info = UserInfo(
                platform=platform_name,
                user_id=str(bot_open_id),
                user_nickname=bot_name,
                user_cardname=bot_name,
            )
            
            # 发送一条虚拟消息来注册机器人
            format_info = FormatInfo(
                content_format=["text"],
                accept_format=["text"]
            )
            
            message_info = BaseMessageInfo(
                platform=platform_name,
                message_id="bot_register",
                time=time.time(),
                user_info=user_info,
                group_info=None,
                template_info=None,
                format_info=format_info,
                additional_config={}
            )
            
            seg = Seg(type="text", data="[Bot Self Registration]")
            submit_seg = Seg(type="seglist", data=[seg])
            
            message_base = MessageBase(
                message_info=message_info,
                message_segment=submit_seg,
                raw_message="[Bot Self Registration]"
            )
            
            # 等待 MaiBot 客户端连接（最多等待 5 秒）
            for _ in range(10):
                if maibot_client.router and hasattr(maibot_client.router, '_targets'):
                    break
                await asyncio.sleep(0.5)
            
            # 发送注册消息
            try:
                await maibot_client.send_message(message_base)
                logger.info("✅ 机器人已注册到 MaiBot")
            except:
                logger.warning("⚠️ 机器人注册失败，但不影响正常使用")
        else:
            logger.warning(f"获取机器人信息失败: {data}")
    except Exception as e:
        logger.error(f"注册机器人失败: {e}")


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("MaiBot 飞书适配器启动中...")
    logger.info("=" * 50)
    
    # 验证配置
    if not global_config.feishu.app_id or not global_config.feishu.app_secret:
        logger.error("❌ 飞书配置不完整，请检查 config.toml")
        sys.exit(1)
    
    logger.info(f"📱 飞书应用 ID: {global_config.feishu.app_id}")
    logger.info(f"🔗 MaiBot 地址: ws://{global_config.maibot.host}:{global_config.maibot.port}/ws")
    logger.info(f"🌐 使用长连接模式接收飞书事件")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(async_main())
    except KeyboardInterrupt:
        logger.warning("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"程序异常: {e}")
    finally:
        loop.close()
        logger.info("✅ 适配器已关闭")


if __name__ == "__main__":
    main()
