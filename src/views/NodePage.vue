<template>
  <div class="node-page">
    <el-container>
      <el-main class="main-content">
        <!-- Session Info Card Row -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="session-info-card">
              <div class="info-section">
                <h2>Participant {{ nodeId }}</h2>
                <div class="tags-group">
                  <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'" size="small">
                    {{ connectionStatus === 'connected' ? 'Connected' : 'Disconnected' }}
                  </el-tag>
                  <el-tag type="danger" effect="dark" size="small">🦹 Byzantine Node (Human Player)</el-tag>
                </div>
              </div>
              <div class="info-section">
                <div class="session-details">
                  <span class="session-id">Session: {{ sessionId }}</span>
                </div>
                <el-button 
                  size="small" 
                  @click="leaveSession" 
                  type="danger" 
                  style="width: 100%; margin-top: 8px; background-color: #ef4444 !important; border-color: #ef4444 !important; color: white !important;"
                >
                  Leave Session
                </el-button>
              </div>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <!-- Left: Consensus Progress -->
          <el-col :xs="24" :sm="12" :md="6">
            <!-- Advanced Options Toggle -->
            <div style="margin-bottom: 15px;">
              <button
                @click="showAdvancedOptions = !showAdvancedOptions"
                class="advanced-options-toggle"
              >
                {{ showAdvancedOptions ? 'Hide Advanced Options' : 'Show Advanced Options' }}
              </button>
            </div>
            
            <el-card class="progress-card">
              <template #header>
                <div class="card-header">
                  <span>Consensus Progress</span>
                  <el-tag type="primary" size="large" effect="dark">Round {{ currentRound }}</el-tag>
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
                      <el-step title="Propose" description="Initiate Proposal" />
                      <el-step title="Prepare" description="Validate Proposal" />
                      <el-step title="Commit" description="Confirm Proposal" />
                      <el-step title="Complete" description="Reach Consensus" />
                    </el-steps>
                  </div>
                </div>
                
                <!-- Current Status -->
                <div class="current-status">
                  <h4>Current Status</h4>
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="Current Phase">{{ getPhaseDisplayName(currentPhase) }}</el-descriptions-item>
                    <el-descriptions-item label="Accepted Content">{{ getAcceptedContentDisplay() }}</el-descriptions-item>
                    <el-descriptions-item label="Network Reliability">{{ sessionConfig.messageDeliveryRate ?? '未设置' }}%</el-descriptions-item>
                  </el-descriptions>
                </div>
                
                <!-- Human Node Actions -->
                <div class="human-node-actions">
                  <h4>Operation Selection</h4>
                  
                  <!-- 等待下一轮共识 -->
                  <div v-if="waitingForNextRound">
                    <el-alert
                      title="Waiting for Next Round to Start"
                      description="You joined in current round, will participate when next round starts. Please wait..."
                      type="info"
                      :closable="false"
                      show-icon
                    />
                  </div>
                  
                  <!-- 可以选择操作 -->
                  <div v-else>
                    <div class="action-buttons" style="display: flex; flex-direction: column; align-items: stretch; gap: 12px;">
                      <!-- 正常共识按钮 -->
                      <button
                        @click="chooseNormalConsensus"
                        :disabled="hasChosenAction"
                        class="bg-green-100 dark:bg-green-900 border-l-4 border-green-500 dark:border-green-700 text-green-900 dark:text-green-100 p-3 rounded-lg flex items-center transition duration-300 ease-in-out hover:bg-green-200 dark:hover:bg-green-800 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                      >
                        <svg
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          fill="none"
                          class="h-5 w-5 flex-shrink-0 mr-2 text-green-600"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            stroke-width="2"
                            stroke-linejoin="round"
                            stroke-linecap="round"
                          ></path>
                        </svg>
                        <span class="text-sm font-semibold flex-1 text-left">
                          {{ hasChosenAction && isNormalMode ? '✓ Normal Consensus Selected (Robot Proxy)' : 'Normal Consensus' }}
                        </span>
                      </button>
                      
                      <!-- 拜占庭攻击按钮 -->
                      <button
                        @click="chooseByzantineAttack"
                        :disabled="hasChosenAction"
                        class="bg-red-100 dark:bg-red-900 border-l-4 border-red-500 dark:border-red-700 text-red-900 dark:text-red-100 p-3 rounded-lg flex items-center transition duration-300 ease-in-out hover:bg-red-200 dark:hover:bg-red-800 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                      >
                        <svg
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          fill="none"
                          class="h-5 w-5 flex-shrink-0 mr-2 text-red-600"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            stroke-width="2"
                            stroke-linejoin="round"
                            stroke-linecap="round"
                          ></path>
                        </svg>
                        <span class="text-sm font-semibold flex-1 text-left">
                          {{ hasChosenAction && !isNormalMode ? '✓ Byzantine Attack Selected' : 'Byzantine Attack' }}
                        </span>
                      </button>
                    </div>
                    <div class="action-tip" style="margin-top: 10px;">
                      <el-alert
                        v-if="!hasChosenAction"
                        title="Please Select Operation Mode for This Round"
                        description="After selecting normal consensus, robot will execute correct PBFT process for you; after selecting Byzantine attack, you can manually send incorrect messages."
                        type="info"
                        :closable="false"
                      />
                      <el-alert
                        v-if="hasChosenAction && isNormalMode"
                        title="Robot Proxy Mode"
                        description="Robot is executing correct PBFT process for you, no action needed."
                        type="success"
                        :closable="false"
                      />
                      <el-alert
                        v-if="hasChosenAction && !isNormalMode"
                        title="Byzantine Attack Mode"
                        description="You can send incorrect messages at appropriate time to disrupt consensus."
                        type="warning"
                        :closable="false"
                      />
                    </div>
                  </div>
                </div>



                <!-- Byzantine Attack Control Area (only show when Byzantine mode chosen) -->
                <div class="attack-control" v-if="hasChosenAction && !isNormalMode">
                  <el-divider content-position="left">
                    <span style="color: #f56c6c; font-weight: bold;">🦹 Byzantine Attack Actions</span>
                  </el-divider>
                  
                  <div class="simple-attack-control space-y-3">
                    <!-- 发送错误信息按钮 -->
                    <button
                      @click="sendErrorMessage"
                      class="w-full bg-red-100 dark:bg-red-900 border-l-4 border-red-500 dark:border-red-700 text-red-900 dark:text-red-100 p-3 rounded-lg flex items-center transition duration-300 ease-in-out hover:bg-red-200 dark:hover:bg-red-800 transform hover:scale-105"
                    >
                      <svg
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        fill="none"
                        class="h-5 w-5 flex-shrink-0 mr-2 text-red-600"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M6 18L18 6M6 6l12 12"
                          stroke-width="2"
                          stroke-linejoin="round"
                          stroke-linecap="round"
                        ></path>
                      </svg>
                      <span class="text-sm font-semibold">Send Error Message</span>
                    </button>
                    
                    <!-- 差异化消息按钮 -->
                    <button
                      @click="sendRandomDifferentialMessage"
                      class="w-full bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 dark:border-yellow-700 text-yellow-900 dark:text-yellow-100 p-3 rounded-lg flex items-center transition duration-300 ease-in-out hover:bg-yellow-200 dark:hover:bg-yellow-800 transform hover:scale-105"
                    >
                      <svg
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        fill="none"
                        class="h-5 w-5 flex-shrink-0 mr-2 text-yellow-600"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M13 10V3L4 14h7v7l9-11h-7z"
                          stroke-width="2"
                          stroke-linejoin="round"
                          stroke-linecap="round"
                        ></path>
                      </svg>
                      <span class="text-sm font-semibold">🎲 Send Differential Message (Random)</span>
                    </button>
                  </div>
                  
                  <!-- Message Reliability Control -->
                  <el-divider content-position="left" style="margin-top: 20px;">
                    <span style="color: #409eff; font-weight: bold;">📡 Message Reliability Control</span>
                  </el-divider>
                  
                  <div class="reliability-control">
                    <button
                      @click="showReliabilityMatrix = !showReliabilityMatrix"
                      class="w-full mb-3 bg-blue-100 dark:bg-blue-900 border-l-4 border-blue-500 dark:border-blue-700 text-blue-900 dark:text-blue-100 p-3 rounded-lg flex items-center transition duration-300 ease-in-out hover:bg-blue-200 dark:hover:bg-blue-800 transform hover:scale-105"
                    >
                      <svg
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        fill="none"
                        class="h-5 w-5 flex-shrink-0 mr-2 text-blue-600"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M13 16h-1v-4h1m0-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          stroke-width="2"
                          stroke-linejoin="round"
                          stroke-linecap="round"
                        ></path>
                      </svg>
                      <span class="text-sm font-semibold">
                        {{ showReliabilityMatrix ? 'Hide Reliability Matrix' : 'Show Reliability Matrix' }}
                      </span>
                    </button>
                    
                    <div v-if="showReliabilityMatrix" class="reliability-matrix">
                      <div class="quick-set mb-4">
                        <div class="text-xs text-gray-600 dark:text-gray-400 mb-2 font-medium">Quick Set:</div>
                        <div class="grid grid-cols-4 gap-2">
                          <button
                            @click="setAllReliability(100)"
                            class="bg-green-100 dark:bg-green-900 border-l-2 border-green-500 dark:border-green-700 text-green-900 dark:text-green-100 px-3 py-2 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-green-200 dark:hover:bg-green-800 transform hover:scale-105"
                          >
                            <span class="text-xs font-semibold">100%</span>
                          </button>
                          <button
                            @click="setAllReliability(75)"
                            class="bg-blue-100 dark:bg-blue-900 border-l-2 border-blue-500 dark:border-blue-700 text-blue-900 dark:text-blue-100 px-3 py-2 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-blue-200 dark:hover:bg-blue-800 transform hover:scale-105"
                          >
                            <span class="text-xs font-semibold">75%</span>
                          </button>
                          <button
                            @click="setAllReliability(50)"
                            class="bg-yellow-100 dark:bg-yellow-900 border-l-2 border-yellow-500 dark:border-yellow-700 text-yellow-900 dark:text-yellow-100 px-3 py-2 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-yellow-200 dark:hover:bg-yellow-800 transform hover:scale-105"
                          >
                            <span class="text-xs font-semibold">50%</span>
                          </button>
                          <button
                            @click="setAllReliability(0)"
                            class="bg-red-100 dark:bg-red-900 border-l-2 border-red-500 dark:border-red-700 text-red-900 dark:text-red-100 px-3 py-2 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-red-200 dark:hover:bg-red-800 transform hover:scale-105"
                          >
                            <span class="text-xs font-semibold">0%</span>
                          </button>
                        </div>
                      </div>
                      
                      <div class="reliability-items">
                        <div 
                          v-for="targetNode in Object.keys(reliabilityConfig)" 
                          :key="targetNode"
                          class="reliability-item"
                        >
                          <div class="reliability-label">
                            <span>→ 节点{{ targetNode }}</span>
                            <span class="reliability-value">{{ reliabilityConfig[targetNode] }}%</span>
                          </div>
                          <el-slider 
                            v-model="reliabilityConfig[targetNode]" 
                            :min="0" 
                            :max="100" 
                            :step="5"
                            @change="updateReliability(targetNode, reliabilityConfig[targetNode])"
                            :show-tooltip="true"
                          />
                        </div>
                      </div>
                      
                      <div class="reliability-tip" style="margin-top: 10px;">
                        <el-alert
                          title="Tip"
                          description="Adjust slider to set message arrival probability for each node. 0% means message will not reach that node, 100% means message will definitely arrive."
                          type="info"
                          :closable="false"
                          show-icon
                        />
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Consensus Result Display -->
                <div class="consensus-result-control" style="margin-top: 20px; border-top: 1px solid #e4e7ed; padding-top: 15px;">
                  <button
                    @click="showConsensusResult"
                    class="w-full bg-blue-100 dark:bg-blue-900 border-l-4 border-blue-500 dark:border-blue-700 text-blue-900 dark:text-blue-100 p-3 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-blue-200 dark:hover:bg-blue-800 transform hover:scale-105"
                  >
                    <svg
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      fill="none"
                      class="h-5 w-5 flex-shrink-0 mr-2 text-blue-600"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        stroke-width="2"
                        stroke-linejoin="round"
                        stroke-linecap="round"
                      ></path>
                    </svg>
                    <span class="text-sm font-semibold">Show Consensus Result</span>
                  </button>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- Middle: Received Messages -->
          <el-col :xs="24" :sm="12" :md="6" v-if="showAdvancedOptions">
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
                  <span>消息数量: {{ receivedMessages.length }}</span>
                </div>
                
                <div class="message-list">
                  <div 
                    v-for="msg in receivedMessages.slice(0, 8)" 
                    :key="msg.id"
                    class="message-item-compact"
                  >
                    <div class="message-header-compact">
                      <span class="message-from">From: Participant {{ msg.from }}</span>
                      <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
                    </div>
                    <div class="message-content-compact">
                      <span class="message-type">{{ getMessageTypeName(msg.type) }}</span>
                      <span class="message-value" v-if="msg.value !== null">
                        内容: {{ msg.value === -1 ? 'Reject' : (msg.value === 0 ? 'Option A' : 'Option B') }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div v-if="receivedMessages.length === 0" class="no-messages">
                  <el-empty description="No Messages" :image-size="60" />
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- Right: Topology and Consensus Results -->
          <el-col :xs="24" :sm="24" :md="12" v-if="showAdvancedOptions">
            <!-- Topology -->
            <el-card class="topology-card">
              <template #header>
                <div class="card-header">
                  <span>Network Topology</span>
                  <el-button size="small" @click="refreshTopology">Refresh</el-button>
                </div>
              </template>
              
              <div class="dynamic-topology">
                <div class="topology-info">
                  <p><strong>Network Type:</strong> {{ getTopologyName(sessionConfig.topology) }}</p>
                  <p><strong>Total Participants:</strong> {{ sessionConfig.nodeCount }}</p>
                  <p><strong>活跃连接:</strong> {{ getActiveConnections() }}</p>
                </div>
                
                <!-- Topology Container -->
                <div class="topology-container">
                  <!-- Connection Lines + Message Animations -->
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
                    <!-- Flying message dots -->
                    <circle
                      v-for="anim in messageAnimations"
                      :key="anim.id"
                      r="7"
                      :fill="anim.color"
                      opacity="0.9"
                    >
                      <animate
                        attributeName="cx"
                        :from="anim.x1" :to="anim.x2"
                        dur="0.8s" fill="freeze"
                      />
                      <animate
                        attributeName="cy"
                        :from="anim.y1" :to="anim.y2"
                        dur="0.8s" fill="freeze"
                      />
                      <animate
                        attributeName="opacity"
                        from="0.9" to="0"
                        begin="0.6s" dur="0.2s" fill="freeze"
                      />
                    </circle>
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
          <h4>Messages from this Participant</h4>
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
const currentRound = ref(1)
const acceptedValue = ref(null)
const receivedMessages = ref([])

// Human node action choice
const hasChosenAction = ref(false)
const isNormalMode = ref(false)
const waitingForNextRound = ref(true)  // 初始时等待下一轮共识
const showAdvancedOptions = ref(false)  // 控制高级选项显示
const nodeDetailsVisible = ref(false)
const selectedNode = ref(null)

// 消息可靠性配置
const reliabilityConfig = ref({})  // {targetNodeId: percentage}
const showReliabilityMatrix = ref(false)

// 差异化消息配置
const differentialMessageConfig = ref({})  // {targetNodeId: value (0 or 1)}
const showDifferentialMatrix = ref(false)

// Topology related
const topologyWidth = ref(500)
const topologyHeight = ref(400)
const topologyConnections = ref([])
const messageAnimations = ref([])  // flying dot animations

const triggerMessageAnimation = (fromNode, toNode, isCorrect) => {
  const nodeSize = 40
  const x1 = getNodeX(fromNode) + nodeSize / 2
  const y1 = getNodeY(fromNode) + nodeSize / 2
  const x2 = getNodeX(toNode) + nodeSize / 2
  const y2 = getNodeY(toNode) + nodeSize / 2
  const id = Date.now() + Math.random()
  messageAnimations.value.push({ id, x1, y1, x2, y2, color: isCorrect ? '#67c23a' : '#f56c6c' })
  // remove after animation completes
  setTimeout(() => {
    messageAnimations.value = messageAnimations.value.filter(a => a.id !== id)
  }, 900)
}


// Message sending form (custom message functionality removed)
const messageForm = reactive({
  type: 'prepare',
  value: 0,
  target: 'all'
})


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
    ElMessage.success('Connected Successfully')
  })

  socket.value.on('disconnect', () => {
    connectionStatus.value = 'disconnected'
    ElMessage.warning('Connection Lost')
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
    
    // 初始化可靠性配置（默认100%）
    initializeReliabilityConfig()
    
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
  
  socket.value.on('new_round', (data) => {
    console.log('进入新一轮共识:', data)
    currentRound.value = data.round
    currentPhase.value = data.phase
    phaseStep.value = data.step
    receivedMessages.value = []  // 清空消息列表
    
    // ResetOperation Selection
    hasChosenAction.value = false
    isNormalMode.value = false
    waitingForNextRound.value = false  // 可以参与共识了
    
    ElMessage.info(`Round ${data.round} consensus started`)
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

    // Animate the message as a flying dot (green = correct, red = byzantine)
    const fromNode = message.from
    const toNode = message.to ?? nodeId
    if (fromNode !== undefined && fromNode !== toNode) {
      const isCorrect = message.value === (acceptedValue.value ?? message.value)
      triggerMessageAnimation(fromNode, toNode, isCorrect && !message.byzantine)
    }

    refreshTopology()
  })

  socket.value.on('consensus_result', (result) => {
    console.log('收到Consensus Result:', result)
    console.log('Consensus Result状态:', result.status)
    console.log('Consensus Result描述:', result.description)
    
    // 根据Consensus Result显示不同的消息
    if (result.status === 'Consensus Succeeded') {
      console.log('显示Success消息')
      ElMessage.success(`Consensus Succeeded: ${result.description}`)
    } else if (result.status === 'Consensus Failed') {
      console.log('显示Failure消息')
      ElMessage.error(`Consensus Failed: ${result.description}`)
    } else if (result.status === 'Proposal Rejected') {
      console.log('显示Reject消息')
      ElMessage.warning(`Proposal Rejected: ${result.description}`)
    } else if (result.status === 'No Honest Nodes') {
      console.log('显示No Honest Nodes消息')
      ElMessage.error(`None诚实Node: ${result.description}`)
    } else {
      console.log('显示其他消息')
      ElMessage.info(`Consensus Result: ${result.status} - ${result.description}`)
    }
  })

  socket.value.on('error', (error) => {
    ElMessage.error(`错误: ${error.message}`)
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

const chooseNormalConsensus = () => {
  hasChosenAction.value = true
  isNormalMode.value = true
  
  // 通知后端，这个Node选择Normal Consensus，由机器人代理
  if (socket.value) {
    socket.value.emit('choose_normal_consensus', {
      sessionId,
      nodeId
    })
  }
  
  ElMessage.success('Normal consensus selected, robot will execute PBFT process for you')
}

const chooseByzantineAttack = () => {
  hasChosenAction.value = true
  isNormalMode.value = false
  
  // 通知后端，这个Node选择Byzantine Attack Mode
  if (socket.value) {
    socket.value.emit('choose_byzantine_attack', {
      sessionId,
      nodeId
    })
  }
  
  ElMessage.warning('Byzantine attack mode selected, you can send error messages')
}

const sendErrorMessage = () => {
  if (!hasChosenAction.value || isNormalMode.value) {
    ElMessage.error('Please select Byzantine attack mode first')
    return
  }
  
  if (socket.value) {
    // 发送与当前共识值相反的错误信息
    const errorValue = acceptedValue.value === 0 ? 1 : 0
    const errorMessage = {
      sessionId,
      nodeId,
      value: errorValue,
      byzantine: true
    }
    
    // 根据Current Phase发送相应的错误消息
    if (currentPhase.value === 'prepare') {
      socket.value.emit('send_prepare', errorMessage)
    } else if (currentPhase.value === 'commit') {
      socket.value.emit('send_commit', errorMessage)
    }
    
    ElMessage.warning(`🦹 Send error message: ${errorValue}`)
  }
}

const sendPrepare = () => {
  if (socket.value) {
    const message = {
      sessionId,
      nodeId,
      value: acceptedValue.value
    }
    socket.value.emit('send_prepare', message)
  }
}

const sendCommit = () => {
  if (socket.value) {
    const message = {
      sessionId,
      nodeId,
      value: acceptedValue.value
    }
    socket.value.emit('send_commit', message)
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
    'pre-prepare': 'Proposal Phase',
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
    full: 'Full Mesh',
    ring: 'Ring',
    star: 'Star',
    tree: 'Tree'
  }
  return names[topology] || topology
}

const getActiveConnections = () => {
  return topologyConnections.value.filter(conn => conn.active).length
}

// 初始化可靠性配置
const initializeReliabilityConfig = () => {
  const config = {}
  for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
    if (i !== nodeId) {
      config[i] = 100  // 默认100%可靠性
    }
  }
  reliabilityConfig.value = config
  console.log('初始化可靠性配置:', reliabilityConfig.value)
  
  // 初始化后立即发送到后端
  if (socket.value) {
    socket.value.emit('update_reliability', {
      sessionId,
      nodeId,
      reliability: reliabilityConfig.value
    })
    console.log('已发送初始可靠性配置到后端')
  }
}

// 初始化差异化消息配置
const initializeDifferentialConfig = () => {
  const config = {}
  for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
    if (i !== nodeId) {
      config[i] = 0  // 默认发送correct value
    }
  }
  differentialMessageConfig.value = config
  console.log('初始化差异化消息配置:', differentialMessageConfig.value)
}

// 切换差异化消息矩阵显示
const toggleDifferentialMatrix = () => {
  showDifferentialMatrix.value = !showDifferentialMatrix.value
  if (showDifferentialMatrix.value) {
    // 第一次打开时初始化配置
    if (Object.keys(differentialMessageConfig.value).length === 0) {
      initializeDifferentialConfig()
    }
  }
}

// 批量设置差异化消息
const setAllDifferential = (value) => {
  for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
    if (i !== nodeId) {
      differentialMessageConfig.value[i] = value
    }
  }
  const valueText = value === 0 ? 'correct value' : 'error value'
  ElMessage.success(`Set all nodes to send${valueText}`)
}

// 随机设置差异化消息
const randomizeDifferential = () => {
  for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
    if (i !== nodeId) {
      differentialMessageConfig.value[i] = Math.random() < 0.5 ? 0 : 1
    }
  }
  ElMessage.success('Randomly set message values for each node')
}

