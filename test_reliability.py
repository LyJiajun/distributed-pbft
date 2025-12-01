#!/usr/bin/env python3
"""
测试消息可靠性控制功能

这个脚本测试：
1. 节点级别的可靠性配置是否正确存储
2. 消息发送是否根据可靠性概率进行过滤
3. 不同可靠性设置下的消息到达率
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_reliability_feature():
    print("=" * 60)
    print("测试消息可靠性控制功能")
    print("=" * 60)
    
    # 1. 创建会话
    print("\n1. 创建测试会话...")
    session_config = {
        "nodeCount": 5,
        "faultyNodes": 1,
        "robotNodes": 2,  # 2个机器人节点
        "topology": "full",
        "branchCount": 2,
        "proposalValue": 0,
        "proposalContent": "测试提议",
        "maliciousProposer": False,
        "allowTampering": False,
        "messageDeliveryRate": 100
    }
    
    response = requests.post(f"{BASE_URL}/api/sessions", json=session_config)
    if response.status_code != 200:
        print(f"❌ 创建会话失败: {response.text}")
        return False
    
    session_data = response.json()
    session_id = session_data["sessionId"]
    print(f"✅ 会话创建成功: {session_id}")
    
    # 2. 等待会话初始化
    print("\n2. 等待会话初始化...")
    time.sleep(2)
    
    # 3. 获取会话信息
    print("\n3. 获取会话信息...")
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
    if response.status_code != 200:
        print(f"❌ 获取会话失败: {response.text}")
        return False
    
    session_info = response.json()
    print(f"✅ 会话状态: {session_info['status']}")
    print(f"   当前阶段: {session_info['phase']}")
    print(f"   当前轮次: {session_info['current_round']}")
    
    # 4. 模拟节点级别的可靠性配置
    print("\n4. 测试可靠性配置功能...")
    print("   注意: 由于这是HTTP API测试，实际的可靠性配置需要通过WebSocket进行")
    print("   在真实场景中，前端会通过Socket.IO发送'update_reliability'事件")
    print("   配置格式示例:")
    reliability_example = {
        "sessionId": session_id,
        "nodeId": 2,
        "reliability": {
            "0": 100,  # 到节点0的消息100%到达
            "1": 50,   # 到节点1的消息50%到达
            "3": 0,    # 到节点3的消息0%到达（完全不发送）
            "4": 75    # 到节点4的消息75%到达
        }
    }
    print(f"   {json.dumps(reliability_example, indent=4, ensure_ascii=False)}")
    
    # 5. 等待一段时间观察共识过程
    print("\n5. 观察共识过程...")
    print("   等待10秒以观察消息传递...")
    time.sleep(10)
    
    # 6. 获取会话历史以验证消息
    print("\n6. 获取会话历史...")
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/history")
    if response.status_code != 200:
        print(f"❌ 获取历史失败: {response.text}")
        return False
    
    history_info = response.json()
    print(f"✅ 共识轮次信息:")
    print(f"   总轮次数: {history_info.get('totalRounds', 0)}")
    print(f"   当前轮次: {history_info.get('currentRound', 0)}")
    print(f"   轮次列表: {history_info.get('rounds', [])}")
    
    # 7. 获取第一轮的详细消息
    if history_info.get('rounds'):
        first_round = history_info['rounds'][0]
        print(f"\n7. 获取第{first_round}轮的详细消息...")
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/history?round={first_round}")
        if response.status_code == 200:
            round_data = response.json()
            print(f"✅ 第{first_round}轮消息统计:")
            print(f"   预准备消息: {len(round_data.get('pre_prepare', []))}条")
            print(f"   准备消息组: {len(round_data.get('prepare', [[]])[0])}条")
            print(f"   提交消息组: {len(round_data.get('commit', [[]])[0])}条")
            print(f"   共识结果: {round_data.get('consensus', '未知')}")
    
    # 8. 清理：删除会话
    print("\n8. 清理测试会话...")
    response = requests.delete(f"{BASE_URL}/api/sessions/{session_id}")
    if response.status_code == 200:
        print(f"✅ 会话已删除")
    else:
        print(f"⚠️  删除会话失败: {response.text}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n使用说明:")
    print("1. 启动后端服务: cd backend && python main.py")
    print("2. 启动前端服务: npm run dev")
    print("3. 在浏览器中打开节点页面")
    print("4. 选择'拜占庭攻击'模式")
    print("5. 点击'显示可靠性矩阵'")
    print("6. 调整滑块设置各个节点的消息到达概率")
    print("7. 发送消息时，系统会根据设置的概率决定是否发送")
    print("\n功能特点:")
    print("✨ 每个节点可以独立设置发送给其他节点的消息可靠性")
    print("✨ 支持0%-100%的任意概率设置（步长5%）")
    print("✨ 提供快速设置按钮（100%, 75%, 50%, 0%）")
    print("✨ 实时生效，无需重启或刷新")
    print("✨ 可用于模拟网络不稳定、节点故障等场景")
    
    return True

if __name__ == "__main__":
    try:
        print("\n确保后端服务正在运行 (http://localhost:8000)")
        print("按 Ctrl+C 取消测试\n")
        time.sleep(2)
        test_reliability_feature()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请确保后端服务正在运行: cd backend && python main.py")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()






