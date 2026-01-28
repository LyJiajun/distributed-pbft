<template>
  <div class="join-page">
    <el-container>
      <el-header class="header">
        <h1>Auto-Assign Node</h1>
        <p>Scan QR code or enter session ID to join consensus process</p>
      </el-header>
      
      <el-main class="main-content">
        <el-card class="join-card">
          <template #header>
            <div class="card-header">
                  <span>Session Information</span>
            </div>
          </template>
          
          <div v-if="sessionInfo" class="session-details">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="会话ID">{{ sessionInfo.sessionId }}</el-descriptions-item>
              <el-descriptions-item label="Total Nodes">{{ sessionInfo.nodeCount }}</el-descriptions-item>
              <el-descriptions-item label="Faulty Nodes">{{ sessionInfo.faultyNodes }}</el-descriptions-item>
              <el-descriptions-item label="Topology">{{ getTopologyName(sessionInfo.topology) }}</el-descriptions-item>
              <el-descriptions-item label="Proposal Value">{{ sessionInfo.proposalValue }}</el-descriptions-item>
              <el-descriptions-item label="状态">{{ sessionInfo.status }}</el-descriptions-item>
            </el-descriptions>
            
            <div class="auto-assign-section">
              <div class="assign-info">
                <h3>Auto Node Assignment</h3>
                <p>System will automatically assign an available node for you, no manual selection needed.</p>
                
                <div class="session-stats">
                  <el-row :gutter="20">
                    <el-col :span="12">
                      <div class="stat-item">
                        <div class="stat-number">{{ sessionInfo.nodeCount }}</div>
                        <div class="stat-label">Total Nodes</div>
                      </div>
                    </el-col>
                    <el-col :span="12">
                      <div class="stat-item">
                        <div class="stat-number">{{ connectedNodes.length }}</div>
                        <div class="stat-label">已连接节点</div>
                      </div>
                    </el-col>
                  </el-row>
                </div>
                
                <div class="available-nodes">
                  <h4>Node Status</h4>
                  <div class="nodes-grid">
                    <div 
                      v-for="i in sessionInfo.nodeCount" 
                      :key="i-1"
                      class="node-status-item"
                      :class="{
                        'proposer': (i-1) === 0,
                        'connected': connectedNodes.includes(i-1),
                        'available': !connectedNodes.includes(i-1)
                      }"
                    >
                      <div class="node-number">{{ i-1 }}</div>
                      <div class="node-role">{{ getNodeRole(i-1) }}</div>
                      <div class="node-status">
                        <el-tag 
                          :type="connectedNodes.includes(i-1) ? 'success' : 'info'" 
                          size="small"
                        >
                          {{ connectedNodes.includes(i-1) ? 'Occupied' : 'Available' }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="join-actions flex flex-col gap-3">
                <!-- 自动分配并加入按钮 -->
                <button
                  @click="autoAssignAndJoin"
                  :disabled="joining || sessionInfo.nodeCount === connectedNodes.length"
                  class="w-full bg-blue-100 dark:bg-blue-900 border-l-4 border-blue-500 dark:border-blue-700 text-blue-900 dark:text-blue-100 p-4 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-blue-200 dark:hover:bg-blue-800 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  <svg
                    v-if="!joining"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    fill="none"
                    class="h-6 w-6 flex-shrink-0 mr-2 text-blue-600"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                      stroke-width="2"
                      stroke-linejoin="round"
                      stroke-linecap="round"
                    ></path>
                  </svg>
                  <span class="text-base font-semibold">
                    {{ joining ? 'Joining...' : (sessionInfo.nodeCount === connectedNodes.length ? 'All Nodes Occupied' : 'Auto-Assign and Join') }}
                  </span>
                </button>
                
                <!-- 返回按钮 -->
                <button
                  @click="goBack"
                  class="w-full bg-gray-100 dark:bg-gray-700 border-l-4 border-gray-500 dark:border-gray-600 text-gray-900 dark:text-gray-100 p-4 rounded-lg flex items-center justify-center transition duration-300 ease-in-out hover:bg-gray-200 dark:hover:bg-gray-600 transform hover:scale-105"
                >
                  <svg
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    fill="none"
                    class="h-6 w-6 flex-shrink-0 mr-2 text-gray-600"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M10 19l-7-7m0 0l7-7m-7 7h18"
                      stroke-width="2"
                      stroke-linejoin="round"
                      stroke-linecap="round"
                    ></path>
                  </svg>
                  <span class="text-base font-semibold">Back</span>
                </button>
              </div>
            </div>
          </div>
          
          <div v-else class="loading-section">
            <el-skeleton :rows="6" animated />
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'JoinPage',
  setup() {
    const route = useRoute()
    const router = useRouter()
    
    const sessionId = route.params.sessionId
    const sessionInfo = ref(null)
    const selectedNode = ref(null)
    const connectedNodes = ref([])
    const joining = ref(false)
    
    const getTopologyName = (topology) => {
      const names = {
        full: 'Full Mesh',
        ring: 'Ring',
        star: 'Star',
        tree: 'Tree'
      }
      return names[topology] || topology
    }
    
    const getNodeRole = (nodeId) => {
      if (nodeId === 0) return 'Proposer'
      return 'Validator'
    }
    
    const getNodePermissions = (nodeId) => {
      if (nodeId === 0) return '发起提议，参与共识'
      return '参与共识，投票'
    }
    
    const getNodeResponsibilities = (nodeId) => {
      if (nodeId === 0) return '发起共识提议，协调其他节点'
      return '验证提议，发送准备和提交消息'
    }
    
    const autoAssignAndJoin = async () => {
      joining.value = true
      try {
        // Call backend API to auto-assign node
        const response = await axios.post(`/api/sessions/${sessionId}/assign-node`)
        const { nodeId } = response.data
        
        ElMessage.success(`Node assigned ${nodeId}`)
        
        // Navigate to node page
        router.push(`/node/${sessionId}/${nodeId}`)
      } catch (error) {
        if (error.response?.status === 409) {
          ElMessage.error('All nodes occupied, please retry later')
        } else {
          ElMessage.error('Failed to assign node, please retry')
        }
      } finally {
        joining.value = false
      }
    }
    
    const goBack = () => {
      router.push('/')
    }
    
    const loadSessionInfo = async () => {
      try {
        const response = await axios.get(`/api/sessions/${sessionId}`)
        sessionInfo.value = {
          sessionId: sessionId,
          nodeCount: response.data.config.nodeCount,
          faultyNodes: response.data.config.faultyNodes,
          topology: response.data.config.topology,
          proposalValue: response.data.config.proposalValue,
          status: response.data.status
        }
        
        // Get connected nodes
        await loadConnectedNodes()
      } catch (error) {
        ElMessage.error('Failed to load session info')
        router.push('/')
      }
    }
    
    const loadConnectedNodes = async () => {
      try {
        const response = await axios.get(`/api/sessions/${sessionId}/connected-nodes`)
        connectedNodes.value = response.data.connectedNodes
      } catch (error) {
        console.error('Failed to load connected nodes:', error)
        connectedNodes.value = []
      }
    }
    
    let refreshInterval = null
    
    onMounted(() => {
      loadSessionInfo()
      
      // Refresh connected node status every 3 seconds
      refreshInterval = setInterval(() => {
        if (sessionInfo.value) {
          loadConnectedNodes()
        }
      }, 3000)
    })
    
    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })
    
    return {
      sessionInfo,
      connectedNodes,
      joining,
      getTopologyName,
      getNodeRole,
      autoAssignAndJoin,
      goBack
    }
  }
}
</script>

<style scoped>
.join-page {
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
  display: flex;
  justify-content: center;
}

.join-card {
  max-width: 800px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card-header {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
}

.session-details {
  padding: 20px 0;
}

.auto-assign-section {
  margin-top: 30px;
}

.assign-info h3 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.assign-info p {
  color: #606266;
  margin-bottom: 20px;
  line-height: 1.6;
}

.session-stats {
  margin: 20px 0;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-number {
  font-size: 1.8rem;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #606266;
}

.available-nodes {
  margin: 20px 0;
}

.available-nodes h4 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.node-status-item {
  padding: 20px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
  background: white;
}

.node-status-item.proposer {
  border-color: #e6a23c;
  background: #fdf6ec;
}

.node-status-item.connected {
  border-color: #67c23a;
  background: #f0f9ff;
  opacity: 0.7;
}

.node-status-item.available {
  border-color: #409eff;
  background: #f0f9ff;
}

.node-number {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 8px;
}

.node-role {
  font-size: 0.9rem;
  color: #606266;
  margin-bottom: 10px;
}

.node-status {
  display: flex;
  justify-content: center;
}

.join-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.loading-section {
  padding: 40px 0;
}
</style> 