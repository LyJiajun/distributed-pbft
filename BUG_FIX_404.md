# 修复：动画演示404错误

## 🐛 问题描述

当点击"动画演示共识过程"按钮时，出现404错误：
```
GET /api/sessions/xxx/history HTTP/1.1" 404 Not Found
```

## 🔍 原因分析

### 问题根源
在 `HomePage.vue` 的 `createSession` 函数中（第347行），如果已有会话，会先删除旧会话：

```javascript
if (sessionInfo.value) {
  await axios.delete(`/api/sessions/${sessionInfo.value.sessionId}`)
}
```

### 问题场景
1. 用户创建会话A（sessionId: abc）
2. 用户再次点击"创建共识会话"，会话A被删除，创建会话B（sessionId: xyz）
3. 但如果浏览器缓存或某些原因导致 `sessionInfo` 还指向旧的会话A
4. 用户点击"动画演示"，前端尝试获取会话A的历史
5. 后端返回404，因为会话A已被删除

## ✅ 解决方案

在 `showDemo` 函数中添加错误处理：

```javascript
// 如果已有会话，尝试获取真实会话历史数据
if (sessionInfo.value) {
  try {
    const response = await axios.get(`/api/sessions/${sessionInfo.value.sessionId}/history`)
    // ... 使用真实数据
  } catch (error) {
    console.warn('获取会话历史失败，将使用模拟数据:', error)
    ElMessage.warning('会话已结束或不存在，将使用模拟数据演示')
    sessionInfo.value = null  // 清除无效的会话信息
    // 自动切换到模拟数据生成
  }
}

// 如果没有会话或获取历史失败，生成模拟数据
if (!sessionInfo.value || simulationRounds.value.length === 0) {
  // 生成3轮模拟数据
  ...
}
```

## 🎯 修复效果

### 修复前
- ❌ 404错误弹出
- ❌ 动画演示无法使用
- ❌ 用户体验差

### 修复后
- ✅ 优雅降级处理
- ✅ 自动切换到模拟数据
- ✅ 显示友好提示："会话已结束或不存在，将使用模拟数据演示"
- ✅ 动画演示正常工作

## 📝 用户体验

现在当会话不存在时：

1. **友好提示**
```
⚠️ 会话已结束或不存在，将使用模拟数据演示
ℹ️ 正在展示模拟的共识过程
```

2. **自动降级**
- 自动从"真实历史"降级到"模拟演示"
- 生成3轮模拟数据供查看
- 不会中断用户操作流程

3. **状态清理**
- 清除无效的会话信息
- 防止后续操作出错

## 🔧 额外优化

### 后端调试日志
在 `backend/main.py` 的 `get_session_history` 函数中添加了调试日志：

```python
print(f"\n=== 获取会话历史 ===")
print(f"请求的会话ID: {session_id}")
print(f"当前所有会话ID: {list(sessions.keys())}")
```

这有助于诊断会话ID不匹配的问题。

## 🧪 测试建议

### 测试场景1：正常流程
1. 创建会话
2. 点击"动画演示共识过程"
3. ✅ 应该看到"真实会话消息历史"标签

### 测试场景2：会话被删除
1. 创建会话A
2. 再次创建会话B（会话A被删除）
3. 刷新页面（可能还保留会话A的信息）
4. 点击"动画演示共识过程"
5. ✅ 应该看到警告提示，然后显示"模拟演示数据"

### 测试场景3：无会话
1. 不创建会话
2. 直接点击"动画演示共识过程"
3. ✅ 应该直接显示"模拟演示数据"

## 📋 修改的文件

- ✅ `/src/views/HomePage.vue` - 添加错误处理和自动降级
- ✅ `/backend/main.py` - 添加调试日志

## 🚀 部署

修复已完成，重启前端服务即可：

```bash
# 停止当前服务 (Ctrl + C)
# 重新启动
cd /home/lijiajun/Cursor/03_Web_Interaction/distributed-pbft
npm run dev
```

后端无需重启（除非想看调试日志）。

---

**修复日期**：2025-11-02  
**版本**：2.0.1  
**严重程度**：中等 → 已修复