// 发送随机差异化消息（直接发送，不需要配置）
const sendRandomDifferentialMessage = () => {
  if (!hasChosenAction.value || isNormalMode.value) {
    ElMessage.error('Please select Byzantine attack mode first')
    return
  }

  if (currentPhase.value !== 'prepare' && currentPhase.value !== 'commit') {
    ElMessage.warning('Cannot send differential messages in current phase, please use this feature in prepare or commit phase')
    return
  }
  
  if (socket.value) {
    // 构建差异化Message Count据
    const messageData = {
      sessionId,
      nodeId,
      differential: true,  // 标记为差异化消息
      messages: {}  // {targetNodeId: value}
    }
    
    let correctCount = 0
    let errorCount = 0
    
    // 为每个目标Node随机设置发送的值
    for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
      if (i !== nodeId) {
        const sendCorrect = Math.random() < 0.5
        const valueToSend = sendCorrect ? acceptedValue.value : (acceptedValue.value === 0 ? 1 : 0)
        messageData.messages[i] = valueToSend
        
        if (sendCorrect) correctCount++
        else errorCount++
      }
    }
    
    console.log('发送随机差异化消息:', messageData)
    
    // 根据Current Phase发送相应的差异化消息
    if (currentPhase.value === 'prepare') {
      socket.value.emit('send_differential_prepare', messageData)
    } else if (currentPhase.value === 'commit') {
      socket.value.emit('send_differential_commit', messageData)
    }
    
    ElMessage.warning(`🦹 Execute random differential attack: ${correctCount} correct values，${errorCount} error values`)
  }
}

