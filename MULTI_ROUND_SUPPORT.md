# 支持多轮次查看 - 更新说明

## 🎯 新功能

现在可以查看真实会话的**不同轮次**的共识过程，每轮都是真实的消息数据！

## ✨ 功能特性

### 1. 多轮次支持
- ✅ 自动检测会话有多少轮共识
- ✅ 通过轮次选择器切换不同轮次
- ✅ 每轮都是真实会话中实际发送的消息
- ✅ 每轮都有独立的共识结果

### 2. 智能界面
- 如果只有 1 轮：显示提示"当前仅有 1 轮共识"
- 如果有多轮：显示轮次选择器"第 1 轮、第 2 轮、第 3 轮..."

### 3. 轮次切换
- 点击不同轮次按钮
- 自动加载该轮的消息
- 自动播放动画

## 🔧 技术实现

### 后端改进

#### 1. 消息添加轮次信息
所有消息现在都包含 `round` 字段：

```python
message = {
    "from": node_id,
    "to": "all",
    "type": "prepare",
    "value": value,
    "phase": "prepare",
    "round": session["current_round"],  # 添加轮次信息
    "timestamp": datetime.now().isoformat(),
    ...
}
```

#### 2. 改进的 History API

**获取轮次列表**（不指定round参数）：
```bash
GET /api/sessions/{session_id}/history
```

响应：
```json
{
  "rounds": [1, 2, 3],
  "currentRound": 3,
  "totalRounds": 3
}
```

**获取指定轮次的消息**（指定round参数）：
```bash
GET /api/sessions/{session_id}/history?round=2
```

响应：
```json
{
  "round": 2,
  "pre_prepare": [...],
  "prepare": [[...]],
  "commit": [[...]],
  "consensus": "共识成功：达成共识值 0",
  "nodeCount": 6,
  "topology": "full",
  "proposalValue": 0
}
```

### 前端改进

#### 1. 获取所有轮次
```javascript
const showDemo = async () => {
  // 1. 先获取轮次列表
  const roundsResponse = await axios.get(
    `/api/sessions/${sessionInfo.value.sessionId}/history`
  )
  const rounds = roundsResponse.data.rounds || [1]
  
  // 2. 获取所有轮次的数据
  for (const roundNum of rounds) {
    const response = await axios.get(
      `/api/sessions/${sessionInfo.value.sessionId}/history?round=${roundNum}`
    )
    simulationRounds.value.push({
      id: roundNum,
      data: response.data,
      isReal: true
    })
  }
}
```

#### 2. 轮次切换功能
```javascript
const onRoundChange = (roundId) => {
  const round = simulationRounds.value.find(r => r.id === roundId)
  if (round) {
    currentSimulation.value = round.data
    // 自动播放新轮次的动画
    nextTick(() => {
      playAnimation()
    })
  }
}
```

#### 3. 智能界面显示
```html
<!-- 如果有多轮，显示轮次选择器 -->
<el-radio-group v-if="simulationRounds.length > 1" v-model="currentRound" @change="onRoundChange">
  <el-radio-button v-for="round in simulationRounds" :key="round.id" :label="round.id">
    第 {{ round.id }} 轮
  </el-radio-button>
</el-radio-group>

<!-- 如果只有 1 轮，显示提示 -->
<el-text v-else>当前仅有 1 轮共识</el-text>
```

## 📊 使用场景

### 场景 1：单轮共识
```
第1轮: 所有节点正常参与
共识成功 ✅

界面显示:
┌─────────────────────────────────┐
│ [真实会话消息历史] 🟢              │
│ 当前仅有 1 轮共识                 │
│ [重新播放动画] 按钮                │
└─────────────────────────────────┘
```

### 场景 2：多轮共识
```
第1轮: 共识成功 ✅
第2轮: 共识失败 ❌ (拜占庭节点太多)
第3轮: 共识成功 ✅

界面显示:
┌─────────────────────────────────┐
│ [真实会话消息历史] 🟢              │
│ 选择轮次: ⚪第1轮 ⚪第2轮 ⚪第3轮   │
│ [重新播放动画] 按钮                │
└─────────────────────────────────┘

用户可以:
- 点击"第2轮"查看失败的共识过程
- 观察拜占庭节点的错误消息(红色)
- 分析为什么共识失败
```

## 🎨 用户体验

### 完整流程

#### 1. 创建会话
```bash
用户A: 配置参数(6个节点，1个拜占庭节点)
用户A: 点击"创建共识会话"
```

#### 2. 多轮共识
```bash
# 第1轮
- 所有节点参与，共识成功 ✅

# 第2轮 (10秒后自动开始)
- 节点2选择拜占庭攻击，发送错误值
- 共识失败 ❌

# 第3轮 (再10秒后)
- 所有节点恢复正常
- 共识成功 ✅
```

