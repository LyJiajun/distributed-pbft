#!/usr/bin/env python3
"""
测试后端API是否正常工作
"""

import requests
import json

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🔍 测试后端API...")
    
    # 测试1: 检查服务是否运行
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
        else:
            print(f"❌ 后端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端在 http://localhost:8000 运行")
        return False
    
    # 测试2: 创建会话
    try:
        session_data = {
            "nodeCount": 5,
            "faultyNodes": 1,
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
            
            # 测试3: 获取会话信息
            response = requests.get(f"{base_url}/api/sessions/{session_id}")
            if response.status_code == 200:
                print("✅ 成功获取会话信息")
            else:
                print(f"❌ 获取会话信息失败: {response.status_code}")
                return False
                
        else:
            print(f"❌ 创建会话失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False
    
    print("🎉 所有测试通过！后端API工作正常")
    return True

if __name__ == "__main__":
    test_backend() 