// 发送差异化消息（保留原函数以防其他地方使用）
const sendDifferentialMessage = () => {
  if (!hasChosenAction.value || isNormalMode.value) {
    ElMessage.error('Please select Byzantine attack mode first')
    return
  }
  
  if (socket.value) {
    // 构建差异化Message Count据
    const messageData = {
      sessionId,
      nodeId,
      differential: true,  // 标记为差异化消息
      messages: {}  // {targetNodeId: value}
    }
    
    // 为每个目标Node设置发送的值
    Object.keys(differentialMessageConfig.value).forEach(targetNode => {
      const sendCorrect = differentialMessageConfig.value[targetNode] === 0
      const valueToSend = sendCorrect ? acceptedValue.value : (acceptedValue.value === 0 ? 1 : 0)
      messageData.messages[parseInt(targetNode)] = valueToSend
    })
    
    console.log('发送差异化消息:', messageData)
    
    // 根据Current Phase发送相应的差异化消息
    if (currentPhase.value === 'prepare') {
      socket.value.emit('send_differential_prepare', messageData)
    } else if (currentPhase.value === 'commit') {
      socket.value.emit('send_differential_commit', messageData)
    }
    
    // 统计发送情况
    let correctCount = 0
    let errorCount = 0
    Object.values(differentialMessageConfig.value).forEach(val => {
      if (val === 0) correctCount++
      else errorCount++
    })
    
    ElMessage.warning(`🦹 Execute differential attack: ${correctCount} correct values，${errorCount} error values`)
  }
}

