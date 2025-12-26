#!/usr/bin/env python3
"""
诊断脚本：详细追踪PBFT共识流程
用于检查点对点独立链路模型的实现是否正确
"""

import random
from typing import Dict, List, Set

def simulate_one_round(n: int, p: float, seed: int = None):
    """
    模拟一轮PBFT共识（点对点独立链路模型）
    
    参数:
        n: 节点总数
        p: 每条链路的成功概率
        seed: 随机种子（用于复现）
    
    返回:
        success: 是否共识成功
        details: 详细信息字典
    """
    if seed is not None:
        random.seed(seed)
    
    f = (n - 1) // 3
    # 论文式(6)：单节点在 prepare/commit 阶段需要“至少收到 2f 条来自其他节点的成功消息”
    k_required = 2 * f
    Nc_required = n - f  # 口径A：共识成功要求 commit 节点数 ≥ N-f
    
    nodes = list(range(n))
    primary = 0
    
    print("=" * 80)
    print(f"🔬 模拟一轮PBFT共识（点对点独立链路模型）")
    print("=" * 80)
    print(f"参数: n={n}, f={f}, k_required(2f)={k_required}, Nc_required={Nc_required}, p={p}")
    print(f"节点: {nodes}")
    print(f"主节点: {primary}")
    print()
    
    # ========== 阶段1: Pre-prepare ==========
    print("📍 阶段1: Pre-prepare")
    print("-" * 80)
    
    received_pre_prepare = {node: False for node in nodes}
    received_pre_prepare[primary] = True  # 主节点自己知道pre-prepare
    
    print(f"主节点{primary}向其他节点发送pre-prepare:")
    for target in nodes:
        if target == primary:
            continue
        
        success = random.random() < p
        if success:
            received_pre_prepare[target] = True
            print(f"  ✅ {primary}→{target}: 成功")
        else:
            print(f"  ❌ {primary}→{target}: 失败")
    
    V_pp = [node for node, received in received_pre_prepare.items() if received]
    print(f"\n收到pre-prepare的节点集合 V_pp = {V_pp} (共{len(V_pp)}个)")
    
    # 口径A：要最终达到 N_c ≥ N-f，则必有 N_pp ≥ N-f
    if len(V_pp) < Nc_required:
        print(f"❌ V_pp={len(V_pp)} < Nc_required={Nc_required}，无法继续，本轮失败")
        return False, {"phase": "pre-prepare", "V_pp": len(V_pp)}
    
    # ========== 阶段2: Prepare ==========
    print("\n📍 阶段2: Prepare")
    print("-" * 80)
    
    # Prepare：对齐论文特例化（与我们 A 理论闭式一致）
    # - 主节点不发送 prepare
    # - 副本之间互发 prepare
    # - 统计“来自其他副本”的prepare数（不计自己）
    received_prepare_count = {node: 0 for node in nodes}
    
    replicas_in_vpp = [node for node in V_pp if node != primary]
    for sender in replicas_in_vpp:
        print(f"节点{sender}发送prepare:")
        for target in nodes:
            if target == sender:
                continue
            
            # 关键修复：只有target也在V_pp中，才会接收这条prepare
            if target not in V_pp:
                print(f"  ⏭️  {sender}→{target}: 目标节点不在V_pp中，不接收")
                continue
            
            success = random.random() < p
            if success:
                received_prepare_count[target] += 1
                print(f"  ✅ {sender}→{target}: 成功")
            else:
                print(f"  ❌ {sender}→{target}: 失败")
    
    print(f"\n每个节点收到的prepare数量（包括自己）:")
    for node in nodes:
        if node not in V_pp:
            print(f"  ⏭️  节点{node}: 不在V_pp中，不参与prepare阶段")
        else:
            count = received_prepare_count[node]
            status = "✅" if count >= k_required else "❌"
            print(f"  {status} 节点{node}: {count} 条prepare (需要≥{k_required}, 来自其他节点)")
    
    V_p = [node for node in V_pp if received_prepare_count[node] >= k_required]
    print(f"\nPrepare阶段达标的节点集合 V_p = {V_p} (共{len(V_p)}个)")
    
    # 口径A：要最终达到 N_c ≥ N-f，则必有 N_p ≥ N-f
    if len(V_p) < Nc_required:
        print(f"❌ V_p={len(V_p)} < Nc_required={Nc_required}，无法继续，本轮失败")
        return False, {"phase": "prepare", "V_pp": len(V_pp), "V_p": len(V_p)}
    
    # ========== 阶段3: Commit ==========
    print("\n📍 阶段3: Commit")
    print("-" * 80)
    
    # Commit：V_p 内部互发 commit，统计“来自其他节点”的commit数（不计自己）
    received_commit_count = {node: 0 for node in nodes}
    
    for sender in V_p:
        print(f"节点{sender}发送commit:")
        for target in nodes:
            if target == sender:
                continue
            
            # 关键修复：只有target也在V_p中，才会接收这条commit
            if target not in V_p:
                print(f"  ⏭️  {sender}→{target}: 目标节点不在V_p中，不接收")
                continue
            
            success = random.random() < p
            if success:
                received_commit_count[target] += 1
                print(f"  ✅ {sender}→{target}: 成功")
            else:
                print(f"  ❌ {sender}→{target}: 失败")
    
    
    print(f"\n每个节点收到的commit数量（包括自己）:")
    for node in nodes:
        if node not in V_p:
            print(f"  ⏭️  节点{node}: 不在V_p中，不参与commit阶段")
        else:
            count = received_commit_count[node]
            status = "✅" if count >= k_required else "❌"
            print(f"  {status} 节点{node}: {count} 条commit (需要≥{k_required}, 来自其他节点)")
    
    V_c = [node for node in V_p if received_commit_count[node] >= k_required]
    print(f"\nCommit阶段达标的节点集合 V_c (commit节点) = {V_c} (共{len(V_c)}个)")
    
    # ========== 最终判断 ==========
    print("\n📊 最终判断")
    print("-" * 80)
    print(f"commit节点数量: {len(V_c)}")
    print(f"单节点commit达标阈值(2f): {k_required}")
    print(f"共识成功阈值(N-f): {Nc_required}")
    
    if len(V_c) >= Nc_required:
        print(f"\n✅✅✅ 共识成功！")
        print(f"   {len(V_c)} 个commit节点 ≥ {Nc_required} (N-f)")
        return True, {
            "phase": "success",
            "V_pp": len(V_pp),
            "V_p": len(V_p),
            "V_c": len(V_c)
        }
    else:
        print(f"\n❌ 共识失败")
        print(f"   {len(V_c)} 个commit节点 < {Nc_required} (N-f)")
        return False, {
            "phase": "commit",
            "V_pp": len(V_pp),
            "V_p": len(V_p),
            "V_c": len(V_c)
        }


