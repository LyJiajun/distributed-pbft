# 项目结构说明

```
distributed-pbft/
├── 📁 src/                          # 前端源代码
│   ├── 📁 views/                    # 页面组件
│   │   ├── 🎯 HomePage.vue          # 主控页面（创建会话、生成二维码）
│   │   ├── 🔗 JoinPage.vue          # 加入页面（选择节点）
│   │   └── 🖥️ NodePage.vue          # 节点页面（参与共识）
│   ├── 🎨 App.vue                   # 主应用组件
│   └── 🚀 main.js                   # 应用入口（路由配置）
├── 📁 backend/                      # 后端源代码
│   ├── 🐍 main.py                   # 主服务器（FastAPI + Socket.IO）
│   └── 📋 requirements.txt          # Python依赖
├── 📄 package.json                  # 前端依赖配置
├── ⚙️ vite.config.js                # Vite构建配置
├── 🏠 index.html                    # HTML入口文件
├── 🚀 start.sh                      # 一键启动脚本
├── 📖 README.md                     # 项目说明文档
├── 🎬 demo.md                       # 演示指南
└── 📊 PROJECT_STRUCTURE.md          # 项目结构说明（本文件）
```

## 核心组件说明

### 前端组件 (Vue 3)

#### 🎯 HomePage.vue - 主控页面
- **功能**: 创建共识会话，配置参数，生成二维码
- **主要特性**:
  - 参数配置表单（节点数、容错数、拓扑结构等）
  - 二维码生成和显示
  - 节点链接列表
  - 会话状态监控

#### 🔗 JoinPage.vue - 加入页面
- **功能**: 处理二维码扫描后的节点选择
- **主要特性**:
  - 会话信息展示
  - 节点选择界面
  - 节点角色和权限说明
  - 连接状态显示

#### 🖥️ NodePage.vue - 节点页面
- **功能**: 用户扮演具体节点参与共识过程
- **主要特性**:
  - 实时连接状态
  - 节点状态和角色显示
  - 消息收发界面
  - 共识进度展示
  - 网络拓扑可视化

### 后端服务 (FastAPI + Socket.IO)

#### 🐍 main.py - 主服务器
- **功能**: 提供HTTP API和WebSocket服务
- **主要模块**:
  - 会话管理（创建、查询、状态更新）
  - WebSocket连接处理
  - PBFT共识算法实现
  - 消息路由和广播
  - 节点状态管理

## 数据流

```
用户操作流程:
1. 主控用户 → HomePage → 创建会话 → 生成二维码
2. 参与用户 → 扫描二维码 → JoinPage → 选择节点
3. 参与用户 → NodePage → 连接WebSocket → 参与共识
4. 所有节点 → 实时通信 → 达成共识 → 显示结果
```

## 技术架构

### 前端技术栈
- **Vue 3**: 现代响应式框架
- **Vue Router**: 单页应用路由
- **Element Plus**: UI组件库
- **Socket.IO Client**: 实时通信
- **QRCode.js**: 二维码生成
- **Vite**: 快速构建工具

### 后端技术栈
- **FastAPI**: 现代Python Web框架
- **Socket.IO**: 实时双向通信
- **Pydantic**: 数据验证
- **Uvicorn**: ASGI服务器

## 核心算法

### PBFT共识流程
1. **预准备阶段**: 提议者发送提议
2. **准备阶段**: 节点验证并广播准备消息
3. **提交阶段**: 节点确认并广播提交消息
4. **执行阶段**: 达成共识并执行提议

### 容错机制
- 最多容忍 `(n-1)/3` 个故障节点
- 支持恶意提议者和消息篡改
- 自动检测和处理节点故障

## 部署说明

### 开发环境
```bash
# 一键启动
./start.sh

# 或分别启动
cd backend && python main.py
cd .. && npm run dev
```

### 生产环境
```bash
# 构建前端
npm run build

# 部署后端
pip install -r requirements.txt
python main.py
```

## 扩展方向

### 功能扩展
- [ ] 支持更多共识算法（Raft、Paxos）
- [ ] 添加网络延迟和丢包模拟
- [ ] 实现更复杂的恶意行为模式
- [ ] 添加历史记录和回放功能

### 技术优化
- [ ] 数据库持久化
- [ ] 负载均衡
- [ ] 安全认证
- [ ] 性能监控

### 用户体验
- [ ] 移动端优化
- [ ] 多语言支持
- [ ] 主题切换
- [ ] 无障碍访问 