// 更新可靠性配置并发送到后端
const updateReliability = (targetNode, value) => {
  // 确保 targetNode 是整数Type
  const targetNodeInt = parseInt(targetNode)
  reliabilityConfig.value[targetNodeInt] = value
  
  // 发送到后端（转换所有键为整数）
  if (socket.value) {
    const reliabilityToSend = {}
    Object.keys(reliabilityConfig.value).forEach(key => {
      reliabilityToSend[parseInt(key)] = reliabilityConfig.value[key]
    })
    
    socket.value.emit('update_reliability', {
      sessionId,
      nodeId,
      reliability: reliabilityToSend
    })
  }
  
  console.log(`Update node ${targetNodeInt}  reliability to ${value}%`)
}

// 批量设置所有Node的可靠性
const setAllReliability = (value) => {
  for (let i = 0; i < sessionConfig.value.nodeCount; i++) {
    if (i !== nodeId) {
      reliabilityConfig.value[i] = value
    }
  }
  
  // 发送到后端（转换所有键为整数）
  if (socket.value) {
    const reliabilityToSend = {}
    Object.keys(reliabilityConfig.value).forEach(key => {
      reliabilityToSend[parseInt(key)] = reliabilityConfig.value[key]
    })
    
    socket.value.emit('update_reliability', {
      sessionId,
      nodeId,
      reliability: reliabilityToSend
    })
  }
  
  console.log(`Batch set reliability to ${value}%:`, reliabilityConfig.value)
  ElMessage.success(`Set reliability of all nodes to ${value}%`)
}

