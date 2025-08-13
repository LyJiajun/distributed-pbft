<template>
  <div class="join-page">
    <el-container>
      <el-header class="header">
        <h1>Auto-Assign Node</h1>
        <p>Scan QR code or enter session ID to join the consensus process</p>
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
              <el-descriptions-item label="Session ID">{{ sessionInfo.sessionId }}</el-descriptions-item>
              <el-descriptions-item label="Total Nodes">{{ sessionInfo.nodeCount }}</el-descriptions-item>
              <el-descriptions-item label="Faulty Nodes">{{ sessionInfo.faultyNodes }}</el-descriptions-item>
              <el-descriptions-item label="Topology">{{ getTopologyName(sessionInfo.topology) }}</el-descriptions-item>
              <el-descriptions-item label="Proposal Value">{{ sessionInfo.proposalValue }}</el-descriptions-item>
              <el-descriptions-item label="Status">{{ sessionInfo.status }}</el-descriptions-item>
            </el-descriptions>
            
            <div class="auto-assign-section">
              <div class="assign-info">
                <h3>Auto Node Assignment</h3>
                <p>The system will automatically assign you an available node, no manual selection required.</p>
                
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
                        <div class="stat-label">Connected Nodes</div>
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
              
              <div class="join-actions">
                <el-button 
                  type="primary" 
                  size="large" 
                  @click="autoAssignAndJoin"
                  :loading="joining"
                  :disabled="sessionInfo.nodeCount === connectedNodes.length"
                >
                  {{ sessionInfo.nodeCount === connectedNodes.length ? 'All nodes occupied' : 'Auto-assign and Join' }}
                </el-button>
                
                <el-button 
                  size="large" 
                  @click="goBack"
                >
                  Back
                </el-button>
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
        full: 'Full Connected',
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
      if (nodeId === 0) return 'Initiate proposals, participate in consensus'
      return 'Participate in consensus, vote'
    }
    
    const getNodeResponsibilities = (nodeId) => {
      if (nodeId === 0) return 'Initiate consensus proposals, coordinate other nodes'
      return 'Validate proposals, send prepare and commit messages'
    }
    
    const autoAssignAndJoin = async () => {
      joining.value = true
      try {
        // Call backend API to auto-assign node
        const response = await axios.post(`/api/sessions/${sessionId}/assign-node`)
        const { nodeId } = response.data
        
        ElMessage.success(`Assigned node ${nodeId}`)
        
        // Navigate to node page
        router.push(`/node/${sessionId}/${nodeId}`)
      } catch (error) {
        if (error.response?.status === 409) {
          ElMessage.error('All nodes are occupied, please try again later')
        } else {
          ElMessage.error('Failed to assign node, please try again')
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
        ElMessage.error('Failed to load session information')
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  text-align: center;
  padding: 20px;
}

.header h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 300;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header p {
  margin: 10px 0 0 0;
  opacity: 0.9;
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