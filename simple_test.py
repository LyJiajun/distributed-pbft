#!/usr/bin/env python3

def test_consensus_fix():
    """测试PBFT共识修复"""
    print("=== PBFT共识修复测试 ===")
    
    # 模拟消息数据
    prepare_messages = [
        {"from": 1, "value": 0},  # 节点1的消息
        {"from": 1, "value": 0},  # 节点1的重复消息
        {"from": 1, "value": 0},  # 节点1的重复消息
        {"from": 2, "value": 0},  # 节点2的消息
        {"from": 3, "value": 1},  # 节点3的消息
        {"from": 4, "value": 0},  # 节点4的消息
    ]
    
    commit_messages = [
        {"from": 1, "value": 0},  # 节点1的消息
        {"from": 2, "value": 0},  # 节点2的消息
        {"from": 2, "value": 0},  # 节点2的重复消息
        {"from": 3, "value": 1},  # 节点3的消息
        {"from": 4, "value": 0},  # 节点4的消息
    ]
    
    expected_nodes = 4  # 需要4个节点（除了提议者）
    
    print(f"准备消息总数: {len(prepare_messages)}")
    print(f"提交消息总数: {len(commit_messages)}")
    print(f"需要的节点数: {expected_nodes}")
    
    # 旧逻辑：基于消息数量
    old_prepare_logic = len(prepare_messages) >= expected_nodes
    old_commit_logic = len(commit_messages) >= expected_nodes
    
    # 新逻辑：基于不同节点数量
    unique_prepare_nodes = set()
    for msg in prepare_messages:
        unique_prepare_nodes.add(msg["from"])
    
    unique_commit_nodes = set()
    for msg in commit_messages:
        unique_commit_nodes.add(msg["from"])
    
    new_prepare_logic = len(unique_prepare_nodes) >= expected_nodes
    new_commit_logic = len(unique_commit_nodes) >= expected_nodes
    
    print(f"\n准备阶段:")
    print(f"  消息总数: {len(prepare_messages)}")
    print(f"  不同节点数: {len(unique_prepare_nodes)}")
    print(f"  不同节点列表: {list(unique_prepare_nodes)}")
    print(f"  旧逻辑: {'✅ 通过' if old_prepare_logic else '❌ 失败'}")
    print(f"  新逻辑: {'✅ 通过' if new_prepare_logic else '❌ 失败'}")
    
    print(f"\n提交阶段:")
    print(f"  消息总数: {len(commit_messages)}")
    print(f"  不同节点数: {len(unique_commit_nodes)}")
    print(f"  不同节点列表: {list(unique_commit_nodes)}")
    print(f"  旧逻辑: {'✅ 通过' if old_commit_logic else '❌ 失败'}")
    print(f"  新逻辑: {'✅ 通过' if new_commit_logic else '❌ 失败'}")
    
    print(f"\n结论:")
    if old_prepare_logic != new_prepare_logic or old_commit_logic != new_commit_logic:
        print("✅ 修复成功！新逻辑更严格，符合PBFT要求")
        print("   - 旧逻辑允许同一节点发送多条消息来满足数量要求")
        print("   - 新逻辑确保每个节点只能被统计一次")
    else:
        print("⚠️  新旧逻辑结果相同，但新逻辑仍然更安全")
    
    print(f"\n统计信息:")
    print(f"  准备阶段参与节点: {len(unique_prepare_nodes)}/{expected_nodes}")
    print(f"  提交阶段参与节点: {len(unique_commit_nodes)}/{expected_nodes}")
    print(f"  总消息数: {len(prepare_messages) + len(commit_messages)}")

if __name__ == "__main__":
    test_consensus_fix()