// Consensus result display function
const showConsensusResult = () => {
  console.log('Show Consensus Result')
  
  // 根据Current Phase和状态模拟不同的Consensus Result
  let result
  
  if (currentPhase.value === 'prepare') {
    result = {
      status: 'Prepare Phase Incomplete',
      description: 'Prepare Phase需要更多Node参与',
      stats: {
        expected_nodes: sessionConfig.value.nodeCount,
        expected_prepare_nodes: sessionConfig.value.nodeCount - 1,
        total_messages: receivedMessages.value.length
      }
    }
  } else if (currentPhase.value === 'commit') {
    // 根据实际接Received Messages分析Consensus Result
    const commitMessages = receivedMessages.value.filter(msg => msg.type === 'commit')
    const correctMessages = commitMessages.filter(msg => msg.value === 0).length
    const errorMessages = commitMessages.filter(msg => msg.value === 1).length
    
    // 计算Faulty Nodes f = floor((n-1)/3)
    const n = sessionConfig.value.nodeCount
    const f = Math.floor((n - 1) / 3)
    const requiredCorrect = 2 * f + 1
    const requiredError = f + 1
    
    console.log(`Commit Phase分析 - Total Nodes: ${n}, 故障节点数: ${f}`)
    console.log(`Commit Phase分析 - 正确消息: ${correctMessages}, 错误消息: ${errorMessages}`)
    console.log(`Commit Phase分析 - 需要正确消息: ${requiredCorrect}, 需要错误消息: ${requiredError}`)
    
    if (correctMessages >= requiredCorrect) {
      result = {
        status: 'Consensus Succeeded',
        description: `收到${correctMessages}个正确消息（需要${requiredCorrect}个）`,
        stats: {
          expected_nodes: sessionConfig.value.nodeCount,
          expected_prepare_nodes: sessionConfig.value.nodeCount - 1,
          total_messages: receivedMessages.value.length
        }
      }
    } else if (errorMessages >= requiredError) {
      result = {
        status: 'Consensus Failed',
        description: `收到${errorMessages}个错误消息（需要${requiredError}个）`,
        stats: {
          expected_nodes: sessionConfig.value.nodeCount,
          expected_prepare_nodes: sessionConfig.value.nodeCount - 1,
          total_messages: receivedMessages.value.length
        }
      }
    } else {
      result = {
        status: 'Commit Phase Waiting',
        description: `正确消息: ${correctMessages}, 错误消息: ${errorMessages}，等待更多消息`,
        stats: {
          expected_nodes: sessionConfig.value.nodeCount,
          expected_prepare_nodes: sessionConfig.value.nodeCount - 1,
          total_messages: receivedMessages.value.length
        }
      }
    }
  } else if (currentPhase.value === 'completed') {
    result = {
      status: 'Consensus Completed',
      description: '共识过程已经Complete',
      stats: {
        expected_nodes: sessionConfig.value.nodeCount,
        expected_prepare_nodes: sessionConfig.value.nodeCount - 1,
        total_messages: receivedMessages.value.length
      }
    }
  } else {
    result = {
      status: 'Proposal Phase',
      description: '正在等待Propose',
      stats: {
        expected_nodes: sessionConfig.value.nodeCount,
        expected_prepare_nodes: sessionConfig.value.nodeCount - 1,
        total_messages: receivedMessages.value.length
      }
    }
  }
  
  // 直接调用事件处理函数
  console.log('收到Consensus Result:', result)
  console.log('Consensus Result状态:', result.status)
  console.log('Consensus Result描述:', result.description)
  
  // 根据Consensus Result显示不同的消息
  if (result.status === 'Consensus Succeeded') {
    console.log('显示Success消息')
    ElMessage.success(`Consensus Succeeded: ${result.description}`)
  } else if (result.status === 'Consensus Failed') {
    console.log('显示Failure消息')
    ElMessage.error(`Consensus Failed: ${result.description}`)
  } else if (result.status === 'Proposal Rejected') {
    console.log('显示Reject消息')
    ElMessage.warning(`Proposal Rejected: ${result.description}`)
  } else if (result.status === 'No Honest Nodes') {
    console.log('显示No Honest Nodes消息')
    ElMessage.error(`None诚实Node: ${result.description}`)
  } else {
    console.log('显示其他消息')
    ElMessage.info(`Consensus Result: ${result.status} - ${result.description}`)
  }
}



