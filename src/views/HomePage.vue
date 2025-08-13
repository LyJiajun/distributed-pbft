<template>
  <div class="home-page">
    <el-container>
      <el-header class="header">
        <h1>Distributed PBFT Consensus System</h1>
        <p>Create consensus sessions and let users play nodes to participate in the consensus process</p>
      </el-header>
      
      <el-main class="main-content">
        <el-row :gutter="40">
          <!-- Left: Parameter Configuration -->
          <el-col :span="12">
            <el-card class="config-card">
              <template #header>
                <div class="card-header">
                  <span>Consensus Parameter Configuration</span>
                </div>
              </template>
              
              <el-form 
                :model="formData" 
                :rules="rules" 
                ref="formRef" 
                label-width="120px"
                class="config-form"
              >
                <el-form-item label="Total Nodes" prop="nodeCount">
                  <el-input-number 
                    v-model="formData.nodeCount" 
                    :min="3" 
                    :max="20"
                    controls-position="right"
                  />
                  <span class="form-tip">Recommended 3-20 nodes</span>
                </el-form-item>
                
                <el-form-item label="Faulty Nodes" prop="faultyNodes">
                  <el-input-number 
                    v-model="formData.faultyNodes" 
                    :min="0" 
                    :max="formData.nodeCount"
                    controls-position="right"
                  />
                  <span class="form-tip">All nodes can choose to become Byzantine nodes</span>
                </el-form-item>
                
                <el-form-item label="Topology" prop="topology">
                  <el-select v-model="formData.topology" placeholder="Select topology">
                    <el-option label="Full Connected" value="full" />
                    <el-option label="Ring" value="ring" />
                    <el-option label="Star" value="star" />
                    <el-option label="Tree" value="tree" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="Branch Count" v-if="formData.topology === 'tree'" prop="branchCount">
                  <el-input-number 
                    v-model="formData.branchCount" 
                    :min="2" 
                    :max="5"
                    controls-position="right"
                  />
                </el-form-item>
                
                <el-form-item label="Proposal Value" prop="proposalValue">
                  <el-radio-group v-model="formData.proposalValue">
                    <el-radio :label="0">0</el-radio>
                    <el-radio :label="1">1</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item label="Proposal Content" prop="proposalContent">
                  <el-input 
                    v-model="formData.proposalContent" 
                    type="textarea" 
                    :rows="3"
                    placeholder="Enter specific proposal content, e.g., 'Have hotpot for lunch today', 'Choose plan A', etc."
                  />
                  <span class="form-tip">Enter specific proposal content that will be displayed on the node page</span>
                </el-form-item>
                
                <el-form-item label="Malicious Proposer" prop="maliciousProposer">
                  <el-switch v-model="formData.maliciousProposer" />
                  <span class="form-tip">When enabled, the proposer may send incorrect values</span>
                </el-form-item>
                
                <el-form-item label="Allow Message Tampering" prop="allowTampering">
                  <el-switch v-model="formData.allowTampering" />
                  <span class="form-tip">When enabled, faulty nodes may tamper with messages</span>
                </el-form-item>
                
                <el-form-item label="Message Delivery Rate" prop="messageDeliveryRate">
                  <el-slider 
                    v-model="formData.messageDeliveryRate" 
                    :min="50" 
                    :max="100" 
                    :step="5"
                    show-stops
                    show-input
                    :format-tooltip="(val) => `${val}%`"
                  />
                  <span class="form-tip">Simulate network packet loss to test the impact of network reliability on consensus</span>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="createSession" :loading="creating">
                    Create Consensus Session
                  </el-button>
                  <el-button @click="resetForm">Reset</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
          
          <!-- Right: QR Code and Session Information -->
          <el-col :span="12">
            <el-card class="qr-card" v-if="sessionInfo">
              <template #header>
                <div class="card-header">
                  <span>Session Information</span>
                </div>
              </template>
              
              <div class="session-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Session ID">{{ sessionInfo.sessionId }}</el-descriptions-item>
                  <el-descriptions-item label="Total Nodes">{{ sessionInfo.config.nodeCount }}</el-descriptions-item>
                  <el-descriptions-item label="Faulty Nodes">{{ sessionInfo.config.faultyNodes }}</el-descriptions-item>
                  <el-descriptions-item label="Topology">{{ getTopologyName(sessionInfo.config.topology) }}</el-descriptions-item>
                  <el-descriptions-item label="Proposal Value">{{ sessionInfo.config.proposalValue }}</el-descriptions-item>
                  <el-descriptions-item label="Proposal Content">{{ sessionInfo.config.proposalContent || 'None' }}</el-descriptions-item>
                  <el-descriptions-item label="Message Delivery Rate">{{ sessionInfo.config.messageDeliveryRate }}%</el-descriptions-item>
                  <el-descriptions-item label="Status">{{ sessionInfo.status }}</el-descriptions-item>
                </el-descriptions>
                
                <div class="qr-section">
                  <h3>Scan QR Code to Join Node</h3>
                  <div class="qr-container" ref="qrContainer"></div>
                  <p class="qr-tip">Other users can scan this QR code to join the consensus process</p>
                </div>
                
                <div class="node-links">
                  <h3>Node Links</h3>
                  <el-table :data="nodeLinks" style="width: 100%">
                    <el-table-column prop="nodeId" label="Node ID" width="80" />
                    <el-table-column prop="url" label="Link" />
                    <el-table-column label="Action" width="120">
                      <template #default="scope">
                        <el-button size="small" @click="copyLink(scope.row.url)">
                          Copy Link
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
                  <span>Welcome</span>
                </div>
              </template>
              
              <div class="welcome-content">
                <el-icon size="60" color="#409EFF"><Connection /></el-icon>
                <h2>Distributed PBFT Consensus System</h2>
                <p>Configure parameters to create a consensus session and generate QR codes for other users to scan and join</p>
                <p>Each user will play a node and participate in the consensus process in real-time</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import axios from 'axios'

