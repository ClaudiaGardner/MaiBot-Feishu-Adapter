"""飞书 API 客户端"""
import requests
import json
import time
from typing import Optional, Dict, Any
from src.logger import logger
from src.config import global_config
from requests_toolbelt import MultipartEncoder

class FeishuClient:
    """飞书 API 客户端 (Requests 版)"""
    
    def __init__(self):
        self.app_id = global_config.feishu.app_id
        self.app_secret = global_config.feishu.app_secret
        self._tenant_access_token = None
        self._token_expire_time = 0
        self.base_url = "https://open.feishu.cn/open-apis"
    
    def _get_tenant_access_token(self) -> str:
        """获取 tenant_access_token (带缓存)"""
        now = time.time()
        if self._tenant_access_token and now < self._token_expire_time:
            return self._tenant_access_token
        
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                self._tenant_access_token = data.get("tenant_access_token")
                # 提前 5 分钟过期
                self._token_expire_time = now + data.get("expire", 7200) - 300
                logger.info("✅ 成功获取 tenant_access_token")
                return self._tenant_access_token
            else:
                logger.error(f"❌ 获取 tenant_access_token 失败: {data}")
                return ""
        except Exception as e:
            logger.error(f"❌ 获取 tenant_access_token 异常: {e}")
            return ""

    def send_message(
        self,
        receive_id: str,
        receive_id_type: str,
        msg_type: str,
        content: str
    ) -> bool:
        """发送消息"""
        token = self._get_tenant_access_token()
        if not token:
            return False
            
        url = f"{self.base_url}/im/v1/messages"
        params = {"receive_id_type": receive_id_type}
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content
        }
        
        try:
            response = requests.post(url, params=params, headers=headers, json=payload, timeout=10)
            
            # 记录 logid 方便排查
            if "X-Tt-Logid" in response.headers:
                logger.debug(f"Feishu Request LogID: {response.headers['X-Tt-Logid']}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                logger.info(f"✅ 消息发送成功: {receive_id} (msg_id: {data.get('data', {}).get('message_id')})")
                return True
            else:
                logger.error(f"❌ 消息发送失败: {data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送消息异常: {e}")
            return False

    def reply_message(
        self,
        message_id: str,
        msg_type: str,
        content: str
    ) -> bool:
        """回复消息"""
        token = self._get_tenant_access_token()
        if not token:
            return False
            
        url = f"{self.base_url}/im/v1/messages/{message_id}/reply"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "msg_type": msg_type,
            "content": content
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if "X-Tt-Logid" in response.headers:
                logger.debug(f"Feishu Reply LogID: {response.headers['X-Tt-Logid']}")
                
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 0:
                logger.info(f"✅ 回复消息成功: {message_id}")
                return True
            else:
                logger.error(f"❌ 回复消息失败: {data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 回复消息异常: {e}")
            return False

    def get_user_info(self, open_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        token = self._get_tenant_access_token()
        if not token:
            return None
            
        url = f"{self.base_url}/contact/v3/users/{open_id}"
        params = {
            "user_id_type": "open_id"
        }
        headers = {
            "Authorization": f"Bearer {token}",
             "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                 logger.warning(f"获取用户信息 HTTP 状态码异常: {response.status_code}")
            
            data = response.json()
            
            if data.get("code") == 0:
                return data.get("data", {}).get("user", {})
            else:
                logger.warning(f"获取用户信息失败: {data}")
                return None
        except Exception as e:
            logger.error(f"获取用户信息异常: {e}")
            return None
    # 🟢 [新增] 上传图片到飞书
    def upload_image(self, image_data: bytes) -> Optional[str]:
        """上传图片并获取 image_key"""
        token = self._get_tenant_access_token()
        if not token: return None

        url = f"{self.base_url}/im/v1/images"
        headers = {"Authorization": f"Bearer {token}"}
        
        # 构造 multipart/form-data
        # image_type 必须是 message
        files = {
            'image_type': (None, 'message'),
            'image': ('image.jpg', image_data)
        }
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=20)
            data = response.json()
            
            if data.get("code") == 0:
                image_key = data.get("data", {}).get("image_key")
                logger.info(f"✅ 图片上传成功, key: {image_key}")
                return image_key
            else:
                logger.error(f"❌ 图片上传失败: {data}")
                return None
        except Exception as e:
            logger.error(f"❌ 上传图片异常: {e}")
            return None

    # 🟢 [新增] 发送图片消息
    def send_image_message(self, receive_id: str, receive_id_type: str, image_key: str) -> bool:
        """发送图片消息"""
        content = json.dumps({"image_key": image_key})
        return self.send_message(receive_id, receive_id_type, "image", content)

# 全局飞书客户端实例
feishu_client = FeishuClient()
