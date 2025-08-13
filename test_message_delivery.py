#!/usr/bin/env python3
"""
测试消息传达概率功能
"""

import requests
import json
import time

def test_message_delivery_rate():
    """测试消息传达概率功能"""
    
    # 后端服务地址
    base_url = "http://localhost:8000"
    
    print("🧪 测试消息传达概率功能")
    print("=" * 50)
    
    # 1. 创建会话，设置消息传达概率为80%
    print("1. 创建会话，设置消息传达概率为80%")
    session_config = {
        "nodeCount": 3,
        "faultyNodes": 0,
        "topology": "full",
        "proposalValue": 0,
        "maliciousProposer": False,
        "allowTampering": False,
        "messageDeliveryRate": 80
    }
    
    try:
        response = requests.post(f"{base_url}/api/sessions", json=session_config)
        response.raise_for_status()
        session_info = response.json()
        session_id = session_info["sessionId"]
        print(f"✅ 会话创建成功: {session_id}")
        print(f"   配置: {session_info['config']}")
        
        # 验证配置中是否包含messageDeliveryRate
        if "messageDeliveryRate" in session_info["config"]:
            print(f"✅ 消息传达概率配置正确: {session_info['config']['messageDeliveryRate']}%")
        else:
            print("❌ 消息传达概率配置缺失")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 创建会话失败: {e}")
        return False
    
    # 2. 获取会话信息
    print("\n2. 获取会话信息")
    try:
        response = requests.get(f"{base_url}/api/sessions/{session_id}")
        response.raise_for_status()
        session = response.json()
        print(f"✅ 会话信息获取成功")
        print(f"   配置: {session['config']}")
        
        # 验证配置中是否包含messageDeliveryRate
        if "messageDeliveryRate" in session["config"]:
            print(f"✅ 消息传达概率配置正确: {session['config']['messageDeliveryRate']}%")
        else:
            print("❌ 消息传达概率配置缺失")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取会话信息失败: {e}")
        return False
    
    print("\n✅ 消息传达概率功能测试通过！")
    return True

if __name__ == "__main__":
    test_message_delivery_rate()