export default {
  name: 'HomePage',
  setup() {
    const formRef = ref(null)
    const qrContainer = ref(null)
    const creating = ref(false)
    const sessionInfo = ref(null)
    
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
        { required: true, message: 'Please enter total number of nodes', trigger: 'blur' }
      ],
      faultyNodes: [
        { required: true, message: 'Please enter number of faulty nodes', trigger: 'blur' }
      ],
      topology: [
        { required: true, message: 'Please select topology', trigger: 'change' }
      ]
    }
    
    const nodeLinks = computed(() => {
      if (!sessionInfo.value) return []
      
      const links = []
      for (let i = 0; i < sessionInfo.value.config.nodeCount; i++) {
        links.push({
          nodeId: i,
          url: `${window.location.origin}/node/${sessionInfo.value.sessionId}/${i}`
        })
      }
      return links
    })
    
    const getTopologyName = (topology) => {
      const names = {
        full: 'Full Connected',
        ring: 'Ring',
        star: 'Star',
        tree: 'Tree'
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
          topology: formData.topology,
          branchCount: formData.branchCount,
          proposalValue: formData.proposalValue,
          proposalContent: formData.proposalContent,
          maliciousProposer: formData.maliciousProposer,
          allowTampering: formData.allowTampering,
          messageDeliveryRate: formData.messageDeliveryRate
        })
        
        sessionInfo.value = response.data
        
        ElMessage.success('Consensus session created successfully!')
      } catch (error) {
        console.error('Failed to create session:', error)
        ElMessage.error('Failed to create session, please try again')
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
            <div>QR code generation failed</div>
            <div style="margin-top: 10px; font-size: 12px;">
              Please use the following link to join:<br>
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
        ElMessage.success('Link copied to clipboard')
      } catch (error) {
        ElMessage.error('Copy failed')
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
      resetForm
    }
  }
}
</script>

<style scoped>
.home-page {
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
</style> 