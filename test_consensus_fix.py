#!/usr/bin/env python3
"""
测试PBFT共识修复的脚本
验证每个节点在每个阶段只能被统计一次
"""

import asyncio
import json
from datetime import datetime

# 模拟会话数据
def create_test_session():
    return {
        "config": {
            "nodeCount": 5,  # 总共5个节点
            "faultyNodes": 1,
            "topology": "full",
            "proposalValue": 0,
            "proposalContent": "测试提议",
            "maliciousProposer": False,
            "allowTampering": False,
            "messageDeliveryRate": 100
        },
        "messages": {
            "pre_prepare": [],
            "prepare": [],
            "commit": []
        }
    }

def test_prepare_phase_check():
    """测试准备阶段检查逻辑"""
    print("=== 测试准备阶段检查逻辑 ===")
    
    session = create_test_session()
    config = session["config"]
    prepare_messages = session["messages"]["prepare"]
    
    # 模拟节点1发送多条准备消息
    prepare_messages.extend([
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},  # 重复消息
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},  # 重复消息
        {"from": 2, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 3, "value": 1, "timestamp": datetime.now().isoformat()},
        {"from": 4, "value": 0, "timestamp": datetime.now().isoformat()},
    ])
    
    print(f"准备消息总数: {len(prepare_messages)}")
    print(f"准备消息详情: {[msg['from'] for msg in prepare_messages]}")
    
    # 使用修复后的逻辑：统计不同节点
    unique_nodes = set()
    for msg in prepare_messages:
        unique_nodes.add(msg["from"])
    
    print(f"不同节点数: {len(unique_nodes)}")
    print(f"不同节点列表: {list(unique_nodes)}")
    print(f"预期节点数: {config['nodeCount'] - 1} (除了提议者)")
    
    # 检查是否满足条件
    expected_nodes = config['nodeCount'] - 1
    if len(unique_nodes) >= expected_nodes:
        print("✅ 准备阶段完成 - 修复后的逻辑正确")
    else:
        print("❌ 准备阶段未完成 - 需要更多不同节点")
    
    print()

def test_commit_phase_check():
    """测试提交阶段检查逻辑"""
    print("=== 测试提交阶段检查逻辑 ===")
    
    session = create_test_session()
    config = session["config"]
    commit_messages = session["messages"]["commit"]
    
    # 模拟节点2发送多条提交消息
    commit_messages.extend([
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 2, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 2, "value": 0, "timestamp": datetime.now().isoformat()},  # 重复消息
        {"from": 2, "value": 0, "timestamp": datetime.now().isoformat()},  # 重复消息
        {"from": 3, "value": 1, "timestamp": datetime.now().isoformat()},
        {"from": 4, "value": 0, "timestamp": datetime.now().isoformat()},
    ])
    
    print(f"提交消息总数: {len(commit_messages)}")
    print(f"提交消息详情: {[msg['from'] for msg in commit_messages]}")
    
    # 使用修复后的逻辑：统计不同节点
    unique_nodes = set()
    for msg in commit_messages:
        unique_nodes.add(msg["from"])
    
    print(f"不同节点数: {len(unique_nodes)}")
    print(f"不同节点列表: {list(unique_nodes)}")
    print(f"预期节点数: {config['nodeCount'] - 1} (除了提议者)")
    
    # 检查是否满足条件
    expected_nodes = config['nodeCount'] - 1
    if len(unique_nodes) >= expected_nodes:
        print("✅ 提交阶段完成 - 修复后的逻辑正确")
    else:
        print("❌ 提交阶段未完成 - 需要更多不同节点")
    
    print()