#### 3. 查看动画
```bash
用户A: 点击"动画演示共识过程"
系统: ✅ 已加载 3 轮共识历史

用户查看第1轮:
  🟢 所有消息都是绿色(正确值)
  ✅ 结果: 共识成功

用户切换到第2轮:
  🟢 节点0,1,3,4,5的消息是绿色
  🔴 节点2的消息是红色(拜占庭攻击)
  ❌ 结果: 共识失败

用户切换到第3轮:
  🟢 所有消息都是绿色
  ✅ 结果: 共识成功
```

## 🔍 消息过滤逻辑

### 后端按轮次过滤
```python
def filter_by_round(msg_list, target_round):
    """按轮次过滤消息"""
    return [msg for msg in msg_list if msg.get("round", 1) == target_round]

# 过滤各阶段的消息
round_pre_prepare = filter_by_round(messages["pre_prepare"], round)
round_prepare = filter_by_round(messages["prepare"], round)
round_commit = filter_by_round(messages["commit"], round)
```

### 轮次识别
- 每条消息都有 `round` 字段
- 从所有消息中提取不同的轮次号
- 返回已完成的所有轮次列表

## 📈 数据结构

### 消息结构
```python
{
    "from": 0,
    "to": "all",
    "type": "prepare",
    "value": 0,
    "phase": "prepare",
    "round": 2,  # ⭐ 新增：轮次信息
    "timestamp": "2025-11-02T10:30:00",
    "tampered": False,
    "byzantine": False
}
```

### 轮次信息响应
```json
{
  "rounds": [1, 2, 3],        // 所有可用轮次
  "currentRound": 3,          // 当前进行中的轮次
  "totalRounds": 3            // 总轮次数
}
```

### 单轮消息响应
```json
{
  "round": 2,                 // 当前查看的轮次
  "pre_prepare": [...],       // 该轮的pre-prepare消息
  "prepare": [[...]],         // 该轮的prepare消息
  "commit": [[...]],          // 该轮的commit消息
  "consensus": "共识失败：未能达成一致",
  "nodeCount": 6,
  "topology": "full",
  "proposalValue": 0
}
```

## 🎯 优势

### 1. 教学价值
- ✅ 观察多轮共识的演变
- ✅ 对比成功和失败的轮次
- ✅ 理解拜占庭容错机制

### 2. 调试价值
- ✅ 定位哪一轮出现问题
- ✅ 分析节点行为变化
- ✅ 验证修复效果

### 3. 真实性
- ✅ 100%真实数据
- ✅ 反映实际共识过程
- ✅ 包含所有历史轮次

### 4. 灵活性
- ✅ 支持任意轮次数
- ✅ 自动检测可用轮次
- ✅ 界面自适应

## ⚠️ 注意事项

### 消息存储
- 所有轮次的消息都保存在同一个会话中
- 通过 `round` 字段区分不同轮次
- 旧消息不会被删除（可以回看历史）

### 性能考虑
- 如果轮次很多（>10），加载可能需要几秒
- 每轮都会生成独立的动画数据
- 建议在共识结束后查看

### 轮次编号
- 轮次从 1 开始
- 连续递增
- 不会跳号

## 📋 修改的文件

### 后端
- ✅ `/backend/main.py`
  - 所有消息添加 `round` 字段
  - history API 支持轮次查询
  - 返回轮次列表

### 前端
- ✅ `/src/views/HomePage.vue`
  - 获取轮次列表
  - 获取所有轮次数据
  - 添加轮次选择器
  - 实现轮次切换

### 文档
- ✅ `MULTI_ROUND_SUPPORT.md` - 本文档

## 🚀 测试建议

### 测试场景 1：单轮共识
```bash
1. 创建会话
2. 等待第1轮完成
3. 点击"动画演示"
✅ 应该看到"当前仅有 1 轮共识"
✅ 能正常播放第1轮动画
```

### 测试场景 2：多轮共识
```bash
1. 创建会话
2. 等待第1轮完成(10秒)
3. 等待第2轮开始并完成(再10秒)
4. 等待第3轮开始并完成(再10秒)
5. 点击"动画演示"
✅ 应该看到轮次选择器: 第1轮、第2轮、第3轮
✅ 点击不同轮次能正确切换
✅ 每轮显示对应的消息和结果
```

### 测试场景 3：拜占庭攻击
```bash
1. 创建会话
2. 第1轮正常完成
3. 第2轮中，某个节点选择拜占庭攻击
4. 第3轮恢复正常
5. 点击"动画演示"
6. 切换到第2轮
✅ 应该看到红色消息(拜占庭攻击)
✅ 结果显示共识失败
```

## 🔄 升级指南

### 从之前的版本升级
- ⚠️ 旧会话的消息没有 `round` 字段
- 系统会默认为轮次 1
- 建议创建新会话测试多轮功能

### 兼容性
- ✅ 向后兼容
- ✅ 旧消息仍可正常显示
- ✅ 新消息自动包含轮次信息

---

**更新日期**：2025-11-02  
**版本**：3.1.0  
**类型**：功能增强 - 多轮次支持

