#!/usr/bin/env python3
"""
独立的飞书文档知识库导入工具
将飞书 Wiki/云文档导出为 MaiBot LPMM 可用的格式
"""
import os
import requests
import json
from pathlib import Path


class FeishuWikiExporter:
    """飞书文档导出器"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        
    def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if data.get("code") == 0:
            self.access_token = data.get("tenant_access_token")
            print("✅ 成功获取 access token")
            return self.access_token
        else:
            raise Exception(f"获取 token 失败: {data}")
    
    def get_wiki_node_list(self, space_id: str) -> list:
        """获取 Wiki 空间的节点列表"""
        if not self.access_token:
            self.get_tenant_access_token()
        
        url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("code") == 0:
            nodes = data.get("data", {}).get("items", [])
            print(f"✅ 获取到 {len(nodes)} 个 Wiki 节点")
            return nodes
        else:
            print(f"❌ 获取 Wiki 节点失败: {data}")
            return []
    
    def get_doc_raw_content(self, doc_token: str) -> str:
        """获取新版文档原始内容（纯文本）"""
        if not self.access_token:
            self.get_tenant_access_token()
        
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("code") == 0:
            return data.get("data", {}).get("content", "")
        else:
            print(f"⚠️ 获取文档内容失败: {data.get('msg')}")
            return ""
    
    def export_wiki_to_file(self, space_id: str, output_dir: str):
        """导出 Wiki 内容到文件
        
        Args:
            space_id: Wiki 空间 ID
            output_dir: 输出目录（MaiBot 的 data/lpmm_raw_data）
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"feishu_wiki_{space_id}.txt")
        
        # 获取所有节点
        nodes = self.get_wiki_node_list(space_id)
        
        if not nodes:
            print("❌ 没有找到任何文档")
            return None
        
        # 导出到文件
        with open(output_file, "w", encoding="utf-8") as f:
            for i, node in enumerate(nodes, 1):
                title = node.get("title", "未命名")
                node_token = node.get("node_token", "")
                obj_type = node.get("obj_type", "")
                
                print(f"[{i}/{len(nodes)}] 正在导出: {title}")
                
                # 写入标题
                f.write(f"# {title}\n\n")
                
                # 获取内容
                try:
                    if obj_type == "docx":
                        content = self.get_doc_raw_content(node_token)
                    else:
                        print(f"  ⚠️ 跳过不支持的类型: {obj_type}")
                        continue
                    
                    if content:
                        f.write(content.strip())
                        f.write("\n\n" + "="*80 + "\n\n")
                except Exception as e:
                    print(f"  ❌ 导出失败: {e}")
        
        print(f"\n✅ 导出完成: {output_file}")
        return output_file


def main():
    """主函数"""
    print("=" * 80)
    print("飞书文档知识库导出工具")
    print("=" * 80)
    
    # 读取配置
    config_file = "feishu_wiki_config.json"
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            app_id = config.get("app_id", "")
            app_secret = config.get("app_secret", "")
    else:
        print("\n⚠️  未找到配置文件，请输入飞书应用信息：")
        app_id = input("App ID: ").strip()
        app_secret = input("App Secret: ").strip()
        
        # 保存配置
        save_config = input("\n是否保存配置到文件？(y/n): ").strip().lower()
        if save_config == 'y':
            with open(config_file, "w") as f:
                json.dump({"app_id": app_id, "app_secret": app_secret}, f)
            print(f"✅ 配置已保存到 {config_file}")
    
    if not app_id or not app_secret:
        print("❌ App ID 和 App Secret 不能为空")
        return
    
    # 输入 Wiki 空间 ID
    print("\n请输入飞书 Wiki 空间 ID：")
    print("（在 Wiki URL 中：https://xxx.feishu.cn/wiki/[space_id]）")
    space_id = input("Space ID: ").strip()
    
    if not space_id:
        print("❌ 空间 ID 不能为空")
        return
    
    # 输入输出目录
    print("\n请输入 MaiBot 的 lpmm_raw_data 目录路径：")
    print("（例如：/home/cloud/maimai/MaiBot/data/lpmm_raw_data）")
    output_dir = input("输出目录: ").strip()
    
    if not output_dir:
        output_dir = "../MaiBot/data/lpmm_raw_data"
        print(f"使用默认路径: {output_dir}")
    
    # 执行导出
    print("\n" + "=" * 80)
    print("开始导出...")
    print("=" * 80 + "\n")
    
    try:
        exporter = FeishuWikiExporter(app_id, app_secret)
        result = exporter.export_wiki_to_file(space_id, output_dir)
        
        if result:
            print("\n" + "=" * 80)
            print("✅ 导出成功！")
            print("=" * 80)
            print(f"\n输出文件: {result}")
            print("\n下一步：")
            print("1. 检查导出的文件内容")
            print("2. 在 MaiBot 目录运行数据处理：")
            print("   cd /path/to/MaiBot")
            print("   bash scripts/run_lpmm.sh")
            print("3. 重启 MaiBot")
            print("=" * 80)
    
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
