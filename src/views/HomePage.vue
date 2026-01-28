<template>
  <div class="home-page">
    <el-container>
      <el-main class="main-content">
        <div class="page-container">
          <!-- 左侧导航 -->
          <div class="side-navigation">
            <div class="radio-container">
              <input :checked="currentPage === 'consensus'" id="radio-consensus" name="page-nav" type="radio" @change="currentPage = 'consensus'" />
              <label for="radio-consensus">Consensus</label>
              <input :checked="currentPage === 'experiment'" id="radio-experiment" name="page-nav" type="radio" @change="currentPage = 'experiment'" />
              <label for="radio-experiment">Experiment</label>
              <div class="glider-container">
                <div class="glider"></div>
              </div>
            </div>
          </div>

          <!-- 右侧内容区 -->
          <div class="content-area">
            <!-- 共识系统页面 -->
            <div v-show="currentPage === 'consensus'" class="page-content">
              <el-row :gutter="40">
                <!-- Left: Parameter Configuration -->
                <el-col :span="12">
            <el-card class="config-card">
              <template #header>
                <div class="card-header">
                  <span>Consensus Parameters</span>
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
                  <span class="form-tip">Recommended: 3-20 nodes</span>
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
                    <el-option label="Full Mesh" value="full" />
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
                    <el-radio :value="0">0</el-radio>
                    <el-radio :value="1">1</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item label="Proposal Content" prop="proposalContent">
                  <el-input 
                    v-model="formData.proposalContent" 
                    type="textarea" 
                    :rows="3"
                    placeholder="Enter specific proposal content, e.g., 'Have hotpot for lunch', 'Choose Plan A', etc."
                  />
                  <span class="form-tip">Enter specific proposal content to display on node pages</span>
                </el-form-item>
                
                <el-form-item label="Malicious Proposer" prop="maliciousProposer">
                  <el-switch v-model="formData.maliciousProposer" />
                  <span class="form-tip">When enabled, proposer may send incorrect values</span>
                </el-form-item>
                
                <el-form-item label="Allow Tampering" prop="allowTampering">
                  <el-switch v-model="formData.allowTampering" />
                  <span class="form-tip">When enabled, faulty nodes may tamper messages</span>
                </el-form-item>
                
                <el-form-item label="Message Delivery Rate" prop="messageDeliveryRate">
                  <el-slider 
                    v-model="formData.messageDeliveryRate" 
                    :min="50" 
                    :max="100" 
                    :step="1"
                    show-stops
                    show-input
                    :format-tooltip="(val) => `${val}%`"
                  />
                  <span class="form-tip">Simulate packet loss to test impact of network reliability on consensus</span>
                </el-form-item>
                
                <el-form-item>
                  <div class="flex flex-col gap-3 w-full">
                    <!-- 创建Session按钮 -->
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
                      <span class="text-sm font-semibold">{{ creating ? 'Creating...' : 'Create Consensus Session' }}</span>
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
                      <span class="text-sm font-semibold">{{ simulating ? 'Demonstrating...' : 'Animate Consensus Process' }}</span>
                    </button>
                    
                    <!-- Reset按钮 -->
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
                      <span class="text-sm font-semibold">Reset</span>
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
                  <span>Session Information</span>
                </div>
              </template>
              
              <div class="session-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="SessionID">{{ sessionInfo.sessionId }}</el-descriptions-item>
                  <el-descriptions-item label="Total Nodes">{{ sessionInfo.config.nodeCount }}</el-descriptions-item>
                  <el-descriptions-item label="Faulty Nodes">{{ sessionInfo.config.faultyNodes }}</el-descriptions-item>
                  <el-descriptions-item label="Robot Nodes">{{ sessionInfo.config.robotNodes }}</el-descriptions-item>
                  <el-descriptions-item label="Human Nodes">{{ sessionInfo.config.nodeCount - sessionInfo.config.robotNodes }}</el-descriptions-item>
                  <el-descriptions-item label="Topology">{{ getTopologyName(sessionInfo.config.topology) }}</el-descriptions-item>
                  <el-descriptions-item label="Proposal Value">{{ sessionInfo.config.proposalValue }}</el-descriptions-item>
                  <el-descriptions-item label="Proposal Content">{{ sessionInfo.config.proposalContent || 'None' }}</el-descriptions-item>
                  <el-descriptions-item label="Message Delivery Rate">{{ sessionInfo.config.messageDeliveryRate }}%</el-descriptions-item>
                  <el-descriptions-item label="状态">{{ sessionInfo.status }}</el-descriptions-item>
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
                    <el-table-column label="Actions" width="120">
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
                <p>Configure parameters to create consensus session and generate QR code for other users to join</p>
                <p>Each user will play a node role and participate in consensus process in real-time</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
            </div>
        
            <!-- Experiment页面 -->
            <div v-show="currentPage === 'experiment'" class="page-content">
              <el-row :gutter="40">
                <el-col :span="24">
                  <el-card class="experiment-card">
              <template #header>
                <div class="card-header" style="display: flex; align-items: center; justify-content: space-between;">
                  <span>🔬 Communication Reliability Impact on Consensus Experiment</span>
                  <el-tag :type="experimentRunning ? 'success' : 'info'" effect="dark">
                    {{ experimentRunning ? 'Experiment Running' : 'Not Running' }}
                  </el-tag>
                </div>
              </template>
              
              <div class="experiment-content">
                <el-row :gutter="40">
                  <!-- 左侧：Experiment Configuration -->
                  <el-col :span="8">
                    <div class="experiment-config">
                      <h3>Experiment Configuration</h3>
                      <el-form label-width="120px">
                        <el-form-item label="Total Nodes">
                          <el-input-number 
                            v-model="experimentConfig.nodeCount" 
                            :min="4" 
                            :max="10"
                            :disabled="experimentRunning"
                            controls-position="right"
                          />
                        </el-form-item>
                        
                        <el-form-item label="Faulty Nodes">
                          <el-input-number 
                            v-model="experimentConfig.faultyNodes" 
                            :min="0" 
                            :max="Math.floor((experimentConfig.nodeCount - 1) / 3)"
                            :disabled="experimentRunning"
                            controls-position="right"
                          />
                          <div class="form-tip">Byzantine fault tolerance requires: f < n/3</div>
                        </el-form-item>
                        
                        <el-form-item label="Topology">
                          <el-select 
                            v-model="experimentConfig.topology" 
                            placeholder="Select topology"
                            :disabled="experimentRunning"
                          >
                            <el-option label="Full Mesh" value="full" />
                            <el-option label="Ring" value="ring" />
                            <el-option label="Star" value="star" />
                            <el-option label="Tree" value="tree" />
                          </el-select>
                        </el-form-item>
                        
                        <el-form-item label="Branch Count" v-if="experimentConfig.topology === 'tree'">
                          <el-input-number 
                            v-model="experimentConfig.branchCount" 
                            :min="2" 
                            :max="5"
                            :disabled="experimentRunning"
                            controls-position="right"
                          />
                        </el-form-item>
                        
                        <el-form-item label="Reliability Configuration">
                          <el-radio-group 
                            v-model="experimentConfig.reliabilityMode"
                            :disabled="experimentRunning"
                          >
                            <el-radio value="uniform">Uniform Reliability</el-radio>
                            <el-radio value="custom">Custom Matrix</el-radio>
                          </el-radio-group>
                          <!-- Custom Matrix编辑按钮 -->
                          <el-button
                            v-if="experimentConfig.reliabilityMode === 'custom'"
                            type="primary"
                            size="small"
                            style="margin-top: 10px; width: 100%;"
                            :disabled="experimentRunning"
                            @click="showMatrixEditor = true"
                          >
                            <el-icon><Edit /></el-icon>
                            Edit Reliability Matrix
                          </el-button>
                        </el-form-item>
                        
                        <el-form-item 
                          v-if="experimentConfig.reliabilityMode === 'uniform'" 
                          label="Communication Reliability"
                        >
                          <el-slider 
                            v-model="experimentConfig.reliability" 
                            :min="50" 
                            :max="100" 
                            :step="1"
                            :disabled="experimentRunning"
                            show-stops
                            show-input
                            :format-tooltip="(val) => `${val}%`"
                          />
                        </el-form-item>
                        
                        <el-form-item label="Experiment Rounds">
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
                            v-if="!experimentRunning && !allProposersRunning"
                            type="primary" 
                            @click="startExperiment"
                            :icon="VideoPlay"
                            style="width: 100%;"
                          >
                            Start Experiment
                          </el-button>
                          <el-button 
                            v-if="experimentRunning || allProposersRunning"
                            type="danger" 
                            @click="stopExperiment"
                            style="width: 100%;"
                          >
                            Stop Experiment
                          </el-button>
                        </el-form-item>
                        
                        <el-form-item>
                          <el-button 
                            v-if="!experimentRunning && !allProposersRunning"
                            type="success" 
                            @click="runAllProposersExperiment"
                            style="width: 100%;"
                          >
                            <el-icon><Histogram /></el-icon>
                            Run All Proposers Experiment
                          </el-button>
                          <div v-if="allProposersRunning" style="text-align: center; color: #67C23A; font-weight: 600;">
                            Testing Proposer {{ currentProposerIndex }} / {{ experimentConfig.nodeCount }}
                          </div>
                        </el-form-item>
                      </el-form>
                    </div>
                  </el-col>
                  
                  <!-- 中间：拓扑编辑器或Experiment Progress -->
                  <el-col :span="8">
                    <!-- Experiment Progress -->
                    <div class="experiment-progress">
                      <h3>Experiment Progress</h3>
                      <div v-if="experimentRunning || experimentResults.length > 0">
                        <el-statistic title="Current Round" :value="currentExperimentRound" :suffix="`/ ${experimentConfig.rounds}`" />
                        
                        <!-- 波浪形加载动画 -->
                        <div class="wave-loader-container" style="margin-top: 20px;">
                          <ul class="wave-menu" :class="{ 'completed': !experimentRunning }">
                            <li v-for="i in 9" :key="i"></li>
                          </ul>
                          <div class="progress-text">
                            {{ Math.round((currentExperimentRound / experimentConfig.rounds) * 100) }}%
                          </div>
                        </div>
                        
                        <div class="stats-grid" style="margin-top: 30px;">
                          <div class="stat-item">
                            <div class="stat-label">Successful Rounds</div>
                            <div class="stat-value success">{{ successCount }}</div>
                          </div>
                          <div class="stat-item">
                            <div class="stat-label">Failed Rounds</div>
                            <div class="stat-value danger">{{ failureCount }}</div>
                          </div>
                          <div class="stat-item">
                            <div class="stat-label">Success Rate</div>
                            <div class="stat-value primary">{{ successRate }}%</div>
                          </div>
                        </div>
                      </div>
                      <el-empty 
                        v-else 
                        description="No Experiment Data" 
                        :image-size="100"
                      />
                    </div>
                  </el-col>
                  
                  <!-- 右侧：Experiment Results -->
                  <el-col :span="8">
                    <div class="experiment-results">
                      <h3>Experiment Results</h3>
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
                                {{ result.success ? 'Success' : 'Failure' }}
                              </el-tag>
                            </div>
                            <div class="result-details">
                              <span>Message Count: {{ result.messageCount }}</span>
                              <span>Duration: {{ result.duration }}ms</span>
                            </div>
                            <div v-if="!result.success && result.failureReason" class="failure-reason">
                              <el-tag size="small" type="info">Reason: {{ result.failureReason }}</el-tag>
                            </div>
                          </div>
                        </el-scrollbar>
                        
                        <el-button 
                          type="primary" 
                          @click="showChartDialog = true"
                          style="width: 100%; margin-top: 15px;"
                          :disabled="experimentResults.length === 0"
                        >
                          View Success Rate Trend
                        </el-button>
                        
                        <el-button 
                          type="default" 
                          @click="exportResults"
                          style="width: 100%; margin-top: 10px;"
                          :disabled="experimentResults.length === 0"
                        >
                          Export Results
                        </el-button>
                      </div>
                      <el-empty 
                        v-else 
                        description="No Experiment Results" 
                        :image-size="100"
                      />
                    </div>
                  </el-col>
                </el-row>
                
                <!-- All Proposers Experiment Results Chart -->
                <el-row v-if="allProposersResults.length > 0" :gutter="20" style="margin-top: 30px;">
                  <el-col :span="24">
                    <el-card class="experiment-card">
                      <template #header>
                        <div class="card-header">
                          <span>All Proposers Comparison Results</span>
                        </div>
                      </template>
                      
                      <div ref="allProposersChartContainer" style="width: 100%; height: 500px;"></div>
                      
                      <div style="margin-top: 20px; text-align: center;">
                        <el-button type="primary" @click="exportAllProposersResults">
                          Export Comparison Results
                        </el-button>
                        <el-button 
                          type="warning" 
                          @click="calculateCorrelations"
                          :disabled="historicalData.length < 3"
                        >
                          Calculate Correlations ({{ historicalData.length }} experiments)
                        </el-button>
                        <el-button 
                          type="danger" 
                          plain
                          @click="clearHistoricalData"
                          :disabled="historicalData.length === 0"
                        >
                          Clear Historical Data
                        </el-button>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </div>
            </el-card>
                </el-col>
              </el-row>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>
    
    <!-- 可靠度矩阵编辑器对话框 -->
    <el-dialog
      v-model="showMatrixEditor"
      title="Edit Reliability Matrix"
      width="95%"
      top="2vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <TopologyEditor
        v-if="showMatrixEditor"
        :node-count="experimentConfig.nodeCount"
        :topology="experimentConfig.topology"
        :branch-count="experimentConfig.branchCount"
        :default-reliability="experimentConfig.reliability"
        :initial-matrix="experimentConfig.customReliabilityMatrix"
        :proposer-id="experimentConfig.proposerId"
        :random-min="experimentConfig.randomMin"
        :random-max="experimentConfig.randomMax"
        @update:reliabilityMatrix="onReliabilityMatrixUpdate"
        @update:proposerId="onProposerIdUpdate"
        @update:randomRange="onRandomRangeUpdate"
      />
    </el-dialog>
    
    <!-- 动画演示对话框 -->
    <el-dialog
      v-model="demoDialogVisible"
      title="PBFT Consensus Process Animation"
      width="90%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="demo-container">
        <div class="demo-content">
          <div class="topology-section">
            <h3>Network Topology and Message Transmission Animation</h3>
            
            <!-- 浮动控制面板 -->
            <div class="floating-controls">
              <el-card class="control-card">
                <template #header>
                  <div class="card-header">
                    <span>🎮 Animation Controls</span>
                  </div>
                </template>
                
                <!-- Session Information -->
                <div class="control-section">
                  <el-tag type="success" style="width: 100%; padding: 8px 12px; font-size: 14px;">
                    Real Session Message History
                  </el-tag>
                </div>
                
                <!-- Round选择 -->
                <div class="control-section" v-if="simulationRounds.length > 1">
                  <label class="control-label">Select Round</label>
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
                  <el-text type="info">Only 1 round of consensus available</el-text>
                </div>
                
                <!-- Animation Speed控制 -->
                <div class="control-section">
                  <label class="control-label">⚡ Animation Speed</label>
                  <el-slider 
                    v-model="animationSpeed" 
                    :min="0.5" 
                    :max="3" 
                    :step="0.25"
                    :marks="{ 0.5: '0.5x', 1: '1x', 1.5: '1.5x', 2: '2x', 2.5: '2.5x', 3: '3x' }"
                    show-stops
                  />
                  <div class="speed-display">
                    <el-tag type="primary">Current Speed: {{ animationSpeed }}x</el-tag>
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
                    <span class="ml-2 text-sm font-semibold">Replay Animation</span>
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
            <h3>Message Details Table</h3>
            <PBFTTable
              v-if="currentSimulation"
              :filteredSimulationResult="currentSimulation"
              :nodeCount="formData.nodeCount"
            />
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="demoDialogVisible = false">Close</el-button>
      </template>
    </el-dialog>
    
    <!-- Success Rate趋势图弹窗 -->
    <el-dialog
      v-model="showChartDialog"
      title="Cumulative Success Rate Trend"
      width="70%"
      :close-on-click-modal="true"
      destroy-on-close
      center
    >
      <div v-if="experimentResults.length > 0" class="chart-dialog-content">
        <div ref="chartContainer" style="width: 100%; height: 500px;"></div>
      </div>
      <el-empty v-else description="No Data" />
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, Edit, Histogram } from '@element-plus/icons-vue'
import QRCode from 'qrcode'
import axios from 'axios'
import * as echarts from 'echarts'
import Topology from '@/components/Topology.vue'
import PBFTTable from '@/components/PBFTTable.vue'
import TopologyEditor from '@/components/TopologyEditor.vue'

