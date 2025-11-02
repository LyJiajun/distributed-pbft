# 修复：保留历史轮次消息

## 🐛 问题描述

**症状**：
- ✅ 可以查看当前轮次的共识情况
- ❌ 无法查看以前轮次的共识情况
- ❌ 轮次选择器只显示当前轮次

**原因**：
在 `start_next_round` 函数中，每次开始新一轮共识时会清空所有消息：

```python
# ❌ 问题代码（第970-975行）
# 清空消息
session["messages"] = {
    "pre_prepare": [],
    "prepare": [],
    "commit": []
}
```

这导致：
1. 第1轮的消息被清空
2. 第2轮开始后，只能看到第2轮的消息
3. 第3轮开始后，只能看到第3轮的消息
4. 历史轮次的消息全部丢失

## ✅ 解决方案

**移除清空消息的代码，保留所有历史消息**：

```python
# ✅ 修复后的代码
# 不再清空消息，保留历史轮次的消息
# 所有消息通过 round 字段区分不同轮次
# session["messages"] 保持累积，不清空
```

### 工作原理

1. **消息累积存储**：
   - 所有轮次的消息都保存在 `session["messages"]` 中
   - 不会被清空

2. **轮次区分**：
   - 每条消息都有 `round` 字段
   - 通过 `round` 字段识别属于哪一轮

3. **按需过滤**：
   - 查询时通过 `filter_by_round` 函数过滤
   - 只返回指定轮次的消息

## 📊 数据结构

### 修复前（❌ 只有当前轮）
```python
# 第1轮完成后
session["messages"] = {
    "pre_prepare": [msg1_round1, msg2_round1, ...],
    "prepare": [msg3_round1, msg4_round1, ...],
    "commit": [msg5_round1, msg6_round1, ...]
}

# 第2轮开始后 - 消息被清空！
session["messages"] = {
    "pre_prepare": [],
    "prepare": [],
    "commit": []
}

# 第2轮完成后 - 只有第2轮的消息
session["messages"] = {
    "pre_prepare": [msg1_round2, msg2_round2, ...],
    "prepare": [msg3_round2, msg4_round2, ...],
    "commit": [msg5_round2, msg6_round2, ...]
}
```

### 修复后（✅ 保留所有轮次）
```python
# 第1轮完成后
session["messages"] = {
    "pre_prepare": [
        {"from": 0, "value": 0, "round": 1, ...},
        {"from": 1, "value": 0, "round": 1, ...}
    ],
    "prepare": [...],
    "commit": [...]
}

# 第2轮开始后 - 不清空，保留第1轮的消息
session["messages"] = {
    "pre_prepare": [
        {"from": 0, "value": 0, "round": 1, ...},  # 第1轮
        {"from": 1, "value": 0, "round": 1, ...}   # 第1轮
    ],
    "prepare": [...],
    "commit": [...]
}

# 第2轮完成后 - 包含第1轮和第2轮的消息
session["messages"] = {
    "pre_prepare": [
        {"from": 0, "value": 0, "round": 1, ...},  # 第1轮
        {"from": 1, "value": 0, "round": 1, ...},  # 第1轮
        {"from": 0, "value": 0, "round": 2, ...},  # 第2轮
        {"from": 1, "value": 0, "round": 2, ...}   # 第2轮
    ],
    "prepare": [...],
    "commit": [...]
}

# 第3轮完成后 - 包含所有轮次的消息
session["messages"] = {
    "pre_prepare": [
        # 第1轮的消息
        {"from": 0, "value": 0, "round": 1, ...},
        # 第2轮的消息
        {"from": 0, "value": 0, "round": 2, ...},
        # 第3轮的消息
        {"from": 0, "value": 0, "round": 3, ...}
    ],
    ...
}
```

## 🔍 查询流程

### 获取轮次列表
```python
GET /api/sessions/{session_id}/history

# 后端逻辑
all_rounds = set()
for msg in session["messages"]["prepare"]:
    if "round" in msg:
        all_rounds.add(msg["round"])

# 响应
{
    "rounds": [1, 2, 3],  # ✅ 现在能看到所有轮次！
    "currentRound": 3,
    "totalRounds": 3
}
```

