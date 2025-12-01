<template>
  <div class="home-page">
    <el-container>
      <el-header class="header">
        <h1>分布式PBFT共识系统</h1>
        <p>创建共识会话，让用户扮演节点参与共识过程</p>
      </el-header>
      
      <el-main class="main-content">
        <el-row :gutter="40">
          <!-- Left: Parameter Configuration -->
          <el-col :span="12">
            <el-card class="config-card">
              <template #header>
                <div class="card-header">
                  <span>共识参数配置</span>
                </div>
              </template>
              
              <el-form 
                :model="formData" 
                :rules="rules" 
                ref="formRef" 
                label-width="120px"
                class="config-form"
              >
                <el-form-item label="总节点数" prop="nodeCount">
                  <el-input-number 
                    v-model="formData.nodeCount" 
                    :min="3" 
                    :max="20"
                    controls-position="right"
                  />
                  <span class="form-tip">建议3-20个节点</span>
                </el-form-item>
                
                <el-form-item label="故障节点数" prop="faultyNodes">
                  <el-input-number 
                    v-model="formData.faultyNodes" 
                    :min="0" 
                    :max="formData.nodeCount"
                    controls-position="right"
                  />
                  <span class="form-tip">所有节点都可以选择成为拜占庭节点</span>
                </el-form-item>
                
                
                <el-form-item label="拓扑结构" prop="topology">
                  <el-select v-model="formData.topology" placeholder="选择拓扑结构">
                    <el-option label="全连接" value="full" />
                    <el-option label="环形" value="ring" />
                    <el-option label="星形" value="star" />
                    <el-option label="树形" value="tree" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="分支数量" v-if="formData.topology === 'tree'" prop="branchCount">
                  <el-input-number 
                    v-model="formData.branchCount" 
                    :min="2" 
                    :max="5"
                    controls-position="right"
                  />
                </el-form-item>
                
                <el-form-item label="提议值" prop="proposalValue">
                  <el-radio-group v-model="formData.proposalValue">
                    <el-radio :value="0">0</el-radio>
                    <el-radio :value="1">1</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item label="提议内容" prop="proposalContent">
                  <el-input 
                    v-model="formData.proposalContent" 
                    type="textarea" 
                    :rows="3"
                    placeholder="输入具体的提议内容，例如：'今天中午吃火锅'、'选择方案A'等"
                  />
                  <span class="form-tip">输入具体的提议内容，将在节点页面显示</span>
                </el-form-item>
                
                <el-form-item label="恶意提议者" prop="maliciousProposer">
                  <el-switch v-model="formData.maliciousProposer" />
                  <span class="form-tip">启用时，提议者可能发送错误的值</span>
                </el-form-item>
                
                <el-form-item label="允许消息篡改" prop="allowTampering">
                  <el-switch v-model="formData.allowTampering" />
                  <span class="form-tip">启用时，故障节点可能篡改消息</span>
                </el-form-item>
                
                <el-form-item label="消息传递率" prop="messageDeliveryRate">
                  <el-slider 
                    v-model="formData.messageDeliveryRate" 
                    :min="50" 
                    :max="100" 
                    :step="5"
                    show-stops
                    show-input
                    :format-tooltip="(val) => `${val}%`"
                  />
                  <span class="form-tip">模拟网络丢包，测试网络可靠性对共识的影响</span>
                </el-form-item>
                
                <el-form-item>
                  <div class="flex flex-col gap-3 w-full">
                    <!-- 创建会话按钮 -->
                    <button
                      @click="createSession"
                      :disabled="creating"
                      class="w-full bg-blue-100 dark:bg-blue-900 border-l-4 border-blue-500 dark:border-blue-700 text-blue-900 dark:text-blue-100 p-3 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-blue-200 dark:hover:bg-blue-800 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                    >
                      <svg
                        v-if="!creating"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        fill="none"
                        class="h-5 w-5 flex-shrink-0 mr-2 text-blue-600"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M12 4v16m8-8H4"
                          stroke-width="2"
                          stroke-linejoin="round"
                          stroke-linecap="round"
                        ></path>
                      </svg>
                      <span class="text-sm font-semibold">{{ creating ? '创建中...' : '创建共识会话' }}</span>
                    </button>
                    
                    <!-- 动画演示按钮 -->
                    <button
                      @click="showDemo"
                      :disabled="simulating"
                      class="w-full bg-green-100 dark:bg-green-900 border-l-4 border-green-500 dark:border-green-700 text-green-900 dark:text-green-100 p-3 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-green-200 dark:hover:bg-green-800 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                    >
                      <svg
                        v-if="!simulating"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        fill="none"
                        class="h-5 w-5 flex-shrink-0 mr-2 text-green-600"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                          stroke-width="2"
                          stroke-linejoin="round"
                          stroke-linecap="round"
                        ></path>
                        <path
                          d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          stroke-width="2"
                          stroke-linejoin="round"
                          stroke-linecap="round"
                        ></path>
                      </svg>
                      <span class="text-sm font-semibold">{{ simulating ? '演示中...' : '动画演示共识过程' }}</span>
                    </button>
                    
                    <!-- 重置按钮 -->
                    <button
                      @click="resetForm"
                      class="w-full bg-gray-100 dark:bg-gray-700 border-l-4 border-gray-500 dark:border-gray-600 text-gray-900 dark:text-gray-100 p-3 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-gray-200 dark:hover:bg-gray-600 transform hover:scale-105"
                    >
                      <svg
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        fill="none"
                        class="h-5 w-5 flex-shrink-0 mr-2 text-gray-600"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                          stroke-width="2"
                          stroke-linejoin="round"
                          stroke-linecap="round"
                        ></path>
                      </svg>
                      <span class="text-sm font-semibold">重置</span>
                    </button>
                  </div>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
          
          <!-- Right: QR Code and Session Information -->
          <el-col :span="12">
            <el-card class="qr-card" v-if="sessionInfo">
              <template #header>
                <div class="card-header">
                  <span>会话信息</span>
                </div>
              </template>
              
              <div class="session-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="会话ID">{{ sessionInfo.sessionId }}</el-descriptions-item>
                  <el-descriptions-item label="总节点数">{{ sessionInfo.config.nodeCount }}</el-descriptions-item>
                  <el-descriptions-item label="故障节点数">{{ sessionInfo.config.faultyNodes }}</el-descriptions-item>
                  <el-descriptions-item label="机器人节点数">{{ sessionInfo.config.robotNodes }}</el-descriptions-item>
                  <el-descriptions-item label="人类节点数">{{ sessionInfo.config.nodeCount - sessionInfo.config.robotNodes }}</el-descriptions-item>
                  <el-descriptions-item label="拓扑结构">{{ getTopologyName(sessionInfo.config.topology) }}</el-descriptions-item>
                  <el-descriptions-item label="提议值">{{ sessionInfo.config.proposalValue }}</el-descriptions-item>
                  <el-descriptions-item label="提议内容">{{ sessionInfo.config.proposalContent || '无' }}</el-descriptions-item>
                  <el-descriptions-item label="消息传递率">{{ sessionInfo.config.messageDeliveryRate }}%</el-descriptions-item>
                  <el-descriptions-item label="状态">{{ sessionInfo.status }}</el-descriptions-item>
                </el-descriptions>
                
                <div class="qr-section">
                  <h3>扫描二维码加入节点</h3>
                  <div class="qr-container" ref="qrContainer"></div>
                  <p class="qr-tip">其他用户可以扫描此二维码加入共识过程</p>
                </div>
                
                <div class="node-links">
                  <h3>节点链接</h3>
                  <el-table :data="nodeLinks" style="width: 100%">
                    <el-table-column prop="nodeId" label="节点ID" width="80" />
                    <el-table-column prop="url" label="链接" />
                    <el-table-column label="操作" width="120">
                      <template #default="scope">
                        <el-button size="small" @click="copyLink(scope.row.url)">
                          复制链接
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-card>
            
            <el-card class="welcome-card" v-else>
              <template #header>
                <div class="card-header">
                  <span>欢迎</span>
                </div>
              </template>
              
              <div class="welcome-content">
                <el-icon size="60" color="#409EFF"><Connection /></el-icon>
                <h2>分布式PBFT共识系统</h2>
                <p>配置参数创建共识会话，生成二维码供其他用户扫描加入</p>
                <p>每个用户将扮演一个节点，实时参与共识过程</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 可靠度实验模块 -->
        <el-row :gutter="40" style="margin-top: 40px;">
          <el-col :span="24">
            <el-card class="experiment-card">
              <template #header>
                <div class="card-header" style="display: flex; align-items: center; justify-content: space-between;">
                  <span>🔬 通信可靠度对共识影响实验</span>
                  <el-tag :type="experimentRunning ? 'success' : 'info'" effect="dark">
                    {{ experimentRunning ? '实验进行中' : '未运行' }}
                  </el-tag>
                </div>
              </template>
              
              <div class="experiment-content">
                <el-row :gutter="30">
                  <!-- 左侧：实验配置 -->
                  <el-col :span="8">
                    <div class="experiment-config">
                      <h3>实验配置</h3>
                      <el-form label-width="120px">
                        <el-form-item label="总节点数">
                          <el-input-number 
                            v-model="experimentConfig.nodeCount" 
                            :min="4" 
                            :max="10"
                            :disabled="experimentRunning"
                            controls-position="right"
                          />
                        </el-form-item>
                        
                        <el-form-item label="故障节点数">
                          <el-input-number 
                            v-model="experimentConfig.faultyNodes" 
                            :min="0" 
                            :max="Math.floor((experimentConfig.nodeCount - 1) / 3)"
                            :disabled="experimentRunning"
                            controls-position="right"
                          />
                          <div class="form-tip">拜占庭容错要求: f < n/3</div>
                        </el-form-item>
                        
                        <el-form-item label="通信可靠度">
                          <el-slider 
                            v-model="experimentConfig.reliability" 
                            :min="50" 
                            :max="100" 
                            :step="5"
                            :disabled="experimentRunning"
                            show-stops
                            show-input
                            :format-tooltip="(val) => `${val}%`"
                          />
                        </el-form-item>
                        
                        <el-form-item label="实验轮数">
                          <el-input-number 
                            v-model="experimentConfig.rounds" 
                            :min="10"
                            :step="10"
                            :disabled="experimentRunning"
                            controls-position="right"
                          />
                        </el-form-item>
                        
                        <el-form-item>
                          <el-button 
                            v-if="!experimentRunning"
                            type="primary" 
                            @click="startExperiment"
                            :icon="VideoPlay"
                            style="width: 100%;"
                          >
                            开始实验
                          </el-button>
                          <el-button 
                            v-else
                            type="danger" 
                            @click="stopExperiment"
                            style="width: 100%;"
                          >
                            停止实验
                          </el-button>
                        </el-form-item>
                      </el-form>
                    </div>
                  </el-col>
                  
                  <!-- 中间：实验进度 -->
                  <el-col :span="8">
                    <div class="experiment-progress">
                      <h3>实验进度</h3>
                      <div v-if="experimentRunning || experimentResults.length > 0">
                        <el-statistic title="当前轮次" :value="currentExperimentRound" :suffix="`/ ${experimentConfig.rounds}`" />
                        <el-progress 
                          :percentage="Math.round((currentExperimentRound / experimentConfig.rounds) * 100)" 
                          :status="experimentRunning ? 'success' : 'info'"
                          style="margin-top: 20px;"
                        />
                        
                        <div class="stats-grid" style="margin-top: 30px;">
                          <div class="stat-item">
                            <div class="stat-label">成功轮次</div>
                            <div class="stat-value success">{{ successCount }}</div>
                          </div>
                          <div class="stat-item">
                            <div class="stat-label">失败轮次</div>
                            <div class="stat-value danger">{{ failureCount }}</div>
                          </div>
                          <div class="stat-item">
                            <div class="stat-label">成功率</div>
                            <div class="stat-value primary">{{ successRate }}%</div>
                          </div>
                        </div>
                      </div>
                      <el-empty 
                        v-else 
                        description="暂无实验数据" 
                        :image-size="100"
                      />
                    </div>
                  </el-col>
                  
                  <!-- 右侧：实验结果 -->
                  <el-col :span="8">
                    <div class="experiment-results">
                      <h3>实验结果</h3>
                      <div v-if="experimentResults.length > 0" class="results-list">
                        <el-scrollbar height="400px">
                          <div 
                            v-for="(result, index) in experimentResults" 
                            :key="index"
                            class="result-item"
                            :class="result.success ? 'success' : 'failure'"
                          >
                            <div class="result-header">
                              <span class="round-label">第 {{ result.round }} 轮</span>
                              <el-tag :type="result.success ? 'success' : 'danger'" size="small">
                                {{ result.success ? '成功' : '失败' }}
                              </el-tag>
                            </div>
                            <div class="result-details">
                              <span>消息数: {{ result.messageCount }}</span>
                              <span>耗时: {{ result.duration }}ms</span>
                            </div>
                            <div v-if="!result.success && result.failureReason" class="failure-reason">
                              <el-tag size="small" type="info">原因: {{ result.failureReason }}</el-tag>
                            </div>
                          </div>
                        </el-scrollbar>
                        
                        <el-button 
                          type="primary" 
                          @click="showChartDialog = true"
                          style="width: 100%; margin-top: 15px;"
                          :disabled="experimentResults.length === 0"
                        >
                          查看成功率趋势图
                        </el-button>
                        
                        <el-button 
                          type="default" 
                          @click="exportResults"
                          style="width: 100%; margin-top: 10px;"
                          :disabled="experimentResults.length === 0"
                        >
                          导出结果
                        </el-button>
                      </div>
                      <el-empty 
                        v-else 
                        description="暂无实验结果" 
                        :image-size="100"
                      />
                    </div>
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
    
    <!-- 动画演示对话框 -->
    <el-dialog
      v-model="demoDialogVisible"
      title="PBFT共识过程动画演示"
      width="90%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="demo-container">
        <div class="demo-content">
          <div class="topology-section">
            <h3>网络拓扑与消息传递动画</h3>
            
            <!-- 浮动控制面板 -->
            <div class="floating-controls">
              <el-card class="control-card">
                <template #header>
                  <div class="card-header">
                    <span>🎮 动画控制</span>
                  </div>
                </template>
                
                <!-- 会话信息 -->
                <div class="control-section">
                  <el-tag type="success" style="width: 100%; padding: 8px 12px; font-size: 14px;">
                    真实会话消息历史
                  </el-tag>
                </div>
                
                <!-- 轮次选择 -->
                <div class="control-section" v-if="simulationRounds.length > 1">
                  <label class="control-label">选择轮次</label>
                  <el-radio-group v-model="currentRound" @change="onRoundChange">
                    <el-radio-button 
                      v-for="round in simulationRounds" 
                      :key="round.id" 
                      :label="round.id"
                    >
                      第 {{ round.id }} 轮
                    </el-radio-button>
                  </el-radio-group>
                </div>
                <div class="control-section" v-else>
                  <el-text type="info">当前仅有 1 轮共识</el-text>
                </div>
                
                <!-- 动画速度控制 -->
                <div class="control-section">
                  <label class="control-label">⚡ 动画速度</label>
                  <el-slider 
                    v-model="animationSpeed" 
                    :min="0.5" 
                    :max="3" 
                    :step="0.25"
                    :marks="{ 0.5: '0.5x', 1: '1x', 1.5: '1.5x', 2: '2x', 2.5: '2.5x', 3: '3x' }"
                    show-stops
                  />
                  <div class="speed-display">
                    <el-tag type="primary">当前速度: {{ animationSpeed }}x</el-tag>
                  </div>
                </div>
                
                <!-- 播放按钮 -->
                <div class="control-section">
                  <button
                    @click="playAnimation"
                    :disabled="!currentSimulation"
                    class="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-3 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-500 disabled:transform-none flex items-center justify-center"
                  >
                    <svg
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      fill="none"
                      class="h-5 w-5 flex-shrink-0 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                        stroke-width="2"
                        stroke-linejoin="round"
                        stroke-linecap="round"
                      ></path>
                      <path
                        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        stroke-width="2"
                        stroke-linejoin="round"
                        stroke-linecap="round"
                      ></path>
                    </svg>
                    <span class="ml-2 text-sm font-semibold">重新播放动画</span>
                  </button>
                </div>
              </el-card>
            </div>
            
            <Topology
              v-if="currentSimulation"
              ref="topologyRef"
              :topologyType="formData.topology"
              :nodeCount="formData.nodeCount"
              :byzantineNodes="formData.faultyNodes"
              :simulationResult="currentSimulation"
              :proposalValue="formData.proposalValue"
              :animationSpeed="animationSpeed"
            />
          </div>
          
          <div class="table-section">
            <h3>消息详情表</h3>
            <PBFTTable
              v-if="currentSimulation"
              :filteredSimulationResult="currentSimulation"
              :nodeCount="formData.nodeCount"
            />
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="demoDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 成功率趋势图弹窗 -->
    <el-dialog
      v-model="showChartDialog"
      title="累计成功率趋势图"
      width="70%"
      :close-on-click-modal="true"
      destroy-on-close
      center
    >
      <div v-if="experimentResults.length > 0" class="chart-dialog-content">
        <div ref="chartContainer" style="width: 100%; height: 500px;"></div>
      </div>
      <el-empty v-else description="暂无数据" />
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import QRCode from 'qrcode'
import axios from 'axios'
import * as echarts from 'echarts'
import Topology from '@/components/Topology.vue'
import PBFTTable from '@/components/PBFTTable.vue'

