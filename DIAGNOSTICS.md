# 问题诊断和解决方案

## 问题1：只能查看一轮共识

### 诊断步骤

1. **检查后端是否重启**
   ```bash
   # 后端必须重启才能应用新代码（不清空消息）
   cd /home/lijiajun/Cursor/03_Web_Interaction/distributed-pbft/backend
   # 停止当前服务 (Ctrl + C)
   python main.py
   ```

2. **创建新会话**
   - 旧会话可能还在使用旧代码
   - 创建新会话后，消息才会包含 `round` 字段

3. **等待多轮共识**
   - 至少等待2-3轮共识完成
   - 每轮间隔约10秒

4. **查看浏览器控制台**
   ```javascript
   // 打开浏览器开发者工具 (F12)
   // 在Console标签中查看：
   console.log('可用的轮次:', rounds)
   ```

5. **检查后端日志**
   ```
   # 应该看到类似输出：
   === 获取会话历史 ===
   请求的会话ID: xxx, 轮次: 所有
   会话共有 3 轮: [1, 2, 3], 当前轮次: 3
   ```

### 可能的原因

#### 原因A：后端未重启 ⭐ 最可能
- **症状**：消息仍被清空，只有最新轮次
- **解决**：重启后端服务

#### 原因B：使用旧会话
- **症状**：旧消息没有 `round` 字段
- **解决**：创建新会话测试

#### 原因C：前端缓存
- **症状**：前端代码未更新
- **解决**：硬刷新 (Ctrl+Shift+R) 或重启前端

## 问题2：消息显示两遍

### 问题分析

#### 数据流程
```
用户点击"发送准备消息"
    ↓
前端: socket.emit('send_prepare', {nodeId, value})
    ↓
后端: send_prepare() 函数
    ↓
后端: session["messages"]["prepare"].append(message)  ← 存储消息
    ↓
后端: sio.emit('message_received', message)          ← 广播消息
    ↓
前端: socket.on('message_received')                   ← 所有客户端接收
    ↓
前端: receivedMessages.push(message)                  ← 实时显示
```

#### 可能的原因

##### 原因A：用户点击了两次 ⭐ 最可能
- **症状**：快速连续点击发送按钮
- **结果**：发送了两条消息
- **验证**：检查后端日志

##### 原因B：PBFTTable 组件显示问题
- **症状**：消息只发送一次，但表格显示两次
- **原因**：数据转换或渲染逻辑错误
- **需要检查**：PBFTTable.vue 组件

##### 原因C：消息广播重复
- **症状**：每条消息被广播两次
- **原因**：广播逻辑错误
- **验证**：检查后端日志

### 诊断步骤

#### 步骤1：检查后端日志
```bash
# 启动后端时应该看到：
节点 5 的准备消息已发送 (传达概率: 100%)

# 如果看到两次，说明确实发送了两次：
节点 5 的准备消息已发送 (传达概率: 100%)
节点 5 的准备消息已发送 (传达概率: 100%)  ← 重复！
```

#### 步骤2：检查浏览器控制台
```javascript
// 在NodePage.vue的 sendPrepare 函数中添加日志：
const sendPrepare = () => {
  console.log('🔵 发送准备消息', {nodeId, value: acceptedValue.value})
  // ...
}

// 如果看到两次日志，说明用户点击了两次
```

#### 步骤3：检查消息表格
```javascript
// 在HomePage的动画演示中查看原始数据：
console.log('第1轮准备消息:', simulationRounds[0].data.prepare)

// 检查是否有重复的消息（相同的from、to、value、timestamp）
```

## 测试脚本

创建一个测试脚本来验证：

```python
# test_rounds.py
import requests

session_id = "YOUR_SESSION_ID"  # 替换为实际的会话ID

# 1. 获取轮次列表
response = requests.get(f"http://localhost:8000/api/sessions/{session_id}/history")
print("轮次列表:", response.json())

# 2. 获取第1轮消息
response = requests.get(f"http://localhost:8000/api/sessions/{session_id}/history?round=1")
data = response.json()
print(f"\n第1轮消息数量:")
print(f"  pre_prepare: {len(data['pre_prepare'])}")
print(f"  prepare: {len(data['prepare'][0]) if data['prepare'] else 0}")
print(f"  commit: {len(data['commit'][0]) if data['commit'] else 0}")

# 3. 检查是否有重复消息
prepare_msgs = data['prepare'][0] if data['prepare'] else []
unique_msgs = set()
duplicates = []

for msg in prepare_msgs:
    key = (msg['src'], msg['dst'], msg['value'], msg['type'])
    if key in unique_msgs:
        duplicates.append(msg)
    else:
        unique_msgs.add(key)

if duplicates:
    print(f"\n⚠️ 发现 {len(duplicates)} 条重复消息:")
    for msg in duplicates:
        print(f"  {msg['src']} -> {msg['dst']}: {msg['value']}")
else:
    print("\n✅ 没有重复消息")
```

## 解决方案

### 方案1：重启服务（解决问题1）

```bash
# 1. 停止后端 (Ctrl+C)
# 2. 重新启动后端
cd /home/lijiajun/Cursor/03_Web_Interaction/distributed-pbft/backend
python main.py

# 3. 前端不需要重启（如果已经在运行）
```

### 方案2：防止重复点击（解决问题2）

如果确认是用户重复点击导致的，可以在前端添加防抖：

```javascript
// NodePage.vue
let sendingPrepare = false

const sendPrepare = () => {
  if (sendingPrepare) {
    ElMessage.warning('消息发送中，请稍候...')
    return
  }
  
  sendingPrepare = true
  
  if (socket.value) {
    const message = {
      sessionId,
      nodeId,
      value: acceptedValue.value
    }
    socket.value.emit('send_prepare', message)
    
    // 1秒后重置
    setTimeout(() => {
      sendingPrepare = false
    }, 1000)
  }
}
```

### 方案3：检查PBFTTable（如果是显示问题）

检查 PBFTTable.vue 的 getStageMessages 函数是否有重复逻辑。

## 验证清单

### 问题1：多轮次查看
- [ ] 后端已重启
- [ ] 创建了新会话
- [ ] 等待至少2轮共识完成（约20秒）
- [ ] 点击"动画演示"
- [ ] 看到轮次选择器显示多个轮次
- [ ] 可以切换不同轮次查看

### 问题2：消息重复
- [ ] 检查后端日志，确认每条消息只记录一次
- [ ] 检查浏览器控制台，确认没有重复发送
- [ ] 检查动画数据，确认没有重复消息
- [ ] 如果确认重复，添加防抖机制

## 快速诊断命令

```bash
# 1. 检查后端进程
ps aux | grep python

# 2. 检查后端端口
lsof -i :8000

# 3. 重启后端
cd /home/lijiajun/Cursor/03_Web_Interaction/distributed-pbft/backend
pkill -f "python main.py"
python main.py

# 4. 查看后端日志
tail -f backend.log  # 如果有日志文件
```

## 联系我们

如果问题仍然存在，请提供：
1. 浏览器控制台截图
2. 后端日志输出
3. 会话ID
4. 重现步骤

---

**诊断日期**：2025-11-02  
**版本**：3.1.2  

