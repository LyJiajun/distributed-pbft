#!/usr/bin/env python3
"""
测试提议内容功能
"""

import requests
import json
import time

def test_proposal_content():
    """测试提议内容功能"""
    
    # 后端服务地址
    base_url = "http://localhost:8000"
    
    print("🧪 测试提议内容功能")
    print("=" * 50)
    
    # 1. 创建会话，设置提议内容
    print("1. 创建会话，设置提议内容")
    session_config = {
        "nodeCount": 3,
        "faultyNodes": 0,
        "topology": "full",
        "proposalValue": 0,
        "proposalContent": "选择方案a",  # 使用您输入的内容
        "maliciousProposer": False,
        "allowTampering": False,
        "messageDeliveryRate": 100
    }
    
    print(f"发送的配置: {session_config}")
    
    try:
        response = requests.post(f"{base_url}/api/sessions", json=session_config)
        response.raise_for_status()
        session_info = response.json()
        session_id = session_info["sessionId"]
        print(f"✅ 会话创建成功: {session_id}")
        print(f"   返回的配置: {session_info['config']}")
        print(f"   提议内容: '{session_info['config']['proposalContent']}'")
        
        # 验证配置中是否包含proposalContent
        if "proposalContent" in session_info["config"]:
            proposal_content = session_info["config"]["proposalContent"]
            print(f"✅ 提议内容配置正确: '{proposal_content}'")
            print(f"   内容长度: {len(proposal_content)}")
            print(f"   是否为空: {proposal_content == ''}")
            print(f"   去除空格后: '{proposal_content.strip()}'")
        else:
            print("❌ 提议内容配置缺失")
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
        print(f"   提议内容: '{session['config']['proposalContent']}'")
        
        # 验证配置中是否包含proposalContent
        if "proposalContent" in session["config"]:
            proposal_content = session["config"]["proposalContent"]
            print(f"✅ 提议内容配置正确: '{proposal_content}'")
            print(f"   内容长度: {len(proposal_content)}")
            print(f"   是否为空: {proposal_content == ''}")
            print(f"   去除空格后: '{proposal_content.strip()}'")
        else:
            print("❌ 提议内容配置缺失")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取会话信息失败: {e}")
        return False
    
    print("\n✅ 提议内容功能测试完成！")
    print("请检查后端控制台日志，确认提议内容是否正确传递。")
    return True

if __name__ == "__main__":
    test_proposal_content()