export default {
  name: 'HomePage',
  components: {
    VideoPlay,
    Topology,
    PBFTTable
  },
  setup() {
    const formRef = ref(null)
    const qrContainer = ref(null)
    const creating = ref(false)
    const sessionInfo = ref(null)
    
    // 演示相关
    const demoDialogVisible = ref(false)
    const simulating = ref(false)
    const simulationRounds = ref([])
    const currentRound = ref(1)
    const currentSimulation = ref(null)
    const topologyRef = ref(null)
    const animationSpeed = ref(1) // 动画速度：0.5x, 1x, 1.5x, 2x等
    
    // 实验相关
    const experimentRunning = ref(false)
    const experimentStopRequested = ref(false)
    const currentExperimentRound = ref(0)
    const experimentResults = ref([])
    const experimentSessionId = ref(null)
    const chartContainer = ref(null)
    const showChartDialog = ref(false)
    let chartInstance = null
    const experimentConfig = reactive({
      nodeCount: 6,
      faultyNodes: 1,
      reliability: 80,
      rounds: 30
    })
    
    const formData = reactive({
      nodeCount: 6,
      faultyNodes: 1,
      topology: 'full',
      branchCount: 2,
      proposalValue: 0,
      proposalContent: '',
      maliciousProposer: false,
      allowTampering: false,
      messageDeliveryRate: 100
    })
    
    const rules = {
      nodeCount: [
        { required: true, message: '请输入总节点数', trigger: 'blur' }
      ],
      faultyNodes: [
        { required: true, message: '请输入故障节点数', trigger: 'blur' }
      ],
      topology: [
        { required: true, message: '请选择拓扑结构', trigger: 'change' }
      ]
    }
    
    const nodeLinks = computed(() => {
      if (!sessionInfo.value) return []
      
      const links = []
      const robotNodes = sessionInfo.value.config.robotNodes || 0
      const humanNodeCount = sessionInfo.value.config.nodeCount - robotNodes
      
      // 只显示人类节点的链接，从robotNodes开始编号
      for (let i = 0; i < humanNodeCount; i++) {
        const nodeId = robotNodes + i
        links.push({
          nodeId: nodeId,
          url: `${window.location.origin}/node/${sessionInfo.value.sessionId}/${nodeId}`
        })
      }
      return links
    })
    
    const getTopologyName = (topology) => {
      const names = {
        full: '全连接',
        ring: '环形',
        star: '星形',
        tree: '树形'
      }
      return names[topology] || topology
    }
    
    const createSession = async () => {
      try {
        await formRef.value.validate()
        creating.value = true
        
        const response = await axios.post('/api/sessions', {
        nodeCount: formData.nodeCount,
        faultyNodes: formData.faultyNodes,
        robotNodes: formData.nodeCount - formData.faultyNodes, // 自动计算机器人节点数
        topology: formData.topology,
        branchCount: formData.branchCount,
        proposalValue: formData.proposalValue,
        proposalContent: formData.proposalContent,
        maliciousProposer: formData.maliciousProposer,
        allowTampering: formData.allowTampering,
        messageDeliveryRate: formData.messageDeliveryRate
      })
        
        sessionInfo.value = response.data
        
        ElMessage.success('共识会话创建成功！')
      } catch (error) {
        console.error('Failed to create session:', error)
        ElMessage.error('创建会话失败，请重试')
      } finally {
        creating.value = false
      }
    }
    
    const generateQRCode = async () => {
      if (!qrContainer.value || !sessionInfo.value) {
        console.log('QR container or session info does not exist:', { qrContainer: !!qrContainer.value, sessionInfo: !!sessionInfo.value })
        return
      }
      
      try {
        // Clear container
        qrContainer.value.innerHTML = ''
        
        const qrData = {
          sessionId: sessionInfo.value.sessionId,
          nodeCount: sessionInfo.value.config.nodeCount,
          joinUrl: `${window.location.origin}/join/${sessionInfo.value.sessionId}`,
          autoAssign: true,
          description: 'Scan QR code to auto-assign node'
        }
        
        console.log('Generate QR code data:', qrData)
        
        // Method 1: Direct use of container
        try {
          await QRCode.toCanvas(qrContainer.value, JSON.stringify(qrData), {
            width: 200,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF'
            }
          })
          console.log('QR code generated successfully (method 1)')
          return
        } catch (error1) {
          console.log('Method 1 failed, trying method 2:', error1)
        }
        
        // Method 2: Create canvas element
        try {
          const canvas = document.createElement('canvas')
          qrContainer.value.appendChild(canvas)
          
          await QRCode.toCanvas(canvas, JSON.stringify(qrData), {
            width: 200,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF'
            }
          })
          console.log('QR code generated successfully (method 2)')
          return
        } catch (error2) {
          console.log('Method 2 failed, trying method 3:', error2)
        }
        
        // Method 3: Use toDataURL
        try {
          const dataURL = await QRCode.toDataURL(JSON.stringify(qrData), {
            width: 200,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF'
            }
          })
          
          const img = document.createElement('img')
          img.src = dataURL
          img.style.width = '200px'
          img.style.height = '200px'
          qrContainer.value.appendChild(img)
          console.log('QR code generated successfully (method 3)')
          return
        } catch (error3) {
          console.log('Method 3 failed:', error3)
        }
        
        throw new Error('All QR code generation methods failed')
        
      } catch (error) {
        console.error('Failed to generate QR code:', error)
        // Show error message and fallback link
        qrContainer.value.innerHTML = `
          <div style="color: red; padding: 20px; text-align: center;">
            <div>二维码生成失败</div>
            <div style="margin-top: 10px; font-size: 12px;">
              请使用以下链接加入：<br>
              <a href="${window.location.origin}/join/${sessionInfo.value.sessionId}" target="_blank">
                ${window.location.origin}/join/${sessionInfo.value.sessionId}
              </a>
            </div>
          </div>
        `
      }
    }
    
    const copyLink = async (url) => {
      try {
        await navigator.clipboard.writeText(url)
        ElMessage.success('链接已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }
    
    const resetForm = () => {
      formRef.value.resetFields()
      sessionInfo.value = null
    }
    
    // Watch sessionInfo changes, auto-generate QR code
    watch(sessionInfo, async (newSessionInfo) => {
      if (newSessionInfo) {
        console.log('Session info updated, preparing to generate QR code')
        // Wait for DOM update
        await new Promise(resolve => setTimeout(resolve, 100))
        await generateQRCode()
      }
    })
    
    // 演示相关方法
    const showDemo = async () => {
      try {
        simulating.value = true
        
        // 检查是否已创建会话
        if (!sessionInfo.value) {
          ElMessage.error('请先创建共识会话！')
          return
        }
        
        simulationRounds.value = []
        
        // 1. 先获取轮次列表
        const roundsResponse = await axios.get(`/api/sessions/${sessionInfo.value.sessionId}/history`)
        const rounds = roundsResponse.data.rounds || [1]
        
        console.log('可用的轮次:', rounds)
        
        // 2. 获取所有轮次的数据
        for (const roundNum of rounds) {
          const response = await axios.get(`/api/sessions/${sessionInfo.value.sessionId}/history?round=${roundNum}`)
          simulationRounds.value.push({
            id: roundNum,
            data: response.data,
            isReal: true
          })
        }
        
        // 默认显示第一轮
        currentRound.value = rounds[0]
        currentSimulation.value = simulationRounds.value[0].data
        
        // 打开对话框
        demoDialogVisible.value = true
        
        // 等待DOM更新后播放动画
        await nextTick()
        await new Promise(resolve => setTimeout(resolve, 300))
        playAnimation()
        
        ElMessage.success(`已加载 ${rounds.length} 轮共识历史`)
      } catch (error) {
        console.error('Failed to get session history:', error)
        if (error.response && error.response.status === 404) {
          ElMessage.error('会话不存在或已过期，请重新创建会话')
        } else {
          ElMessage.error('获取会话历史失败，请稍后重试')
        }
      } finally {
        simulating.value = false
      }
    }
    
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
    
    const playAnimation = () => {
      if (topologyRef.value && topologyRef.value.startAnimation) {
        topologyRef.value.startAnimation()
      }
    }
    
    // 实验统计计算属性
    const successCount = computed(() => {
      return experimentResults.value.filter(r => r.success).length
    })
    
    const failureCount = computed(() => {
      return experimentResults.value.filter(r => !r.success).length
    })
    
    const successRate = computed(() => {
      if (experimentResults.value.length === 0) return 0
      return Math.round((successCount.value / experimentResults.value.length) * 100)
    })
    
    // 计算每轮的累计成功率（用于图表）
    const cumulativeSuccessRate = computed(() => {
      if (experimentResults.value.length === 0) return []
      
      const rates = []
      let successCountSoFar = 0
      
      for (let i = 0; i < experimentResults.value.length; i++) {
        if (experimentResults.value[i].success) {
          successCountSoFar++
        }
        const rate = (successCountSoFar / (i + 1)) * 100
        rates.push({
          round: i + 1,
          rate: Math.round(rate * 100) / 100 // 保留两位小数
        })
      }
      
      return rates
    })
    
    // 初始化图表
    const initChart = () => {
      if (!chartContainer.value) return
      
      // 如果图表已存在，先销毁
      if (chartInstance) {
        chartInstance.dispose()
      }
      
      chartInstance = echarts.init(chartContainer.value)
      
      const rounds = cumulativeSuccessRate.value.map(item => item.round)
      const rates = cumulativeSuccessRate.value.map(item => item.rate)
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const param = params[0]
            return `第${param.value[0]}轮<br/>累计成功率: ${param.value[1]}%`
          }
        },
        grid: {
          left: '10%',
          right: '10%',
          top: '15%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          name: '轮次',
          data: rounds,
          nameLocation: 'middle',
          nameGap: 30,
          nameTextStyle: {
            fontSize: 12,
            color: '#606266'
          }
        },
        yAxis: {
          type: 'value',
          name: '成功率 (%)',
          min: 0,
          max: 100,
          nameLocation: 'middle',
          nameGap: 50,
          nameTextStyle: {
            fontSize: 12,
            color: '#606266'
          },
          axisLabel: {
            formatter: '{value}%'
          }
        },
        series: [
          {
            name: '累计成功率',
            type: 'line',
            data: rates.map((rate, index) => [rounds[index], rate]),
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              color: '#409EFF',
              width: 2
            },
            itemStyle: {
              color: '#409EFF'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                  { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
                ]
              }
            }
          }
        ]
      }
      
      chartInstance.setOption(option)
    }
    
    // 监听实验结果变化，更新图表
    watch(
      () => [experimentResults.value.length, experimentRunning.value],
      () => {
        if (!experimentRunning.value && experimentResults.value.length > 0) {
          // 实验结束后自动弹出图表
          nextTick(() => {
            showChartDialog.value = true
            // 延迟一下再初始化图表，确保弹窗已渲染
            setTimeout(() => {
              initChart()
              // 监听窗口大小变化，自动调整图表大小
              if (chartInstance) {
                window.addEventListener('resize', handleChartResize)
              }
            }, 100)
          })
        }
      },
      { deep: true }
    )
    
    // 监听弹窗显示状态，更新图表
    watch(showChartDialog, (visible) => {
      if (visible && experimentResults.value.length > 0) {
        nextTick(() => {
          initChart()
          // 监听窗口大小变化，自动调整图表大小
          if (chartInstance) {
            window.addEventListener('resize', handleChartResize)
          }
        })
      }
    })
    
    // 处理图表大小调整
    const handleChartResize = () => {
      if (chartInstance) {
        chartInstance.resize()
      }
    }
    
    // 组件卸载时销毁图表
    onUnmounted(() => {
      window.removeEventListener('resize', handleChartResize)
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
    })
    
    // 开始实验
    const startExperiment = async () => {
      try {
        experimentRunning.value = true
        experimentStopRequested.value = false
        currentExperimentRound.value = 0
        experimentResults.value = []
        
        ElMessage.success('实验启动成功！')
        
        // 创建实验会话（全机器人节点）
        const response = await axios.post('/api/sessions', {
          nodeCount: experimentConfig.nodeCount,
          faultyNodes: experimentConfig.faultyNodes,
          robotNodes: experimentConfig.nodeCount, // 全部为机器人节点
          topology: 'full',
          branchCount: 2,
          proposalValue: 0,
          proposalContent: '实验共识',
          maliciousProposer: false,
          allowTampering: false,
          messageDeliveryRate: experimentConfig.reliability
        })
        
        experimentSessionId.value = response.data.sessionId
        
        // 开始多轮实验
        for (let round = 1; round <= experimentConfig.rounds; round++) {
          if (experimentStopRequested.value) {
            break
          }
          if (!experimentRunning.value) break // 检查是否被停止
          
          currentExperimentRound.value = round
          
          const startTime = Date.now()
          
          // 触发一轮共识（通过重置轮次）
          const resetResponse = await axios.post(`/api/sessions/${experimentSessionId.value}/reset-round`)
          const actualRound = resetResponse.data.currentRound || round
          console.log(`[实验] 触发第${round}轮共识，后端实际轮次: ${actualRound}`)
          
          // 等待足够的时间，让后端开始共识流程并发送消息
          // 加速模式：机器人节点现在立即初始化，无延迟
          // 机器人节点需要：pre-prepare (立即) + prepare (立即) + commit (立即) = 约0.05s
          // 设置等待时间为500ms，匹配后端加速后的实际时间
          await new Promise(resolve => setTimeout(resolve, 500))
          
          // 等待共识完成（使用后端返回的实际轮次）
          const result = await waitForConsensus(experimentSessionId.value, actualRound)
          if (experimentStopRequested.value || result.aborted) {
            break
          }
          
          const duration = Date.now() - startTime
          
          experimentResults.value.push({
            round: round,
            success: result.success,
            messageCount: result.messageCount,
            duration: duration,
            failureReason: result.failureReason || null
          })
          
          // 延迟一下再进行下一轮（确保上一轮完全清理完毕）
          if (experimentStopRequested.value) {
            break
          }

          await new Promise(resolve => setTimeout(resolve, 1500))
        }
        
        experimentRunning.value = false
        const wasStopped = experimentStopRequested.value
        await cleanupExperimentSession()
        experimentStopRequested.value = false
        experimentRunning.value = false
        if (!wasStopped) {
          currentExperimentRound.value = experimentConfig.rounds
          ElMessage.success('实验完成！')
        }
        
      } catch (error) {
        console.error('实验失败:', error)
        ElMessage.error('实验启动失败: ' + (error.response?.data?.detail || error.message))
        experimentRunning.value = false
        await cleanupExperimentSession()
        experimentStopRequested.value = false
      }
    }
    
    const cleanupExperimentSession = async () => {
      if (!experimentSessionId.value) return
      try {
        await axios.delete(`/api/sessions/${experimentSessionId.value}`)
      } catch (error) {
        console.warn('清理实验会话失败', error)
      } finally {
        experimentSessionId.value = null
      }
    }
    
    // 等待共识完成
    const waitForConsensus = async (sessionId, round, maxWait = 10000) => {
      const startTime = Date.now()
      const n = experimentConfig.nodeCount
      // 使用PBFT标准：f = floor((n-1)/3)，需要超过2f个commit消息
      // 注意：所有节点都是好节点，都会发送commit消息
      const f = Math.floor((n - 1) / 3)
      const requiredCommit = 2 * f // 需要超过2f个commit消息（使用>判断）
      const buildResult = (success, messageCount, reason = null, aborted = false) => ({
        success,
        messageCount,
        aborted,
        failureReason: success ? null : reason
      })
      const parseHistoryResult = (history, targetRound) => {
        if (!Array.isArray(history)) return null
        const entry = history.find(item => item.round === targetRound)
        if (!entry) return null
        const statusText = entry.status || ''
        const description = entry.description || ''
        const success = statusText.includes('成功') && !statusText.includes('失败')
        let reason = null
        if (!success) {
          if (statusText.includes('超时')) {
            reason = '超时'
          } else if (description) {
            reason = description
          } else {
            reason = statusText || '失败'
          }
        }
        return { success, reason }
      }
      const describeFailure = (baseReason, commitCount) => {
        if (!baseReason) {
          return commitCount > requiredCommit ? '未知失败' : '消息不足'
        }
        if (baseReason.includes('超时') && commitCount <= requiredCommit) {
          return '消息不足（超时）'
        }
        return baseReason
      }
      
      console.log(`[实验] 开始等待第${round}轮共识完成，需要超过${requiredCommit}个commit消息（f=${f}, n=${n}）`)
      
      while (Date.now() - startTime < maxWait) {
        try {
          const response = await axios.get(`/api/sessions/${sessionId}/status`)
          const status = response.data.status
          const phase = response.data.phase
          const currentRound = response.data.currentRound || 1
          const messages = response.data.messages || []
          const history = response.data.history || []
          
          // 如果轮次已经改变，说明这一轮已经结束
          if (currentRound > round) {
            console.log(`[实验] 第${round}轮已结束，当前轮次: ${currentRound}`)
            console.log(`[实验] 总消息数: ${messages.length}`)
            console.log(`[实验] 所有消息详情:`, messages.map(m => ({ 
              round: m.round, 
              roundType: typeof m.round,
              type: m.type, 
              from: m.from,
              to: m.to,
              phase: m.phase
            })))
            
            // 使用宽松匹配：round字段可能是数字或字符串
            const roundMessages = messages.filter(m => {
              const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
              return msgRound === round
            })
            console.log(`[实验] 第${round}轮消息数: ${roundMessages.length}`)
            
            const commitMessages = roundMessages.filter(m => m.type === 'commit')
            console.log(`[实验] 第${round}轮commit消息:`, commitMessages.map(m => ({ from: m.from, to: m.to, round: m.round })))
            
            // 使用PBFT标准：需要超过2f个commit消息（所有节点都是好节点）
            const historyResult = parseHistoryResult(history, round)
            if (historyResult) {
              const failureReason = historyResult.success ? null : describeFailure(historyResult.reason, commitMessages.length)
              console.log(`[实验] 第${round}轮历史记录结果: ${historyResult.success ? '成功' : '失败'}，原因: ${failureReason || '无'}`)
              return buildResult(historyResult.success, roundMessages.length, failureReason)
            }
            const success = commitMessages.length > requiredCommit
            console.log(`[实验] 第${round}轮结果: ${success ? '成功' : '失败'}, commit消息数: ${commitMessages.length}（需要超过${requiredCommit}个）`)
            return buildResult(success, roundMessages.length, success ? null : '轮次重置')
          }
          
          // 如果后端已经完成共识
          if (status === 'completed' && currentRound === round) {
            const roundMessages = messages.filter(m => {
              const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
              return msgRound === round
            })
            const commitMessages = roundMessages.filter(m => m.type === 'commit')
            // 使用PBFT标准：需要超过2f个commit消息（所有节点都是好节点）
            const historyResult = parseHistoryResult(history, round)
            if (historyResult) {
              const failureReason = historyResult.success ? null : describeFailure(historyResult.reason, commitMessages.length)
              console.log(`[实验] 第${round}轮共识完成（来自历史）: ${historyResult.success ? '成功' : '失败'}, commit消息数: ${commitMessages.length}`)
              return buildResult(historyResult.success, roundMessages.length, failureReason)
            }
            const success = commitMessages.length > requiredCommit
            console.log(`[实验] 第${round}轮共识完成: ${success ? '成功' : '失败'}, commit消息数: ${commitMessages.length}（需要超过${requiredCommit}个）`)
            return buildResult(success, roundMessages.length, success ? null : '消息不足')
          }
          
          // 如果还在运行中，检查消息数量
          if (status === 'running' && currentRound === round) {
            const roundMessages = messages.filter(m => {
              const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
              return msgRound === round
            })
            const commitMessages = roundMessages.filter(m => m.type === 'commit')
            
            // 如果收到足够的commit消息（超过2f个），等待后端完成判断
            if (commitMessages.length > requiredCommit) {
              console.log(`[实验] 第${round}轮收到足够commit消息(${commitMessages.length}，需要超过${requiredCommit}个)，等待后端确认...`)
              // 等待后端完成共识判断（最多等3秒）
              let waitCount = 0
              while (waitCount < 6) {
                await new Promise(resolve => setTimeout(resolve, 500))
                const checkResponse = await axios.get(`/api/sessions/${sessionId}/status`)
                const checkHistory = checkResponse.data.history || []
                const historyResult = parseHistoryResult(checkHistory, round)
                if (historyResult) {
                  const failureReason = historyResult.success ? null : describeFailure(historyResult.reason, commitMessages.length)
                  console.log(`[实验] 第${round}轮等待确认后根据历史结果判定: ${historyResult.success ? '成功' : '失败'}`)
                  return buildResult(historyResult.success, messages.filter(m => {
                    const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
                    return msgRound === round
                  }).length, failureReason)
                }
                if (checkResponse.data.status === 'completed' || checkResponse.data.currentRound > round) {
                  const finalMessages = checkResponse.data.messages || []
                  const finalRoundMessages = finalMessages.filter(m => {
                    const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
                    return msgRound === round
                  })
                  const finalCommitMessages = finalRoundMessages.filter(m => m.type === 'commit')
                  // 使用PBFT标准：需要超过2f个commit消息（所有节点都是好节点）
                  const success = finalCommitMessages.length > requiredCommit
                  console.log(`[实验] 第${round}轮最终结果: ${success ? '成功' : '失败'}, commit消息数: ${finalCommitMessages.length}（需要超过${requiredCommit}个）`)
                  return buildResult(success, finalRoundMessages.length, success ? null : '消息不足')
                }
                waitCount++
              }
            }
          }
          
          await new Promise(resolve => setTimeout(resolve, 500))
        } catch (error) {
          if (experimentStopRequested.value && error.response?.status === 404) {
            return buildResult(false, 0, '实验终止', true)
          }
          console.error('检查共识状态失败:', error)
        }
      }
      
      // 超时（10秒），检查最后一次状态
      console.log(`[实验] 第${round}轮等待超时（10秒），检查最终状态...`)
      try {
        const response = await axios.get(`/api/sessions/${sessionId}/status`)
        const messages = response.data.messages || []
        console.log(`[实验] 超时检查 - 总消息数: ${messages.length}`)
        console.log(`[实验] 超时检查 - 消息示例:`, messages.slice(0, 5).map(m => ({ round: m.round, type: m.type, from: m.from })))
        
        const roundMessages = messages.filter(m => {
          const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
          return msgRound === round
        })
        const commitMessages = roundMessages.filter(m => m.type === 'commit')
        
        // 即使超时，如果收到足够消息也算成功（使用PBFT标准：需要超过2f个commit消息）
        const success = commitMessages.length > requiredCommit
        console.log(`[实验] 第${round}轮超时检查结果: ${success ? '成功' : '失败'}, commit消息数: ${commitMessages.length}（需要超过${requiredCommit}个）`)
        
        return buildResult(success, roundMessages.length, success ? null : '超时', experimentStopRequested.value)
      } catch (error) {
        console.error(`[实验] 第${round}轮超时检查失败:`, error)
        return buildResult(false, 0, '状态查询失败', experimentStopRequested.value)
      }
    }
    
    // 停止实验
    const stopExperiment = async () => {
      if (!experimentRunning.value && !experimentSessionId.value) {
        ElMessage.info('当前没有正在运行的实验')
        return
      }
      experimentStopRequested.value = true
      experimentRunning.value = false
      await cleanupExperimentSession()
      ElMessage.success('实验已停止')
    }
    
    // 导出实验结果
    const exportResults = () => {
      const data = {
        config: experimentConfig,
        results: experimentResults.value,
        statistics: {
          totalRounds: experimentResults.value.length,
          successCount: successCount.value,
          failureCount: failureCount.value,
          successRate: successRate.value
        }
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `experiment-results-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('结果已导出！')
    }
    
    return {
      formRef,
      qrContainer,
      creating,
      sessionInfo,
      formData,
      rules,
      nodeLinks,
      getTopologyName,
      createSession,
      copyLink,
      resetForm,
      // 演示相关
      demoDialogVisible,
      simulating,
      simulationRounds,
      currentRound,
      currentSimulation,
      topologyRef,
      animationSpeed,
      showDemo,
      onRoundChange,
      playAnimation,
      // 实验相关
      experimentRunning,
      currentExperimentRound,
      experimentResults,
      experimentConfig,
      successCount,
      failureCount,
      successRate,
      startExperiment,
      stopExperiment,
      exportResults,
      chartContainer,
      showChartDialog,
      VideoPlay
    }
  }
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #d1d5db 0%, #e5e7eb 100%);
}

.header {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  color: #1f2937;
  text-align: center;
  padding: 30px 20px;
  height: auto !important;
}

.header h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 300;
  text-shadow: none;
}

.header p {
  margin: 10px 0 0 0;
  opacity: 0.8;
  font-size: 1.1rem;
}

.main-content {
  padding: 40px;
}

.config-card, .qr-card, .welcome-card {
  height: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card-header {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
}

.config-form {
  padding: 20px 0;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 0.9rem;
}

.session-info {
  padding: 20px 0;
}

.qr-section {
  margin: 30px 0;
  text-align: center;
}

.qr-section h3 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.qr-container {
  display: inline-block;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.qr-tip {
  margin-top: 15px;
  color: #606266;
  font-size: 0.9rem;
}

.node-links {
  margin-top: 30px;
}

.node-links h3 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.welcome-content {
  text-align: center;
  padding: 60px 20px;
  color: #606266;
}

.welcome-content h2 {
  margin: 20px 0;
  color: #2c3e50;
}

.welcome-content p {
  margin: 10px 0;
  line-height: 1.6;
}

/* 演示对话框样式 */
.demo-container {
  padding: 20px;
}

.demo-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.topology-section,
.table-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.topology-section {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.topology-section h3,
.table-section h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 1.3rem;
  text-align: center;
}

/* 浮动控制面板 */
.floating-controls {
  position: absolute;
  top: 60px;
  left: 20px;
  z-index: 100;
  width: 360px;
}

.control-card {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
}

.control-card :deep(.el-card__header) {
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px 12px 0 0;
}

.control-card :deep(.el-card__header .card-header) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.control-card :deep(.el-card__body) {
  padding: 20px;
}

.control-section {
  margin-bottom: 20px;
}

.control-section:last-child {
  margin-bottom: 0;
}

.control-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.speed-display {
  text-align: center;
  margin-top: 12px;
}

.control-card :deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-card :deep(.el-radio-button) {
  width: 100%;
}

.control-card :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 10px 15px;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .floating-controls {
    position: static;
    width: 100%;
    margin-bottom: 20px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .floating-controls {
    width: 320px;
  }
}

/* 实验模块样式 */
.experiment-card {
  margin-top: 40px;
}

.experiment-content h3 {
  font-size: 1.2rem;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e4e7ed;
}

.experiment-config,
.experiment-progress,
.experiment-results {
  height: 100%;
}

.chart-container {
  background: #fff;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  margin-bottom: 15px;
}

.chart-dialog-content {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
}

.stat-item {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.danger {
  color: #f56c6c;
}

.stat-value.primary {
  color: #409eff;
}

.results-list {
  margin-top: 20px;
}

.result-item {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 10px;
  border-left: 4px solid #e4e7ed;
  transition: all 0.3s;
}

.result-item.success {
  border-left-color: #67c23a;
  background: #f0f9ff;
}

.result-item.failure {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.result-item:hover {
  transform: translateX(5px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.round-label {
  font-weight: 600;
  color: #2c3e50;
}

.result-details {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #606266;
}

.result-details span {
  display: flex;
  align-items: center;
}

.failure-reason {
  margin-top: 8px;
}

.failure-reason .el-tag {
  background: #ffffff;
  color: #606266;
  border-color: #dcdfe6;
}
</style> 