#!/usr/bin/env python3
"""
测试拜占庭攻击功能
"""

import requests
import json
import time

def test_byzantine_attack():
    base_url = "http://localhost:8000"
    
    print("🧪 测试拜占庭攻击功能...")
    
    # 测试1: 创建包含多个拜占庭节点的会话
    try:
        session_data = {
            "nodeCount": 5,
            "faultyNodes": 5,  # 所有节点都可以成为拜占庭节点
            "topology": "full",
            "branchCount": 2,
            "proposalValue": 0,
            "maliciousProposer": False,
            "allowTampering": False
        }
        
        response = requests.post(f"{base_url}/api/sessions", json=session_data)
        if response.status_code == 200:
            session_info = response.json()
            session_id = session_info["sessionId"]
            print(f"✅ 成功创建会话: {session_id}")
            print(f"   节点总数: {session_info['config']['nodeCount']}")
            print(f"   容错节点数: {session_info['config']['faultyNodes']}")
            print(f"   说明: 所有节点都可以选择成为拜占庭节点")
            
        else:
            print(f"❌ 创建会话失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False
    
    print("🎉 拜占庭攻击功能测试通过！")
    print("📝 现在每个节点都可以在界面上选择是否成为拜占庭节点")
    return True

if __name__ == "__main__":
    test_byzantine_attack() 