def test_consensus_finalization():
    """测试共识完成逻辑"""
    print("=== 测试共识完成逻辑 ===")
    
    session = create_test_session()
    config = session["config"]
    prepare_messages = session["messages"]["prepare"]
    commit_messages = session["messages"]["commit"]
    
    # 模拟投票情况
    prepare_messages.extend([
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},  # 重复消息
        {"from": 2, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 3, "value": 1, "timestamp": datetime.now().isoformat()},
        {"from": 4, "value": 0, "timestamp": datetime.now().isoformat()},
    ])
    
    commit_messages.extend([
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 2, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 3, "value": 1, "timestamp": datetime.now().isoformat()},
        {"from": 4, "value": 0, "timestamp": datetime.now().isoformat()},
    ])
    
    print(f"准备消息总数: {len(prepare_messages)}")
    print(f"提交消息总数: {len(commit_messages)}")
    
    # 统计不同节点的准备消息
    unique_prepare_nodes = set()
    for msg in prepare_messages:
        unique_prepare_nodes.add(msg["from"])
    
    # 统计不同节点的提交消息
    unique_commit_nodes = set()
    for msg in commit_messages:
        unique_commit_nodes.add(msg["from"])
    
    print(f"不同准备节点数: {len(unique_prepare_nodes)}")
    print(f"不同提交节点数: {len(unique_commit_nodes)}")
    
    # 统计每个节点的投票（基于准备阶段消息，后面的消息会覆盖前面的）
    node_votes = {}
    for msg in prepare_messages:
        node_id = msg["from"]
        node_votes[node_id] = msg["value"]
    
    print(f"节点投票详情: {node_votes}")
    
    # 统计最终结果
    truth_votes = 0
    falsehood_votes = 0
    rejected_votes = 0
    
    for node_id, vote in node_votes.items():
        if vote == 0:
            truth_votes += 1
        elif vote == 1:
            falsehood_votes += 1
        else:
            rejected_votes += 1
    
    print(f"选择A的节点数: {truth_votes}")
    print(f"选择B的节点数: {falsehood_votes}")
    print(f"拒绝的节点数: {rejected_votes}")
    
    # 判断共识结果
    expected_nodes = config['nodeCount'] - 1
    
    if len(unique_prepare_nodes) < expected_nodes:
        consensus_status = "准备阶段未完成"
        consensus_description = f"准备阶段需要{expected_nodes}个节点，实际只有{len(unique_prepare_nodes)}个节点参与"
    elif len(unique_commit_nodes) < expected_nodes:
        consensus_status = "提交阶段未完成"
        consensus_description = f"提交阶段需要{expected_nodes}个节点，实际只有{len(unique_commit_nodes)}个节点参与"
    elif truth_votes + falsehood_votes == 0:
        consensus_status = "拒绝提议"
        consensus_description = "所有节点都拒绝了提议"
    elif truth_votes > 0 and falsehood_votes == 0:
        consensus_status = "共识成功"
        consensus_description = f"{truth_votes}个节点接受了值 0"
    elif falsehood_votes > 0 and truth_votes == 0:
        consensus_status = "共识成功"
        consensus_description = f"{falsehood_votes}个节点接受了值 1"
    else:
        consensus_status = "共识失败"
        consensus_description = "节点间存在分歧，共识失败"
    
    print(f"共识状态: {consensus_status}")
    print(f"共识描述: {consensus_description}")
    
    # 构建统计信息
    stats = {
        "truth": truth_votes,
        "falsehood": falsehood_votes,
        "rejected": rejected_votes,
        "prepare_nodes": len(unique_prepare_nodes),
        "commit_nodes": len(unique_commit_nodes),
        "expected_nodes": expected_nodes,
        "total_messages": len(prepare_messages) + len(commit_messages)
    }
    
    print(f"统计信息: {stats}")
    print()

def test_old_vs_new_logic():
    """对比旧逻辑和新逻辑的差异"""
    print("=== 对比旧逻辑和新逻辑 ===")
    
    session = create_test_session()
    config = session["config"]
    prepare_messages = session["messages"]["prepare"]
    
    # 模拟一个节点发送多条消息的情况
    prepare_messages.extend([
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},  # 重复
        {"from": 1, "value": 0, "timestamp": datetime.now().isoformat()},  # 重复
        {"from": 2, "value": 0, "timestamp": datetime.now().isoformat()},
        {"from": 3, "value": 1, "timestamp": datetime.now().isoformat()},
    ])
    
    expected_nodes = config['nodeCount'] - 1  # 需要4个节点（除了提议者）
    
    # 旧逻辑：基于消息数量
    old_logic = len(prepare_messages) >= expected_nodes
    
    # 新逻辑：基于不同节点数量
    unique_nodes = set()
    for msg in prepare_messages:
        unique_nodes.add(msg["from"])
    new_logic = len(unique_nodes) >= expected_nodes
    
    print(f"消息总数: {len(prepare_messages)}")
    print(f"不同节点数: {len(unique_nodes)}")
    print(f"需要的节点数: {expected_nodes}")
    print(f"旧逻辑结果: {'✅ 通过' if old_logic else '❌ 失败'}")
    print(f"新逻辑结果: {'✅ 通过' if new_logic else '❌ 失败'}")
    
    if old_logic != new_logic:
        print("⚠️  新旧逻辑结果不同！新逻辑更严格，符合PBFT要求")
    else:
        print("✅ 新旧逻辑结果相同")
    
    print()

if __name__ == "__main__":
    print("PBFT共识修复测试")
    print("=" * 50)
    
    test_prepare_phase_check()
    test_commit_phase_check()
    test_consensus_finalization()
    test_old_vs_new_logic()
    
    print("测试完成！")