export default {
  name: 'HomePage',
  components: {
    VideoPlay,
    Topology,
    PBFTTable,
    TopologyEditor
  },
  setup() {
    // 页面导航
    const currentPage = ref('consensus')
    
    const formRef = ref(null)
    const qrContainer = ref(null)
    const creating = ref(false)
    const sessionInfo = ref(null)
    
    // 演示相关
    const demoDialogVisible = ref(false)
    const showMatrixEditor = ref(false)
    const simulating = ref(false)
    const simulationRounds = ref([])
    const currentRound = ref(1)
    const currentSimulation = ref(null)
    const topologyRef = ref(null)
    const animationSpeed = ref(1) // Animation Speed：0.5x, 1x, 1.5x, 2x等
    
    // Experiment相关
    const experimentRunning = ref(false)
    const experimentStopRequested = ref(false)
    const currentExperimentRound = ref(0)
    const experimentResults = ref([])
    const experimentSessionId = ref(null)
    const chartContainer = ref(null)
    const showChartDialog = ref(false)
    const theoreticalSuccessRate = ref(0) // Theoretical Success Rate
    const averageReliabilityTheoretical = ref(0) // 基于平均直连可靠度的理论值
    let chartInstance = null
    
    // All Proposers Experiment相关
    const allProposersRunning = ref(false)
    const currentProposerIndex = ref(0)
    const allProposersResults = ref([]) // 存储所有主节点的实验结果
    const allProposersChartContainer = ref(null)
    let allProposersChartInstance = null
    
    // 历史数据存储
    const historicalData = ref([])  // 存储历史实验数据
    const correlationResults = ref(null)  // 存储相关性分析结果
    const shouldSaveHistory = ref(true)  // 控制是否保存历史数据的标志
    
    const experimentConfig = reactive({
      nodeCount: 6,
      faultyNodes: 1,
      reliability: 80,
      rounds: 30,
      topology: 'full',
      branchCount: 2,
      reliabilityMode: 'uniform',  // 'uniform' | 'custom'
      customReliabilityMatrix: null,  // Custom Reliability Matrix
      proposerId: 0,  // Primary node ID
      randomMin: 50,  // Random range minimum
      randomMax: 100  // Random range maximum
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
        { required: true, message: '请输入Total Nodes', trigger: 'blur' }
      ],
      faultyNodes: [
        { required: true, message: '请输入Faulty Nodes', trigger: 'blur' }
      ],
      topology: [
        { required: true, message: '请Select topology', trigger: 'change' }
      ]
    }
    
    const nodeLinks = computed(() => {
      if (!sessionInfo.value) return []
      
      const links = []
      const robotNodes = sessionInfo.value.config.robotNodes || 0
      const humanNodeCount = sessionInfo.value.config.nodeCount - robotNodes
      
      // 只显示人类Node的Link，从robotNodes开始编号
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
        full: 'Full Mesh',
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
        robotNodes: formData.nodeCount - formData.faultyNodes, // 自动计算Robot Nodes
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
        ElMessage.error('Failed to create session, please retry')
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
            <div>二维码生成Failure</div>
            <div style="margin-top: 10px; font-size: 12px;">
              请使用以下Link加入：<br>
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
        ElMessage.error('Failed to copy')
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
        
        // 检查是否已创建Session
        if (!sessionInfo.value) {
          ElMessage.error('Please create consensus session first!')
          return
        }
        
        simulationRounds.value = []
        
        // 1. 先获取Round列表
        const roundsResponse = await axios.get(`/api/sessions/${sessionInfo.value.sessionId}/history`)
        const rounds = roundsResponse.data.rounds || [1]
        
        console.log('Available的Round:', rounds)
        
        // 2. 获取所有Round的数据
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
          ElMessage.error('Session does not exist or has expired, please create new session')
        } else {
          ElMessage.error('Failed to get session history, please retry later')
        }
      } finally {
        simulating.value = false
      }
    }
    
    const onRoundChange = (roundId) => {
      const round = simulationRounds.value.find(r => r.id === roundId)
      if (round) {
        currentSimulation.value = round.data
        // 自动播放新Round的动画
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
    
    // Experiment统计计算属性
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
    
    // 计算每轮的累计Success Rate（用于图表）
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
    
    // ========== 相关性分析工具函数 ==========
    
    // 计算排名
    const getRanks = (arr) => {
      const sorted = arr.map((val, idx) => ({ val, idx })).sort((a, b) => a.val - b.val)
      const ranks = new Array(arr.length)
      for (let i = 0; i < sorted.length; i++) {
        ranks[sorted[i].idx] = i + 1
      }
      return ranks
    }
    
    // 计算 Spearman 相关系数
    const calculateSpearman = (x, y) => {
      if (x.length !== y.length || x.length === 0) return null
      
      const n = x.length
      const rankX = getRanks(x)
      const rankY = getRanks(y)
      
      // 计算 d^2 的和
      let sumD2 = 0
      for (let i = 0; i < n; i++) {
        const d = rankX[i] - rankY[i]
        sumD2 += d * d
      }
      
      // Spearman 公式: ρ = 1 - (6 * Σd²) / (n * (n² - 1))
      const rho = 1 - (6 * sumD2) / (n * (n * n - 1))
      return rho
    }
    
    // 计算相关性分析
    const calculateCorrelations = () => {
      if (historicalData.value.length < 3) {
        ElMessage.warning('Need at least 3 historical experiments for correlation analysis')
        return
      }
      
      const CV_values = historicalData.value.map(d => d.CV)
      const CV_out_values = historicalData.value.map(d => d.CV_out)
      const CV_link_values = historicalData.value.map(d => d.CV_link)
      
      // 计算 Spearman 相关系数
      const rho_CV_CVout = calculateSpearman(CV_values, CV_out_values)
      const rho_CV_CVlink = calculateSpearman(CV_values, CV_link_values)
      
      correlationResults.value = {
        rho_CV_CVout,
        rho_CV_CVlink,
        sampleSize: historicalData.value.length
      }
      
      console.log('[Correlation Analysis] Results:')
      console.log(`  - Sample Size: ${historicalData.value.length}`)
      console.log(`  - ρ(CV, CV_out): ${rho_CV_CVout?.toFixed(4) || 'N/A'}`)
      console.log(`  - ρ(CV, CV_link): ${rho_CV_CVlink?.toFixed(4) || 'N/A'}`)
      
      // 临时禁用历史数据保存，重新渲染图表
      shouldSaveHistory.value = false
      nextTick(() => {
        createAllProposersChart()
        // 重新启用历史数据保存
        shouldSaveHistory.value = true
      })
      
      ElMessage.success('Correlation analysis completed!')
    }
    
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
      
      console.log('[Chart] initChart 开始')
      console.log(`  - theoreticalSuccessRate: ${theoreticalSuccessRate.value}`)
      console.log(`  - averageReliabilityTheoretical: ${averageReliabilityTheoretical.value}`)
      
      // 构建系列数据
      const seriesData = [
        {
          name: 'Experimental Success Rate',
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
      
      // 如果有Theoretical Success Rate，添加理论值虚线
      if (theoreticalSuccessRate.value > 0) {
        seriesData.push({
          name: 'Theoretical Success Rate',
          type: 'line',
          data: rounds.map(round => [round, theoreticalSuccessRate.value]),
          lineStyle: {
            color: '#F56C6C',
            width: 2,
            type: 'dashed' // 虚线
          },
          symbol: 'none', // 不显示数据点
          itemStyle: {
            color: '#F56C6C'
          },
          markLine: {
            silent: true,
            symbol: 'none',
            label: {
              show: true,
              position: 'end',
              formatter: `理论值: ${theoreticalSuccessRate.value.toFixed(2)}%`,
              color: '#F56C6C'
            }
          }
        })
      }
      
      // 如果有平均可靠度理论值，添加红色实线
      if (averageReliabilityTheoretical.value > 0) {
        seriesData.push({
          name: 'Average Reliability Theoretical',
          type: 'line',
          data: rounds.map(round => [round, averageReliabilityTheoretical.value]),
          lineStyle: {
            color: '#E6001A',  // 深红色
            width: 2,
            type: 'solid'  // 实线
          },
          symbol: 'none',
          itemStyle: {
            color: '#E6001A'
          },
          markLine: {
            silent: true,
            symbol: 'none',
            label: {
              show: true,
              position: 'end',
              formatter: `平均值理论: ${averageReliabilityTheoretical.value.toFixed(2)}%`,
              color: '#E6001A'
            }
          }
        })
      }
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            let result = `第${params[0].value[0]}轮<br/>`
            params.forEach(param => {
              result += `${param.seriesName}: ${param.value[1].toFixed(2)}%<br/>`
            })
            return result
          }
        },
        legend: {
          data: (() => {
            const legendData = ['Experimental Success Rate']
            if (theoreticalSuccessRate.value > 0) legendData.push('Theoretical Success Rate')
            if (averageReliabilityTheoretical.value > 0) legendData.push('Average Reliability Theoretical')
            return legendData
          })(),
          top: '5%',
          left: 'center'
        },
        grid: {
          left: '10%',
          right: '10%',
          top: '20%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          name: 'Round',
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
          name: 'Success Rate (%)',
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
        series: seriesData
      }
      
      chartInstance.setOption(option)
    }
    
    // 监听Experiment Results变化，更新图表
    watch(
      () => [experimentResults.value.length, experimentRunning.value, theoreticalSuccessRate.value, averageReliabilityTheoretical.value],
      () => {
        if (!experimentRunning.value && experimentResults.value.length > 0) {
          // Experiment结束后自动弹出图表
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
    
    // 监听拓扑或节点数变化，清除自定义矩阵
    watch(
      () => [experimentConfig.topology, experimentConfig.nodeCount, experimentConfig.branchCount],
      ([newTopology, newNodeCount, newBranchCount], [oldTopology, oldNodeCount, oldBranchCount]) => {
        // 当拓扑或节点数或分支数改变时，清除自定义矩阵（因为连接关系变了）
        if (oldTopology !== undefined) { // 跳过初始化时的触发
          experimentConfig.customReliabilityMatrix = null
          console.log(`[Experiment] Configuration changed (topology: ${oldTopology}→${newTopology}, nodes: ${oldNodeCount}→${newNodeCount}, branch: ${oldBranchCount}→${newBranchCount}), custom matrix cleared`)
        }
      }
    )
    
    // 监听模式切换，如果从uniform切换到custom且没有矩阵，确保矩阵为null
    watch(
      () => experimentConfig.reliabilityMode,
      (newMode, oldMode) => {
        if (newMode === 'custom' && !experimentConfig.customReliabilityMatrix) {
          console.log('[Experiment] Switched to custom mode, matrix is null (will initialize when opening editor)')
        } else if (newMode === 'uniform') {
          console.log('[Experiment] Switched to uniform mode, custom matrix will be ignored')
        }
      }
    )
    
    // 组件卸载时销毁图表
    onUnmounted(() => {
      window.removeEventListener('resize', handleChartResize)
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
      if (allProposersChartInstance) {
        allProposersChartInstance.dispose()
        allProposersChartInstance = null
      }
    })
    
    // Run All Proposers Experiment（依次让每个节点当主节点）
    const runAllProposersExperiment = async () => {
      try {
        allProposersRunning.value = true
        experimentStopRequested.value = false
        allProposersResults.value = []
        currentProposerIndex.value = 0
        
        const nodeCount = experimentConfig.nodeCount
        ElMessage.success(`Starting All Proposers Experiment: Testing ${nodeCount} proposers...`)
        
        // 依次让每个节点当主节点
        for (let proposerId = 0; proposerId < nodeCount; proposerId++) {
          if (experimentStopRequested.value) {
            ElMessage.warning('Experiment stopped by user')
            break
          }
          
          currentProposerIndex.value = proposerId
          console.log(`\n=== Running Experiment with Proposer ${proposerId} ===`)
          
          // 临时设置主节点ID
          const originalProposerId = experimentConfig.proposerId
          experimentConfig.proposerId = proposerId
          
          try {
            // 创建ExperimentSession
            const response = await axios.post('/api/sessions', {
              nodeCount: experimentConfig.nodeCount,
              faultyNodes: experimentConfig.faultyNodes,
              robotNodes: experimentConfig.nodeCount,
              topology: experimentConfig.topology,
              branchCount: experimentConfig.branchCount,
              proposalValue: 0,
              proposalContent: `Experiment with Proposer ${proposerId}`,
              maliciousProposer: false,
              allowTampering: false,
              messageDeliveryRate: experimentConfig.reliability,
              proposerId: proposerId
            })
            
            const sessionId = response.data.sessionId
            
            // Prepare请求数据
            const requestData = {
              rounds: experimentConfig.rounds
            }
            
            // 如果使用Custom Matrix模式，添加矩阵数据
            if (experimentConfig.reliabilityMode === 'custom' && experimentConfig.customReliabilityMatrix) {
              requestData.customReliabilityMatrix = experimentConfig.customReliabilityMatrix
              
              // 计算平均直连可靠度
              const n = experimentConfig.nodeCount
              const topology = experimentConfig.topology
              let directEdgeCount = 0
              let totalReliability = 0
              
              // 遍历所有直连边（不包括对角线）
              for (let i = 0; i < n; i++) {
                for (let j = 0; j < n; j++) {
                  if (i !== j) {
                    // 检查是否是直连边
                    const isDirect = (() => {
                      if (topology === 'full') return true
                      if (topology === 'ring') return Math.abs(i - j) === 1 || (i === 0 && j === n - 1) || (i === n - 1 && j === 0)
                      if (topology === 'star') return i === 0 || j === 0
                      if (topology === 'tree') {
                        const branchCount = experimentConfig.branchCount
                        const parentOfJ = Math.floor((j - 1) / branchCount)
                        const parentOfI = Math.floor((i - 1) / branchCount)
                        return (i === parentOfJ && j < n) || (j === parentOfI && i < n)
                      }
                      return false
                    })()
                    
                    if (isDirect && experimentConfig.customReliabilityMatrix[i][j] > 0) {
                      totalReliability += experimentConfig.customReliabilityMatrix[i][j]
                      directEdgeCount++
                    }
                  }
                }
              }
              
              const avgReliability = directEdgeCount > 0 ? totalReliability / directEdgeCount : 0
              requestData.averageDirectReliability = avgReliability
              
              console.log(`[All Proposers] Proposer ${proposerId}: 使用自定义可靠度矩阵, 平均直连可靠度=${(avgReliability * 100).toFixed(2)}%`)
            }
            
            // 运行实验
            const batchResponse = await axios.post(
              `/api/sessions/${sessionId}/run-batch-experiment`,
              requestData,
              { timeout: 300000 }
            )
            
            // 保存结果
            const batchData = batchResponse.data
            allProposersResults.value.push({
              proposerId: proposerId,
              theoreticalSuccessRate: batchData.theoreticalSuccessRate,
              experimentalSuccessRate: batchData.experimentalSuccessRate,
              averageReliabilityTheoretical: batchData.averageReliabilityTheoretical || 0,
              successCount: batchData.successCount,
              failureCount: batchData.failureCount,
              totalRounds: batchData.totalRounds,
              results: batchData.results
            })
            
            console.log(`Proposer ${proposerId}: Theoretical=${batchData.theoreticalSuccessRate}%, Experimental=${batchData.experimentalSuccessRate}%, AvgTheoretical=${batchData.averageReliabilityTheoretical || 0}%`)
            
            // 清理session
            await axios.delete(`/api/sessions/${sessionId}`)
            
          } catch (error) {
            console.error(`Experiment with Proposer ${proposerId} failed:`, error)
            allProposersResults.value.push({
              proposerId: proposerId,
              error: error.message,
              theoreticalSuccessRate: 0,
              experimentalSuccessRate: 0
            })
          }
          
          // 恢复原始主节点ID
          experimentConfig.proposerId = originalProposerId
        }
        
        allProposersRunning.value = false
        experimentStopRequested.value = false
        
        // 绘制图表
        await nextTick()
        createAllProposersChart()
        
        ElMessage.success(`All Proposers Experiment completed! Tested ${allProposersResults.value.length} proposers.`)
        
      } catch (error) {
        console.error('All Proposers Experiment failed:', error)
        ElMessage.error('All Proposers Experiment failed: ' + error.message)
        allProposersRunning.value = false
        experimentStopRequested.value = false
      }
    }
    
    // Create All Proposers Comparison Chart
    const createAllProposersChart = () => {
      if (!allProposersChartContainer.value || allProposersResults.value.length === 0) {
        return
      }
      
      // 清理已存在的图表
      if (allProposersChartInstance) {
        allProposersChartInstance.dispose()
      }
      
      // 创建新图表
      allProposersChartInstance = echarts.init(allProposersChartContainer.value)
      
      // 准备数据
      const proposerLabels = allProposersResults.value.map(r => `Node ${r.proposerId}`)
      const theoreticalData = allProposersResults.value.map(r => r.theoreticalSuccessRate)
      const experimentalData = allProposersResults.value.map(r => r.experimentalSuccessRate)
      const averageTheoreticalData = allProposersResults.value.map(r => r.averageReliabilityTheoretical || 0)
      
      // 检查是否有平均理论值
      const hasAverageTheoretical = averageTheoreticalData.some(val => val > 0)
      
      // 计算统计指标（基于理论成功率）
      const P_best = Math.max(...theoreticalData)
      const P_worst = Math.min(...theoreticalData)
      const P_avg = theoreticalData.reduce((sum, val) => sum + val, 0) / theoreticalData.length
      
      // 1. Range: 最大 - 最小
      const deltaRange = P_best - P_worst
      
      // 2. Expected Gain: (P_best - P_avg) / P_avg
      const gainAvg = ((P_best - P_avg) / P_avg) * 100
      
      // 3. Worst-case Improvement: (P_best - P_worst) / P_worst
      const gainWorst = ((P_best - P_worst) / P_worst) * 100
      
      // 4. Coefficient of Variation: σ / μ
      const variance = theoreticalData.reduce((sum, val) => sum + Math.pow(val - P_avg, 2), 0) / theoreticalData.length
      const sigma = Math.sqrt(variance)
      const CV = (sigma / P_avg) * 100
      
      // 5. 节点层面不均匀性（CV_out）- 如果有自定义矩阵
      let CV_out = 0
      let CV_link = 0
      
      if (experimentConfig.reliabilityMode === 'custom' && experimentConfig.customReliabilityMatrix) {
        const matrix = experimentConfig.customReliabilityMatrix
        const n = matrix.length
        
        // 计算每个节点的平均出链可靠度
        const p_out = []
        for (let i = 0; i < n; i++) {
          let sum = 0
          for (let j = 0; j < n; j++) {
            if (i !== j) {
              sum += matrix[i][j]
            }
          }
          p_out.push(sum / (n - 1))
        }
        
        // 计算 p_out 的均值和标准差
        const mu_out = p_out.reduce((sum, val) => sum + val, 0) / n
        const var_out = p_out.reduce((sum, val) => sum + Math.pow(val - mu_out, 2), 0) / n
        const sigma_out = Math.sqrt(var_out)
        CV_out = (sigma_out / mu_out) * 100
        
        // 6. 链路层面不均匀性（CV_link）
        const allLinks = []
        for (let i = 0; i < n; i++) {
          for (let j = 0; j < n; j++) {
            if (i !== j) {
              allLinks.push(matrix[i][j])
            }
          }
        }
        
        const mu_link = allLinks.reduce((sum, val) => sum + val, 0) / allLinks.length
        const var_link = allLinks.reduce((sum, val) => sum + Math.pow(val - mu_link, 2), 0) / allLinks.length
        const sigma_link = Math.sqrt(var_link)
        CV_link = (sigma_link / mu_link) * 100
      }
      
      console.log('[All Proposers Chart] 统计指标:')
      console.log(`  - Range: ${deltaRange.toFixed(2)}%`)
      console.log(`  - Expected Gain: ${gainAvg.toFixed(2)}%`)
      console.log(`  - Worst-case Improvement: ${gainWorst.toFixed(2)}%`)
      console.log(`  - CV: ${CV.toFixed(2)}%`)
      console.log(`  - CV_out (Node-level): ${CV_out.toFixed(2)}%`)
      console.log(`  - CV_link (Link-level): ${CV_link.toFixed(2)}%`)
      
      // 保存历史数据（仅在自定义矩阵模式下，且标志为 true）
      if (shouldSaveHistory.value && experimentConfig.reliabilityMode === 'custom' && CV_out > 0 && CV_link > 0) {
        historicalData.value.push({
          timestamp: new Date().toISOString(),
          nodeCount: experimentConfig.nodeCount,
          topology: experimentConfig.topology,
          CV,
          CV_out,
          CV_link,
          deltaRange,
          gainAvg,
          gainWorst
        })
        console.log(`[Historical Data] Saved experiment #${historicalData.value.length}`)
      }
      
      console.log('[All Proposers Chart] 数据准备:')
      console.log('  - Theoretical:', theoreticalData)
      console.log('  - Experimental:', experimentalData)
      console.log('  - Average Theoretical:', averageTheoreticalData)
      console.log('  - Has Average Theoretical:', hasAverageTheoretical)
      
      // 为每个节点生成不同的颜色
      const colors = [
        '#409EFF', // 蓝色
        '#67C23A', // 绿色
        '#E6A23C', // 橙色
        '#F56C6C', // 红色
        '#909399', // 灰色
        '#B37FEB', // 紫色
        '#13C2C2', // 青色
        '#FA8C16', // 橙黄色
        '#52C41A', // 草绿色
        '#1890FF', // 天蓝色
      ]
      
      const option = {
        title: {
          text: 'Success Rate Comparison by Proposer',
          left: 'center',
          textStyle: {
            fontSize: 18,
            fontWeight: 600
          }
        },
        // 添加图形元素显示统计指标
        graphic: [
          {
            type: 'group',
            right: 40,
            top: 40,  // 和legend同高，在右侧
            children: [
              {
                type: 'rect',
                shape: {
                  width: 280,
                  height: correlationResults.value ? 190 : 155  // 动态调整高度
                },
                style: {
                  fill: 'rgba(255, 255, 255, 0.95)',
                  stroke: '#ddd',
                  lineWidth: 1
                }
              },
              {
                type: 'text',
                style: {
                  text: 'Statistical Metrics',
                  font: 'bold 13px sans-serif',
                  fill: '#333'
                },
                left: 10,
                top: 8
              },
              {
                type: 'text',
                style: {
                  text: `Range (Δ): ${deltaRange.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 30
              },
              {
                type: 'text',
                style: {
                  text: `Expected Gain: ${gainAvg.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 50
              },
              {
                type: 'text',
                style: {
                  text: `Worst-case Improvement: ${gainWorst.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 70
              },
              {
                type: 'text',
                style: {
                  text: `CV: ${CV.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 90
              },
              {
                type: 'text',
                style: {
                  text: `CV_out (Node): ${CV_out.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 110
              },
              {
                type: 'text',
                style: {
                  text: `CV_link (Link): ${CV_link.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 130
              },
              // 添加分隔线
              ...(correlationResults.value ? [{
                type: 'line',
                shape: {
                  x1: 10,
                  y1: 148,
                  x2: 270,
                  y2: 148
                },
                style: {
                  stroke: '#ddd',
                  lineWidth: 1
                }
              },
              {
                type: 'text',
                style: {
                  text: `ρ(CV,CV_out): ${correlationResults.value.rho_CV_CVout?.toFixed(3) || 'N/A'}`,
                  font: '11px sans-serif',
                  fill: '#E6A23C',
                  fontWeight: 'bold'
                },
                left: 10,
                top: 153
              },
              {
                type: 'text',
                style: {
                  text: `ρ(CV,CV_link): ${correlationResults.value.rho_CV_CVlink?.toFixed(3) || 'N/A'}`,
                  font: '11px sans-serif',
                  fill: '#E6A23C',
                  fontWeight: 'bold'
                },
                left: 10,
                top: 168
              },
              {
                type: 'text',
                style: {
                  text: `(n=${correlationResults.value.sampleSize})`,
                  font: '10px sans-serif',
                  fill: '#999'
                },
                left: 235,
                top: 153
              }] : [])
            ]
          }
        ],
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: function(params) {
            let result = `<strong>${params[0].axisValue}</strong><br/>`
            params.forEach(item => {
              result += `${item.marker} ${item.seriesName}: ${item.value}%<br/>`
            })
            return result
          }
        },
        legend: {
          data: (() => {
            const legendData = ['Theoretical Success Rate', 'Experimental Success Rate']
            if (hasAverageTheoretical) legendData.push('Average Reliability Theoretical')
            return legendData
          })(),
          top: 40,
          left: 'center'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '180px',  // 增加顶部空间，为统计框留出位置
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: proposerLabels,
          axisLabel: {
            rotate: 0,
            fontSize: 12
          }
        },
        yAxis: {
          type: 'value',
          name: 'Success Rate (%)',
          min: 0,
          max: 100,
          axisLabel: {
            formatter: '{value}%'
          }
        },
        series: [
          {
            name: 'Theoretical Success Rate',
            type: 'bar',
            data: theoreticalData,
            itemStyle: {
              color: function(params) {
                return colors[params.dataIndex % colors.length]
              },
              opacity: 0.6
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}%',
              fontSize: 10,
              color: '#000',  // 黑色
              fontWeight: 600  // 加粗
            }
          },
          {
            name: 'Experimental Success Rate',
            type: 'bar',
            data: experimentalData,
            itemStyle: {
              color: function(params) {
                return colors[params.dataIndex % colors.length]
              },
              borderColor: '#000',
              borderWidth: 2
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}%',
              fontSize: 10,
              color: '#000',  // 黑色
              fontWeight: 600  // 加粗
            }
          },
          // 添加平均可靠度理论值线（如果存在）
          ...(hasAverageTheoretical ? [{
            name: 'Average Reliability Theoretical',
            type: 'line',
            data: averageTheoreticalData,
            lineStyle: {
              color: '#E6001A',  // 深红色
              width: 1.5,  // 更细的线
              type: 'solid'
            },
            symbol: 'none',  // 不显示数据点
            itemStyle: { 
              color: '#E6001A'
            },
            label: {
              show: false  // 不显示每个点的标签
            },
            markLine: {
              silent: false,
              symbol: ['none', 'none'],  // 两端都不显示箭头
              label: {
                show: true,
                position: 'insideEndBottom',  // 标签在左端底部
                distance: -50,  // 向左偏移
                formatter: function() {
                  // 取第一个非零值作为标签
                  const avgValue = averageTheoreticalData.find(v => v > 0) || 0
                  return `${avgValue.toFixed(2)}%`  // 只显示数值
                },
                color: '#E6001A',
                fontSize: 11,
                fontWeight: 'bold',
                backgroundColor: 'transparent',  // 透明背景
                padding: [2, 4]
              },
              lineStyle: {
                color: '#E6001A',
                width: 1.5,  // 更细的线
                type: 'solid'
              },
              data: [
                {
                  yAxis: averageTheoreticalData[0]  // 使用第一个值作为基准线
                }
              ]
            },
            z: 0  // 最低层级，显示在所有柱状图和标签后面
          }] : [])
        ]
      }
      
      allProposersChartInstance.setOption(option)
      
      // 响应窗口大小变化
      window.addEventListener('resize', () => {
        allProposersChartInstance?.resize()
      })
    }
    
    // Start Experiment
    const startExperiment = async () => {
      try {
        experimentRunning.value = true
        experimentStopRequested.value = false
        currentExperimentRound.value = 0
        experimentResults.value = []
        theoreticalSuccessRate.value = 0
        averageReliabilityTheoretical.value = 0  // 清空平均可靠度理论值
        
        ElMessage.success('Starting experiment, please wait...')
        
        // 创建ExperimentSession（全机器人Node）
        const response = await axios.post('/api/sessions', {
          nodeCount: experimentConfig.nodeCount,
          faultyNodes: experimentConfig.faultyNodes,
          robotNodes: experimentConfig.nodeCount, // 全部为机器人Node
          topology: experimentConfig.topology,
          branchCount: experimentConfig.branchCount,
          proposalValue: 0,
          proposalContent: 'Experiment共识',
          maliciousProposer: false,
          allowTampering: false,
          messageDeliveryRate: experimentConfig.reliability,
          proposerId: experimentConfig.proposerId  // 传递主节点ID
        })
        
        experimentSessionId.value = response.data.sessionId
        
        console.log(`[实验] 开始批量实验: ${experimentConfig.rounds}轮`)
        
        // Prepare请求数据
        const requestData = {
          rounds: experimentConfig.rounds
        }
        
        // 如果使用Custom Matrix模式，添加矩阵数据
        if (experimentConfig.reliabilityMode === 'custom' && experimentConfig.customReliabilityMatrix) {
          requestData.customReliabilityMatrix = experimentConfig.customReliabilityMatrix
          
          // 计算平均直连可靠度
          const n = experimentConfig.nodeCount
          const topology = experimentConfig.topology
          let directEdgeCount = 0
          let totalReliability = 0
          
          // 遍历所有直连边（不包括对角线）
          for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
              if (i !== j) {
                // 检查是否是直连边
                let isDirect = false
                if (topology === 'full') {
                  isDirect = true
                } else if (topology === 'ring') {
                  isDirect = (j === (i + 1) % n) || (i === (j + 1) % n)
                } else if (topology === 'star') {
                  isDirect = i === 0 || j === 0
                } else if (topology === 'tree') {
                  const branchCount = experimentConfig.branchCount
                  const parentOfJ = Math.floor((j - 1) / branchCount)
                  const parentOfI = Math.floor((i - 1) / branchCount)
                  isDirect = (i === parentOfJ && j < n) || (j === parentOfI && i < n)
                }
                
                if (isDirect) {
                  totalReliability += experimentConfig.customReliabilityMatrix[i][j]
                  directEdgeCount++
                }
              }
            }
          }
          
          const avgReliability = directEdgeCount > 0 ? totalReliability / directEdgeCount : 0
          requestData.averageDirectReliability = avgReliability
          
          console.log('[Experiment] 使用自定义可靠度矩阵')
          console.log(`[Experiment] 直连边数量: ${directEdgeCount}, 平均可靠度: ${(avgReliability * 100).toFixed(2)}%`)
          console.log(`[Experiment] 发送 averageDirectReliability = ${avgReliability}`)
        }
        
        // 调用批量ExperimentAPI，后端一次性Complete所有Round
        const batchResponse = await axios.post(
          `/api/sessions/${experimentSessionId.value}/run-batch-experiment`,
          requestData,
          { 
            timeout: 300000 // 5分钟超时
          }
        )
        
        // 获取批量结果
        const batchData = batchResponse.data
        experimentResults.value = batchData.results
        theoreticalSuccessRate.value = batchData.theoreticalSuccessRate
        averageReliabilityTheoretical.value = batchData.averageReliabilityTheoretical || 0
        currentExperimentRound.value = experimentConfig.rounds
        
        console.log(`[Experiment] 批量ExperimentComplete:`)
        console.log(`  - Total Rounds: ${batchData.totalRounds}`)
        console.log(`  - Success: ${batchData.successCount}`)
        console.log(`  - Failure: ${batchData.failureCount}`)
        console.log(`  - Experimental Success Rate: ${batchData.experimentalSuccessRate}%`)
        console.log(`  - Theoretical Success Rate: ${batchData.theoreticalSuccessRate}%`)
        console.log(`  - Average Reliability Theoretical: ${batchData.averageReliabilityTheoretical || 'N/A'}%`)
        if (batchData.averageReliabilityTheoretical) {
          console.log(`  ✓ 平均可靠度理论值已设置: ${averageReliabilityTheoretical.value}%`)
        } else {
          console.log(`  ✗ 未收到平均可靠度理论值`)
        }
        
        experimentRunning.value = false
        await cleanupExperimentSession()
        experimentStopRequested.value = false
        
        ElMessage.success(`Experiment completed!Success Rate: ${batchData.experimentalSuccessRate}% (理论: ${batchData.theoreticalSuccessRate}%)`)
        
      } catch (error) {
        console.error('Experiment failed:', error)
        ElMessage.error('Experiment failed: ' + (error.response?.data?.detail || error.message))
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
        console.warn('清理ExperimentSessionFailure', error)
      } finally {
        experimentSessionId.value = null
      }
    }
    
    // 等待共识Complete
    const waitForConsensus = async (sessionId, round, maxWait = 10000) => {
      const startTime = Date.now()
      const n = experimentConfig.nodeCount
      // 使用PBFT标准：f = floor((n-1)/3)，需要超过2f个commit消息
      // 注意：所有Node都是好Node，都会发送commit消息
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
        const success = statusText.includes('Success') && !statusText.includes('Failure')
        let reason = null
        if (!success) {
          if (statusText.includes('超时')) {
            reason = '超时'
          } else if (description) {
            reason = description
          } else {
            reason = statusText || 'Failure'
          }
        }
        return { success, reason }
      }
      const describeFailure = (baseReason, commitCount) => {
        if (!baseReason) {
          return commitCount > requiredCommit ? '未知Failure' : '消息不足'
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
          
          // 如果Round已经改变，说明这一轮已经结束
          if (currentRound > round) {
            console.log(`[Experiment] 第${round}轮已结束，Current Round: ${currentRound}`)
            console.log(`[Experiment] 总Message Count: ${messages.length}`)
            console.log(`[Experiment] 所有消息详情:`, messages.map(m => ({ 
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
            console.log(`[Experiment] 第${round}轮Message Count: ${roundMessages.length}`)
            
            const commitMessages = roundMessages.filter(m => m.type === 'commit')
            console.log(`[Experiment] 第${round}轮commit消息:`, commitMessages.map(m => ({ from: m.from, to: m.to, round: m.round })))
            
            // 使用PBFT标准：需要超过2f个commit消息（所有Node都是好Node）
            const historyResult = parseHistoryResult(history, round)
            if (historyResult) {
              const failureReason = historyResult.success ? null : describeFailure(historyResult.reason, commitMessages.length)
              console.log(`[Experiment] 第${round}轮历史记录结果: ${historyResult.success ? 'Success' : 'Failure'}，Reason: ${failureReason || 'None'}`)
              return buildResult(historyResult.success, roundMessages.length, failureReason)
            }
            const success = commitMessages.length > requiredCommit
            console.log(`[Experiment] 第${round}轮结果: ${success ? 'Success' : 'Failure'}, commitMessage Count: ${commitMessages.length}（需要超过${requiredCommit}个）`)
            return buildResult(success, roundMessages.length, success ? null : 'RoundReset')
          }
          
          // 如果后端已经Complete共识
          if (status === 'completed' && currentRound === round) {
            const roundMessages = messages.filter(m => {
              const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
              return msgRound === round
            })
            const commitMessages = roundMessages.filter(m => m.type === 'commit')
            // 使用PBFT标准：需要超过2f个commit消息（所有Node都是好Node）
            const historyResult = parseHistoryResult(history, round)
            if (historyResult) {
              const failureReason = historyResult.success ? null : describeFailure(historyResult.reason, commitMessages.length)
              console.log(`[Experiment] 第${round}轮共识完成（From历史）: ${historyResult.success ? 'Success' : 'Failure'}, commitMessage Count: ${commitMessages.length}`)
              return buildResult(historyResult.success, roundMessages.length, failureReason)
            }
            const success = commitMessages.length > requiredCommit
            console.log(`[Experiment] 第${round}轮共识Complete: ${success ? 'Success' : 'Failure'}, commitMessage Count: ${commitMessages.length}（需要超过${requiredCommit}个）`)
            return buildResult(success, roundMessages.length, success ? null : '消息不足')
          }
          
          // 如果还在运行中，检查Message Count
          if (status === 'running' && currentRound === round) {
            const roundMessages = messages.filter(m => {
              const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
              return msgRound === round
            })
            const commitMessages = roundMessages.filter(m => m.type === 'commit')
            
            // 如果收到足够的commit消息（超过2f个），等待后端完成判断
            if (commitMessages.length > requiredCommit) {
              console.log(`[Experiment] 第${round}轮收到足够commit消息(${commitMessages.length}，需要超过${requiredCommit}个)，等待后端Confirm...`)
              // 等待后端Complete共识判断（最多等3秒）
              let waitCount = 0
              while (waitCount < 6) {
                await new Promise(resolve => setTimeout(resolve, 500))
                const checkResponse = await axios.get(`/api/sessions/${sessionId}/status`)
                const checkHistory = checkResponse.data.history || []
                const historyResult = parseHistoryResult(checkHistory, round)
                if (historyResult) {
                  const failureReason = historyResult.success ? null : describeFailure(historyResult.reason, commitMessages.length)
                  console.log(`[Experiment] 第${round}轮等待Confirm后根据历史结果判定: ${historyResult.success ? 'Success' : 'Failure'}`)
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
                  // 使用PBFT标准：需要超过2f个commit消息（所有Node都是好Node）
                  const success = finalCommitMessages.length > requiredCommit
                  console.log(`[Experiment] 第${round}轮最终结果: ${success ? 'Success' : 'Failure'}, commitMessage Count: ${finalCommitMessages.length}（需要超过${requiredCommit}个）`)
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
          console.error('检查共识状态Failure:', error)
        }
      }
      
      // 超时（10秒），检查最后一次状态
      console.log(`[Experiment] 第${round}轮等待超时（10秒），检查最终状态...`)
      try {
        const response = await axios.get(`/api/sessions/${sessionId}/status`)
        const messages = response.data.messages || []
        console.log(`[Experiment] 超时检查 - 总Message Count: ${messages.length}`)
        console.log(`[Experiment] 超时检查 - 消息示例:`, messages.slice(0, 5).map(m => ({ round: m.round, type: m.type, from: m.from })))
        
        const roundMessages = messages.filter(m => {
          const msgRound = typeof m.round === 'string' ? parseInt(m.round) : m.round
          return msgRound === round
        })
        const commitMessages = roundMessages.filter(m => m.type === 'commit')
        
        // 即使超时，如果收到足够消息也算Success（使用PBFT标准：需要超过2f个commit消息）
        const success = commitMessages.length > requiredCommit
        console.log(`[Experiment] 第${round}轮超时检查结果: ${success ? 'Success' : 'Failure'}, commitMessage Count: ${commitMessages.length}（需要超过${requiredCommit}个）`)
        
        return buildResult(success, roundMessages.length, success ? null : '超时', experimentStopRequested.value)
      } catch (error) {
        console.error(`[Experiment] 第${round}轮超时检查Failure:`, error)
        return buildResult(false, 0, '状态查询失败', experimentStopRequested.value)
      }
    }
    
    // Stop Experiment
    const stopExperiment = async () => {
      if (!experimentRunning.value && !allProposersRunning.value && !experimentSessionId.value) {
        ElMessage.info('No running experiment')
        return
      }
      experimentStopRequested.value = true
      experimentRunning.value = false
      allProposersRunning.value = false
      await cleanupExperimentSession()
      ElMessage.success('Experiment stopped')
    }
    
    // Handle Reliability Matrix update
    const onReliabilityMatrixUpdate = (matrix) => {
      experimentConfig.customReliabilityMatrix = matrix
      
      // 统计矩阵信息
      const n = matrix.length
      let nonZeroCount = 0
      let totalReliability = 0
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
          if (i !== j && matrix[i][j] > 0) {
            nonZeroCount++
            totalReliability += matrix[i][j]
          }
        }
      }
      const avgReliability = nonZeroCount > 0 ? totalReliability / nonZeroCount : 0
      
      console.log(`[Experiment] Reliability Matrix Updated:`)
      console.log(`  - Size: ${n}x${n}`)
      console.log(`  - Non-zero connections: ${nonZeroCount}`)
      console.log(`  - Average reliability: ${(avgReliability * 100).toFixed(1)}%`)
      console.log(`  - Topology: ${experimentConfig.topology}`)
    }
    
    // Handle Proposer ID update
    const onProposerIdUpdate = (proposerId) => {
      experimentConfig.proposerId = proposerId
      console.log('[Experiment] Proposer ID Updated:', proposerId)
      ElMessage.success(`Primary node switched to Node ${proposerId}`)
    }
    
    // Handle Random Range update
    const onRandomRangeUpdate = ({ min, max }) => {
      experimentConfig.randomMin = min
      experimentConfig.randomMax = max
      console.log('[Experiment] Random Range Updated:', { min, max })
    }
    
    // Export Experiment Results
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
      
      ElMessage.success('Results exported!')
    }
    
    // Export All Proposers Results
    const exportAllProposersResults = () => {
      const data = {
        config: {
          nodeCount: experimentConfig.nodeCount,
          faultyNodes: experimentConfig.faultyNodes,
          topology: experimentConfig.topology,
          reliability: experimentConfig.reliability,
          rounds: experimentConfig.rounds,
          reliabilityMode: experimentConfig.reliabilityMode
        },
        proposersComparison: allProposersResults.value.map(r => ({
          proposerId: r.proposerId,
          theoreticalSuccessRate: r.theoreticalSuccessRate,
          experimentalSuccessRate: r.experimentalSuccessRate,
          difference: r.experimentalSuccessRate - r.theoreticalSuccessRate,
          successCount: r.successCount,
          failureCount: r.failureCount,
          totalRounds: r.totalRounds
        })),
        summary: {
          totalProposersTested: allProposersResults.value.length,
          averageTheoreticalRate: (allProposersResults.value.reduce((sum, r) => sum + r.theoreticalSuccessRate, 0) / allProposersResults.value.length).toFixed(2),
          averageExperimentalRate: (allProposersResults.value.reduce((sum, r) => sum + r.experimentalSuccessRate, 0) / allProposersResults.value.length).toFixed(2)
        }
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `all-proposers-comparison-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('Comparison results exported successfully!')
    }
    
    // 清除历史数据
    const clearHistoricalData = () => {
      historicalData.value = []
      correlationResults.value = null
      ElMessage.success('Historical data cleared')
      console.log('[Historical Data] Cleared all data')
    }
    
    return {
      // 页面导航
      currentPage,
      // 表单
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
      showMatrixEditor,
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
      theoreticalSuccessRate,
      startExperiment,
      stopExperiment,
      exportResults,
      chartContainer,
      showChartDialog,
      VideoPlay,
      Histogram,
      onReliabilityMatrixUpdate,
      onProposerIdUpdate,
      onRandomRangeUpdate,
      // All Proposers Experiment
      allProposersRunning,
      currentProposerIndex,
      allProposersResults,
      allProposersChartContainer,
      runAllProposersExperiment,
      exportAllProposersResults,
      // 历史数据和相关性分析
      historicalData,
      correlationResults,
      calculateCorrelations,
      clearHistoricalData,
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
  padding: 40px 60px;
  max-width: none;
  width: 100%;
}

/* 页面容器和导航 */
.page-container {
  display: flex;
  gap: 30px;
  width: 100%;
  max-width: none;
}

.side-navigation {
  position: fixed;
  left: 20px;
  top: 40px;
  width: 180px;
  z-index: 100;
}

.content-area {
  flex: 1;
  min-width: 0;
  margin-left: 210px;
}

.page-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 导航单选按钮样式 */
.radio-container {
  --main-color: #f7e479;
  --main-color-opacity: #f7e4791c;
  --total-radio: 2;
  display: flex;
  flex-direction: column;
  position: relative;
  padding-left: 0.5rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.radio-container input {
  cursor: pointer;
  appearance: none;
  position: absolute;
  opacity: 0;
}

.radio-container .glider-container {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(
    0deg,
    rgba(0, 0, 0, 0) 0%,
    rgba(27, 27, 27, 1) 50%,
    rgba(0, 0, 0, 0) 100%
  );
  width: 1px;
}

.radio-container .glider-container .glider {
  position: relative;
  height: calc(100% / var(--total-radio));
  width: 100%;
  background: linear-gradient(
    0deg,
    rgba(0, 0, 0, 0) 0%,
    var(--main-color) 50%,
    rgba(0, 0, 0, 0) 100%
  );
  transition: transform 0.5s cubic-bezier(0.37, 1.95, 0.66, 0.56);
}

.radio-container .glider-container .glider::before {
  content: "";
  position: absolute;
  height: 60%;
  width: 300%;
  top: 50%;
  transform: translateY(-50%);
  background: var(--main-color);
  filter: blur(10px);
}

.radio-container .glider-container .glider::after {
  content: "";
  position: absolute;
  left: 0;
  height: 100%;
  width: 150px;
  background: linear-gradient(
    90deg,
    var(--main-color-opacity) 0%,
    rgba(0, 0, 0, 0) 100%
  );
}

.radio-container label {
  cursor: pointer;
  padding: 1.2rem 1rem;
  position: relative;
  color: #909399;
  transition: all 0.3s ease-in-out;
  font-size: 15px;
  font-weight: 500;
  user-select: none;
}

.radio-container input:checked + label {
  color: var(--main-color);
  font-weight: 600;
}

.radio-container input:nth-of-type(1):checked ~ .glider-container .glider {
  transform: translateY(0);
}

.radio-container input:nth-of-type(2):checked ~ .glider-container .glider {
  transform: translateY(100%);
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
  max-width: 100%;
  width: 100%;
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
.experiment-results,
.topology-editor-container {
  height: 100%;
}

.topology-editor-container {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
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

/* 波浪形加载器样式 */
.wave-loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.wave-menu {
  border: 4px solid #545FE5;
  border-radius: 50px;
  width: 350px;
  height: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;
  margin: 0;
  cursor: pointer;
  transition: ease 0.2s;
  position: relative;
  background: #fff;
  list-style: none;
}

.wave-menu.completed {
  border-color: #67c23a;
}

.wave-menu li {
  list-style: none;
  height: 35px;
  width: 5px;
  border-radius: 10px;
  background: #545FE5;
  margin: 0 10px;
  padding: 0;
  animation-name: wave1;
  animation-duration: 0.3s;
  animation-iteration-count: infinite;
  animation-direction: alternate;
  transition: ease 0.2s;
}

.wave-menu.completed li {
  background: #67c23a;
  animation: none;
  transform: scaleY(1);
}

.wave-menu:hover > li {
  background: #fff;
}

.wave-menu:hover {
  background: #545FE5;
}

.wave-menu.completed:hover {
  background: #67c23a;
}

.wave-menu li:nth-child(2) {
  animation-name: wave2;
  animation-delay: 0.2s;
}

.wave-menu li:nth-child(3) {
  animation-name: wave3;
  animation-delay: 0.23s;
  animation-duration: 0.4s;
}

.wave-menu li:nth-child(4) {
  animation-name: wave4;
  animation-delay: 0.1s;
  animation-duration: 0.3s;
}

.wave-menu li:nth-child(5) {
  animation-delay: 0.5s;
}

.wave-menu li:nth-child(6) {
  animation-name: wave2;
  animation-duration: 0.5s;
}

.wave-menu li:nth-child(8) {
  animation-name: wave4;
  animation-delay: 0.4s;
  animation-duration: 0.25s;
}

.wave-menu li:nth-child(9) {
  animation-name: wave3;
  animation-delay: 0.15s;
}

@keyframes wave1 {
  from {
    transform: scaleY(1);
  }
  to {
    transform: scaleY(0.5);
  }
}

@keyframes wave2 {
  from {
    transform: scaleY(0.3);
  }
  to {
    transform: scaleY(0.6);
  }
}

@keyframes wave3 {
  from {
    transform: scaleY(0.6);
  }
  to {
    transform: scaleY(0.8);
  }
}

@keyframes wave4 {
  from {
    transform: scaleY(0.2);
  }
  to {
    transform: scaleY(0.5);
  }
}

.progress-text {
  font-size: 18px;
  font-weight: 600;
  color: #545FE5;
}

.wave-menu.completed ~ .progress-text {
  color: #67c23a;
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