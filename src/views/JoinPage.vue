<template>
  <div class="join-page">
    <el-container>
      <el-header class="header">
        <h1>自动分配节点</h1>
        <p>扫描二维码或输入会话ID加入共识过程</p>
      </el-header>
      
      <el-main class="main-content">
        <el-card class="join-card">
          <template #header>
            <div class="card-header">
                  <span>会话信息</span>
            </div>
          </template>
          
          <div v-if="sessionInfo" class="session-details">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="会话ID">{{ sessionInfo.sessionId }}</el-descriptions-item>
              <el-descriptions-item label="总节点数">{{ sessionInfo.nodeCount }}</el-descriptions-item>
              <el-descriptions-item label="故障节点数">{{ sessionInfo.faultyNodes }}</el-descriptions-item>
              <el-descriptions-item label="拓扑结构">{{ getTopologyName(sessionInfo.topology) }}</el-descriptions-item>
              <el-descriptions-item label="提议值">{{ sessionInfo.proposalValue }}</el-descriptions-item>
              <el-descriptions-item label="状态">{{ sessionInfo.status }}</el-descriptions-item>
            </el-descriptions>
            
            <div class="auto-assign-section">
              <div class="assign-info">
                <h3>自动节点分配</h3>
                <p>系统将自动为您分配一个可用节点，无需手动选择。</p>
                
                <div class="session-stats">
                  <el-row :gutter="20">
                    <el-col :span="12">
                      <div class="stat-item">
                        <div class="stat-number">{{ sessionInfo.nodeCount }}</div>
                        <div class="stat-label">总节点数</div>
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
                  <h4>节点状态</h4>
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
                          {{ connectedNodes.includes(i-1) ? '已占用' : '可用' }}
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
                  {{ sessionInfo.nodeCount === connectedNodes.length ? '所有节点已占用' : '自动分配并加入' }}
                </el-button>
                
                <el-button 
                  size="large" 
                  @click="goBack"
                >
                  返回
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
        full: '全连接',
        ring: '环形',
        star: '星形',
        tree: '树形'
      }
      return names[topology] || topology
    }
    
    const getNodeRole = (nodeId) => {
      if (nodeId === 0) return '提议者'
      return '验证者'
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
        
        ElMessage.success(`已分配节点 ${nodeId}`)
        
        // Navigate to node page
        router.push(`/node/${sessionId}/${nodeId}`)
      } catch (error) {
        if (error.response?.status === 409) {
          ElMessage.error('所有节点已占用，请稍后重试')
        } else {
          ElMessage.error('分配节点失败，请重试')
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
        ElMessage.error('加载会话信息失败')
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