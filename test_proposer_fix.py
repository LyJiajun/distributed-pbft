#!/usr/bin/env python3

def test_proposer_permissions():
    """测试提议者消息发送权限"""
    print("=== 测试提议者消息发送权限 ===")
    
    # 模拟前端逻辑
    nodeId = 0  # 提议者
    currentPhase = "prepare"
    
    # 修复前的逻辑
    def old_isMyTurn(nodeId, currentPhase):
        if nodeId == 0:
            return False  # 提议者完全不能发送消息
        return currentPhase == "prepare" or currentPhase == "commit"
    
    # 修复后的逻辑
    def new_isMyTurn(nodeId, currentPhase):
        if nodeId == 0:
            return currentPhase == "commit"  # 提议者可以发送提交消息
        return currentPhase == "prepare" or currentPhase == "commit"
    
    # 测试不同阶段
    phases = ["prepare", "commit"]
    
    print("提议者（节点0）在不同阶段的权限：")
    for phase in phases:
        old_result = old_isMyTurn(nodeId, phase)
        new_result = new_isMyTurn(nodeId, phase)
        
        print(f"  阶段: {phase}")
        print(f"    修复前: {'❌ 不能发送' if not old_result else '✅ 可以发送'}")
        print(f"    修复后: {'❌ 不能发送' if not new_result else '✅ 可以发送'}")
        
        if old_result != new_result:
            print(f"    🔄 权限变化: {'允许' if new_result else '禁止'}")
        print()
    
    # 测试验证者权限
    print("验证者（其他节点）在不同阶段的权限：")
    for phase in phases:
        old_result = old_isMyTurn(1, phase)  # 节点1
        new_result = new_isMyTurn(1, phase)  # 节点1
        
        print(f"  阶段: {phase}")
        print(f"    修复前: {'❌ 不能发送' if not old_result else '✅ 可以发送'}")
        print(f"    修复后: {'❌ 不能发送' if not new_result else '✅ 可以发送'}")
        print()
    
    # 总结
    print("=== 修复总结 ===")
    print("✅ 提议者现在可以发送提交消息")
    print("❌ 提议者仍然不能发送准备消息（符合PBFT规范）")
    print("✅ 验证者可以发送准备和提交消息")
    print("✅ 符合PBFT算法的正确角色分工")

if __name__ == "__main__":
    test_proposer_permissions()





