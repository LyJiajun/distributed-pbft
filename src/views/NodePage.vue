<template>
  <div class="node-page">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <div class="node-info">
            <h2 :class="{ 'bad-node': attackForm.enabled }">参与者 {{ nodeId }}</h2>
            <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'">
              {{ connectionStatus === 'connected' ? '已连接' : '未连接' }}
            </el-tag>
            <el-tag v-if="attackForm.enabled" type="danger" effect="dark">🦹 拜占庭节点</el-tag>
          </div>
          <div class="session-info">
            <span>会话: {{ sessionId }}</span>
            <el-button size="small" @click="leaveSession" type="danger">离开会话</el-button>
          </div>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <el-row :gutter="20">
          <!-- 左侧：共识进度 -->
          <el-col :span="6">
            <el-card class="progress-card">
              <template #header>
                <div class="card-header">
                  <span>共识进度</span>
                </div>
              </template>
              
              <div class="consensus-progress">
                <!-- 共识进度条 -->
                <div class="phase-progress">
                  <el-progress 
                    :percentage="getPhasePercentage()" 
                    :status="getPhaseStatus()"
                    :stroke-width="8"
                  />
                  <div class="phase-steps">
                    <el-steps :active="phaseStep" finish-status="success" simple>
                      <el-step title="提议" description="发起提议" />
                      <el-step title="准备" description="验证提议" />
                      <el-step title="确认" description="确认提议" />
                      <el-step title="完成" description="达成共识" />
                    </el-steps>
                  </div>
                </div>
                
                <!-- 当前状态 -->
                <div class="current-status">
                  <h4>当前状态</h4>
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="当前阶段">{{ getPhaseDisplayName(currentPhase) }}</el-descriptions-item>
                    <el-descriptions-item label="接受内容">{{ getAcceptedContentDisplay() }}</el-descriptions-item>
                    <el-descriptions-item label="网络可靠性">{{ sessionConfig.messageDeliveryRate ?? '未设置' }}%</el-descriptions-item>
                  </el-descriptions>
                </div>
                
                <!-- 快速操作 -->
                <!-- 验证者快速操作 -->
                <div class="quick-actions" v-if="isMyTurn">
                  <h4>快速操作</h4>
                  <div class="quick-actions-buttons">
                    <el-button 
                      type="primary" 
                      @click="sendPrepare" 
                      :disabled="currentPhase !== 'prepare'"
                      class="quick-action-btn"
                    >
                      发送准备消息
                    </el-button>
                    <el-button 
                      type="success" 
                      @click="sendCommit" 
                      :disabled="currentPhase !== 'commit'"
                      class="quick-action-btn"
                    >
                      发送确认消息
                    </el-button>
                  </div>
                </div>

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



                <!-- 拜占庭攻击控制区域 -->
                <div class="attack-control">
                  <el-divider content-position="left">
                    <span style="color: #f56c6c; font-weight: bold;">🦹 拜占庭攻击控制</span>
                  </el-divider>
                  
                  <el-form :model="attackForm" label-width="100px" size="small">
                    <el-form-item label="成为拜占庭节点">
                      <el-switch 
                        v-model="attackForm.enabled" 
                        active-text="是"
                        inactive-text="否"
                        @change="toggleAttackMode"
                      />
                      <span class="form-tip">选择是否成为拜占庭节点进行攻击</span>
                    </el-form-item>

                    <el-form-item v-if="attackForm.enabled" label="攻击强度">
                      <el-slider 
                        v-model="attackForm.intensity" 
                        :min="1" 
                        :max="10" 
                        :step="1"
                        show-stops
                        show-input
                      />
                    </el-form-item>

                    <el-form-item v-if="attackForm.enabled" label="攻击策略">
                      <el-radio-group v-model="attackForm.byzantineStrategy">
                        <el-radio label="always">总是发送错误值</el-radio>
                        <el-radio label="sometimes">有时发送错误值</el-radio>
                        <el-radio label="random">随机发送不同值</el-radio>
                        <el-radio label="targeted">针对不同节点发送不同值</el-radio>
                      </el-radio-group>
                    </el-form-item>

                    <el-form-item v-if="attackForm.enabled && attackForm.byzantineStrategy === 'targeted'" label="目标节点配置">
                      <div style="margin-bottom: 10px;">
                        <el-button size="small" @click="addTargetNode">添加目标节点</el-button>
                        <el-button size="small" @click="clearTargetNodes">清空配置</el-button>
                      </div>
                      <div v-for="(target, index) in attackForm.targetNodes" :key="index" style="margin-bottom: 8px;">
                        <el-row :gutter="10">
                          <el-col :span="8">
                            <el-select v-model="target.nodeId" placeholder="选择节点" size="small">
                              <el-option 
                                v-for="nodeId in availableTargetNodes" 
                                :key="nodeId" 
                                :label="`节点 ${nodeId}`" 
                                :value="nodeId"
                              />
                            </el-select>
                          </el-col>
                          <el-col :span="8">
                            <el-select v-model="target.value" placeholder="发送值" size="small">
                              <el-option label="0" :value="0" />
                              <el-option label="1" :value="1" />
                              <el-option label="随机" :value="null" />
                            </el-select>
                          </el-col>
                          <el-col :span="4">
                            <el-button 
                              type="danger" 
                              size="small" 
                              @click="removeTargetNode(index)"
                              icon="Delete"
                            />
                          </el-col>
                        </el-row>
                      </div>
                    </el-form-item>

                    <el-form-item>
                      <el-button 
                        type="danger" 
                        @click="toggleAttackMode" 
                        :icon="attackForm.enabled ? 'Close' : 'VideoPlay'"
                        style="width: 100%"
                      >
                        {{ attackForm.enabled ? '停止拜占庭攻击' : '开始拜占庭攻击' }}
                      </el-button>
                    </el-form-item>
                  </el-form>

                  <!-- 攻击统计 -->
                  <div class="attack-stats" v-if="attackForm.enabled">
                    <h5 style="color: #f56c6c; margin: 10px 0;">拜占庭攻击效果统计</h5>
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="错误消息">{{ attackStats.byzantineMessages }}</el-descriptions-item>
                      <el-descriptions-item label="目标攻击">{{ attackStats.targetedMessages }}</el-descriptions-item>
                    </el-descriptions>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- 中间：收到的消息 -->
          <el-col :span="6">
            <el-card class="messages-card">
              <template #header>
                <div class="card-header">
                  <span>收到的消息</span>
                  <div>
                    <el-button size="small" @click="exportMessages">导出</el-button>
                    <el-button size="small" @click="clearMessages">清空</el-button>
                  </div>
                </div>
              </template>
              
              <div class="messages-container">
                <div class="messages-header">
                  <span>消息数量: {{ receivedMessages.length }}</span>
                </div>
                
                <div class="message-list">
                  <div 
                    v-for="msg in receivedMessages.slice(0, 8)" 
                    :key="msg.id"
                    class="message-item-compact"
                  >
                    <div class="message-header-compact">
                      <span class="message-from">来自: 参与者{{ msg.from }}</span>
                      <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
                    </div>
                    <div class="message-content-compact">
                      <span class="message-type">{{ getMessageTypeName(msg.type) }}</span>
                      <span class="message-value" v-if="msg.value !== null">
                        内容: {{ msg.value === -1 ? '拒绝' : (msg.value === 0 ? '选项A' : '选项B') }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div v-if="receivedMessages.length === 0" class="no-messages">
                  <el-empty description="暂无消息" :image-size="60" />
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- 右侧：拓扑图和共识结果 -->
          <el-col :span="12">
            <!-- 拓扑图 -->
            <el-card class="topology-card">
              <template #header>
                <div class="card-header">
                  <span>网络拓扑图</span>
                  <el-button size="small" @click="refreshTopology">刷新</el-button>
                </div>
              </template>
              
              <div class="dynamic-topology">
                <div class="topology-info">
                  <p><strong>网络类型:</strong> {{ getTopologyName(sessionConfig.topology) }}</p>
                  <p><strong>总人数:</strong> {{ sessionConfig.nodeCount }}</p>
                  <p><strong>活跃连接:</strong> {{ getActiveConnections() }}</p>
                </div>
                
                <!-- 拓扑图容器 -->
                <div class="topology-container">
                  <!-- 连接线 -->
                  <svg class="connection-lines" :width="topologyWidth" :height="topologyHeight">
                    <line 
                      v-for="connection in topologyConnections" 
                      :key="`${connection.from}-${connection.to}`"
                      :x1="connection.x1" 
                      :y1="connection.y1" 
                      :x2="connection.x2" 
                      :y2="connection.y2"
                      :class="connection.active ? 'active-connection' : 'inactive-connection'"
                    />
                  </svg>
                  
                  <!-- 节点 -->
                  <div 
                    v-for="i in sessionConfig.nodeCount" 
                    :key="i-1"
                    class="topology-node"
                    :class="{
                      'current-node': (i-1) === nodeId,
                      'proposer': (i-1) === 0,
                      'visible-node': isNodeVisible(i-1),
                      'invisible-node': !isNodeVisible(i-1),
                      'has-messages': hasNodeMessages(i-1),
                      'active': isNodeActive(i-1)
                    }"
                    :style="{
                      left: getNodeX(i-1) + 'px',
                      top: getNodeY(i-1) + 'px'
                    }"
                    @click="showNodeDetails(i-1)"
                  >
                    <div class="node-number">{{ i-1 }}</div>
                    <div class="node-status-indicator" v-if="isNodeActive(i-1)"></div>
                    <div class="message-count" v-if="getNodeMessageCount(i-1) > 0">
                      {{ getNodeMessageCount(i-1) }}
                    </div>
                  </div>
                </div>
                
                <!-- 共识结果 -->
                <div class="consensus-result-section">
                  <div v-if="consensusResult" class="result-summary">
                    <el-alert
                      :title="consensusResult.status"
                      :type="getConsensusAlertType(consensusResult.status)"
                      :description="consensusResult.description"
                      show-icon
                      :closable="false"
                      style="margin-bottom: 15px;"
                    />
                    
                    <div class="consensus-stats">
                      <el-row :gutter="20">
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.truth }}</div>
                            <div class="consensus-stat-label">选项A (节点)</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.falsehood }}</div>
                            <div class="consensus-stat-label">选项B (节点)</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.rejected }}</div>
                            <div class="consensus-stat-label">拒绝 (节点)</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.prepare_nodes }}/{{ consensusResult.stats.expected_prepare_nodes || consensusResult.stats.expected_nodes - 1 }}</div>
                            <div class="consensus-stat-label">准备阶段参与</div>
                          </div>
                        </el-col>
                      </el-row>
                      <el-row :gutter="20" style="margin-top: 10px;">
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.commit_nodes }}/{{ consensusResult.stats.expected_nodes }}</div>
                            <div class="consensus-stat-label">提交阶段参与</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.total_messages }}</div>
                            <div class="consensus-stat-label">总消息数</div>
                          </div>
                        </el-col>
                      </el-row>
                    </div>
                  </div>
                  <div v-else class="consensus-no-result">
                    <el-empty description="共识尚未完成" :image-size="60" />
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
    
    <!-- 节点详情对话框 -->
    <el-dialog v-model="nodeDetailsVisible" title="参与者详情" width="500px">
      <div v-if="selectedNode !== null">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="参与者ID">{{ selectedNode }}</el-descriptions-item>
          <el-descriptions-item label="连接状态">
            <el-tag :type="connectedNodes.includes(selectedNode) ? 'success' : 'danger'">
              {{ connectedNodes.includes(selectedNode) ? '已连接' : '未连接' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="角色">{{ selectedNode === 0 ? '提议者' : '验证者' }}</el-descriptions-item>
          <el-descriptions-item label="消息数量">{{ getNodeMessageCount(selectedNode) }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="node-messages" style="margin-top: 20px;">
          <h4>来自此参与者的消息</h4>
          <div v-for="msg in getNodeMessages(selectedNode)" :key="msg.id" class="message-item">
            <div class="message-header">
              <span>{{ getMessageTypeName(msg.type) }}</span>
              <span>{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div class="message-content">
              内容: {{ msg.value === -1 ? '拒绝' : (msg.value !== null ? (msg.value === 0 ? (sessionConfig.proposalContent || '选项A') : (sessionConfig.proposalContent || '选项B')) : '无') }}
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import io from 'socket.io-client'

const route = useRoute()
const router = useRouter()

// 路由参数
const sessionId = route.params.sessionId
const nodeId = parseInt(route.params.nodeId)

// 响应式数据
const socket = ref(null)
const connectionStatus = ref('connecting')
const sessionConfig = ref({
  nodeCount: 5,
  topology: 'full',
  proposalValue: 0,
  proposalContent: '',
  faultyNodes: 1,
  maliciousProposer: false,
  allowTampering: false,
  messageDeliveryRate: 100
})
const connectedNodes = ref([])
const currentPhase = ref('pre-prepare')
const phaseStep = ref(0)
const acceptedValue = ref(null)
const receivedMessages = ref([])
const consensusResult = ref(null)
const nodeDetailsVisible = ref(false)
const selectedNode = ref(null)

// 拓扑图相关
const topologyWidth = ref(500)
const topologyHeight = ref(400)
const topologyConnections = ref([])

// 消息发送表单（已移除自定义消息功能）
const messageForm = reactive({
  type: 'prepare',
  value: 0,
  target: 'all'
})

// 坏节点攻击控制表单
const attackForm = reactive({
  enabled: false,
  intensity: 5,
  byzantineStrategy: 'sometimes',
  targetNodes: []
})

// 攻击统计
const attackStats = reactive({
  byzantineMessages: 0,
  targetedMessages: 0
})

// 可用目标节点列表
const availableTargetNodes = ref([])

// 方法
const connectToServer = () => {
  socket.value = io(window.location.origin, {
    query: {
      sessionId,
      nodeId
    }
  })

  socket.value.on('connect', () => {
    connectionStatus.value = 'connected'
    ElMessage.success('连接成功')
  })

  socket.value.on('disconnect', () => {
    connectionStatus.value = 'disconnected'
    ElMessage.warning('连接断开')
  })

  socket.value.on('session_config', (config) => {
    console.log('收到会话配置:', config)
    console.log('提议内容检查:', {
      proposalContent: config.proposalContent,
      hasProposalContent: config.proposalContent && config.proposalContent.trim(),
      proposalValue: config.proposalValue
    })
    
    // 合并配置，确保所有字段都存在
    sessionConfig.value = {
      ...sessionConfig.value,
      ...config
    }
    console.log('合并后的配置:', sessionConfig.value)
    console.log('最终proposalContent:', sessionConfig.value.proposalContent)
    
    // 设置接受的值为提议值
    acceptedValue.value = config.proposalValue
    console.log('设置acceptedValue:', acceptedValue.value)
    
    updateAvailableTargetNodes()
    refreshTopology()
  })

  socket.value.on('node_connected', (data) => {
    if (!connectedNodes.value.includes(data.nodeId)) {
      connectedNodes.value.push(data.nodeId)
    }
    refreshTopology()
  })

  socket.value.on('node_disconnected', (data) => {
    const index = connectedNodes.value.indexOf(data.nodeId)
    if (index > -1) {
      connectedNodes.value.splice(index, 1)
    }
    refreshTopology()
  })

  socket.value.on('phase_update', (data) => {
    currentPhase.value = data.phase
    phaseStep.value = data.step
    refreshTopology()
  })

  socket.value.on('message_received', (message) => {
    receivedMessages.value.unshift({
      ...message,
      id: Date.now() + Math.random(),
      timestamp: new Date()
    })
    
    // 如果是预准备消息，设置接受的值
    if (message.type === 'pre_prepare' && message.from === 0) {
      acceptedValue.value = message.value
    }
    
    refreshTopology()
  })

  socket.value.on('consensus_result', (result) => {
    consensusResult.value = result
    ElMessage.success('共识完成！')
  })

  socket.value.on('error', (error) => {
    ElMessage.error(`错误: ${error.message}`)
  })
}

const leaveSession = async () => {
  try {
    await ElMessageBox.confirm('确定要离开会话吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    if (socket.value) {
      socket.value.disconnect()
    }
    
    router.push('/')
  } catch {
    // 用户取消
  }
}

const sendPrepare = () => {
  if (socket.value) {
    const baseMessage = {
      sessionId,
      nodeId,
      value: acceptedValue.value
    }

    // 应用拜占庭攻击策略
    if (isBadNode.value && attackForm.enabled) {
      if (attackForm.byzantineStrategy === 'targeted') {
        // 针对不同节点发送不同消息
        const messages = sendTargetedMessages(baseMessage)
        messages.forEach(msg => {
          socket.value.emit('send_prepare', msg)
        })
      } else {
        // 应用普通攻击策略
        const message = applyByzantineAttack(baseMessage, attackForm.intensity / 10)
        socket.value.emit('send_prepare', message)
      }
    } else {
      socket.value.emit('send_prepare', baseMessage)
    }
  }
}

const sendCommit = () => {
  if (socket.value) {
    const baseMessage = {
      sessionId,
      nodeId,
      value: acceptedValue.value
    }

    // 应用拜占庭攻击策略
    if (isBadNode.value && attackForm.enabled) {
      if (attackForm.byzantineStrategy === 'targeted') {
        // 针对不同节点发送不同消息
        const messages = sendTargetedMessages(baseMessage)
        messages.forEach(msg => {
          socket.value.emit('send_commit', msg)
        })
      } else {
        // 应用普通攻击策略
        const message = applyByzantineAttack(baseMessage, attackForm.intensity / 10)
        socket.value.emit('send_commit', message)
      }
    } else {
      socket.value.emit('send_commit', baseMessage)
    }
  }
}

const getPhasePercentage = () => {
  return Math.round((phaseStep.value / 4) * 100)
}

const getPhaseStatus = () => {
  if (phaseStep.value === 4) return 'success'
  if (phaseStep.value > 0) return 'warning'
  return ''
}

const getPhaseDisplayName = (phase) => {
  const names = {
    'pre-prepare': '提议阶段',
    'prepare': '准备阶段',
    'commit': '确认阶段',
    'reply': '完成阶段'
  }
  return names[phase] || phase
}

const getMessageTypeName = (type) => {
  const names = {
    'pre-prepare': '提议',
    'prepare': '准备',
    'commit': '确认',
    'reply': '回复'
  }
  return names[type] || type
}

const getAcceptedContentDisplay = () => {
  const proposalContent = sessionConfig.value.proposalContent
  const currentAcceptedValue = acceptedValue.value
  
  console.log('getAcceptedContentDisplay 调用:', {
    acceptedValue: currentAcceptedValue,
    proposalContent: proposalContent,
    proposalContentType: typeof proposalContent,
    proposalContentLength: proposalContent ? proposalContent.length : 0,
    hasProposalContent: proposalContent && proposalContent.trim(),
    sessionConfig: sessionConfig.value
  })
  
  // 如果有提议内容，优先显示提议内容
  if (proposalContent && proposalContent.trim()) {
    console.log('显示提议内容:', proposalContent)
    return proposalContent
  }
  
  // 如果acceptedValue为null，显示未决定
  if (currentAcceptedValue === null) {
    console.log('显示未决定')
    return '未决定'
  }
  
  // 否则显示默认的选项A/B
  const result = currentAcceptedValue === 0 ? '选项A' : '选项B'
  console.log('显示默认选项:', result)
  return result
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const exportMessages = () => {
  const data = receivedMessages.value.map(msg => ({
    时间: formatTime(msg.timestamp),
    来源: `参与者${msg.from}`,
    类型: getMessageTypeName(msg.type),
    内容: msg.value === -1 ? '拒绝' : (msg.value !== null ? (msg.value === 0 ? (sessionConfig.value.proposalContent || '选项A') : (sessionConfig.value.proposalContent || '选项B')) : '无')
  }))
  
  const csv = [
    Object.keys(data[0]).join(','),
    ...data.map(row => Object.values(row).join(','))
  ].join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `messages_${sessionId}_${nodeId}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
  
  ElMessage.success('消息已导出')
}

const clearMessages = () => {
  receivedMessages.value = []
  ElMessage.success('消息已清空')
}

const refreshTopology = () => {
  topologyConnections.value = []
  
  // 根据拓扑结构生成连接
  if (sessionConfig.value.topology === 'full') {
    for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
      for (let j = i + 1; j < sessionConfig.value.nodeCount; j++) {
        // 计算节点中心位置
        const nodeSize = 40
        const x1 = getNodeX(i) + nodeSize / 2
        const y1 = getNodeY(i) + nodeSize / 2
        const x2 = getNodeX(j) + nodeSize / 2
        const y2 = getNodeY(j) + nodeSize / 2
        
        topologyConnections.value.push({
          from: i,
          to: j,
          x1: x1,
          y1: y1,
          x2: x2,
          y2: y2,
          active: connectedNodes.value.includes(i) && connectedNodes.value.includes(j)
        })
      }
    }
  }
}

const getNodeX = (nodeId) => {
  const containerWidth = topologyWidth.value
  const radius = Math.min(containerWidth, topologyHeight.value) / 2.2  // 增大半径，让节点更靠近边缘
  const nodeSize = 40  // 节点尺寸
  
  if (sessionConfig.value.topology === 'full' || sessionConfig.value.topology === 'ring') {
    const angle = (2 * Math.PI * nodeId) / sessionConfig.value.nodeCount
    const centerX = containerWidth / 2 + radius * Math.cos(angle)
    // 调整位置，使节点中心对齐
    return centerX - nodeSize / 2
  }
  
  return (containerWidth / (sessionConfig.value.nodeCount + 1)) * (nodeId + 1) - nodeSize / 2
}

const getNodeY = (nodeId) => {
  const containerHeight = topologyHeight.value
  const radius = Math.min(topologyWidth.value, containerHeight) / 2.2  // 增大半径，让节点更靠近边缘
  const nodeSize = 40  // 节点尺寸
  
  if (sessionConfig.value.topology === 'full' || sessionConfig.value.topology === 'ring') {
    const angle = (2 * Math.PI * nodeId) / sessionConfig.value.nodeCount
    const centerY = containerHeight / 2 + radius * Math.sin(angle)
    // 调整位置，使节点中心对齐
    return centerY - nodeSize / 2
  }
  
  return containerHeight / 2 - nodeSize / 2
}

const isNodeVisible = (nodeId) => {
  return connectedNodes.value.includes(nodeId)
}

const isNodeActive = (nodeId) => {
  return connectedNodes.value.includes(nodeId)
}

const hasNodeMessages = (nodeId) => {
  return receivedMessages.value.some(msg => msg.from === nodeId)
}

const getNodeMessageCount = (nodeId) => {
  return receivedMessages.value.filter(msg => msg.from === nodeId).length
}

const getNodeMessages = (nodeId) => {
  return receivedMessages.value.filter(msg => msg.from === nodeId)
}

const showNodeDetails = (nodeId) => {
  selectedNode.value = nodeId
  nodeDetailsVisible.value = true
}

const getTopologyName = (topology) => {
  const names = {
    full: '全连接',
    ring: '环形',
    star: '星形',
    tree: '树形'
  }
  return names[topology] || topology
}

const getActiveConnections = () => {
  return topologyConnections.value.filter(conn => conn.active).length
}

const getConsensusAlertType = (status) => {
  if (status.includes('成功')) return 'success'
  if (status.includes('失败')) return 'error'
  return 'info'
}

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

// 判断是否为拜占庭节点（基于用户选择）
const isBadNode = computed(() => {
  return attackForm.enabled
})

// 消息发送相关方法（已移除自定义消息功能）

// 应用拜占庭攻击策略
const applyByzantineAttack = (message, intensity) => {
  if (!attackForm.enabled || Math.random() > intensity) return message

  const strategy = attackForm.byzantineStrategy
  let shouldAttack = false
  let attackValue = null

  switch (strategy) {
    case 'always':
      shouldAttack = true
      attackValue = message.value === 0 ? 1 : 0
      break
    case 'sometimes':
      shouldAttack = Math.random() < intensity
      attackValue = message.value === 0 ? 1 : 0
      break
    case 'random':
      shouldAttack = Math.random() < intensity
      attackValue = Math.random() > 0.5 ? 1 : 0
      break
    case 'targeted':
      // 针对不同节点发送不同值的逻辑在发送时处理
      return message
  }

  if (shouldAttack) {
    message.value = attackValue
    message.byzantine = true
    attackStats.byzantineMessages++
    console.log(`🦹 坏节点 ${nodeId} 拜占庭攻击: 发送错误值 ${message.value}`)
  }

  return message
}

// 发送针对特定节点的不同消息
const sendTargetedMessages = (baseMessage) => {
  if (!attackForm.enabled || attackForm.byzantineStrategy !== 'targeted') {
    return [baseMessage]
  }

  const messages = []
  const targetConfigs = attackForm.targetNodes.filter(target => target.nodeId !== null)

  if (targetConfigs.length === 0) {
    // 如果没有配置目标节点，使用默认攻击
    const attackMessage = { ...baseMessage }
    attackMessage.value = baseMessage.value === 0 ? 1 : 0
    attackMessage.byzantine = true
    attackStats.byzantineMessages++
    messages.push(attackMessage)
    return messages
  }

  // 为每个目标节点创建不同的消息
  targetConfigs.forEach(target => {
    const targetMessage = { ...baseMessage }
    if (target.value !== null) {
      targetMessage.value = target.value
    } else {
      // 随机值
      targetMessage.value = Math.random() > 0.5 ? 1 : 0
    }
    targetMessage.byzantine = true
    targetMessage.targetNode = target.nodeId
    attackStats.targetedMessages++
    messages.push(targetMessage)
  })

  // 为未配置的节点发送原始消息
  const configuredNodes = targetConfigs.map(t => t.nodeId)
  const allNodes = Array.from({ length: sessionConfig.value.nodeCount }, (_, i) => i)
  const unconfiguredNodes = allNodes.filter(n => 
    n !== nodeId && !configuredNodes.includes(n)
  )

  if (unconfiguredNodes.length > 0) {
    const originalMessage = { ...baseMessage }
    messages.push(originalMessage)
  }

  console.log(`🦹 坏节点 ${nodeId} 发送针对不同节点的消息:`, messages)
  return messages
}

// 切换攻击模式
const toggleAttackMode = () => {
  if (attackForm.enabled) {
    ElMessage.warning(`🦹 参与者 ${nodeId} 已选择成为拜占庭节点`)
  } else {
    ElMessage.info(`🦹 参与者 ${nodeId} 已停止拜占庭攻击`)
  }
}

// 添加目标节点
const addTargetNode = () => {
  attackForm.targetNodes.push({
    nodeId: null,
    value: null
  })
}

// 移除目标节点
const removeTargetNode = (index) => {
  attackForm.targetNodes.splice(index, 1)
}

// 清空目标节点配置
const clearTargetNodes = () => {
  attackForm.targetNodes = []
}

// 更新可用目标节点列表
const updateAvailableTargetNodes = () => {
  availableTargetNodes.value = Array.from({ length: sessionConfig.value.nodeCount }, (_, i) => i)
}

// 生命周期
onMounted(() => {
  connectToServer()
  updateAvailableTargetNodes()
})

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect()
  }
})
</script>

<style scoped>
.node-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  color: white;
}

.node-info h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 300;
}

.session-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.main-content {
  padding: 20px;
}

.progress-card, .messages-card, .topology-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #2c3e50;
}

.consensus-progress {
  padding: 10px 0;
}

.phase-progress {
  margin-bottom: 20px;
}

.phase-steps {
  margin-top: 15px;
}

.current-status {
  margin-bottom: 20px;
}

.current-status h4 {
  margin-bottom: 10px;
  color: #2c3e50;
}

.quick-actions {
  margin-top: 20px;
}

.quick-actions h4 {
  margin-bottom: 10px;
  color: #2c3e50;
}

.quick-actions-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-action-btn {
  width: 100%;
}

.proposer-info {
  margin-top: 10px;
  text-align: center;
}

/* 拜占庭节点标识 */
.node-info h2.bad-node {
  color: #f56c6c;
  position: relative;
}

.node-info h2.bad-node::after {
  content: '🦹';
  position: absolute;
  right: -25px;
  top: 0;
  font-size: 16px;
}

/* 消息发送表单 */
.message-form {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.message-form h4 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

/* 攻击控制区域样式 */
.attack-control {
  margin-top: 20px;
  padding: 15px;
  border: 2px solid #f56c6c;
  border-radius: 8px;
  background: linear-gradient(135deg, #fff5f5 0%, #fef0f0 100%);
  position: relative;
}

.attack-control::before {
  content: '⚠️';
  position: absolute;
  top: -10px;
  left: 15px;
  background: #fff;
  padding: 0 8px;
  font-size: 16px;
}

.attack-control h4 {
  color: #f56c6c;
  margin: 0 0 15px 0;
  font-weight: bold;
}

.attack-control .el-form-item {
  margin-bottom: 12px;
}

.attack-control .el-slider {
  margin-top: 5px;
}

.attack-control .el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attack-stats {
  margin-top: 15px;
  padding: 10px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 4px;
  border-left: 3px solid #f56c6c;
}

.attack-stats h5 {
  margin: 0 0 10px 0;
  font-size: 13px;
}

.attack-stats .el-descriptions {
  font-size: 12px;
}

.attack-stats .el-descriptions-item__label {
  color: #f56c6c;
  font-weight: bold;
}

.attack-stats .el-descriptions-item__content {
  color: #303133;
  font-weight: bold;
}

.messages-container {
  height: 400px;
  overflow-y: auto;
}

.messages-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: 600;
  color: #2c3e50;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-item-compact {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 10px;
  border-left: 3px solid #409eff;
}

.message-header-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
  color: #606266;
}

.message-content-compact {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
}

.message-type {
  font-weight: 600;
  color: #409eff;
}

.message-value {
  color: #2c3e50;
}

.no-messages {
  text-align: center;
  padding: 40px 0;
}

.dynamic-topology {
  padding: 10px 0;
}

.topology-info {
  margin-bottom: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.topology-info p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.topology-container {
  position: relative;
  width: 100%;
  height: 400px;
  background: #f8f9fa;
  border-radius: 10px;
  margin-bottom: 20px;
}

.connection-lines {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
}

.active-connection {
  stroke: #67c23a;
  stroke-width: 2;
}

.inactive-connection {
  stroke: #dcdfe6;
  stroke-width: 1;
}

.topology-node {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  cursor: pointer;
  z-index: 2;
  transition: all 0.3s ease;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.topology-node:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.topology-node.current-node {
  background: #67c23a;
  border-color: #67c23a;
}

.topology-node.proposer {
  background: #e6a23c;
  border-color: #e6a23c;
}

.topology-node.visible-node {
  opacity: 1;
}

.topology-node.invisible-node {
  opacity: 0.3;
}

.topology-node.has-messages {
  border-color: #f56c6c;
}

.topology-node.active {
  animation: pulse 2s infinite;
}

.node-number {
  font-size: 14px;
  font-weight: 600;
}

.node-status-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background: #67c23a;
  border-radius: 50%;
  border: 1px solid white;
}

.message-count {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #f56c6c;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid white;
}

.consensus-result-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.consensus-stats {
  margin-top: 15px;
}

.consensus-stat-item {
  text-align: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.consensus-stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 5px;
}

.consensus-stat-label {
  font-size: 12px;
  color: #606266;
}

.consensus-no-result {
  text-align: center;
  padding: 40px 0;
}

.node-messages {
  max-height: 300px;
  overflow-y: auto;
}

.message-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  border-left: 3px solid #409eff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
  color: #606266;
}

.message-content {
  font-size: 13px;
  color: #2c3e50;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(64, 158, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0);
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 10px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 10px;
  }
  
  .node-info h2 {
    font-size: 1.2rem;
  }
}
</style> 