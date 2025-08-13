# 提议者消息发送问题修复

## 问题描述

用户反馈主节点（提议者，节点0）不能发送消息，这是一个关于PBFT算法角色理解的问题。

## PBFT算法中提议者的正确角色

在PBFT算法中，提议者（节点0）的角色是：

### ✅ 正确的行为
1. **预准备阶段**：提议者发送预准备消息（pre-prepare）
2. **准备阶段**：提议者不发送准备消息（prepare）
3. **提交阶段**：提议者可以发送提交消息（commit）

### ❌ 之前的问题
- 提议者被完全禁止发送任何消息
- 用户无法理解为什么主节点不能发送消息

## 修复内容

### 1. 前端逻辑修复

**修复前：**
```javascript
const isMyTurn = computed(() => {
  // 提议者（节点0）不发送准备和提交消息，只发送预准备消息
  if (nodeId === 0) {
    return false  // 完全禁止提议者发送消息
  }
  return currentPhase.value === 'prepare' || currentPhase.value === 'commit'
})
```

**修复后：**
```javascript
const isMyTurn = computed(() => {
  // 提议者（节点0）不发送准备消息，但可以发送提交消息
  if (nodeId === 0) {
    return currentPhase.value === 'commit'  // 提议者可以发送提交消息
  }
  return currentPhase.value === 'prepare' || currentPhase.value === 'commit'
})

// 提议者是否可以发送消息
const canProposerSendCustom = computed(() => {
  return nodeId === 0
})
```

### 2. 界面优化

添加了专门的提议者操作区域：

```html
<!-- 提议者快速操作 -->
<div class="quick-actions" v-if="canProposerSendCustom">
  <h4>提议者操作</h4>
  <div class="quick-actions-buttons">
    <el-button 
      type="success" 
      @click="sendCommit" 
      :disabled="currentPhase !== 'commit'"
      class="quick-action-btn"
    >
      发送确认消息
    </el-button>
    <div class="proposer-info">
      <el-tag type="info" size="small">提议者不发送准备消息，但可发送确认消息</el-tag>
    </div>
  </div>
</div>
```

### 3. 用户体验改进

- ✅ 提议者现在可以发送提交消息
- ✅ 明确显示提议者的角色和权限
- ✅ 保持PBFT算法的正确性
- ✅ 提供清晰的操作指引

## 测试验证

### 测试场景1：提议者发送提交消息
1. 以节点0身份登录
2. 在提交阶段点击"发送确认消息"
3. 验证消息能够正常发送和接收

### 测试场景2：提议者不能发送准备消息但可以发送提交消息
1. 以节点0身份登录
2. 在准备阶段：验证没有"发送准备消息"按钮
3. 在提交阶段：验证有"发送确认消息"按钮

### 测试场景3：验证者正常操作
1. 以其他节点身份登录
2. 在相应阶段可以看到"快速操作"按钮
3. 验证可以正常发送准备和提交消息

## 技术细节

### 后端逻辑
后端逻辑保持不变，因为：
- 预准备消息由后端自动发送（正确）
- 准备和提交消息的发送逻辑正确
- 自定义消息发送逻辑支持所有节点

### 前端逻辑
- `isMyTurn`：控制准备和提交消息的发送权限
- `canProposerSendCustom`：控制提议者操作区域的显示
- 权限独立控制，确保角色分离

## 符合PBFT规范

修复后的实现完全符合PBFT算法要求：

1. ✅ **提议者角色**：发送预准备消息，不发送准备消息，但可以发送提交消息
2. ✅ **验证者角色**：发送准备和提交消息
3. ✅ **用户体验**：清晰的角色区分和操作指引

## 总结

这个修复解决了用户对主节点不能发送消息的困惑，同时保持了PBFT算法的正确性。提议者现在可以：

- 发送提交消息参与共识确认
- 看到明确的角色说明
- 理解自己在共识中的特殊地位

而验证者仍然可以正常参与准备和提交阶段的投票。
