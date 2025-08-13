<template>
  <div class="node-page">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <div class="node-info">
            <h2 :class="{ 'bad-node': attackForm.enabled }">Participant {{ nodeId }}</h2>
            <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'">
              {{ connectionStatus === 'connected' ? 'Connected' : 'Disconnected' }}
            </el-tag>
            <el-tag v-if="attackForm.enabled" type="danger" effect="dark">🦹 Byzantine Node</el-tag>
          </div>
          <div class="session-info">
            <span>Session: {{ sessionId }}</span>
            <el-button size="small" @click="leaveSession" type="danger">Leave Session</el-button>
          </div>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <el-row :gutter="20">
          <!-- Left: Consensus Progress -->
          <el-col :span="6">
            <el-card class="progress-card">
              <template #header>
                <div class="card-header">
                  <span>Consensus Progress</span>
                </div>
              </template>
              
              <div class="consensus-progress">
                <!-- Consensus Progress Bar -->
                <div class="phase-progress">
                  <el-progress 
                    :percentage="getPhasePercentage()" 
                    :status="getPhaseStatus()"
                    :stroke-width="8"
                  />
                  <div class="phase-steps">
                    <el-steps :active="phaseStep" finish-status="success" simple>
                      <el-step title="Propose" description="Initiate proposal" />
                      <el-step title="Prepare" description="Validate proposal" />
                      <el-step title="Commit" description="Confirm proposal" />
                      <el-step title="Complete" description="Reach consensus" />
                    </el-steps>
                  </div>
                </div>
                
                <!-- Current Status -->
                <div class="current-status">
                  <h4>Current Status</h4>
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="Current Phase">{{ getPhaseDisplayName(currentPhase) }}</el-descriptions-item>
                    <el-descriptions-item label="Accepted Content">{{ getAcceptedContentDisplay() }}</el-descriptions-item>
                    <el-descriptions-item label="Network Reliability">{{ sessionConfig.messageDeliveryRate ?? 'Not Set' }}%</el-descriptions-item>
                  </el-descriptions>
                </div>
                
                <!-- Quick Actions -->
                <!-- Validator Quick Actions -->
                <div class="quick-actions" v-if="isMyTurn">
                  <h4>Quick Actions</h4>
                  <div class="quick-actions-buttons">
                    <el-button 
                      type="primary" 
                      @click="sendPrepare" 
                      :disabled="currentPhase !== 'prepare'"
                      class="quick-action-btn"
                    >
                      Send Prepare Message
                    </el-button>
                    <el-button 
                      type="success" 
                      @click="sendCommit" 
                      :disabled="currentPhase !== 'commit'"
                      class="quick-action-btn"
                    >
                      Send Commit Message
                    </el-button>
                  </div>
                </div>

                <!-- Proposer Quick Actions -->
                <div class="quick-actions" v-if="canProposerSendCustom">
                  <h4>Proposer Actions</h4>
                  <div class="quick-actions-buttons">
                    <el-button 
                      type="success" 
                      @click="sendCommit" 
                      :disabled="currentPhase !== 'commit'"
                      class="quick-action-btn"
                    >
                      Send Commit Message
                    </el-button>
                    <div class="proposer-info">
                      <el-tag type="info" size="small">Proposer doesn't send prepare messages, but can send commit messages</el-tag>
                    </div>
                  </div>
                </div>



                <!-- Byzantine Attack Control Area -->
                <div class="attack-control">
                  <el-divider content-position="left">
                    <span style="color: #f56c6c; font-weight: bold;">🦹 Byzantine Attack Control</span>
                  </el-divider>
                  
                  <el-form :model="attackForm" label-width="100px" size="small">
                    <el-form-item label="Become Byzantine Node">
                      <el-switch 
                        v-model="attackForm.enabled" 
                        active-text="Yes"
                        inactive-text="No"
                        @change="toggleAttackMode"
                      />
                      <span class="form-tip">Choose whether to become a Byzantine node for attacks</span>
                    </el-form-item>

                    <el-form-item v-if="attackForm.enabled" label="Attack Intensity">
                      <el-slider 
                        v-model="attackForm.intensity" 
                        :min="1" 
                        :max="10" 
                        :step="1"
                        show-stops
                        show-input
                      />
                    </el-form-item>

                    <el-form-item v-if="attackForm.enabled" label="Attack Strategy">
                      <el-radio-group v-model="attackForm.byzantineStrategy">
                        <el-radio label="always">Always send incorrect values</el-radio>
                        <el-radio label="sometimes">Sometimes send incorrect values</el-radio>
                        <el-radio label="random">Randomly send different values</el-radio>
                        <el-radio label="targeted">Send different values to different nodes</el-radio>
                      </el-radio-group>
                    </el-form-item>

                    <el-form-item v-if="attackForm.enabled && attackForm.byzantineStrategy === 'targeted'" label="Target Node Configuration">
                      <div style="margin-bottom: 10px;">
                        <el-button size="small" @click="addTargetNode">Add Target Node</el-button>
                        <el-button size="small" @click="clearTargetNodes">Clear Configuration</el-button>
                      </div>
                      <div v-for="(target, index) in attackForm.targetNodes" :key="index" style="margin-bottom: 8px;">
                        <el-row :gutter="10">
                          <el-col :span="8">
                            <el-select v-model="target.nodeId" placeholder="Select Node" size="small">
                              <el-option 
                                v-for="nodeId in availableTargetNodes" 
                                :key="nodeId" 
                                :label="`Node ${nodeId}`" 
                                :value="nodeId"
                              />
                            </el-select>
                          </el-col>
                          <el-col :span="8">
                            <el-select v-model="target.value" placeholder="Send Value" size="small">
                              <el-option label="0" :value="0" />
                              <el-option label="1" :value="1" />
                              <el-option label="Random" :value="null" />
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
                        {{ attackForm.enabled ? 'Stop Byzantine Attack' : 'Start Byzantine Attack' }}
                      </el-button>
                    </el-form-item>
                  </el-form>

                  <!-- Attack Statistics -->
                  <div class="attack-stats" v-if="attackForm.enabled">
                    <h5 style="color: #f56c6c; margin: 10px 0;">Byzantine Attack Effect Statistics</h5>
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="Incorrect Messages">{{ attackStats.byzantineMessages }}</el-descriptions-item>
                      <el-descriptions-item label="Targeted Attacks">{{ attackStats.targetedMessages }}</el-descriptions-item>
                    </el-descriptions>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- Middle: Received Messages -->
          <el-col :span="6">
            <el-card class="messages-card">
              <template #header>
                <div class="card-header">
                  <span>Received Messages</span>
                  <div>
                    <el-button size="small" @click="exportMessages">Export</el-button>
                    <el-button size="small" @click="clearMessages">Clear</el-button>
                  </div>
                </div>
              </template>
              
              <div class="messages-container">
                <div class="messages-header">
                  <span>Message Count: {{ receivedMessages.length }}</span>
                </div>
                
                <div class="message-list">
                  <div 
                    v-for="msg in receivedMessages.slice(0, 8)" 
                    :key="msg.id"
                    class="message-item-compact"
                  >
                    <div class="message-header-compact">
                      <span class="message-from">From: Participant{{ msg.from }}</span>
                      <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
                    </div>
                    <div class="message-content-compact">
                      <span class="message-type">{{ getMessageTypeName(msg.type) }}</span>
                      <span class="message-value" v-if="msg.value !== null">
                        Content: {{ msg.value === -1 ? 'Reject' : (msg.value === 0 ? 'Option A' : 'Option B') }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div v-if="receivedMessages.length === 0" class="no-messages">
                  <el-empty description="No messages yet" :image-size="60" />
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- Right: Topology and Consensus Results -->
          <el-col :span="12">
            <!-- Topology -->
            <el-card class="topology-card">
              <template #header>
                <div class="card-header">
                  <span>Network Topology Map</span>
                  <el-button size="small" @click="refreshTopology">Refresh</el-button>
                </div>
              </template>
              
              <div class="dynamic-topology">
                <div class="topology-info">
                  <p><strong>Network Type:</strong> {{ getTopologyName(sessionConfig.topology) }}</p>
                  <p><strong>Total Participants:</strong> {{ sessionConfig.nodeCount }}</p>
                  <p><strong>Active Connections:</strong> {{ getActiveConnections() }}</p>
                </div>
                
                <!-- Topology Container -->
                <div class="topology-container">
                  <!-- Connection Lines -->
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
                  
                  <!-- Nodes -->
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
                
                <!-- Consensus Results -->
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
                            <div class="consensus-stat-label">Option A (Nodes)</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.falsehood }}</div>
                            <div class="consensus-stat-label">Option B (Nodes)</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.rejected }}</div>
                            <div class="consensus-stat-label">Rejected (Nodes)</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.prepare_nodes }}/{{ consensusResult.stats.expected_prepare_nodes || consensusResult.stats.expected_nodes - 1 }}</div>
                            <div class="consensus-stat-label">Prepare Phase Participants</div>
                          </div>
                        </el-col>
                      </el-row>
                      <el-row :gutter="20" style="margin-top: 10px;">
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.commit_nodes }}/{{ consensusResult.stats.expected_nodes }}</div>
                            <div class="consensus-stat-label">Commit Phase Participants</div>
                          </div>
                        </el-col>
                        <el-col :span="6">
                          <div class="consensus-stat-item">
                            <div class="consensus-stat-number">{{ consensusResult.stats.total_messages }}</div>
                            <div class="consensus-stat-label">Total Messages</div>
                          </div>
                        </el-col>
                      </el-row>
                    </div>
                  </div>
                  <div v-else class="consensus-no-result">
                    <el-empty description="Consensus not yet completed" :image-size="60" />
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
    
    <!-- Node Details Dialog -->
    <el-dialog v-model="nodeDetailsVisible" title="Participant Details" width="500px">
      <div v-if="selectedNode !== null">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Participant ID">{{ selectedNode }}</el-descriptions-item>
          <el-descriptions-item label="Connection Status">
            <el-tag :type="connectedNodes.includes(selectedNode) ? 'success' : 'danger'">
              {{ connectedNodes.includes(selectedNode) ? 'Connected' : 'Disconnected' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Role">{{ selectedNode === 0 ? 'Proposer' : 'Validator' }}</el-descriptions-item>
          <el-descriptions-item label="Message Count">{{ getNodeMessageCount(selectedNode) }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="node-messages" style="margin-top: 20px;">
          <h4>Messages from this participant</h4>
          <div v-for="msg in getNodeMessages(selectedNode)" :key="msg.id" class="message-item">
            <div class="message-header">
              <span>{{ getMessageTypeName(msg.type) }}</span>
              <span>{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div class="message-content">
              Content: {{ msg.value === -1 ? 'Reject' : (msg.value !== null ? (msg.value === 0 ? (sessionConfig.proposalContent || 'Option A') : (sessionConfig.proposalContent || 'Option B')) : 'None') }}
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

// Route parameters
const sessionId = route.params.sessionId
const nodeId = parseInt(route.params.nodeId)

// Reactive data
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

// Topology related
const topologyWidth = ref(500)
const topologyHeight = ref(400)
const topologyConnections = ref([])

// Message sending form (custom message functionality removed)
const messageForm = reactive({
  type: 'prepare',
  value: 0,
  target: 'all'
})

// Byzantine node attack control form
const attackForm = reactive({
  enabled: false,
  intensity: 5,
  byzantineStrategy: 'sometimes',
  targetNodes: []
})

// Attack statistics
const attackStats = reactive({
  byzantineMessages: 0,
  targetedMessages: 0
})

// Available target nodes list
const availableTargetNodes = ref([])

// Methods
const connectToServer = () => {
  socket.value = io(window.location.origin, {
    query: {
      sessionId,
      nodeId
    }
  })

  socket.value.on('connect', () => {
    connectionStatus.value = 'connected'
    ElMessage.success('Connected successfully')
  })

  socket.value.on('disconnect', () => {
    connectionStatus.value = 'disconnected'
    ElMessage.warning('Connection disconnected')
  })

  socket.value.on('session_config', (config) => {
    console.log('Received session config:', config)
    console.log('Proposal content check:', {
      proposalContent: config.proposalContent,
      hasProposalContent: config.proposalContent && config.proposalContent.trim(),
      proposalValue: config.proposalValue
    })
    
    // Merge configuration, ensure all fields exist
    sessionConfig.value = {
      ...sessionConfig.value,
      ...config
    }
    console.log('Merged configuration:', sessionConfig.value)
    console.log('Final proposalContent:', sessionConfig.value.proposalContent)
    
    // Set accepted value to proposal value
    acceptedValue.value = config.proposalValue
    console.log('Set acceptedValue:', acceptedValue.value)
    
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
    
    // If it's a pre-prepare message, set the accepted value
    if (message.type === 'pre_prepare' && message.from === 0) {
      acceptedValue.value = message.value
    }
    
    refreshTopology()
  })

  socket.value.on('consensus_result', (result) => {
    consensusResult.value = result
    ElMessage.success('Consensus completed!')
  })

  socket.value.on('error', (error) => {
    ElMessage.error(`Error: ${error.message}`)
  })
}

const leaveSession = async () => {
  try {
    await ElMessageBox.confirm('Are you sure you want to leave the session?', 'Confirm', {
      confirmButtonText: 'Confirm',
      cancelButtonText: 'Cancel',
      type: 'warning'
    })
    
    if (socket.value) {
      socket.value.disconnect()
    }
    
    router.push('/')
  } catch {
    // User cancelled
  }
}

const sendPrepare = () => {
  if (socket.value) {
    const baseMessage = {
      sessionId,
      nodeId,
      value: acceptedValue.value
    }

    // Apply Byzantine attack strategy
    if (isBadNode.value && attackForm.enabled) {
      if (attackForm.byzantineStrategy === 'targeted') {
        // Send different messages to different nodes
        const messages = sendTargetedMessages(baseMessage)
        messages.forEach(msg => {
          socket.value.emit('send_prepare', msg)
        })
      } else {
        // Apply normal attack strategy
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

    // Apply Byzantine attack strategy
    if (isBadNode.value && attackForm.enabled) {
      if (attackForm.byzantineStrategy === 'targeted') {
        // Send different messages to different nodes
        const messages = sendTargetedMessages(baseMessage)
        messages.forEach(msg => {
          socket.value.emit('send_commit', msg)
        })
      } else {
        // Apply normal attack strategy
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
    'pre-prepare': 'Propose Phase',
    'prepare': 'Prepare Phase',
    'commit': 'Commit Phase',
    'reply': 'Complete Phase'
  }
  return names[phase] || phase
}

const getMessageTypeName = (type) => {
  const names = {
    'pre-prepare': 'Propose',
    'prepare': 'Prepare',
    'commit': 'Commit',
    'reply': 'Reply'
  }
  return names[type] || type
}

const getAcceptedContentDisplay = () => {
  const proposalContent = sessionConfig.value.proposalContent
  const currentAcceptedValue = acceptedValue.value
  
  console.log('getAcceptedContentDisplay called:', {
    acceptedValue: currentAcceptedValue,
    proposalContent: proposalContent,
    proposalContentType: typeof proposalContent,
    proposalContentLength: proposalContent ? proposalContent.length : 0,
    hasProposalContent: proposalContent && proposalContent.trim(),
    sessionConfig: sessionConfig.value
  })
  
  // If there's proposal content, prioritize displaying it
  if (proposalContent && proposalContent.trim()) {
    console.log('Display proposal content:', proposalContent)
    return proposalContent
  }
  
  // If acceptedValue is null, display undecided
  if (currentAcceptedValue === null) {
    console.log('Display undecided')
    return 'Undecided'
  }
  
  // Otherwise display default Option A/B
  const result = currentAcceptedValue === 0 ? 'Option A' : 'Option B'
  console.log('Display default option:', result)
  return result
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const exportMessages = () => {
  const data = receivedMessages.value.map(msg => ({
    Time: formatTime(msg.timestamp),
    Source: `Participant${msg.from}`,
    Type: getMessageTypeName(msg.type),
    Content: msg.value === -1 ? 'Reject' : (msg.value !== null ? (msg.value === 0 ? (sessionConfig.value.proposalContent || 'Option A') : (sessionConfig.value.proposalContent || 'Option B')) : 'None')
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
  
  ElMessage.success('Messages exported')
}

const clearMessages = () => {
  receivedMessages.value = []
  ElMessage.success('Messages cleared')
}

const refreshTopology = () => {
  topologyConnections.value = []
  
  // Generate connections based on topology
  if (sessionConfig.value.topology === 'full') {
    for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
      for (let j = i + 1; j < sessionConfig.value.nodeCount; j++) {
        // Calculate node center position
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
  const radius = Math.min(containerWidth, topologyHeight.value) / 2.2  // Increase radius to bring nodes closer to edge
  const nodeSize = 40  // Node size
  
  if (sessionConfig.value.topology === 'full' || sessionConfig.value.topology === 'ring') {
    const angle = (2 * Math.PI * nodeId) / sessionConfig.value.nodeCount
    const centerX = containerWidth / 2 + radius * Math.cos(angle)
    // Adjust position to center-align nodes
    return centerX - nodeSize / 2
  }
  
  return (containerWidth / (sessionConfig.value.nodeCount + 1)) * (nodeId + 1) - nodeSize / 2
}

const getNodeY = (nodeId) => {
  const containerHeight = topologyHeight.value
  const radius = Math.min(topologyWidth.value, containerHeight) / 2.2  // Increase radius to bring nodes closer to edge
  const nodeSize = 40  // Node size
  
  if (sessionConfig.value.topology === 'full' || sessionConfig.value.topology === 'ring') {
    const angle = (2 * Math.PI * nodeId) / sessionConfig.value.nodeCount
    const centerY = containerHeight / 2 + radius * Math.sin(angle)
    // Adjust position to center-align nodes
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
    full: 'Full Connected',
    ring: 'Ring',
    star: 'Star',
    tree: 'Tree'
  }
  return names[topology] || topology
}

const getActiveConnections = () => {
  return topologyConnections.value.filter(conn => conn.active).length
}

const getConsensusAlertType = (status) => {
  if (status.includes('Success')) return 'success'
  if (status.includes('Failed')) return 'error'
  return 'info'
}

const isMyTurn = computed(() => {
  // Proposer (node 0) doesn't send prepare messages, but can send commit messages
  if (nodeId === 0) {
    return currentPhase.value === 'commit'  // Proposer can send commit messages
  }
  return currentPhase.value === 'prepare' || currentPhase.value === 'commit'
})

// Whether proposer can send messages
const canProposerSendCustom = computed(() => {
  return nodeId === 0
})

// Determine if it's a Byzantine node (based on user choice)
const isBadNode = computed(() => {
  return attackForm.enabled
})

// Message sending related methods (custom message functionality removed)

// Apply Byzantine attack strategy
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
      // Logic for sending different values to different nodes is handled during sending
      return message
  }

  if (shouldAttack) {
    message.value = attackValue
    message.byzantine = true
    attackStats.byzantineMessages++
    console.log(`🦹 Byzantine node ${nodeId} attack: sending incorrect value ${message.value}`)
  }

  return message
}

// Send different messages to specific nodes
const sendTargetedMessages = (baseMessage) => {
  if (!attackForm.enabled || attackForm.byzantineStrategy !== 'targeted') {
    return [baseMessage]
  }

  const messages = []
  const targetConfigs = attackForm.targetNodes.filter(target => target.nodeId !== null)

  if (targetConfigs.length === 0) {
    // If no target nodes configured, use default attack
    const attackMessage = { ...baseMessage }
    attackMessage.value = baseMessage.value === 0 ? 1 : 0
    attackMessage.byzantine = true
    attackStats.byzantineMessages++
    messages.push(attackMessage)
    return messages
  }

  // Create different messages for each target node
  targetConfigs.forEach(target => {
    const targetMessage = { ...baseMessage }
    if (target.value !== null) {
      targetMessage.value = target.value
    } else {
      // Random value
      targetMessage.value = Math.random() > 0.5 ? 1 : 0
    }
    targetMessage.byzantine = true
    targetMessage.targetNode = target.nodeId
    attackStats.targetedMessages++
    messages.push(targetMessage)
  })

  // Send original message to unconfigured nodes
  const configuredNodes = targetConfigs.map(t => t.nodeId)
  const allNodes = Array.from({ length: sessionConfig.value.nodeCount }, (_, i) => i)
  const unconfiguredNodes = allNodes.filter(n => 
    n !== nodeId && !configuredNodes.includes(n)
  )

  if (unconfiguredNodes.length > 0) {
    const originalMessage = { ...baseMessage }
    messages.push(originalMessage)
  }

  console.log(`🦹 Byzantine node ${nodeId} sending targeted messages:`, messages)
  return messages
}

// Toggle attack mode
const toggleAttackMode = () => {
  if (attackForm.enabled) {
    ElMessage.warning(`🦹 Participant ${nodeId} has chosen to become a Byzantine node`)
  } else {
    ElMessage.info(`🦹 Participant ${nodeId} has stopped Byzantine attacks`)
  }
}

// Add target node
const addTargetNode = () => {
  attackForm.targetNodes.push({
    nodeId: null,
    value: null
  })
}

// Remove target node
const removeTargetNode = (index) => {
  attackForm.targetNodes.splice(index, 1)
}

// Clear target node configuration
const clearTargetNodes = () => {
  attackForm.targetNodes = []
}

// Update available target nodes list
const updateAvailableTargetNodes = () => {
  availableTargetNodes.value = Array.from({ length: sessionConfig.value.nodeCount }, (_, i) => i)
}

// Lifecycle
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

/* Byzantine node identifier */
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

/* Message sending form */
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

/* Attack control area styles */
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