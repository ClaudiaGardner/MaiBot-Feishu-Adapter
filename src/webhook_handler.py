"""Webhook 事件处理器"""
import json
import hashlib
import base64
from flask import Blueprint, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from src.logger import logger
from src.config import global_config
from src.message_converter import process_feishu_message

webhook_bp = Blueprint("webhook", __name__, url_prefix="/feishu")


def verify_signature(timestamp: str, nonce: str, encrypt: str, signature: str) -> bool:
    """验证请求签名"""
    token = global_config.feishu.verification_token
    if not token:
        return True  # 如果没有配置 token，跳过验证
    
    # 拼接字符串
    sign_str = f"{timestamp}{nonce}{encrypt}{token}"
    
    # 计算签名
    calculated_signature = hashlib.sha256(sign_str.encode()).hexdigest()
    
    return calculated_signature == signature


def decrypt_content(encrypt_data: str) -> dict:
    """解密加密内容"""
    encrypt_key = global_config.feishu.encrypt_key
    if not encrypt_key:
        raise ValueError("未配置加密密钥")
    
    # Base64 解码
    cipher_text = base64.b64decode(encrypt_data)
    
    # AES 解密
    cipher = AES.new(encrypt_key.encode(), AES.MODE_CBC, cipher_text[:16])
    decrypted = unpad(cipher.decrypt(cipher_text[16:]), AES.block_size)
    
    # 解析 JSON
    return json.loads(decrypted.decode())


@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    """飞书事件回调"""
    try:
        data = request.json
        
        # 1. 验证 URL（首次配置时）
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            logger.info("✅ URL 验证成功")
            return jsonify({"challenge": challenge})
        
        # 2. 验证签名
        headers = request.headers
        timestamp = headers.get("X-Lark-Request-Timestamp", "")
        nonce = headers.get("X-Lark-Request-Nonce", "")
        signature = headers.get("X-Lark-Signature", "")
        
        # 如果有加密
        encrypt_data = data.get("encrypt")
        if encrypt_data:
            if not verify_signature(timestamp, nonce, encrypt_data, signature):
                logger.warning("❌ 签名验证失败")
                return jsonify({"error": "Invalid signature"}), 401
            
            # 解密内容
            data = decrypt_content(encrypt_data)
        
        # 3. 处理事件
        event_type = data.get("header", {}).get("event_type")
        
        if event_type == "im.message.receive_v1":
            # 接收消息事件
            event = data.get("event", {})
            process_feishu_message(event)
            return jsonify({"code": 0})
        
        logger.debug(f"未处理的事件类型: {event_type}")
        return jsonify({"code": 0})
        
    except Exception as e:
        logger.error(f"处理 Webhook 异常: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@webhook_bp.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "MaiBot-Feishu-Adapter"
    })
