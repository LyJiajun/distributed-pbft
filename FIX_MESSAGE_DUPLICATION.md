# 消息重复问题修复

## 问题描述

用户报告了两个消息重复的问题：

1. **第一轮pre_prepare消息重复**：第一轮共识中，pre_prepare消息会出现2条
2. **人类节点选择正常共识时消息重复**：当人类节点选择"正常共识"模式时，prepare和commit消息会重复发送

## 问题分析

### 问题1：第一轮pre_prepare重复

**根本原因**：两个函数都在创建和追加pre_prepare消息

1. **第一次创建**：在`start_consensus`函数（第724-735行）中
   - 直接创建pre_prepare消息对象
   - 追加到`session["messages"]["pre_prepare"]`
   - 广播消息

2. **第二次创建**：在`robot_send_pre_prepare`函数（第1102行）中
   - 也创建pre_prepare消息对象
   - 也追加到`session["messages"]["pre_prepare"]`
   - 也广播消息

虽然`robot_send_pre_prepare`有重复检查机制（第1110-1112行），但在第一轮时`last_pre_prepare_round`还未设置，所以两次调用都会执行。

### 问题2：人类节点选择正常共识时消息重复

**根本原因**：当人类节点选择正常共识后，消息会被发送两次

以prepare消息为例：

1. **第一次发送**：在`choose_normal_consensus`函数（第640-644行）中
   - 调用`schedule_robot_prepare`来发送消息
   - 10秒后调用`handle_robot_prepare`
   - `handle_robot_prepare`追加消息（第1222行）

2. **第二次发送**：在`robot_send_prepare_messages`函数（第1170行）中
   - 遍历所有`robot_nodes`（第1193行）
   - 对每个机器人节点调用`handle_robot_prepare`（第1201行）
   - 再次追加消息

虽然`robot_send_prepare_messages`有`sent_prepare`标志检查（第1197-1198行），但`choose_normal_consensus`调用`schedule_robot_prepare`时没有设置这个标志，导致重复。

commit消息也有类似的问题。

## 解决方案

### 修复1：统一第一轮pre_prepare消息创建

修改`start_consensus`函数，移除重复的pre_prepare消息创建逻辑，统一使用`robot_send_pre_prepare`：

```python
async def start_consensus(session_id: str):
    """开始共识过程 - 仅用于第一轮共识的初始化"""
    session = get_session(session_id)
    if not session:
        return
    
    session["status"] = "running"
    session["phase"] = "pre-prepare"
    session["phase_step"] = 0
    
    print(f"会话 {session_id} 开始PBFT共识流程")
    
    # 通知所有节点进入预准备阶段
    await sio.emit('phase_update', {
        "phase": "pre-prepare",
        "step": 0,
        "isMyTurn": False
    }, room=session_id)
    
    # 提议者发送预准备消息（统一使用robot_send_pre_prepare）
    await robot_send_pre_prepare(session_id)
```

**改动说明**：
- 移除了直接创建pre_prepare消息的代码（原第724-742行）
- 统一调用`robot_send_pre_prepare`来发送pre_prepare消息
- `robot_send_pre_prepare`内部有重复检查机制，确保每轮只发送一次

### 修复2：设置标志防止重复发送

修改`choose_normal_consensus`函数，在调用`schedule_robot_prepare/commit`前设置标志：

```python
# 根据当前阶段自动发送消息
config = session["config"]

if session["phase"] == "prepare" and node_id != 0:
    # 在准备阶段且不是主节点，发送准备消息
    # 标记为即将发送，防止robot_send_prepare_messages重复发送
    session["robot_node_states"][node_id]["sent_prepare"] = True
    asyncio.create_task(schedule_robot_prepare(session_id, node_id, config["proposalValue"]))
elif session["phase"] == "commit":
    # 在提交阶段，发送提交消息
    # 标记为即将发送，防止robot_send_commit_messages重复发送
    session["robot_node_states"][node_id]["sent_commit"] = True
    asyncio.create_task(schedule_robot_commit(session_id, node_id, config["proposalValue"]))
```

**改动说明**：
- 在prepare阶段，设置`sent_prepare = True`（第643行）
- 在commit阶段，设置`sent_commit = True`（第648行）
- 这样`robot_send_prepare_messages`和`check_robot_nodes_ready_for_commit`中的循环就会跳过这些节点

## 测试验证

修复后，应该验证：

1. ✅ 第一轮共识的pre_prepare消息只有1条
2. ✅ 后续轮次的pre_prepare消息也只有1条
3. ✅ 人类节点选择正常共识后，prepare消息不重复
4. ✅ 人类节点选择正常共识后，commit消息不重复
5. ✅ 动画演示中的消息数量与表格一致

## 相关文件

- `backend/main.py`：
  - `start_consensus`函数（第711-731行）
  - `choose_normal_consensus`函数（第608-649行）
  - `robot_send_pre_prepare`函数（第1102-1168行）
  - `robot_send_prepare_messages`函数（第1170-1202行）
  - `schedule_robot_prepare`函数（第651-665行）
  - `schedule_robot_commit`函数（第1250-1268行）
  - `check_robot_nodes_ready_for_commit`函数（第1240-1248行）

## 修复日期

2025-11-02

