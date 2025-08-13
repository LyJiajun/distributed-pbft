<template>
  <div class="home-page">
    <el-container>
      <el-header class="header">
        <h1>分布式PBFT共识系统</h1>
        <p>创建共识会话，让用户扮演节点参与共识过程</p>
      </el-header>
      
      <el-main class="main-content">
        <el-row :gutter="40">
          <!-- 左侧：参数配置 -->
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
                <el-form-item label="节点总数" prop="nodeCount">
                  <el-input-number 
                    v-model="formData.nodeCount" 
                    :min="3" 
                    :max="20"
                    controls-position="right"
                  />
                  <span class="form-tip">建议3-20个节点</span>
                </el-form-item>
                
                <el-form-item label="容错节点数" prop="faultyNodes">
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
                
                <el-form-item label="分支数" v-if="formData.topology === 'tree'" prop="branchCount">
                  <el-input-number 
                    v-model="formData.branchCount" 
                    :min="2" 
                    :max="5"
                    controls-position="right"
                  />
                </el-form-item>
                
                <el-form-item label="提议值" prop="proposalValue">
                  <el-radio-group v-model="formData.proposalValue">
                    <el-radio :label="0">0</el-radio>
                    <el-radio :label="1">1</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item label="提议内容" prop="proposalContent">
                  <el-input 
                    v-model="formData.proposalContent" 
                    type="textarea" 
                    :rows="3"
                    placeholder="请输入提议的具体内容，例如：'今天中午吃火锅'、'选择方案A'等"
                  />
                  <span class="form-tip">输入具体的提议内容，将在节点页面显示</span>
                </el-form-item>
                
                <el-form-item label="恶意提议者" prop="maliciousProposer">
                  <el-switch v-model="formData.maliciousProposer" />
                  <span class="form-tip">开启后提议者可能发送错误值</span>
                </el-form-item>
                
                <el-form-item label="允许消息篡改" prop="allowTampering">
                  <el-switch v-model="formData.allowTampering" />
                  <span class="form-tip">开启后故障节点可能篡改消息</span>
                </el-form-item>
                
                <el-form-item label="消息传达概率" prop="messageDeliveryRate">
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
                  <el-button type="primary" @click="createSession" :loading="creating">
                    创建共识会话
                  </el-button>
                  <el-button @click="resetForm">重置</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
          
          <!-- 右侧：二维码和会话信息 -->
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
                  <el-descriptions-item label="节点总数">{{ sessionInfo.config.nodeCount }}</el-descriptions-item>
                  <el-descriptions-item label="容错节点数">{{ sessionInfo.config.faultyNodes }}</el-descriptions-item>
                  <el-descriptions-item label="拓扑结构">{{ getTopologyName(sessionInfo.config.topology) }}</el-descriptions-item>
                  <el-descriptions-item label="提议值">{{ sessionInfo.config.proposalValue }}</el-descriptions-item>
                  <el-descriptions-item label="提议内容">{{ sessionInfo.config.proposalContent || '无' }}</el-descriptions-item>
                  <el-descriptions-item label="消息传达概率">{{ sessionInfo.config.messageDeliveryRate }}%</el-descriptions-item>
                  <el-descriptions-item label="状态">{{ sessionInfo.status }}</el-descriptions-item>
                </el-descriptions>
                
                <div class="qr-section">
                  <h3>扫描二维码加入节点</h3>
                  <div class="qr-container" ref="qrContainer"></div>
                  <p class="qr-tip">其他用户扫描此二维码即可加入共识过程</p>
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
                  <span>欢迎使用</span>
                </div>
              </template>
              
              <div class="welcome-content">
                <el-icon size="60" color="#409EFF"><Connection /></el-icon>
                <h2>分布式PBFT共识系统</h2>
                <p>配置参数后创建共识会话，生成二维码供其他用户扫描加入</p>
                <p>每个用户将扮演一个节点，实时参与共识过程</p>
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
        { required: true, message: '请输入节点总数', trigger: 'blur' }
      ],
      faultyNodes: [
        { required: true, message: '请输入容错节点数', trigger: 'blur' }
      ],
      topology: [
        { required: true, message: '请选择拓扑结构', trigger: 'change' }
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
        console.error('创建会话失败:', error)
        ElMessage.error('创建会话失败，请重试')
      } finally {
        creating.value = false
      }
    }
    
    const generateQRCode = async () => {
      if (!qrContainer.value || !sessionInfo.value) {
        console.log('QR容器或会话信息不存在:', { qrContainer: !!qrContainer.value, sessionInfo: !!sessionInfo.value })
        return
      }
      
      try {
        // 清空容器
        qrContainer.value.innerHTML = ''
        
        const qrData = {
          sessionId: sessionInfo.value.sessionId,
          nodeCount: sessionInfo.value.config.nodeCount,
          joinUrl: `${window.location.origin}/join/${sessionInfo.value.sessionId}`,
          autoAssign: true,
          description: '扫描二维码自动分配节点'
        }
        
        console.log('生成二维码数据:', qrData)
        
        // 方法1: 直接使用容器
        try {
          await QRCode.toCanvas(qrContainer.value, JSON.stringify(qrData), {
            width: 200,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF'
            }
          })
          console.log('二维码生成成功 (方法1)')
          return
        } catch (error1) {
          console.log('方法1失败，尝试方法2:', error1)
        }
        
        // 方法2: 创建canvas元素
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
          console.log('二维码生成成功 (方法2)')
          return
        } catch (error2) {
          console.log('方法2失败，尝试方法3:', error2)
        }
        
        // 方法3: 使用toDataURL
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
          console.log('二维码生成成功 (方法3)')
          return
        } catch (error3) {
          console.log('方法3失败:', error3)
        }
        
        throw new Error('所有二维码生成方法都失败了')
        
      } catch (error) {
        console.error('生成二维码失败:', error)
        // 显示错误信息和备用链接
        qrContainer.value.innerHTML = `
          <div style="color: red; padding: 20px; text-align: center;">
            <div>二维码生成失败</div>
            <div style="margin-top: 10px; font-size: 12px;">
              请使用以下链接加入:<br>
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
    
    // 监听sessionInfo变化，自动生成二维码
    watch(sessionInfo, async (newSessionInfo) => {
      if (newSessionInfo) {
        console.log('会话信息更新，准备生成二维码')
        // 等待DOM更新
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