def run_experiments(n: int, p: float, rounds: int = 100):
    """
    运行多轮实验，统计成功率
    """
    print("\n" + "=" * 80)
    print(f"🧪 运行 {rounds} 轮实验")
    print("=" * 80)
    print(f"参数: n={n}, p={p}, rounds={rounds}")
    print()
    
    success_count = 0
    failure_by_phase = {
        "pre-prepare": 0,
        "prepare": 0,
        "commit": 0
    }
    
    for i in range(rounds):
        success, details = simulate_one_round(n, p, seed=i)
        if success:
            success_count += 1
        else:
            phase = details["phase"]
            failure_by_phase[phase] += 1
        
        # 只打印前3轮的详细信息
        if i >= 3:
            print(f"\r进度: {i+1}/{rounds}", end="", flush=True)
    
    print("\n")
    print("=" * 80)
    print("📊 实验结果")
    print("=" * 80)
    print(f"总轮数: {rounds}")
    print(f"成功: {success_count} 轮 ({success_count/rounds*100:.2f}%)")
    print(f"失败: {rounds - success_count} 轮 ({(rounds-success_count)/rounds*100:.2f}%)")
    print()
    print("失败原因分布:")
    print(f"  Pre-prepare阶段: {failure_by_phase['pre-prepare']} 轮")
    print(f"  Prepare阶段: {failure_by_phase['prepare']} 轮")
    print(f"  Commit阶段: {failure_by_phase['commit']} 轮")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    # 默认参数
    n = 6
    p = 0.8
    rounds = 1
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 测试模式：运行多轮实验
            if len(sys.argv) > 2:
                p = float(sys.argv[2])
            if len(sys.argv) > 3:
                rounds = int(sys.argv[3])
            
            run_experiments(n, p, rounds)
        else:
            # 单轮模式：详细追踪
            p = float(sys.argv[1])
            if len(sys.argv) > 2:
                seed = int(sys.argv[2])
            else:
                seed = None
            
            success, details = simulate_one_round(n, p, seed)
            print("\n" + "=" * 80)
            print(f"最终结果: {'✅ 成功' if success else '❌ 失败'}")
            print(f"详细信息: {details}")
            print("=" * 80)
    else:
        # 默认：单轮详细追踪
        success, details = simulate_one_round(n, p)
        print("\n" + "=" * 80)
        print(f"最终结果: {'✅ 成功' if success else '❌ 失败'}")
        print(f"详细信息: {details}")
        print("=" * 80)