### 查询指定轮次
```python
GET /api/sessions/{session_id}/history?round=1

# 后端逻辑
def filter_by_round(msg_list, target_round):
    return [msg for msg in msg_list if msg.get("round", 1) == target_round]

round_prepare = filter_by_round(session["messages"]["prepare"], 1)

# 响应
{
    "round": 1,
    "pre_prepare": [...],  # 只包含第1轮的消息
    "prepare": [...],
    "commit": [...],
    "consensus": "共识成功：达成共识值 0"
}
```

## 🎯 测试验证

### 测试场景：多轮共识

#### 操作步骤
```bash
1. 创建会话
2. 等待第1轮完成 (约20秒)
3. 等待第2轮完成 (约30秒)
4. 等待第3轮完成 (约30秒)
5. 点击"动画演示共识过程"
```

#### 预期结果（修复前 ❌）
```
轮次列表: [3]  # ❌ 只有第3轮
轮次选择器: 第3轮
```

#### 预期结果（修复后 ✅）
```
轮次列表: [1, 2, 3]  # ✅ 所有轮次都在！
轮次选择器: 第1轮、第2轮、第3轮
```

#### 验证操作
```bash
1. 点击"第1轮"
   ✅ 应该看到第1轮的消息动画
   ✅ 显示第1轮的共识结果

2. 点击"第2轮"
   ✅ 应该看到第2轮的消息动画
   ✅ 显示第2轮的共识结果

3. 点击"第3轮"
   ✅ 应该看到第3轮的消息动画
   ✅ 显示第3轮的共识结果
```

## 💡 优势

### 1. 完整的历史记录
- ✅ 保留所有轮次的消息
- ✅ 可以回看任意轮次
- ✅ 分析共识过程的演变

### 2. 调试和分析
- ✅ 对比不同轮次的行为
- ✅ 定位问题发生的轮次
- ✅ 验证修复效果

### 3. 教学价值
- ✅ 展示多轮共识的演变
- ✅ 观察节点行为变化
- ✅ 理解拜占庭容错机制

## ⚠️ 注意事项

### 内存使用
- **影响**：消息累积会占用更多内存
- **评估**：每轮约100-300条消息，每条约200字节
- **计算**：10轮 × 200条 × 200字节 = 400KB（可接受）
- **建议**：单会话建议不超过100轮

### 性能影响
- **查询性能**：需要过滤所有消息
- **影响**：轻微，因为消息量不大
- **优化**：已使用列表推导式，性能良好

### 会话生命周期
- **创建时**：初始化空的 messages
- **运行中**：消息累积增长
- **删除时**：会话和所有消息一起删除

## 🔄 向后兼容性

### 旧会话
- ✅ 已有的会话不受影响
- ✅ 消息结构保持不变
- ✅ 只是不再清空

### 旧代码
- ✅ 所有查询代码无需修改
- ✅ 通过 round 字段自动区分
- ✅ 完全向后兼容

## 📋 修改的文件

### 后端
- ✅ `/backend/main.py`
  - 移除 `start_next_round` 中清空消息的代码
  - 保留所有轮次的消息

### 文档
- ✅ `FIX_HISTORY_ROUNDS.md` - 本文档

## 🚀 部署

### 重启后端服务
```bash
cd /home/lijiajun/Cursor/03_Web_Interaction/distributed-pbft/backend
# 停止当前服务 (Ctrl + C)
python main.py
```

前端无需修改，只需确保后端已重启。

## ✅ 验证清单

- [ ] 创建新会话
- [ ] 等待至少2-3轮共识完成
- [ ] 点击"动画演示共识过程"
- [ ] 确认轮次选择器显示所有轮次
- [ ] 点击不同轮次，确认能正确切换
- [ ] 确认每轮显示对应的消息和结果

## 🎉 修复效果

### 修复前
```
用户: "我想看第1轮的共识过程"
系统: ❌ 只能看到第3轮（当前轮）
```

### 修复后
```
用户: "我想看第1轮的共识过程"
系统: ✅ 显示第1、2、3轮的选择器
用户: 点击"第1轮"
系统: ✅ 播放第1轮的消息动画
```

---

**修复日期**：2025-11-02  
**版本**：3.1.1  
**严重程度**：高 → 已修复
**影响范围**：多轮次历史查看功能