const isMyTurn = computed(() => {
  // Only non-proposer nodes (validators) should show validator quick actions
  if (nodeId === 0) {
    return false  // Proposer should not show validator quick actions
  }
  return currentPhase.value === 'prepare' || currentPhase.value === 'commit'
})

// Whether proposer can send messages
const canProposerSendCustom = computed(() => {
  return nodeId === 0
})


// Message sending related methods (custom message functionality removed)


// Lifecycle
onMounted(() => {
  connectToServer()
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
  background: linear-gradient(135deg, #d1d5db 0%, #e5e7eb 100%);
}

.main-content {
  padding: 20px;
}

.session-info-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-section h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 500;
  color: #1f2937;
}

.tags-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.session-details {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.session-id {
  font-size: 13px;
  color: #6b7280;
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

.phase-steps :deep(.el-step__title) {
  white-space: nowrap;
  font-size: 13px;
}

.phase-steps :deep(.el-steps--simple) {
  padding: 8px 4px;
}

@media (max-width: 768px) {
  .phase-steps :deep(.el-step__title) {
    font-size: 11px;
  }
  .phase-steps :deep(.el-steps--simple) {
    padding: 6px 2px;
    gap: 2px;
  }
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
  align-items: stretch;
}

.quick-action-btn {
  width: 100%;
  text-align: center;
  justify-content: center;
  display: flex;
  align-items: center;
  height: 40px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  box-sizing: border-box;
  margin: 0;
  padding: 0 16px;
  line-height: 1;
  vertical-align: middle;
}

/* 确保两个按钮的尺寸完全一致 */
.quick-actions-buttons .el-button {
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
  border-radius: 6px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 0 16px !important;
  margin: 0 !important;
  box-sizing: border-box !important;
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

.simple-attack-control {
  text-align: center;
}

.attack-tip {
  margin-top: 10px;
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
  background: #93c5fd;
  color: #1f2937;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  cursor: pointer;
  z-index: 2;
  transition: all 0.3s ease;
  border: 2px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.topology-node:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.topology-node.current-node {
  background: #86efac;
  border-color: #86efac;
}

.topology-node.proposer {
  background: #facc15;
  border-color: #facc15;
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

/* 可靠性控制样式 */
.reliability-control {
  margin-top: 15px;
}

.reliability-matrix {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;
}

.reliability-items {
  max-height: 400px;
  overflow-y: auto;
}

.reliability-item {
  margin-bottom: 15px;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.reliability-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.reliability-value {
  color: #409eff;
  font-weight: bold;
  font-size: 15px;
}

.quick-set {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

/* 差异化消息控制样式 */
.differential-message-control {
  padding: 15px;
  border: 2px solid #e6a23c;
  border-radius: 8px;
  background: linear-gradient(135deg, #fffaf0 0%, #fff5e6 100%);
}

.differential-matrix {
  background: #fef8f0;
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;
}

.quick-set-differential {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e6a23c;
}

.differential-items {
  max-height: 400px;
  overflow-y: auto;
}

.differential-item {
  margin-bottom: 15px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e6a23c;
}

.differential-label {
  margin-bottom: 10px;
  font-size: 14px;
  color: #606266;
  font-weight: 600;
}

.differential-item .el-radio-group {
  display: flex;
  gap: 10px;
  width: 100%;
}

.differential-item .el-radio {
  flex: 1;
  margin: 0;
}

.differential-tip {
  margin-top: 10px;
}

.advanced-options-toggle {
  width: 100%;
  padding: 12px 20px;
  background: white;
  color: #1f2937;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.advanced-options-toggle:hover {
  background: #f9fafb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.advanced-options-toggle:active {
  transform: translateY(0);
}

@media (max-width: 768px) {
  .node-page {
    font-size: 14px;
  }

  .main-content {
    padding: 8px;
  }

  .session-info-card {
    padding: 12px;
  }

  .info-section h2 {
    font-size: 1.1rem;
  }

  .session-id {
    font-size: 11px;
    word-break: break-all;
  }

  .tags-group {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .card-header {
    flex-direction: column;
    gap: 8px;
  }

  .el-card {
    margin-bottom: 12px;
  }

  .operation-buttons button,
  .operation-buttons .el-button {
    width: 100%;
    margin-bottom: 8px;
  }
}
</style> 