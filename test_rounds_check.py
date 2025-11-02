#!/usr/bin/env python3
"""
测试脚本：检查多轮次和消息重复问题
"""
import requests
import sys

def check_session_rounds(session_id):
    """检查会话的轮次数据"""
    base_url = "http://localhost:8000"
    
    print(f"\n{'='*60}")
    print(f"检查会话: {session_id}")
    print(f"{'='*60}\n")
    
    try:
        # 1. 获取轮次列表
        print("📊 获取轮次列表...")
        response = requests.get(f"{base_url}/api/sessions/{session_id}/history")
        
        if response.status_code != 200:
            print(f"❌ 错误: {response.status_code} - {response.text}")
            return
        
        rounds_data = response.json()
        rounds = rounds_data.get('rounds', [])
        current_round = rounds_data.get('currentRound')
        
        print(f"✅ 轮次列表: {rounds}")
        print(f"   当前轮次: {current_round}")
        print(f"   总轮次数: {len(rounds)}\n")
        
        if len(rounds) == 0:
            print("⚠️  没有找到任何轮次数据")
            print("   可能原因:")
            print("   1. 会话还没有完成任何轮次")
            print("   2. 消息没有包含 round 字段（需要创建新会话）")
            return
        
        if len(rounds) == 1:
            print("⚠️  只有1轮数据")
            print("   建议: 等待更多轮次完成（每轮约10秒间隔）\n")
        
        # 2. 检查每一轮的消息
        for round_num in rounds:
            print(f"\n{'─'*60}")
            print(f"📋 检查第 {round_num} 轮")
            print(f"{'─'*60}")
            
            response = requests.get(f"{base_url}/api/sessions/{session_id}/history?round={round_num}")
            
            if response.status_code != 200:
                print(f"❌ 错误: {response.status_code}")
                continue
            
            round_data = response.json()
            
            pre_prepare = round_data.get('pre_prepare', [])
            prepare = round_data.get('prepare', [[]])[0]
            commit = round_data.get('commit', [[]])[0]
            consensus = round_data.get('consensus', '未知')
            
            print(f"  Pre-Prepare消息数: {len(pre_prepare)}")
            print(f"  Prepare消息数: {len(prepare)}")
            print(f"  Commit消息数: {len(commit)}")
            print(f"  共识结果: {consensus}")
            
            # 3. 检查Prepare消息是否有重复
            if len(prepare) > 0:
                print(f"\n  🔍 检查Prepare消息重复...")
                
                # 统计每个节点发送的消息
                node_messages = {}
                for msg in prepare:
                    src = msg.get('src')
                    dst = msg.get('dst')
                    value = msg.get('value')
                    
                    key = (src, dst, value)
                    if key in node_messages:
                        node_messages[key] += 1
                    else:
                        node_messages[key] = 1
                
                # 检查重复
                duplicates = [(k, v) for k, v in node_messages.items() if v > 1]
                
                if duplicates:
                    print(f"  ⚠️  发现重复消息:")
                    for (src, dst, value), count in duplicates:
                        print(f"     节点{src} -> 节点{dst} (值:{value}): 出现{count}次")
                else:
                    print(f"  ✅ 没有重复消息")
            
            # 4. 检查Commit消息是否有重复
            if len(commit) > 0:
                print(f"\n  🔍 检查Commit消息重复...")
                
                node_messages = {}
                for msg in commit:
                    src = msg.get('src')
                    dst = msg.get('dst')
                    value = msg.get('value')
                    
                    key = (src, dst, value)
                    if key in node_messages:
                        node_messages[key] += 1
                    else:
                        node_messages[key] = 1
                
                duplicates = [(k, v) for k, v in node_messages.items() if v > 1]
                
                if duplicates:
                    print(f"  ⚠️  发现重复消息:")
                    for (src, dst, value), count in duplicates:
                        print(f"     节点{src} -> 节点{dst} (值:{value}): 出现{count}次")
                else:
                    print(f"  ✅ 没有重复消息")
        
        # 总结
        print(f"\n{'='*60}")
        print("📌 总结")
        print(f"{'='*60}")
        
        if len(rounds) > 1:
            print(f"✅ 多轮次查看: 正常 (共{len(rounds)}轮)")
        else:
            print(f"⚠️  多轮次查看: 需要更多轮次")
        
        print(f"\n💡 建议:")
        if len(rounds) == 1:
            print("  - 等待更多轮次完成后再测试")
            print("  - 每轮间隔约10秒")
        print("  - 在浏览器中点击'动画演示共识过程'按钮")
        print("  - 查看是否能切换不同轮次")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        print("   请确保后端正在运行: http://localhost:8000")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_rounds_check.py <session_id>")
        print("\n如何获取session_id:")
        print("1. 在浏览器中创建会话")
        print("2. 从URL或二维码信息中复制会话ID")
        print("3. 运行: python test_rounds_check.py <session_id>")
        sys.exit(1)
    
    session_id = sys.argv[1]
    check_session_rounds(session_id)

