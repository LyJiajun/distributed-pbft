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
              <input :checked="currentPage === 'primary-selection'" id="radio-primary" name="page-nav" type="radio" @change="currentPage = 'primary-selection'" />
              <label for="radio-primary">Primary Selection</label>
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
                            v-if="!experimentRunning"
                            type="primary" 
                            @click="startExperiment"
                            :icon="VideoPlay"
                            style="width: 100%;"
                          >
                            Start Experiment
                          </el-button>
                          <el-button 
                            v-if="experimentRunning"
                            type="danger" 
                            @click="stopExperiment"
                            style="width: 100%;"
                          >
                            Stop Experiment
                          </el-button>
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
              </div>
            </el-card>
                </el-col>
              </el-row>
            </div>
            
            <!-- 主节点选择实验页面 -->
            <div v-show="currentPage === 'primary-selection'" class="page-content">
              <el-row :gutter="40">
                <el-col :span="24">
                  <el-card class="experiment-card">
              <template #header>
                <div class="card-header" style="display: flex; align-items: center; justify-content: space-between;">
                  <span>🎯 Primary Node Selection Experiments</span>
                  <el-tag :type="(allProposersRunning || batchExperimentRunning) ? 'success' : 'info'" effect="dark">
                    {{ (allProposersRunning || batchExperimentRunning) ? 'Experiment Running' : 'Not Running' }}
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
                            v-model="primarySelectionConfig.nodeCount" 
                            :min="4" 
                            :max="10"
                            :disabled="allProposersRunning || batchExperimentRunning"
                            controls-position="right"
                          />
                        </el-form-item>
                        
                        <el-form-item label="Faulty Nodes">
                          <el-input-number 
                            v-model="primarySelectionConfig.faultyNodes" 
                            :min="0" 
                            :max="Math.floor((primarySelectionConfig.nodeCount - 1) / 3)"
                            :disabled="allProposersRunning || batchExperimentRunning"
                            controls-position="right"
                          />
                          <div class="form-tip">Byzantine fault tolerance requires: f < n/3</div>
                        </el-form-item>
                        
                        <el-form-item label="Topology">
                          <el-select 
                            v-model="primarySelectionConfig.topology" 
                            placeholder="Select topology"
                            :disabled="allProposersRunning || batchExperimentRunning"
                          >
                            <el-option label="Full Mesh" value="full" />
                            <el-option label="Ring" value="ring" />
                            <el-option label="Star" value="star" />
                            <el-option label="Tree" value="tree" />
                          </el-select>
                        </el-form-item>
                        
                        <el-form-item label="Branch Count" v-if="primarySelectionConfig.topology === 'tree'">
                          <el-input-number 
                            v-model="primarySelectionConfig.branchCount" 
                            :min="2" 
                            :max="5"
                            :disabled="allProposersRunning || batchExperimentRunning"
                            controls-position="right"
                          />
                        </el-form-item>
                        
                        <el-form-item label="Reliability Matrix">
                          <el-button
                            type="primary"
                            size="default"
                            style="width: 100%;"
                            :disabled="allProposersRunning || batchExperimentRunning"
                            @click="showPrimaryMatrixEditor = true"
                          >
                            <el-icon><Edit /></el-icon>
                            Edit Reliability Matrix
                          </el-button>
                          <div class="form-tip">Configure node-to-node communication reliability</div>
                        </el-form-item>
                        
                        <el-divider></el-divider>
                        
                        <el-form-item>
                          <el-button 
                            v-if="!experimentRunning && !allProposersRunning && !batchExperimentRunning"
                            type="success" 
                            @click="runAllProposersExperiment"
                            style="width: 100%;"
                          >
                            <el-icon><Histogram /></el-icon>
                            Run All Proposers Experiment
                          </el-button>
                          
                          <el-button 
                            v-if="experimentRunning || allProposersRunning || batchExperimentRunning"
                            type="danger" 
                            @click="stopExperiment"
                            style="width: 100%;"
                          >
                            Stop Experiment
                          </el-button>
                        </el-form-item>
                        
                        <el-form-item>
                          <el-button 
                            type="warning" 
                            @click="runBatchRandomExperiments"
                            style="width: 100%;"
                            :disabled="batchExperimentRunning || allProposersRunning"
                          >
                            <el-icon><Refresh /></el-icon>
                            Batch Random Experiments
                          </el-button>
                          
                          <div v-if="allProposersRunning && !batchExperimentRunning" style="text-align: center; color: #67C23A; font-weight: 600; margin-top: 10px;">
                            Testing Proposer {{ currentProposerIndex }} / {{ primarySelectionConfig.nodeCount }}
                          </div>
                          
                          <div v-if="batchExperimentRunning" style="text-align: center; color: #E6A23C; font-weight: 600; margin-top: 10px;">
                            Batch {{ currentBatchRound }} / {{ batchExperimentRounds }} - Proposer {{ currentProposerIndex }} / {{ primarySelectionConfig.nodeCount }}
                          </div>
                        </el-form-item>
                        
                        <!-- 批量实验配置 -->
                        <el-form-item label="Batch Rounds">
                          <el-input-number 
                            v-model="batchExperimentRounds" 
                            :min="2" 
                            :disabled="batchExperimentRunning"
                            controls-position="right"
                          />
                          <div class="form-tip">Number of random experiments to run (no limit)</div>
                        </el-form-item>
                      </el-form>
                    </div>
                  </el-col>
                  
                  <!-- 中间：Experiment Progress -->
                  <el-col :span="8">
                    <div class="experiment-progress">
                      <h3>Experiment Progress</h3>
                      <div v-if="allProposersRunning || batchExperimentRunning || allProposersResults.length > 0">
                        <el-statistic 
                          v-if="allProposersRunning && !batchExperimentRunning"
                          title="Current Proposer" 
                          :value="currentProposerIndex" 
                          :suffix="`/ ${experimentConfig.nodeCount}`" 
                        />
                        <el-statistic 
                          v-if="batchExperimentRunning"
                          title="Batch Progress" 
                          :value="currentBatchRound" 
                          :suffix="`/ ${batchExperimentRounds}`" 
                        />
                        
                        <!-- 波浪形加载动画 -->
                        <div class="wave-loader-container" style="margin-top: 20px;">
                          <ul class="wave-menu" :class="{ 'completed': !allProposersRunning && !batchExperimentRunning }">
                            <li v-for="i in 9" :key="i"></li>
                          </ul>
                          <div class="progress-text" v-if="allProposersRunning && !batchExperimentRunning">
                            {{ Math.round((currentProposerIndex / experimentConfig.nodeCount) * 100) }}%
                          </div>
                          <div class="progress-text" v-if="batchExperimentRunning">
                            {{ Math.round((currentBatchRound / batchExperimentRounds) * 100) }}%
                          </div>
                        </div>
                        
                        <div class="stats-grid" style="margin-top: 30px;" v-if="allProposersResults.length > 0">
                          <div class="stat-item">
                            <div class="stat-label">Total Proposers Tested</div>
                            <div class="stat-value primary">{{ allProposersResults.length }}</div>
                          </div>
                          <div class="stat-item" v-if="batchExperimentResults.length > 0">
                            <div class="stat-label">Batch Experiments</div>
                            <div class="stat-value success">{{ batchExperimentResults.length }}</div>
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
                  
                  <!-- 右侧：Batch Statistics -->
                  <el-col :span="8">
                    <div class="experiment-results">
                      <h3>Batch Experiment Statistics</h3>
                      <div v-if="gainLossStatsDisplay" class="results-list">
                        <el-scrollbar height="600px" style="width: 100%;">
                          <div style="padding-right: 12px;">
                            <!-- 统计内容将在这里显示 -->
                            <div v-html="gainLossStatsHTML"></div>
                          </div>
                        </el-scrollbar>
                      </div>
                      <el-empty 
                        v-else 
                        description="Run Batch Experiments to see statistics" 
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
                      
                      <div ref="allProposersChartContainer" style="width: 100%; height: 700px;"></div>
                      
                      <div style="margin-top: 20px; text-align: center;">
                        <el-button type="primary" @click="exportAllProposersResults">
                          Export Comparison Results
                        </el-button>
                        <el-button 
                          type="warning"
                          @click="exportBatchExperimentResults"
                          v-if="batchExperimentResults.length > 0"
                          style="margin-left: 10px;"
                        >
                          Export Batch Experiments Data
                        </el-button>
                        <el-button 
                          type="danger"
                          @click="exportMismatchedRounds"
                          v-if="batchExperimentResults.length > 0"
                          style="margin-left: 10px;"
                        >
                          Export Mismatched Rounds (Gain Loss ≠ 0)
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
    
    <!-- 可靠度矩阵编辑器对话框 (Experiment 页面) -->
    <el-dialog
      v-model="showMatrixEditor"
      title="Edit Reliability Matrix - Experiment"
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
    
    <!-- 可靠度矩阵编辑器对话框 (Primary Selection 页面) -->
    <el-dialog
      v-model="showPrimaryMatrixEditor"
      title="Edit Reliability Matrix - Primary Selection"
      width="95%"
      top="2vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <TopologyEditor
        v-if="showPrimaryMatrixEditor"
        :node-count="primarySelectionConfig.nodeCount"
        :topology="primarySelectionConfig.topology"
        :branch-count="primarySelectionConfig.branchCount"
        :default-reliability="primarySelectionConfig.reliability"
        :initial-matrix="primarySelectionConfig.customReliabilityMatrix"
        :proposer-id="primarySelectionConfig.proposerId"
        :random-min="primarySelectionConfig.randomMin"
        :random-max="primarySelectionConfig.randomMax"
        @update:reliabilityMatrix="onPrimaryReliabilityMatrixUpdate"
        @update:proposerId="onPrimaryProposerIdUpdate"
        @update:randomRange="onPrimaryRandomRangeUpdate"
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Edit, Histogram, Refresh } from '@element-plus/icons-vue'
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
    const showMatrixEditor = ref(false)  // Experiment 页面的矩阵编辑器
    const showPrimaryMatrixEditor = ref(false)  // ✅ Primary Selection 页面的矩阵编辑器
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
    let chartInstance = null
    
    // All Proposers Experiment相关
    const allProposersRunning = ref(false)
    const currentProposerIndex = ref(0)
    const allProposersResults = ref([]) // 存储所有主节点的实验结果
    const allProposersChartContainer = ref(null)
    let allProposersChartInstance = null
    
    // 批量随机实验相关
    const batchExperimentRunning = ref(false)
    const batchExperimentRounds = ref(10)  // 默认10轮
    const currentBatchRound = ref(0)
    const batchExperimentResults = ref([])  // 存储所有批次的结果
    const gainLossStatsDisplay = ref(false)  // 是否显示统计信息
    const gainLossStatsHTML = ref('')  // 统计信息的HTML内容
    
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
    
    // ✅ Primary Selection 页面独立配置
    const primarySelectionConfig = reactive({
      nodeCount: 6,
      faultyNodes: 1,
      reliability: 80,
      topology: 'full',
      branchCount: 2,
      customReliabilityMatrix: null,  // 独立的可靠性矩阵
      proposerId: 0,
      randomMin: 50,
      randomMax: 100
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
    
    // 计算单调拟合 + 误差评估（Isotonic Regression + Error Metrics）
    const calculateIsotonicError = (predictor, actual) => {
      if (predictor.length !== actual.length || predictor.length === 0) return null
      
      const n = predictor.length
      
      // 1. MAE (Mean Absolute Error) - 平均绝对误差
      let mae = 0
      for (let i = 0; i < n; i++) {
        mae += Math.abs(actual[i] - predictor[i])
      }
      mae /= n
      
      // 2. RMSE (Root Mean Squared Error) - 均方根误差
      let mse = 0
      for (let i = 0; i < n; i++) {
        mse += Math.pow(actual[i] - predictor[i], 2)
      }
      mse /= n
      const rmse = Math.sqrt(mse)
      
      // 3. R² (Coefficient of Determination) - 决定系数
      const meanActual = actual.reduce((sum, val) => sum + val, 0) / n
      let ssTot = 0  // Total sum of squares
      let ssRes = 0  // Residual sum of squares
      for (let i = 0; i < n; i++) {
        ssTot += Math.pow(actual[i] - meanActual, 2)
        ssRes += Math.pow(actual[i] - predictor[i], 2)
      }
      const r2 = ssTot > 0 ? 1 - (ssRes / ssTot) : 0
      
      // 4. 计算相对误差（百分比）
      const mape = (mae / meanActual) * 100  // Mean Absolute Percentage Error
      
      return {
        mae: mae,
        rmse: rmse,
        r2: r2,
        mape: mape,
        meanActual: meanActual
      }
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
      () => [experimentResults.value.length, experimentRunning.value, theoreticalSuccessRate.value],
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
    
    // 监听拓扑或节点数变化，清除自定义矩阵 (Experiment 页面)
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
    
    // ✅ 监听拓扑或节点数变化，清除自定义矩阵 (Primary Selection 页面)
    watch(
      () => [primarySelectionConfig.topology, primarySelectionConfig.nodeCount, primarySelectionConfig.branchCount],
      ([newTopology, newNodeCount, newBranchCount], [oldTopology, oldNodeCount, oldBranchCount]) => {
        if (oldTopology !== undefined) {
          primarySelectionConfig.customReliabilityMatrix = null
          console.log(`[Primary Selection] Configuration changed (topology: ${oldTopology}→${newTopology}, nodes: ${oldNodeCount}→${newNodeCount}, branch: ${oldBranchCount}→${newBranchCount}), custom matrix cleared`)
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
    // Run All Proposers Experiment（依次让每个节点当主节点）
    
    const runAllProposersExperiment = async () => {
      try {
        allProposersRunning.value = true
        experimentStopRequested.value = false
        allProposersResults.value = []
        
        const nodeCount = primarySelectionConfig.nodeCount
        const f = Math.floor((nodeCount - 1) / 3)
        
        ElMessage.info(`开始计算所有${nodeCount}个节点作为主节点的理论成功率...`)
        
        console.log(`\n=== 轮换主节点实验：仅计算理论值（无机器人模拟）===`)
        console.log(`节点数: ${nodeCount}, f: ${f}`)
        
        // 准备请求数据
        const requestData = {
          nodeCount: nodeCount,
          faultyNodes: f
        }
        
        // 如果有自定义可靠度矩阵，添加到请求中
        if (primarySelectionConfig.customReliabilityMatrix) {
          // ✅ 数据验证和转换：确保矩阵值在 0-1 范围
          const matrix = primarySelectionConfig.customReliabilityMatrix
          let needsConversion = false
          
          // 检查是否有值 > 1（说明是百分比格式）
          for (let i = 0; i < matrix.length && !needsConversion; i++) {
            for (let j = 0; j < matrix[i].length && !needsConversion; j++) {
              if (matrix[i][j] > 1) {
                needsConversion = true
                console.warn(`⚠️ 检测到可靠性矩阵值 > 1: ${matrix[i][j]}，将转换为 0-1 范围`)
              }
            }
          }
          
          // 如果需要转换，创建转换后的矩阵
          if (needsConversion) {
            const convertedMatrix = matrix.map(row => 
              row.map(val => {
                if (val > 1 && val <= 100) {
                  return val / 100  // 百分比转概率
                } else if (val > 100) {
                  console.error(`⚠️ 异常值: ${val}，限制为 1.0`)
                  return 1.0
                }
                return val
              })
            )
            requestData.reliabilityMatrix = convertedMatrix
            console.log('✅ 已将百分比格式转换为 0-1 范围')
          } else {
            requestData.reliabilityMatrix = matrix
          }
          
          console.log('使用自定义可靠度矩阵')
        } else {
          requestData.reliability = primarySelectionConfig.reliability / 100  // ✅ 确保是 0-1 范围
          console.log(`使用均匀可靠度: ${primarySelectionConfig.reliability}% (${requestData.reliability})`)
        }
        
        // 遍历所有节点作为主节点，调用后端理论计算API
        for (let proposerId = 0; proposerId < nodeCount; proposerId++) {
          if (experimentStopRequested.value) {
            ElMessage.warning('计算已被用户停止')
            break
          }
          
          currentProposerIndex.value = proposerId
          
          try {
            // 调用后端理论计算API
            const response = await axios.post('/api/theory/calculate', {
              ...requestData,
              proposerId: proposerId
            }, { timeout: 30000 })
            
            const theoreticalSuccessRate = response.data.theoreticalSuccessRate
            const metrics = response.data.metrics  // 获取后端计算的指标
            
            // ✅ 添加数据验证和调试
            console.log(`\n[API Response Debug] 节点 ${proposerId}:`)
            console.log(`  theoreticalSuccessRate (raw): ${theoreticalSuccessRate}`)
            console.log(`  metrics.Q_pp (raw): ${metrics.Q_pp}`)
            console.log(`  metrics.I_v (raw): ${metrics.I_v}`)
            
            // 检查数据是否异常
            if (theoreticalSuccessRate > 1000 || theoreticalSuccessRate < 0 || isNaN(theoreticalSuccessRate)) {
              console.error(`⚠️ 异常数据: theoreticalSuccessRate = ${theoreticalSuccessRate}`)
              console.error(`  完整响应:`, response.data)
              ElMessage.error(`节点 ${proposerId} 数据异常: ${theoreticalSuccessRate}`)
            }
            
            if (metrics.Q_pp > 1000 || metrics.Q_pp < 0) {
              console.error(`⚠️ 异常数据: Q_pp = ${metrics.Q_pp}`)
            }
            
            // 保存结果（包含理论值和新指标）
            allProposersResults.value.push({
              proposerId,
              theoreticalSuccessRate: theoreticalSuccessRate,
              metrics: metrics  // 包含 Q_pp, P_prep, Phi_min, Phi_q, I_v
            })
            
            console.log(`主节点 ${proposerId}: 理论=${theoreticalSuccessRate.toFixed(2)}%, Q_pp=${metrics.Q_pp.toFixed(2)}%, Φ_q=${metrics.Phi_q.toFixed(2)}%, I(v)=${metrics.I_v.toFixed(2)}%`)
            
          } catch (error) {
            console.error(`计算主节点 ${proposerId} 失败:`, error)
            allProposersResults.value.push({
              proposerId: proposerId,
              error: error.message,
              theoreticalSuccessRate: 0
            })
          }
        }
        
        // ========== 计算 Q_v1：基于所有节点的 Q(v) 和 Q_w(v) ==========
        console.log(`\n=== 开始计算 Q_v1 (tie-breaker) ===`)
        
        // 1. 提取所有节点的 Q(v) 和 Q_w(v)
        const allQv = allProposersResults.value.map(r => r.metrics?.Q_pp || 0)
        const allQw = allProposersResults.value.map(r => r.metrics?.Q_w || 0)
        
        // 🔍 调试：检查原始数据尺度
        console.log(`[数据尺度检查]:`)
        console.log(`  allQv (原始): [${allQv.slice(0, 3).map(v => v.toFixed(2)).join(', ')}...]`)
        console.log(`  allQv 来源示例:`, allProposersResults.value.slice(0, 2).map((r, i) => 
          `Node${i}: Q_pp=${r.metrics?.Q_pp?.toFixed(2) || 'undefined'}`
        ))
        
        // 2. 排序找到 Top-M (M=3)
        const qvWithIndex = allQv.map((val, idx) => ({ val, idx }))
        qvWithIndex.sort((a, b) => b.val - a.val)
        
        console.log(`  排序后 Top2 (转换前): val[0]=${qvWithIndex[0].val}, val[1]=${qvWithIndex[1]?.val}`)
        
        const Q_1 = qvWithIndex[0].val / 100  // 转为 0-1 范围
        const Q_2 = qvWithIndex[1]?.val / 100 || 0
        
        console.log(`  转换后 (0-1): Q_1=${Q_1.toFixed(6)}, Q_2=${Q_2.toFixed(6)}`)
        
        // 3. logit 函数
        const logit = (q) => {
          if (q <= 0 || q >= 1) {
            console.warn(`  ⚠️ logit 边界警告: q=${q}，返回 0`)
            return 0
          }
          return Math.log(q / (1 - q))
        }
        
        // 🔍 详细的 logit 计算
        const logit_1 = logit(Q_1)
        const logit_2 = logit(Q_2)
        console.log(`  logit 计算:`)
        console.log(`    logit(${Q_1.toFixed(6)}) = ${logit_1.toFixed(6)}`)
        console.log(`    logit(${Q_2.toFixed(6)}) = ${logit_2.toFixed(6)}`)
        
        // 4. 计算触发条件（改法 A：只用并列度触发）
        const epsilon_r = 0.15  // logit 阈值：当 top1/top2 在 logit 尺度上几乎相同时触发
        const logit_diff = Math.abs(logit_1 - logit_2)
        const trigger = logit_diff < epsilon_r  // ✅ 去掉 tau_sat，只用并列度判断
        
        console.log(`\n[触发条件详细检查]:`)
        console.log(`  Top1: 节点${qvWithIndex[0].idx} Q(v)=${(Q_1*100).toFixed(2)}%`)
        console.log(`  Top2: 节点${qvWithIndex[1]?.idx} Q(v)=${(Q_2*100).toFixed(2)}%`)
        console.log(`  Logit差距: ${logit_diff.toFixed(6)} (阈值: ${epsilon_r})`)
        console.log(`  触发条件 (Δ_logit < ε_r): ${logit_diff.toFixed(6)} < ${epsilon_r} = ${trigger}`)
        console.log(`  最终触发? ${trigger} (改法A: 只用并列度判断)`)
        
        // 5. 计算 Q_v1（触发时对所有节点统一修正，保持一致标尺）
        const lambda = 0.3  // 改动强度 (建议 0.2~0.5)
        
        console.log(`\n[Q_v1 计算策略]:`)
        console.log(`  触发状态: ${trigger}`)
        console.log(`  策略: ${trigger ? '对所有节点统一修正 Q_v1 = Q(v) + λ·(Q_w - Q(v))' : '不修正，Q_v1 = Q(v)'}`)
        
        for (let i = 0; i < allProposersResults.value.length; i++) {
          const Qv = allQv[i] / 100  // 0-1 范围
          const Qw = allQw[i] / 100  // Q_strong = Q_w
          
          let Qv1
          if (trigger) {
            // ✅ 触发时：对所有节点统一修正，保持一致标尺
            Qv1 = Qv + lambda * (Qw - Qv)
          } else {
            // 不触发：Q_v1 = Q(v)
            Qv1 = Qv
          }
          
          // 存储到 metrics 中
          if (!allProposersResults.value[i].metrics) {
            allProposersResults.value[i].metrics = {}
          }
          allProposersResults.value[i].metrics.Q_v1 = Qv1 * 100
        }
        
        console.log(`✅ Q_v1 计算完成！`)
        
        // ========== 计算 I(v) 和 Q_2、Q_3（用于图表显示）==========
        console.log(`\n[计算 I(v) 和 Q_2、Q_3 用于图表]`)
        const lambda_iv = 0.4  // I(v) 加权系数
        
        for (let i = 0; i < allProposersResults.value.length; i++) {
          const Qv = allQv[i] / 100
          const Qw = allQw[i] / 100
          
          // I(v) = 0.6·Q(v) + 0.4·Q_w
          const Iv = (1 - lambda_iv) * Qv + lambda_iv * Qw
          allProposersResults.value[i].metrics.I_v = Iv * 100
          
          // Q_2 从后端返回（平均发送可靠度已在后端计算）
          // 这里确保值存在
          if (!allProposersResults.value[i].metrics.Q_2) {
            allProposersResults.value[i].metrics.Q_2 = allProposersResults.value[i].metrics.Q_2 || 0
          }
          
          // Q_3 从后端返回（极严格阈值 k=n-1 所有节点，已在后端计算）
          // 这里确保值存在
          if (!allProposersResults.value[i].metrics.Q_3) {
            allProposersResults.value[i].metrics.Q_3 = allProposersResults.value[i].metrics.Q_3 || 0
          }
        }
        
        console.log(`✅ I(v)、Q_2、Q_3 计算完成！`)
        
        allProposersRunning.value = false
        experimentStopRequested.value = false
        
        console.log(`\n=== 计算完成！共${allProposersResults.value.length}个节点 ===`)
        
        // 绘制图表
        await nextTick()
        createAllProposersChart()
        
        ElMessage.success('所有主节点的理论成功率计算完成！')
        
      } catch (error) {
        console.error('计算失败:', error)
        ElMessage.error(`计算失败: ${error.message}`)
        allProposersRunning.value = false
        experimentStopRequested.value = false
      }
    }
    
    // Batch Random Experiments - 批量随机实验
    const runBatchRandomExperiments = async () => {
      try {
        batchExperimentRunning.value = true
        experimentStopRequested.value = false
        batchExperimentResults.value = []
        currentBatchRound.value = 0
        
        const nodeCount = primarySelectionConfig.nodeCount
        const f = Math.floor((nodeCount - 1) / 3)
        const totalRounds = batchExperimentRounds.value
        
        // ✅ 添加 Q_v1 tie-breaker 触发统计
        let qv1TiebreakerTriggered = 0  // 触发次数
        let qv1SelectionDifferent = 0  // 选择不同次数

        
        ElMessage.info(`开始批量随机实验：${totalRounds}轮...`)
        console.log(`\n=== 批量随机实验开始 ===`)
        console.log(`实验轮数: ${totalRounds}, 节点数: ${nodeCount}, f: ${f}`)
        
        // 检查是否启用了自定义矩阵模式
        if (!primarySelectionConfig.customReliabilityMatrix) {
          ElMessage.error('批量随机实验需要先配置 Reliability Matrix！')
          batchExperimentRunning.value = false
          return
        }
        
        // 获取拓扑编辑器中的随机参数
        const minReliability = topologyRef.value?.minReliability || 0.5
        const maxReliability = topologyRef.value?.maxReliability || 1.0
        
        console.log(`随机可靠度范围: [${minReliability}, ${maxReliability}]`)
        
        // ✅ Q_v1 Tie-breaker 配置
        const epsilon_r = 0.15  // logit 尺度阈值（极严格）
        
        // 随机生成矩阵的辅助函数
        const generateRandomMatrix = (n, min, max) => {
          const matrix = []
          for (let i = 0; i < n; i++) {
            matrix[i] = []
            for (let j = 0; j < n; j++) {
              if (i === j) {
                matrix[i][j] = 1.0  // 对角线为1
              } else {
                // 生成 [min, max] 范围内的随机值，步长1%
                const range = max - min
                const steps = Math.round(range / 0.01)
                const randomStep = Math.floor(Math.random() * (steps + 1))
                matrix[i][j] = Math.round((min + randomStep * 0.01) * 100) / 100
              }
            }
          }
          return matrix
        }
        
        // 运行多轮实验
        for (let round = 1; round <= totalRounds; round++) {
          if (experimentStopRequested.value) {
            ElMessage.warning('批量实验已被用户停止')
            break
          }
          
          currentBatchRound.value = round
          console.log(`\n--- 批次 ${round}/${totalRounds} ---`)
          
          // 1. 随机生成新的可靠度矩阵
          const newMatrix = generateRandomMatrix(nodeCount, minReliability, maxReliability)
          
          // 更新到 primarySelectionConfig（用于显示）
          primarySelectionConfig.customReliabilityMatrix = newMatrix
          
          // 如果有拓扑编辑器引用，也更新它的矩阵（用于最后一轮的可视化）
          if (topologyRef.value) {
            topologyRef.value.reliabilityMatrix = JSON.parse(JSON.stringify(newMatrix))
          }
          
          console.log(`生成新随机矩阵（第${round}轮）:`)
          const avgReliability = newMatrix.reduce((sum, row, i) => {
            return sum + row.reduce((rowSum, val, j) => {
              return i === j ? rowSum : rowSum + val
            }, 0)
          }, 0) / (nodeCount * (nodeCount - 1))
          console.log(`  平均可靠度: ${avgReliability.toFixed(3)}`)
          console.log(`  矩阵预览 (前3x3):`, newMatrix.slice(0, 3).map(row => row.slice(0, 3).map(v => v.toFixed(2))))
          
          // 等待一小段时间确保状态更新
          await nextTick()
          
          // 2. 对所有节点作为主节点运行实验
          const roundResults = []
          
          for (let proposerId = 0; proposerId < nodeCount; proposerId++) {
            if (experimentStopRequested.value) break
            
            currentProposerIndex.value = proposerId
            
            try {
              // 调用后端理论计算API
              const response = await axios.post('/api/theory/calculate', {
                nodeCount: nodeCount,
                faultyNodes: f,
                reliabilityMatrix: newMatrix,
                proposerId: proposerId
              }, { timeout: 30000 })
              
              const theoreticalSuccessRate = response.data.theoreticalSuccessRate
              const metrics = response.data.metrics
              
              roundResults.push({
                proposerId,
                theoreticalSuccessRate,
                metrics
              })
              
              console.log(`  节点 ${proposerId}: ${theoreticalSuccessRate.toFixed(2)}%`)
              
            } catch (error) {
              console.error(`  节点 ${proposerId} 计算失败:`, error)
              roundResults.push({
                proposerId,
                error: error.message,
                theoreticalSuccessRate: 0
              })
            }
          }
          
          // 计算本轮的 Gain Loss
          const theoreticalData = roundResults.map(r => r.theoreticalSuccessRate)
          const quorumData = roundResults.map(r => r.metrics?.Q_pp || 0)
          const quorumDataW = roundResults.map(r => r.metrics?.Q_w || 0)  // Q_w
          
          const P_avg = theoreticalData.reduce((sum, val) => sum + val, 0) / theoreticalData.length
          
          // Q(v) 选择
          const maxQvIndex = quorumData.indexOf(Math.max(...quorumData))
          const P_best_Qv = theoreticalData[maxQvIndex]
          
          // Q_w(v) 选择
          const maxQwIndex = quorumDataW.indexOf(Math.max(...quorumDataW))
          const P_best_Qw = theoreticalData[maxQwIndex]
          
          // ✅ Q_2(v) 选择 (平均发送能力)
          const q2Data = roundResults.map(r => r.metrics?.Q_2 || 0)
          const maxQ2Index = q2Data.indexOf(Math.max(...q2Data))
          const P_best_Q2 = theoreticalData[maxQ2Index]
          
          // ✅ Q_3(v) 选择 (极严格阈值 k=n-1, 所有节点)
          const q3Data = roundResults.map(r => r.metrics?.Q_3 || 0)
          const maxQ3Index = q3Data.indexOf(Math.max(...q3Data))
          const P_best_Q3 = theoreticalData[maxQ3Index]
          
          // ========== Q_v1 计算：Q(v) + λ·(Q_strong - Q(v)) 【新公式】 ==========
          // 🔍 调试：检查原始数据尺度
          console.log(`\n[Q_v1 调试 - 数据尺度检查] Round ${round}:`)
          console.log(`  quorumData (原始): [${quorumData.slice(0, 3).map(v => v.toFixed(2)).join(', ')}...]`)
          console.log(`  quorumData 来源检查:`, roundResults.slice(0, 2).map((r, i) => 
            `Node${i}: metrics.Q_pp=${r.metrics?.Q_pp?.toFixed(2) || 'undefined'}`
          ))
          
          // 1. 排序找到 Top-M (M=3)
          const qvWithIndex = quorumData.map((val, idx) => ({ val, idx }))
          qvWithIndex.sort((a, b) => b.val - a.val)
          
          // 🔍 调试：检查转换前的值
          console.log(`  排序后 Top2 (转换前): val[0]=${qvWithIndex[0].val}, val[1]=${qvWithIndex[1]?.val}`)
          
          const top1_qv = qvWithIndex[0].val / 100  // 转为 0-1 范围
          const top2_qv = qvWithIndex.length > 1 ? qvWithIndex[1].val / 100 : 0
          
          // 🔍 调试：检查转换后的值
          console.log(`  转换后 (0-1): top1_qv=${top1_qv.toFixed(6)}, top2_qv=${top2_qv.toFixed(6)}`)
          
          // 2. logit 函数
          const logit = (q) => {
            if (q <= 0 || q >= 1) {
              console.warn(`  ⚠️ logit 边界警告: q=${q}，返回 0`)
              return 0
            }
            const result = Math.log(q / (1 - q))
            return result
          }
          
          // 🔍 调试：详细的 logit 计算
          const logit_top1 = logit(top1_qv)
          const logit_top2 = logit(top2_qv)
          console.log(`  logit 计算:`)
          console.log(`    logit(${top1_qv.toFixed(6)}) = ${logit_top1.toFixed(6)}`)
          console.log(`    logit(${top2_qv.toFixed(6)}) = ${logit_top2.toFixed(6)}`)
          
          // 3. 计算触发条件（改法 A：只用并列度触发）
          const logit_diff = Math.abs(logit_top1 - logit_top2)
          const trigger = logit_diff < epsilon_r  // ✅ 去掉 tau_sat，只用并列度判断
          
          console.log(`\n[Q_v1 触发条件详细检查]:`)
          console.log(`  Top1: 节点${qvWithIndex[0].idx} Q(v)=${(top1_qv*100).toFixed(2)}%`)
          console.log(`  Top2: 节点${qvWithIndex[1]?.idx} Q(v)=${(top2_qv*100).toFixed(2)}%`)
          console.log(`  Logit差距: ${logit_diff.toFixed(6)} (阈值: ${epsilon_r})`)
          console.log(`  触发条件 (Δ_logit < ε_r): ${logit_diff.toFixed(6)} < ${epsilon_r} = ${trigger}`)
          console.log(`  最终触发? ${trigger} (改法A: 只用并列度判断)`)
          
          // 4. 计算 Q_v1 值（触发时对所有节点统一修正，保持一致标尺）
          const lambda = 0.3  // 改动强度
          const qv1Data = []
          
          for (let i = 0; i < roundResults.length; i++) {
            const Qv = quorumData[i] / 100  // Q(v) in 0-1 range
            const Qw = quorumDataW[i] / 100  // Q_strong = Q_w in 0-1 range
            
            let Qv1
            if (trigger) {
              // ✅ 触发时：对所有节点统一修正，保持一致标尺
              Qv1 = Qv + lambda * (Qw - Qv)
            } else {
              // 不触发：Q_v1 = Q(v)
              Qv1 = Qv
            }
            
            qv1Data.push(Qv1 * 100)  // 转回百分比
            
            // 存储到 metrics 中
            if (!roundResults[i].metrics) {
              roundResults[i].metrics = {}
            }
            roundResults[i].metrics.Q_v1 = Qv1 * 100
          }
          
          // 6. 基于 Q_v1 值选择最佳节点
          const maxQv1Index = qv1Data.indexOf(Math.max(...qv1Data))
          const P_best_Qv1 = theoreticalData[maxQv1Index]
          
          // 7. 统计触发情况并保存诊断信息
          let qv1TriggeredThisRound = trigger
          if (qv1TriggeredThisRound) {
            qv1TiebreakerTriggered++
            if (maxQv1Index !== maxQvIndex) {
              qv1SelectionDifferent++
            }
          }
          
          // 🔍 保存 Q_v1 诊断信息（用于错误导出）
          const qv1Diagnosis = {
            top1_node: qvWithIndex[0].idx,
            top2_node: qvWithIndex[1]?.idx || -1,
            top1_Qv_raw: qvWithIndex[0].val,
            top2_Qv_raw: qvWithIndex[1]?.val || 0,
            top1_Qv_01: top1_qv,
            top2_Qv_01: top2_qv,
            logit_top1: logit_top1,
            logit_top2: logit_top2,
            logit_diff: logit_diff,
            epsilon_r: epsilon_r,
            trigger: trigger,  // ✅ 触发时对所有节点统一修正
            lambda: lambda
          }
          
          console.log(`  → Q_v1 选择: 节点${maxQv1Index} (Q_v1=${qv1Data[maxQv1Index].toFixed(2)}%)`)
          
          // ========== I(v) 计算：线性加权 I(v) = (1-λ)·Q(v) + λ·Q_w ==========
          const lambda_iv = 0.4  // 加权系数
          const ivData = []
          
          console.log(`\n[I(v) 计算] Round ${round}:`)
          console.log(`  公式: I(v) = (1-${lambda_iv})·Q(v) + ${lambda_iv}·Q_w`)
          
          for (let i = 0; i < roundResults.length; i++) {
            const Qv = quorumData[i] / 100  // Q(v) in 0-1 range
            const Qw = quorumDataW[i] / 100  // Q_w in 0-1 range
            
            // I(v) = (1-λ)·Q(v) + λ·Q_w
            const Iv = (1 - lambda_iv) * Qv + lambda_iv * Qw
            ivData.push(Iv * 100)  // 转回百分比
            
            // 存储到 metrics 中
            if (!roundResults[i].metrics) {
              roundResults[i].metrics = {}
            }
            roundResults[i].metrics.I_v = Iv * 100
          }
          
          // 选择 I(v) 最大的节点
          const maxIvIndex = ivData.indexOf(Math.max(...ivData))
          const P_best_Iv = theoreticalData[maxIvIndex]
          
          console.log(`  → I(v) 选择: 节点${maxIvIndex} (I(v)=${ivData[maxIvIndex].toFixed(2)}%)`)
          
          // 理论最优
          const maxTheoryIndex = theoreticalData.indexOf(Math.max(...theoreticalData))
          const P_best_Theory = theoreticalData[maxTheoryIndex]
          
          // 计算 I(v) 的 Gain Loss（使用绝对差值）
          const Gain_Iv = P_best_Iv - P_avg
          const Gain_Theory = P_best_Theory - P_avg
          const Gain_Gap_Iv = Gain_Theory - Gain_Iv  // 绝对差值（%）
          const Gain_Gap_Ratio = Gain_Gap_Iv  // 直接使用绝对差值
          
          // 计算 Q(v) 的 Gain Loss
          const Gain_Qv = P_best_Qv - P_avg
          const Gain_Gap_Qv = Gain_Theory - Gain_Qv
          const Gain_Gap_Ratio_Qv = Gain_Gap_Qv  // 绝对差值
          
          // 计算 Q_v1 的 Gain Loss
          const Gain_Qv1 = P_best_Qv1 - P_avg
          const Gain_Gap_Qv1 = Gain_Theory - Gain_Qv1
          const Gain_Gap_Ratio_Qv1 = Gain_Gap_Qv1  // 绝对差值
          
          // 计算 Q_w(v) 的 Gain Loss
          const Gain_Qw = P_best_Qw - P_avg
          const Gain_Gap_Qw = Gain_Theory - Gain_Qw
          const Gain_Gap_Ratio_Qw = Gain_Gap_Qw  // 绝对差值
          
          // ✅ 计算 Q_2(v) 的 Gain Loss
          const Gain_Q2 = P_best_Q2 - P_avg
          const Gain_Gap_Q2 = Gain_Theory - Gain_Q2
          const Gain_Gap_Ratio_Q2 = Gain_Gap_Q2  // 绝对差值
          
          // ✅ 计算 Q_3(v) 的 Gain Loss
          const Gain_Q3 = P_best_Q3 - P_avg
          const Gain_Gap_Q3 = Gain_Theory - Gain_Q3
          const Gain_Gap_Ratio_Q3 = Gain_Gap_Q3  // 绝对差值
          
          // 保存本轮结果
          batchExperimentResults.value.push({
            round: round,
            reliabilityMatrix: JSON.parse(JSON.stringify(newMatrix)),  // 深拷贝
            results: roundResults,
            gainLoss: {
              optimalNode: maxTheoryIndex,
              ivSelectsNode: maxIvIndex,
              qvSelectsNode: maxQvIndex,
              qv1SelectsNode: maxQv1Index,
              qv1TiebreakerTriggered: qv1TriggeredThisRound,
              qv1SelectionSameAsQv: maxQv1Index === maxQvIndex,
              qwSelectsNode: maxQwIndex,
              q2SelectsNode: maxQ2Index,
              q3SelectsNode: maxQ3Index,
              q3SelectsNode: maxQ3Index,  // ✅ 新增 Q_3
              P_best_Theory: P_best_Theory,
              P_best_Iv: P_best_Iv,
              P_best_Qv: P_best_Qv,
              P_best_Qv1: P_best_Qv1,
              P_best_Iv: P_best_Iv,  // 新的 I(v)，原Q_fix
              P_best_Qw: P_best_Qw,
              P_best_Q2: P_best_Q2,
              P_best_Q3: P_best_Q3,
              P_avg: P_avg,
              Gain_Theory: Gain_Theory,
              Gain_Iv: Gain_Iv,  // 新的 I(v) gain
              Gain_Qv: Gain_Qv,
              Gain_Qv1: Gain_Qv1,
              Gain_Qw: Gain_Qw,
              Gain_Gap_Iv: Gain_Gap_Iv,  // 新的 I(v) gap
              Gain_Gap_Ratio: Gain_Gap_Ratio,  // I(v) ratio
              Gain_Gap_Qv: Gain_Gap_Qv,
              Gain_Gap_Ratio_Qv: Gain_Gap_Ratio_Qv,
              Gain_Gap_Qv1: Gain_Gap_Qv1,
              Gain_Gap_Ratio_Qv1: Gain_Gap_Ratio_Qv1,
              Gain_Gap_Qw: Gain_Gap_Qw,
              Gain_Gap_Ratio_Qw: Gain_Gap_Ratio_Qw,
              Gain_Q2: Gain_Q2,
              Gain_Gap_Q2: Gain_Gap_Q2,
              Gain_Gap_Ratio_Q2: Gain_Gap_Ratio_Q2,
              Gain_Q3: Gain_Q3,
              Gain_Gap_Q3: Gain_Gap_Q3,
              Gain_Gap_Ratio_Q3: Gain_Gap_Ratio_Q3,
              // 🔍 Q_v1 诊断信息（用于错误日志导出）
              qv1Diagnosis: qv1Diagnosis
            }
          })
          
          console.log(`批次 ${round} 完成 - I(v): ${Gain_Gap_Ratio.toFixed(2)}%, Q(v): ${Gain_Gap_Ratio_Qv.toFixed(2)}%, Q_v1: ${Gain_Gap_Ratio_Qv1.toFixed(2)}%, Q_w(v): ${Gain_Gap_Ratio_Qw.toFixed(2)}%, Q_2(v): ${Gain_Gap_Ratio_Q2.toFixed(2)}%, Q_3(v): ${Gain_Gap_Ratio_Q3.toFixed(2)}%`)
        }
        
        // 计算所有批次的 Gain Loss 统计数据
        const gainLossValues = batchExperimentResults.value.map(r => r.gainLoss.Gain_Gap_Ratio)
        const gainLossValuesQv = batchExperimentResults.value.map(r => r.gainLoss.Gain_Gap_Ratio_Qv)
        const gainLossValuesQv1 = batchExperimentResults.value.map(r => r.gainLoss.Gain_Gap_Ratio_Qv1)
        const gainLossValuesQw = batchExperimentResults.value.map(r => r.gainLoss.Gain_Gap_Ratio_Qw)
        const gainLossValuesQ2 = batchExperimentResults.value.map(r => r.gainLoss.Gain_Gap_Ratio_Q2)
        const gainLossValuesQ3 = batchExperimentResults.value.map(r => r.gainLoss.Gain_Gap_Ratio_Q3)
        
        // 统计完美匹配（Gain Loss ≈ 0）的次数
        // I(v) Perfect Match
        const perfectMatchCount = gainLossValues.filter(v => v < 0.001).length
        const perfectMatchRate = (perfectMatchCount / gainLossValues.length) * 100
        
        // Q(v) Perfect Match
        const perfectMatchCountQv = gainLossValuesQv.filter(v => v < 0.001).length
        const perfectMatchRateQv = (perfectMatchCountQv / gainLossValuesQv.length) * 100
        
        // Q_v1 Perfect Match
        const perfectMatchCountQv1 = gainLossValuesQv1.filter(v => v < 0.001).length
        const perfectMatchRateQv1 = (perfectMatchCountQv1 / gainLossValuesQv1.length) * 100
        
        // Q_w(v) Perfect Match
        const perfectMatchCountQw = gainLossValuesQw.filter(v => v < 0.001).length
        const perfectMatchRateQw = (perfectMatchCountQw / gainLossValuesQw.length) * 100
        
        // Q_2(v) Perfect Match
        const perfectMatchCountQ2 = gainLossValuesQ2.filter(v => v < 0.001).length
        const perfectMatchRateQ2 = (perfectMatchCountQ2 / gainLossValuesQ2.length) * 100
        
        // Q_3(v) Perfect Match
        const perfectMatchCountQ3 = gainLossValuesQ3.filter(v => v < 0.001).length
        const perfectMatchRateQ3 = (perfectMatchCountQ3 / gainLossValuesQ3.length) * 100
        
        // 找到 I(v) Gain Loss 最大的那轮
        const maxGainLossIndex = gainLossValues.indexOf(Math.max(...gainLossValues))
        const worstCase = batchExperimentResults.value[maxGainLossIndex]
        
        // 找到 Q(v) Gain Loss 最大的那轮
        const maxGainLossIndexQv = gainLossValuesQv.indexOf(Math.max(...gainLossValuesQv))
        const worstCaseQv = batchExperimentResults.value[maxGainLossIndexQv]
        
        // 提取最差案例的所有节点数据 (I(v))
        const worstCaseNodes = worstCase.results.map((r, idx) => ({
          nodeId: r.proposerId,
          theoreticalRate: r.theoreticalSuccessRate,
          ivValue: r.metrics?.I_v || 0,
          qvValue: r.metrics?.Q_pp || 0,
          qwValue: r.metrics?.Q_w || 0,
          isTheoryBest: idx === worstCase.gainLoss.optimalNode,
          isIvSelected: idx === worstCase.gainLoss.ivSelectsNode,
          isQvSelected: idx === worstCase.gainLoss.qvSelectsNode
        }))
        
        const gainLossStats = {
          mean: gainLossValues.reduce((sum, v) => sum + v, 0) / gainLossValues.length,
          min: Math.min(...gainLossValues),
          max: Math.max(...gainLossValues),
          median: (() => {
            const sorted = [...gainLossValues].sort((a, b) => a - b)
            const mid = Math.floor(sorted.length / 2)
            return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
          })(),
          stdDev: (() => {
            const mean = gainLossValues.reduce((sum, v) => sum + v, 0) / gainLossValues.length
            const variance = gainLossValues.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / gainLossValues.length
            return Math.sqrt(variance)
          })(),
          perfectMatchCount: perfectMatchCount,
          perfectMatchRate: perfectMatchRate,
          // Q(v) 统计
          qv: {
            mean: gainLossValuesQv.reduce((sum, v) => sum + v, 0) / gainLossValuesQv.length,
            min: Math.min(...gainLossValuesQv),
            max: Math.max(...gainLossValuesQv),
            median: (() => {
              const sorted = [...gainLossValuesQv].sort((a, b) => a - b)
              const mid = Math.floor(sorted.length / 2)
              return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
            })(),
            stdDev: (() => {
              const mean = gainLossValuesQv.reduce((sum, v) => sum + v, 0) / gainLossValuesQv.length
              const variance = gainLossValuesQv.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / gainLossValuesQv.length
              return Math.sqrt(variance)
            })(),
            perfectMatchCount: perfectMatchCountQv,
            perfectMatchRate: perfectMatchRateQv
          },
          // Q_v1 统计
          qv1: {
            mean: gainLossValuesQv1.reduce((sum, v) => sum + v, 0) / gainLossValuesQv1.length,
            min: Math.min(...gainLossValuesQv1),
            max: Math.max(...gainLossValuesQv1),
            median: (() => {
              const sorted = [...gainLossValuesQv1].sort((a, b) => a - b)
              const mid = Math.floor(sorted.length / 2)
              return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
            })(),
            stdDev: (() => {
              const mean = gainLossValuesQv1.reduce((sum, v) => sum + v, 0) / gainLossValuesQv1.length
              const variance = gainLossValuesQv1.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / gainLossValuesQv1.length
              return Math.sqrt(variance)
            })(),
            perfectMatchCount: perfectMatchCountQv1,
            perfectMatchRate: perfectMatchRateQv1
          },
          // Q_w(v) 统计
          qw: {
            mean: gainLossValuesQw.reduce((sum, v) => sum + v, 0) / gainLossValuesQw.length,
            min: Math.min(...gainLossValuesQw),
            max: Math.max(...gainLossValuesQw),
            median: (() => {
              const sorted = [...gainLossValuesQw].sort((a, b) => a - b)
              const mid = Math.floor(sorted.length / 2)
              return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
            })(),
            stdDev: (() => {
              const mean = gainLossValuesQw.reduce((sum, v) => sum + v, 0) / gainLossValuesQw.length
              const variance = gainLossValuesQw.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / gainLossValuesQw.length
              return Math.sqrt(variance)
            })(),
            perfectMatchCount: perfectMatchCountQw,
            perfectMatchRate: perfectMatchRateQw
          },
          // Q_2(v) 统计
          q2: {
            mean: gainLossValuesQ2.reduce((sum, v) => sum + v, 0) / gainLossValuesQ2.length,
            min: Math.min(...gainLossValuesQ2),
            max: Math.max(...gainLossValuesQ2),
            median: (() => {
              const sorted = [...gainLossValuesQ2].sort((a, b) => a - b)
              const mid = Math.floor(sorted.length / 2)
              return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
            })(),
            stdDev: (() => {
              const mean = gainLossValuesQ2.reduce((sum, v) => sum + v, 0) / gainLossValuesQ2.length
              const variance = gainLossValuesQ2.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / gainLossValuesQ2.length
              return Math.sqrt(variance)
            })(),
            perfectMatchCount: perfectMatchCountQ2,
            perfectMatchRate: perfectMatchRateQ2
          },
          // Q_3(v) 统计
          q3: {
            mean: gainLossValuesQ3.reduce((sum, v) => sum + v, 0) / gainLossValuesQ3.length,
            min: Math.min(...gainLossValuesQ3),
            max: Math.max(...gainLossValuesQ3),
            median: (() => {
              const sorted = [...gainLossValuesQ3].sort((a, b) => a - b)
              const mid = Math.floor(sorted.length / 2)
              return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
            })(),
            stdDev: (() => {
              const mean = gainLossValuesQ3.reduce((sum, v) => sum + v, 0) / gainLossValuesQ3.length
              const variance = gainLossValuesQ3.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / gainLossValuesQ3.length
              return Math.sqrt(variance)
            })(),
            perfectMatchCount: perfectMatchCountQ3,
            perfectMatchRate: perfectMatchRateQ3
          },
          worstCase: {
            round: worstCase.round,
            gainLoss: worstCase.gainLoss.Gain_Gap_Ratio,
            theoreticalBestRate: worstCase.gainLoss.P_best_Theory,
            ivPredictedBestRate: worstCase.gainLoss.P_best_Iv,
            qvPredictedBestRate: worstCase.gainLoss.P_best_Qv,
            theoreticalBestNode: worstCase.gainLoss.optimalNode,
            ivSelectedNode: worstCase.gainLoss.ivSelectsNode,
            qvSelectedNode: worstCase.gainLoss.qvSelectsNode,
            allNodes: worstCaseNodes
          }
        }
        
        console.log(`\n=== I(v) Gain Loss 统计数据 ===`)
        console.log(`  - 平均值 (Mean): ${gainLossStats.mean.toFixed(3)}%`)
        console.log(`  - 标准差 (Std Dev): ${gainLossStats.stdDev.toFixed(3)}%`)
        console.log(`  - 最小值 (Min): ${gainLossStats.min.toFixed(3)}%`)
        console.log(`  - 最大值 (Max): ${gainLossStats.max.toFixed(3)}%`)
        console.log(`  - 中位数 (Median): ${gainLossStats.median.toFixed(3)}%`)
        console.log(`  - 完美匹配: ${perfectMatchCount}/${gainLossValues.length} (${perfectMatchRate.toFixed(1)}%)`)
        console.log(`\n=== Q(v) Gain Loss 统计数据 ===`)
        console.log(`  - 平均值 (Mean): ${gainLossStats.qv.mean.toFixed(3)}%`)
        console.log(`  - 标准差 (Std Dev): ${gainLossStats.qv.stdDev.toFixed(3)}%`)
        console.log(`  - 最小值 (Min): ${gainLossStats.qv.min.toFixed(3)}%`)
        console.log(`  - 最大值 (Max): ${gainLossStats.qv.max.toFixed(3)}%`)
        console.log(`  - 中位数 (Median): ${gainLossStats.qv.median.toFixed(3)}%`)
        console.log(`  - 完美匹配: ${perfectMatchCountQv}/${gainLossValuesQv.length} (${perfectMatchRateQv.toFixed(1)}%)`)
        
        // ✅ 添加 Q_v1 Tie-breaker 触发统计
        console.log(`\n=== Q_v1 Tie-breaker 触发统计 ===`)
        console.log(`  - 总轮次: ${totalRounds}`)
        console.log(`  - Tie-breaker 触发: ${qv1TiebreakerTriggered} 次 (${(qv1TiebreakerTriggered/totalRounds*100).toFixed(1)}%)`)
        console.log(`  - 选择与 Q(v) 不同: ${qv1SelectionDifferent} 次 (${qv1TiebreakerTriggered > 0 ? (qv1SelectionDifferent/qv1TiebreakerTriggered*100).toFixed(1) : 0}% of triggered)`)
        console.log(`  - Q_v1 完美匹配: ${perfectMatchCountQv1}/${gainLossValuesQv1.length} (${perfectMatchRateQv1.toFixed(1)}%)`)
        
        if (qv1TiebreakerTriggered === 0) {
          console.log(`  ⚠️ 警告：Tie-breaker 从未触发！`)
          console.log(`     - 可能原因：epsilon_r 阈值(${epsilon_r})太小`)
          console.log(`     - 建议：增大阈值到 0.1 或 0.2`)
        } else if (qv1SelectionDifferent === 0) {
          console.log(`  ⚠️ 警告：Tie-breaker 触发了 ${qv1TiebreakerTriggered} 次，但从未改变选择！`)
          console.log(`     - 原因：E(v) 与 Q(v) 高度相关`)
          console.log(`     - 建议：改用 Φ_q(v) 作为二级指标`)
        } else {
          console.log(`  ✅ Tie-breaker 工作正常：${qv1SelectionDifferent}/${qv1TiebreakerTriggered} 次改变了选择`)
        }
        
        console.log(`  - 最差案例 (Round ${gainLossStats.worstCase.round}):`)
        console.log(`    - Gain Loss: ${gainLossStats.worstCase.gainLoss.toFixed(3)}%`)
        console.log(`    - 理论最优 (Node ${gainLossStats.worstCase.theoreticalBestNode}): ${gainLossStats.worstCase.theoreticalBestRate.toFixed(2)}%`)
        console.log(`    - I(v)选择 (Node ${gainLossStats.worstCase.ivSelectedNode}): ${gainLossStats.worstCase.ivPredictedBestRate.toFixed(2)}%`)
        console.log(`    - Q(v)选择 (Node ${gainLossStats.worstCase.qvSelectedNode}): ${gainLossStats.worstCase.qvPredictedBestRate.toFixed(2)}%`)
        
        // 保存统计数据
        batchExperimentResults.value.gainLossStats = gainLossStats
        
        // 最后一轮的结果显示在图表上
        if (batchExperimentResults.value.length > 0) {
          const lastRound = batchExperimentResults.value[batchExperimentResults.value.length - 1]
          allProposersResults.value = lastRound.results
          
          // 更新拓扑编辑器显示最后一轮的矩阵
          if (topologyRef.value) {
            topologyRef.value.reliabilityMatrix = JSON.parse(JSON.stringify(lastRound.reliabilityMatrix))
            // 触发拓扑图重绘
            await nextTick()
            topologyRef.value.drawTopology?.()
          }
          
          await nextTick()
          createAllProposersChart()
          
          // 更新统计数据显示
          gainLossStatsDisplay.value = true
          gainLossStatsHTML.value = `<div style="text-align: left;">
              <h3 style="margin-bottom: 15px;">Gain Loss Statistics (${batchExperimentResults.value.length} rounds)</h3>
              
              <h4 style="margin: 10px 0 8px 0; color: #409EFF;">I(v) Selection Performance</h4>
              <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Mean</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.mean.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Std Dev</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.stdDev.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Min</td>
                  <td style="padding: 8px; text-align: right; color: #67C23A;">${gainLossStats.min.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Max</td>
                  <td style="padding: 8px; text-align: right; color: #F56C6C;">${gainLossStats.max.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Median</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.median.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 2px solid #409EFF; background-color: #f0f9ff;">
                  <td style="padding: 8px; font-weight: bold; color: #409EFF;">Perfect Match (I(v))</td>
                  <td style="padding: 8px; text-align: right; font-weight: bold; color: #409EFF;">${gainLossStats.perfectMatchCount}/${batchExperimentResults.value.length} (${gainLossStats.perfectMatchRate.toFixed(1)}%)</td>
                </tr>
              </table>
              
              <h4 style="margin: 15px 0 8px 0; color: #E6A23C;">Q(v) Selection Performance</h4>
              <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Mean</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qv.mean.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Std Dev</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qv.stdDev.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Min</td>
                  <td style="padding: 8px; text-align: right; color: #67C23A;">${gainLossStats.qv.min.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Max</td>
                  <td style="padding: 8px; text-align: right; color: #F56C6C;">${gainLossStats.qv.max.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Median</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qv.median.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 2px solid #E6A23C; background-color: #fff7e6;">
                  <td style="padding: 8px; font-weight: bold; color: #E6A23C;">Perfect Match (Q(v))</td>
                  <td style="padding: 8px; text-align: right; font-weight: bold; color: #E6A23C;">${gainLossStats.qv.perfectMatchCount}/${batchExperimentResults.value.length} (${gainLossStats.qv.perfectMatchRate.toFixed(1)}%)</td>
                </tr>
              </table>
              
              <h4 style="margin: 15px 0 8px 0; color: #13C2C2;">Q_v1 Selection Performance (Q + Tie-breaker) ✨ NEW</h4>
              <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Mean</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qv1.mean.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Std Dev</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qv1.stdDev.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Min</td>
                  <td style="padding: 8px; text-align: right; color: #67C23A;">${gainLossStats.qv1.min.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Max</td>
                  <td style="padding: 8px; text-align: right; color: #F56C6C;">${gainLossStats.qv1.max.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Median</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qv1.median.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 2px solid #13C2C2; background-color: #e6fafa;">
                  <td style="padding: 8px; font-weight: bold; color: #13C2C2;">Perfect Match (Q_v1)</td>
                  <td style="padding: 8px; text-align: right; font-weight: bold; color: #13C2C2;">${gainLossStats.qv1.perfectMatchCount}/${batchExperimentResults.value.length} (${gainLossStats.qv1.perfectMatchRate.toFixed(1)}%)</td>
                </tr>
              </table>
              
              <h4 style="margin: 15px 0 8px 0; color: #909399;">Q_w(v) Selection Performance ⭐ NEW</h4>
              <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Mean</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qw.mean.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Std Dev</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qw.stdDev.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Min</td>
                  <td style="padding: 8px; text-align: right; color: #67C23A;">${gainLossStats.qw.min.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Max</td>
                  <td style="padding: 8px; text-align: right; color: #F56C6C;">${gainLossStats.qw.max.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Median</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.qw.median.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 2px solid #909399; background-color: #f4f4f5;">
                  <td style="padding: 8px; font-weight: bold; color: #909399;">Perfect Match (Q_w(v))</td>
                  <td style="padding: 8px; text-align: right; font-weight: bold; color: #909399;">${gainLossStats.qw.perfectMatchCount}/${batchExperimentResults.value.length} (${gainLossStats.qw.perfectMatchRate.toFixed(1)}%)</td>
                </tr>
              </table>
              
              <h4 style="margin: 15px 0 8px 0; color: #52C41A;">Q_2(v) Selection Performance 📊 NEW (Avg Outgoing)</h4>
              <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Mean</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.q2.mean.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Std Dev</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.q2.stdDev.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Min</td>
                  <td style="padding: 8px; text-align: right; color: #67C23A;">${gainLossStats.q2.min.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Max</td>
                  <td style="padding: 8px; text-align: right; color: #F56C6C;">${gainLossStats.q2.max.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Median</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.q2.median.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 2px solid #52C41A; background-color: #f6ffed;">
                  <td style="padding: 8px; font-weight: bold; color: #52C41A;">Perfect Match (Q_2(v))</td>
                  <td style="padding: 8px; text-align: right; font-weight: bold; color: #52C41A;">${gainLossStats.q2.perfectMatchCount}/${batchExperimentResults.value.length} (${gainLossStats.q2.perfectMatchRate.toFixed(1)}%)</td>
                </tr>
              </table>
              
              <h4 style="margin: 15px 0 8px 0; color: #5B8FF9;">Q_3(v) Selection Performance 🔒 NEW (Ultra-Strict k=n-1)</h4>
              <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Mean</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.q3.mean.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Std Dev</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.q3.stdDev.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Min</td>
                  <td style="padding: 8px; text-align: right; color: #67C23A;">${gainLossStats.q3.min.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Max</td>
                  <td style="padding: 8px; text-align: right; color: #F56C6C;">${gainLossStats.q3.max.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                  <td style="padding: 8px; font-weight: bold;">Median</td>
                  <td style="padding: 8px; text-align: right;">${gainLossStats.q3.median.toFixed(3)}%</td>
                </tr>
                <tr style="border-bottom: 2px solid #5B8FF9; background-color: #f0f5ff;">
                  <td style="padding: 8px; font-weight: bold; color: #5B8FF9;">Perfect Match (Q_3(v))</td>
                  <td style="padding: 8px; text-align: right; font-weight: bold; color: #5B8FF9;">${gainLossStats.q3.perfectMatchCount}/${batchExperimentResults.value.length} (${gainLossStats.q3.perfectMatchRate.toFixed(1)}%)</td>
                </tr>
              </table>
              
              <div style="margin-top: 20px; padding: 12px; background-color: #fff3f3; border-left: 4px solid #F56C6C; border-radius: 4px;">
                <h4 style="margin: 0 0 10px 0; color: #F56C6C; font-size: 14px;">Worst Case Analysis (Round ${gainLossStats.worstCase.round})</h4>
                <table style="width: 100%; font-size: 13px; margin-bottom: 12px;">
                  <tr>
                    <td style="padding: 4px 0; color: #666;">Gain Loss (I(v)):</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold; color: #F56C6C;">${gainLossStats.worstCase.gainLoss.toFixed(2)}%</td>
                  </tr>
                  <tr>
                    <td style="padding: 4px 0; color: #666;">Theory Best (Node ${gainLossStats.worstCase.theoreticalBestNode}):</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${gainLossStats.worstCase.theoreticalBestRate.toFixed(2)}%</td>
                  </tr>
                  <tr>
                    <td style="padding: 4px 0; color: #666;">I(v) Selects (Node ${gainLossStats.worstCase.ivSelectedNode}):</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${gainLossStats.worstCase.ivPredictedBestRate.toFixed(2)}%</td>
                  </tr>
                  <tr>
                    <td style="padding: 4px 0; color: #666;">Q(v) Selects (Node ${gainLossStats.worstCase.qvSelectedNode}):</td>
                    <td style="padding: 4px 0; text-align: right; font-weight: bold;">${gainLossStats.worstCase.qvPredictedBestRate.toFixed(2)}%</td>
                  </tr>
                </table>
                
                <h5 style="margin: 10px 0 8px 0; color: #666; font-size: 12px;">All Nodes in This Round:</h5>
                <div style="max-height: 300px; overflow-y: auto; border: 1px solid #eee; border-radius: 4px;">
                  <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                    <thead style="position: sticky; top: 0; background-color: #fafafa; border-bottom: 2px solid #ddd;">
                      <tr>
                        <th style="padding: 6px 8px; text-align: left; font-weight: bold;">Node</th>
                        <th style="padding: 6px 8px; text-align: right; font-weight: bold;">Theory (%)</th>
                        <th style="padding: 6px 8px; text-align: right; font-weight: bold;">I(v) (%)</th>
                        <th style="padding: 6px 8px; text-align: right; font-weight: bold;">Q(v) (%)</th>
                        <th style="padding: 6px 8px; text-align: center; font-weight: bold;">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${gainLossStats.worstCase.allNodes.map(node => `
                        <tr style="border-bottom: 1px solid #f0f0f0; ${node.isTheoryBest ? 'background-color: #f0f9ff;' : ''} ${node.isIvSelected && !node.isQvSelected ? 'background-color: #fff7e6;' : ''} ${node.isQvSelected && !node.isIvSelected ? 'background-color: #fef0f0;' : ''} ${node.isIvSelected && node.isQvSelected ? 'background-color: #f0fdf4;' : ''}">
                          <td style="padding: 6px 8px; font-weight: ${node.isTheoryBest || node.isIvSelected || node.isQvSelected ? 'bold' : 'normal'};">Node ${node.nodeId}</td>
                          <td style="padding: 6px 8px; text-align: right; ${node.isTheoryBest ? 'color: #409EFF; font-weight: bold;' : ''}">${node.theoreticalRate.toFixed(2)}</td>
                          <td style="padding: 6px 8px; text-align: right; ${node.isIvSelected ? 'color: #E6A23C; font-weight: bold;' : ''}">${node.ivValue.toFixed(2)}</td>
                          <td style="padding: 6px 8px; text-align: right; ${node.isQvSelected ? 'color: #F56C6C; font-weight: bold;' : ''}">${node.qvValue.toFixed(2)}</td>
                          <td style="padding: 6px 8px; text-align: center; font-size: 11px;">
                            ${node.isTheoryBest ? '<span style="color: #409EFF;">✓</span>' : ''}
                            ${node.isIvSelected ? '<span style="color: #E6A23C;">★I</span>' : ''}
                            ${node.isQvSelected ? '<span style="color: #F56C6C;">●Q</span>' : ''}
                          </td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
              
              <div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; font-size: 12px; color: #666;">
                <strong>Legend:</strong><br/>
                <strong style="color: #409EFF;">✓</strong> Theoretically optimal node |
                <strong style="color: #E6A23C;">★I</strong> Node selected by I(v) |
                <strong style="color: #F56C6C;">●Q</strong> Node selected by Q(v)
              </div>
            </div>`
          
          ElMessage.success(`Batch Experiments Completed! ${batchExperimentResults.value.length} rounds finished.`)
        }
        
        batchExperimentRunning.value = false
        experimentStopRequested.value = false
        currentBatchRound.value = 0
        
        console.log(`\n=== 批量实验完成！共${batchExperimentResults.value.length}轮 ===`)
        ElMessage.success(`批量随机实验完成！共${batchExperimentResults.value.length}轮`)
        
      } catch (error) {
        console.error('批量实验失败:', error)
        ElMessage.error(`批量实验失败: ${error.message}`)
        batchExperimentRunning.value = false
        experimentStopRequested.value = false
        currentBatchRound.value = 0
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
      
      console.log('图表数据:', { proposerLabels, theoreticalData })
      
      // 从后端返回的 metrics 中提取新指标
      const quorumReachData = allProposersResults.value.map(r => r.metrics?.Q_pp || 0)
      const quorumReachDataW = allProposersResults.value.map(r => r.metrics?.Q_w || 0)  // Q_w
      const ivData = allProposersResults.value.map(r => r.metrics?.I_v || 0)  // I(v) - 新的复合指标
      const q2Data = allProposersResults.value.map(r => r.metrics?.Q_2 || 0)  // Q_2
      const q3Data = allProposersResults.value.map(r => r.metrics?.Q_3 || 0)  // Q_3 (严格阈值 k=n-1)
      const phiMinData = allProposersResults.value.map(r => r.metrics?.Phi_min || 0)
      const phiQData = allProposersResults.value.map(r => r.metrics?.Phi_q || 0)
      const compositeData = allProposersResults.value.map(r => r.metrics?.I_v || 0)
      
      console.log('主节点选择指标（来自后端）:')
      console.log('  - Q(v) 触达概率:', quorumReachData)
      console.log('  - Q_w(v) 加权触达概率:', quorumReachDataW)
      console.log('  - I(v) 复合指标 (0.6·Q + 0.4·Q_w):', ivData)
      console.log('  - Q_2(v) 平均发送能力:', q2Data)
      console.log('  - Φ_min(v) 最弱节点:', phiMinData)
      console.log('  - Φ_q(v) Quorum聚合(尾概率):', phiQData)
      console.log('  - I(v) 综合指标 (Q_pp×Φ_q):', compositeData)
      
      // 检查是否有平均理论值
      const hasAverageTheoretical = false
      
      // 计算统计指标（基于理论成功率）
      const n = experimentConfig.nodeCount
      const f = experimentConfig.faultyNodes
      
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
      
      // 5. 节点层面不均匀性（CV_I(v)）- 基于 I(v) Composite Index
      let CV_out = 0
      let CV_link = 0
      
      // 计算 I(v) 的变异系数
      if (compositeData.length > 0) {
        const meanComposite = compositeData.reduce((sum, val) => sum + val, 0) / compositeData.length
        const varianceComposite = compositeData.reduce((sum, val) => sum + Math.pow(val - meanComposite, 2), 0) / compositeData.length
        const stdDevComposite = Math.sqrt(varianceComposite)
        CV_out = (stdDevComposite / meanComposite) * 100
      }
      
      if (experimentConfig.reliabilityMode === 'custom' && experimentConfig.customReliabilityMatrix) {
        const matrix = experimentConfig.customReliabilityMatrix
        const n = matrix.length
        
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
      
      // 计算各指标与理论成功率的 Spearman 相关系数
      const rho_Qv_Theory = calculateSpearman(quorumReachData, theoreticalData)
      const rho_Qw_Theory = calculateSpearman(quorumReachDataW, theoreticalData)
      const rho_Iv_Theory = calculateSpearman(ivData, theoreticalData)  // I(v) 相关性
      const rho_Q2_Theory = calculateSpearman(q2Data, theoreticalData)
      const rho_Q3_Theory = calculateSpearman(q3Data, theoreticalData)
      
      // 计算误差指标: I(v) 预测理论成功率的准确性
      const errorMetrics_Iv = calculateIsotonicError(compositeData, theoreticalData)
      
      // 计算误差指标: Q(v) 预测理论成功率的准确性
      const errorMetrics_Qv = calculateIsotonicError(quorumReachData, theoreticalData)
      
      // ========== 新增：计算 I(v) 选择 vs 理论最优选择的 Gain 差异 ==========
      // 1. 找到 I(v) 最大值对应的节点
      const maxIvIndex = compositeData.indexOf(Math.max(...compositeData))
      const P_best_Iv = theoreticalData[maxIvIndex]  // I(v)最大节点的理论成功率
      
      // 2. 找到理论成功率最大值
      const maxTheoryIndex = theoreticalData.indexOf(Math.max(...theoreticalData))
      const P_best_Theory = theoreticalData[maxTheoryIndex]  // 理论最优
      
      // 3. 计算排序位次，用于标记不匹配的节点
      // 为每个节点计算在 I(v) 和理论值中的排名
      const ivRanking = ivData.map((v, idx) => ({ idx, value: v }))
        .sort((a, b) => b.value - a.value)
        .map((item, rank) => ({ idx: item.idx, rank: rank }))
        .sort((a, b) => a.idx - b.idx)
        .map(item => item.rank)
      
      const theoryRanking = theoreticalData.map((v, idx) => ({ idx, value: v }))
        .sort((a, b) => b.value - a.value)
        .map((item, rank) => ({ idx: item.idx, rank: rank }))
        .sort((a, b) => a.idx - b.idx)
        .map(item => item.rank)
      
      console.log('\n=== 排序对比 ===')
      console.log('  I(v) 排名:', ivRanking)
      console.log('  理论值排名:', theoryRanking)
      
      // 3. 平均理论成功率（随机选择的基准）
      // P_avg 已在前面计算
      
      // 4. 计算 Gain
      const Gain_Iv = P_best_Iv - P_avg  // 使用 I(v) 选择的增益
      const Gain_Theory = P_best_Theory - P_avg  // 理论最优增益
      
      // 5. 计算差异比例
      const Gain_Gap = Gain_Theory - Gain_Iv  // 绝对差距
      const Gain_Gap_Ratio = Gain_Theory > 0 ? (Gain_Gap / Gain_Theory) * 100 : 0  // 相对差距（百分比）
      
      console.log('\n=== I(v) 选择 vs 理论最优选择 ===')
      console.log(`  - 理论最优节点: Node ${maxTheoryIndex}, 成功率: ${P_best_Theory.toFixed(2)}%`)
      console.log(`  - I(v) 最大节点: Node ${maxIvIndex}, 成功率: ${P_best_Iv.toFixed(2)}%`)
      console.log(`  - 平均成功率（随机选择）: ${P_avg.toFixed(2)}%`)
      console.log(`  - Gain (理论最优): ${Gain_Theory.toFixed(2)}%`)
      console.log(`  - Gain (I(v) 选择): ${Gain_Iv.toFixed(2)}%`)
      console.log(`  - Gain 差距: ${Gain_Gap.toFixed(2)}%`)
      console.log(`  - Gain 损失比例: ${Gain_Gap_Ratio.toFixed(2)}% (越小越好)`)
      
      console.log('[All Proposers Chart] 统计指标:')
      console.log(`  - Expected Gain: ${gainAvg.toFixed(2)}%`)
      console.log(`  - Worst-case Improvement: ${gainWorst.toFixed(2)}%`)
      console.log(`\n=== 各指标与Theory的Spearman相关性 ===`)
      console.log(`  - ρ(Q(v), Theory): ${rho_Qv_Theory?.toFixed(4) || 'N/A'}`)
      console.log(`  - ρ(Q_w(v), Theory): ${rho_Qw_Theory?.toFixed(4) || 'N/A'}`)
      console.log(`  - ρ(I(v), Theory): ${rho_Iv_Theory?.toFixed(4) || 'N/A'}`)
      console.log(`  - ρ(Q_2(v), Theory): ${rho_Q2_Theory?.toFixed(4) || 'N/A'}`)
      console.log(`  - ρ(Q_3(v), Theory): ${rho_Q3_Theory?.toFixed(4) || 'N/A'} [严格阈值 k=n-1]`)
      
      console.log('\n=== 预测准确性对比 ===')
      if (errorMetrics_Qv) {
        console.log(`  Q(v) 预测误差:`)
        console.log(`    * MAE: ${errorMetrics_Qv.mae.toFixed(3)}%`)
        console.log(`    * RMSE: ${errorMetrics_Qv.rmse.toFixed(3)}%`)
        console.log(`    * R²: ${errorMetrics_Qv.r2.toFixed(4)}`)
      }
      if (errorMetrics_Iv) {
        console.log(`  I(v) 预测误差:`)
        console.log(`    * MAE: ${errorMetrics_Iv.mae.toFixed(3)}%`)
        console.log(`    * RMSE: ${errorMetrics_Iv.rmse.toFixed(3)}%`)
        console.log(`    * R²: ${errorMetrics_Iv.r2.toFixed(4)}`)
      }
      if (errorMetrics_Iv && errorMetrics_Qv) {
        const mae_improvement = ((errorMetrics_Qv.mae - errorMetrics_Iv.mae) / errorMetrics_Qv.mae * 100)
        const rmse_improvement = ((errorMetrics_Qv.rmse - errorMetrics_Iv.rmse) / errorMetrics_Qv.rmse * 100)
        const r2_improvement = ((errorMetrics_Iv.r2 - errorMetrics_Qv.r2) / (1 - errorMetrics_Qv.r2) * 100)
        console.log(`  相对改进:`)
        console.log(`    * MAE改进: ${mae_improvement > 0 ? '+' : ''}${mae_improvement.toFixed(2)}% (${mae_improvement > 0 ? 'I(v)更好 ✓' : 'Q(v)更好'})`)
        console.log(`    * RMSE改进: ${rmse_improvement > 0 ? '+' : ''}${rmse_improvement.toFixed(2)}%`)
        console.log(`    * R²改进: ${r2_improvement > 0 ? '+' : ''}${r2_improvement.toFixed(2)}%`)
      }
      
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
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          formatter: function(params) {
            let result = `<div style="font-weight: bold; margin-bottom: 8px;">${params[0].axisValue}</div>`
            params.forEach(param => {
              const value = param.value !== undefined ? param.value : 0
              result += `
                <div style="display: flex; align-items: center; margin: 4px 0;">
                  <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                  <span style="flex: 1;">${param.seriesName}:</span>
                  <span style="font-weight: bold; margin-left: 8px;">${value.toFixed(2)}%</span>
                </div>`
            })
            return result
          }
        },
        // 添加图形元素显示统计指标
        graphic: [
          {
            type: 'group',
            right: 40,
            top: -50,  // 大幅向上移动，让框的底部高于图表区域
            children: [
              {
                type: 'rect',
                shape: {
                  width: 280,
                  height: 180  // 调整高度：标题 + 2项指标 + 分隔线 + 4项相关性
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
                  text: `Expected Gain: ${gainAvg.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 30
              },
              {
                type: 'text',
                style: {
                  text: `Worst-case Improvement: ${gainWorst.toFixed(2)}%`,
                  font: '12px sans-serif',
                  fill: '#666'
                },
                left: 10,
                top: 50
              },
              {
                type: 'line',
                shape: {
                  x1: 10,
                  y1: 70,
                  x2: 270,
                  y2: 70
                },
                style: {
                  stroke: '#ddd',
                  lineWidth: 1
                }
              },
              {
                type: 'text',
                style: {
                  text: `ρ(Q(v), Theory): ${rho_Qv_Theory?.toFixed(3) || 'N/A'}`,
                  font: '12px sans-serif',
                  fill: '#67C23A',
                  fontWeight: 'bold'
                },
                left: 10,
                top: 78
              },
              {
                type: 'text',
                style: {
                  text: rho_Qv_Theory !== null && rho_Qv_Theory !== undefined ? (Math.abs(rho_Qv_Theory) > 0.7 ? '(Strong ✓)' : Math.abs(rho_Qv_Theory) > 0.4 ? '(Moderate)' : '(Weak)') : '',
                  font: '10px sans-serif',
                  fill: '#999'
                },
                left: 190,
                top: 80
              },
              {
                type: 'text',
                style: {
                  text: `ρ(Q_w(v), Theory): ${rho_Qw_Theory?.toFixed(3) || 'N/A'}`,
                  font: '12px sans-serif',
                  fill: '#13C2C2',
                  fontWeight: 'bold'
                },
                left: 10,
                top: 98
              },
              {
                type: 'text',
                style: {
                  text: rho_Qw_Theory !== null && rho_Qw_Theory !== undefined ? (Math.abs(rho_Qw_Theory) > 0.7 ? '(Strong ✓)' : Math.abs(rho_Qw_Theory) > 0.4 ? '(Moderate)' : '(Weak)') : '',
                  font: '10px sans-serif',
                  fill: '#999'
                },
                left: 210,
                top: 100
              },
              {
                type: 'text',
                style: {
                  text: `ρ(I(v), Theory): ${rho_Iv_Theory?.toFixed(3) || 'N/A'}`,
                  font: '12px sans-serif',
                  fill: '#E6A23C',
                  fontWeight: 'bold'
                },
                left: 10,
                top: 118
              },
              {
                type: 'text',
                style: {
                  text: rho_Iv_Theory !== null && rho_Iv_Theory !== undefined ? (Math.abs(rho_Iv_Theory) > 0.7 ? '(Strong ✓)' : Math.abs(rho_Iv_Theory) > 0.4 ? '(Moderate)' : '(Weak)') : '',
                  font: '10px sans-serif',
                  fill: '#999'
                },
                left: 220,
                top: 120
              },
              {
                type: 'text',
                style: {
                  text: `ρ(Q_3(v), Theory): ${rho_Q3_Theory?.toFixed(3) || 'N/A'}`,
                  font: '12px sans-serif',
                  fill: '#909399',
                  fontWeight: 'bold'
                },
                left: 10,
                top: 138
              },
              {
                type: 'text',
                style: {
                  text: rho_Q3_Theory !== null && rho_Q3_Theory !== undefined ? (Math.abs(rho_Q3_Theory) > 0.7 ? '(Strong ✓)' : Math.abs(rho_Q3_Theory) > 0.4 ? '(Moderate)' : '(Weak)') : '',
                  font: '10px sans-serif',
                  fill: '#999'
                },
                left: 210,
                top: 140
              },
              // 历史数据相关性分析
              ...(correlationResults.value ? [{
                type: 'line',
                shape: {
                  x1: 10,
                  y1: 315,
                  x2: 270,
                  y2: 315
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
                top: 323
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
                top: 341
              },
              {
                type: 'text',
                style: {
                  text: `(n=${correlationResults.value.sampleSize})`,
                  font: '10px sans-serif',
                  fill: '#999'
                },
                left: 235,
                top: 323
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
          data: ['Theoretical Success Rate', 'Q(v) Quorum Reach', 'Q_w(v) Weighted Quorum', 'I(v) (0.6·Q+0.4·Q_w)', 'Q_3(v) Strict Quorum'],
          top: 40,
          left: 10,
          right: 330,
          itemGap: 15
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '240px',  // 进一步增加顶部空间，确保统计框完全在图表上方
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
            data: theoreticalData.map((value, idx) => {
              const isIvSelected = idx === maxIvIndex
              const isTheoryBest = idx === maxTheoryIndex
              const rankMismatch = ivRanking[idx] !== theoryRanking[idx]
              
              return {
                value: value,
                itemStyle: {
                  color: isIvSelected ? '#FA8C16' : colors[idx % colors.length],
                  opacity: isIvSelected ? 1 : 0.75,
                  borderColor: rankMismatch ? '#FF0000' : (isIvSelected ? '#FA8C16' : 'rgba(255,255,255,0.3)'),
                  borderWidth: rankMismatch ? 5 : (isIvSelected ? 4 : 1),
                  shadowBlur: isIvSelected ? 25 : 0,
                  shadowColor: isIvSelected ? 'rgba(250, 140, 22, 0.9)' : 'transparent',
                  shadowOffsetX: 0,
                  shadowOffsetY: 0
                }
              }
            }),
            emphasis: {
              itemStyle: {
                shadowBlur: 25,
                shadowColor: 'rgba(0,0,0,0.4)'
              }
            },
            label: {
              show: true,
              position: 'inside',
              formatter: function(params) {
                const isIvSelected = params.dataIndex === maxIvIndex
                const val = params.value
                return isIvSelected ? `${val}%\n(I(v)选中)` : `${val}%`
              },
              fontSize: 11,
              color: '#000',
              fontWeight: 600
            }
          },
          {
            name: 'Q(v) Quorum Reach',
            type: 'line',
            data: quorumReachData,
            itemStyle: {
              color: '#67C23A'
            },
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2
            },
            label: {
              show: false
            }
          },
          {
            name: 'Q_w(v) Weighted Quorum',
            type: 'line',
            data: quorumReachDataW,
            itemStyle: {
              color: '#13C2C2'
            },
            symbol: 'triangle',
            symbolSize: 7,
            lineStyle: {
              width: 2,
              type: 'dashed'
            },
            label: {
              show: false
            }
          },
          {
            name: 'I(v) (0.6·Q+0.4·Q_w)',
            type: 'line',
            data: ivData,
            itemStyle: {
              color: '#E6A23C'
            },
            symbol: 'diamond',
            symbolSize: 8,
            lineStyle: {
              width: 2
            },
            label: {
              show: false
            }
          },
          {
            name: 'Q_3(v) Strict Quorum',
            type: 'line',
            data: q3Data,
            itemStyle: {
              color: '#909399'
            },
            symbol: 'rect',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              type: 'dotted'
            },
            label: {
              show: false
            }
          }
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
          console.log(`[Experiment] 直连边数量: ${directEdgeCount}`)
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
        currentExperimentRound.value = experimentConfig.rounds
        
        console.log(`[Experiment] 批量ExperimentComplete:`)
        console.log(`  - Total Rounds: ${batchData.totalRounds}`)
        console.log(`  - Success: ${batchData.successCount}`)
        console.log(`  - Failure: ${batchData.failureCount}`)
        
        experimentRunning.value = false
        await cleanupExperimentSession()
        experimentStopRequested.value = false
        
        ElMessage.success(`Experiment completed! Success Rate (理论: ${batchData.theoreticalSuccessRate}%)`)
        
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
    
    // ✅ Handle Reliability Matrix update (Primary Selection 页面)
    const onPrimaryReliabilityMatrixUpdate = (matrix) => {
      primarySelectionConfig.customReliabilityMatrix = matrix
      
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
      
      console.log(`[Primary Selection] Reliability Matrix Updated:`)
      console.log(`  - Size: ${n}x${n}`)
      console.log(`  - Non-zero connections: ${nonZeroCount}`)
      console.log(`  - Average reliability: ${(avgReliability * 100).toFixed(1)}%`)
      console.log(`  - Topology: ${primarySelectionConfig.topology}`)
    }
    
    // ✅ Handle Proposer ID update (Primary Selection 页面)
    const onPrimaryProposerIdUpdate = (proposerId) => {
      primarySelectionConfig.proposerId = proposerId
      console.log('[Primary Selection] Proposer ID Updated:', proposerId)
      ElMessage.success(`Primary Selection - Primary node switched to Node ${proposerId}`)
    }
    
    // ✅ Handle Random Range update (Primary Selection 页面)
    const onPrimaryRandomRangeUpdate = ({ min, max }) => {
      primarySelectionConfig.randomMin = min
      primarySelectionConfig.randomMax = max
      console.log('[Primary Selection] Random Range Updated:', { min, max })
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
          nodeCount: primarySelectionConfig.nodeCount,
          faultyNodes: primarySelectionConfig.faultyNodes,
          topology: primarySelectionConfig.topology,
          reliability: primarySelectionConfig.reliability
        },
        proposersComparison: allProposersResults.value.map((r, idx) => ({
          proposerId: r.proposerId,
          theoreticalSuccessRate: r.theoreticalSuccessRate,
          // 主节点选择指标
          Q_v: r.metrics?.Q_pp || null,      // Q(v): Quorum 触达概率
          I_v: r.metrics?.I_v || null,       // I(v): 复合指标 (0.6·Q + 0.4·Q_w)
          Q_w: r.metrics?.Q_w || null,       // Q_w(v): 加权 Quorum 触达概率
          Q_2: r.metrics?.Q_2 || null,       // Q_2(v): 平均发送可靠度
          Q_3: r.metrics?.Q_3 || null,       // Q_3(v): 严格阈值 (k=n-1)
          // Prepare 阶段辅助指标
          Phi_q: r.metrics?.Phi_q || null,   // Φ_q(v): Quorum 聚合（尾概率）
          Phi_min: r.metrics?.Phi_min || null, // Φ_min(v): 最弱节点瓶颈
          s_v: r.metrics?.s_v || null        // s(v): 节点在线率
        })),
        summary: {
          totalProposersTested: allProposersResults.value.length,
          averageTheoreticalRate: (allProposersResults.value.reduce((sum, r) => sum + r.theoreticalSuccessRate, 0) / allProposersResults.value.length).toFixed(2),
          // 平均指标
          averageIv: allProposersResults.value.length > 0 && allProposersResults.value[0].metrics
            ? (allProposersResults.value.reduce((sum, r) => sum + (r.metrics?.I_v || 0), 0) / allProposersResults.value.length).toFixed(2)
            : null,
          averageQv: allProposersResults.value.length > 0 && allProposersResults.value[0].metrics
            ? (allProposersResults.value.reduce((sum, r) => sum + (r.metrics?.Q_pp || 0), 0) / allProposersResults.value.length).toFixed(2)
            : null,
          averageQw: allProposersResults.value.length > 0 && allProposersResults.value[0].metrics
            ? (allProposersResults.value.reduce((sum, r) => sum + (r.metrics?.Q_w || 0), 0) / allProposersResults.value.length).toFixed(2)
            : null,
          averageQ2: allProposersResults.value.length > 0 && allProposersResults.value[0].metrics
            ? (allProposersResults.value.reduce((sum, r) => sum + (r.metrics?.Q_2 || 0), 0) / allProposersResults.value.length).toFixed(2)
            : null,
          averageQ3: allProposersResults.value.length > 0 && allProposersResults.value[0].metrics
            ? (allProposersResults.value.reduce((sum, r) => sum + (r.metrics?.Q_3 || 0), 0) / allProposersResults.value.length).toFixed(2)
            : null
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
    
    // 导出批量实验结果
    const exportBatchExperimentResults = () => {
      if (batchExperimentResults.value.length === 0) {
        ElMessage.warning('No batch experiment data to export')
        return
      }
      
      const gainLossStats = batchExperimentResults.value.gainLossStats || {}
      
      const data = {
        config: {
          nodeCount: primarySelectionConfig.nodeCount,
          faultyNodes: primarySelectionConfig.faultyNodes,
          topology: primarySelectionConfig.topology,
          batchRounds: batchExperimentResults.value.length
        },
        gainLossStatistics: {
          iv: {
            mean: gainLossStats.mean?.toFixed(3),
            stdDev: gainLossStats.stdDev?.toFixed(3),
            min: gainLossStats.min?.toFixed(3),
            max: gainLossStats.max?.toFixed(3),
            median: gainLossStats.median?.toFixed(3),
            perfectMatchCount: gainLossStats.perfectMatchCount,
            perfectMatchRate: gainLossStats.perfectMatchRate?.toFixed(1) + '%'
          },
          iw: {
            mean: gainLossStats.iw?.mean?.toFixed(3),
            stdDev: gainLossStats.iw?.stdDev?.toFixed(3),
            min: gainLossStats.iw?.min?.toFixed(3),
            max: gainLossStats.iw?.max?.toFixed(3),
            median: gainLossStats.iw?.median?.toFixed(3),
            perfectMatchCount: gainLossStats.iw?.perfectMatchCount,
            perfectMatchRate: gainLossStats.iw?.perfectMatchRate?.toFixed(1) + '%'
          },
          qv: {
            mean: gainLossStats.qv?.mean?.toFixed(3),
            stdDev: gainLossStats.qv?.stdDev?.toFixed(3),
            min: gainLossStats.qv?.min?.toFixed(3),
            max: gainLossStats.qv?.max?.toFixed(3),
            median: gainLossStats.qv?.median?.toFixed(3),
            perfectMatchCount: gainLossStats.qv?.perfectMatchCount,
            perfectMatchRate: gainLossStats.qv?.perfectMatchRate?.toFixed(1) + '%'
          },
          qv1: {  // ✅ 新增
            mean: gainLossStats.qv1?.mean?.toFixed(3),
            stdDev: gainLossStats.qv1?.stdDev?.toFixed(3),
            min: gainLossStats.qv1?.min?.toFixed(3),
            max: gainLossStats.qv1?.max?.toFixed(3),
            median: gainLossStats.qv1?.median?.toFixed(3),
            perfectMatchCount: gainLossStats.qv1?.perfectMatchCount,
            perfectMatchRate: gainLossStats.qv1?.perfectMatchRate?.toFixed(1) + '%'
          },
          qw: {
            mean: gainLossStats.qw?.mean?.toFixed(3),
            stdDev: gainLossStats.qw?.stdDev?.toFixed(3),
            min: gainLossStats.qw?.min?.toFixed(3),
            max: gainLossStats.qw?.max?.toFixed(3),
            median: gainLossStats.qw?.median?.toFixed(3),
            perfectMatchCount: gainLossStats.qw?.perfectMatchCount,
            perfectMatchRate: gainLossStats.qw?.perfectMatchRate?.toFixed(1) + '%'
          },
          worstCase: {
            round: gainLossStats.worstCase?.round,
            gainLoss_Iv: gainLossStats.worstCase?.gainLoss?.toFixed(2) + '%',
            theoreticalBestNode: gainLossStats.worstCase?.theoreticalBestNode,
            theoreticalBestRate: gainLossStats.worstCase?.theoreticalBestRate?.toFixed(2) + '%',
            ivSelectedNode: gainLossStats.worstCase?.ivSelectedNode,
            ivPredictedBestRate: gainLossStats.worstCase?.ivPredictedBestRate?.toFixed(2) + '%',
            qvSelectedNode: gainLossStats.worstCase?.qvSelectedNode,
            qvPredictedBestRate: gainLossStats.worstCase?.qvPredictedBestRate?.toFixed(2) + '%',
            allNodes: gainLossStats.worstCase?.allNodes?.map(node => ({
              nodeId: node.nodeId,
              theoreticalRate: node.theoreticalRate.toFixed(2) + '%',
              ivValue: node.ivValue.toFixed(2) + '%',
              iwValue: node.iwValue.toFixed(2) + '%',
              qvValue: node.qvValue.toFixed(2) + '%',
              qwValue: node.qwValue.toFixed(2) + '%',
              isTheoryBest: node.isTheoryBest,
              isIvSelected: node.isIvSelected,
              isQvSelected: node.isQvSelected
            })) || []
          },
          unit: '%'
        },
        batchResults: batchExperimentResults.value.map(batch => ({
          round: batch.round,
          gainLoss: {
            optimalNode: batch.gainLoss.optimalNode,
            ivSelectsNode: batch.gainLoss.ivSelectsNode,
            iwSelectsNode: batch.gainLoss.iwSelectsNode,
            qvSelectsNode: batch.gainLoss.qvSelectsNode,
            qv1SelectsNode: batch.gainLoss.qv1SelectsNode,  // ✅ 新增
            qv1TiebreakerTriggered: batch.gainLoss.qv1TiebreakerTriggered,  // ✅ 新增
            qv1SelectionSameAsQv: batch.gainLoss.qv1SelectionSameAsQv,  // ✅ 新增
            qwSelectsNode: batch.gainLoss.qwSelectsNode,
            P_best_Theory: batch.gainLoss.P_best_Theory.toFixed(2),
            P_best_Iv: batch.gainLoss.P_best_Iv.toFixed(2),
            P_best_Qv: batch.gainLoss.P_best_Qv.toFixed(2),
            P_best_Qv1: batch.gainLoss.P_best_Qv1.toFixed(2),
            P_best_Qw: batch.gainLoss.P_best_Qw.toFixed(2),
            P_avg: batch.gainLoss.P_avg.toFixed(2),
            Gain_Theory: batch.gainLoss.Gain_Theory.toFixed(2),
            Gain_Iv: batch.gainLoss.Gain_Iv.toFixed(2),
            Gain_Qv: batch.gainLoss.Gain_Qv.toFixed(2),
            Gain_Qv1: batch.gainLoss.Gain_Qv1.toFixed(2),
            Gain_Qw: batch.gainLoss.Gain_Qw.toFixed(2),
            Gain_Gap_Iv: batch.gainLoss.Gain_Gap_Iv.toFixed(2),
            Gain_Gap_Ratio: batch.gainLoss.Gain_Gap_Ratio.toFixed(3) + '%',
            Gain_Gap_Qv: batch.gainLoss.Gain_Gap_Qv.toFixed(2),
            Gain_Gap_Ratio_Qv: batch.gainLoss.Gain_Gap_Ratio_Qv.toFixed(3) + '%',
            Gain_Gap_Qv1: batch.gainLoss.Gain_Gap_Qv1.toFixed(2),
            Gain_Gap_Ratio_Qv1: batch.gainLoss.Gain_Gap_Ratio_Qv1.toFixed(3) + '%',
            Gain_Gap_Qw: batch.gainLoss.Gain_Gap_Qw.toFixed(2),
            Gain_Gap_Ratio_Qw: batch.gainLoss.Gain_Gap_Ratio_Qw.toFixed(3) + '%'
          },
          nodeResults: batch.results.map(r => ({
            proposerId: r.proposerId,
            theoreticalSuccessRate: r.theoreticalSuccessRate.toFixed(2),
            I_v: r.metrics?.I_v?.toFixed(2) || 'N/A',
            Q_v: r.metrics?.Q_pp?.toFixed(2) || 'N/A',
            Q_w: r.metrics?.Q_w?.toFixed(2) || 'N/A'
          }))
        }))
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `batch-experiments-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('Batch experiment results exported successfully!')
    }
    
    // 导出 Gain Loss 不为 0 的轮次数据
    const exportMismatchedRounds = () => {
      if (batchExperimentResults.value.length === 0) {
        ElMessage.warning('No batch experiment data to export')
        return
      }
      
      // 分类统计 - 扩展到四种指标
      const allCorrect = []      // 四种指标都正确
      const anyMismatched = []   // 至少一种指标选错
      
      batchExperimentResults.value.forEach(batch => {
        const ivWrong = batch.gainLoss.Gain_Gap_Ratio >= 0.001
        const iwWrong = batch.gainLoss.Gain_Gap_Ratio_Iw >= 0.001
        const qvWrong = batch.gainLoss.Gain_Gap_Ratio_Qv >= 0.001
        const qv1Wrong = batch.gainLoss.Gain_Gap_Ratio_Qv1 >= 0.001
        const qwWrong = batch.gainLoss.Gain_Gap_Ratio_Qw >= 0.001
        const q2Wrong = batch.gainLoss.Gain_Gap_Ratio_Q2 >= 0.001
        const q3Wrong = batch.gainLoss.Gain_Gap_Ratio_Q3 >= 0.001
        
        // 记录哪些指标选错了
        const wrongMetrics = []
        if (ivWrong) wrongMetrics.push('I(v)')
        if (qvWrong) wrongMetrics.push('Q(v)')
        if (qv1Wrong) wrongMetrics.push('Q_v1(v)')
        if (qwWrong) wrongMetrics.push('Q_w(v)')
        if (q2Wrong) wrongMetrics.push('Q_2(v)')
        if (q3Wrong) wrongMetrics.push('Q_3(v)')
        if (qwWrong) wrongMetrics.push('Q_w(v)')
        if (q2Wrong) wrongMetrics.push('Q_2(v)')  // ✅ 新增 Q_2
        
        if (wrongMetrics.length > 0) {
          anyMismatched.push({
            ...batch,
            wrongMetrics: wrongMetrics,
            wrongCount: wrongMetrics.length
          })
        } else {
          allCorrect.push(batch)
        }
      })
      
      const totalMismatched = anyMismatched.length
      
      if (totalMismatched === 0) {
        ElMessage.info('All rounds are perfect matches for all metrics (I(v), Q(v), Q_v1, Q_w, Q_2, Q_3)! No mismatched data to export.')
        return
      }
      
      // 按轮次排序
      const sortedMismatched = anyMismatched.sort((a, b) => a.round - b.round)
      
      // 统计各指标的错误次数（删除I_w和Q_fix）
      let ivErrors = 0, qvErrors = 0, qv1Errors = 0, qwErrors = 0, q2Errors = 0, q3Errors = 0
      anyMismatched.forEach(batch => {
        if (batch.gainLoss.Gain_Gap_Ratio >= 0.001) ivErrors++
        if (batch.gainLoss.Gain_Gap_Ratio_Qv >= 0.001) qvErrors++
        if (batch.gainLoss.Gain_Gap_Ratio_Qv1 >= 0.001) qv1Errors++
        if (batch.gainLoss.Gain_Gap_Ratio_Qw >= 0.001) qwErrors++
        if (batch.gainLoss.Gain_Gap_Ratio_Q2 >= 0.001) q2Errors++
        if (batch.gainLoss.Gain_Gap_Ratio_Q3 >= 0.001) q3Errors++
      })
      
      const data = {
        summary: {
          totalRounds: batchExperimentResults.value.length,
          perfectMatchAll: allCorrect.length,
          mismatchedTotal: totalMismatched,
          mismatchRate: ((totalMismatched / batchExperimentResults.value.length) * 100).toFixed(1) + '%',
          errorsByMetric: {
            'I(v)': {
              count: ivErrors,
              rate: ((ivErrors / batchExperimentResults.value.length) * 100).toFixed(1) + '%'
            },
            'Q(v)': {
              count: qvErrors,
              rate: ((qvErrors / batchExperimentResults.value.length) * 100).toFixed(1) + '%'
            },
            'Q_v1(v)': {
              count: qv1Errors,
              rate: ((qv1Errors / batchExperimentResults.value.length) * 100).toFixed(1) + '%'
            },
            'Q_w(v)': {
              count: qwErrors,
              rate: ((qwErrors / batchExperimentResults.value.length) * 100).toFixed(1) + '%'
            },
            'Q_2(v)': {
              count: q2Errors,
              rate: ((q2Errors / batchExperimentResults.value.length) * 100).toFixed(1) + '%'
            },
            'Q_3(v)': {
              count: q3Errors,
              rate: ((q3Errors / batchExperimentResults.value.length) * 100).toFixed(1) + '%'
            }
          }
        },
        config: {
          nodeCount: primarySelectionConfig.nodeCount,
          faultyNodes: primarySelectionConfig.faultyNodes,
          topology: primarySelectionConfig.topology
        },
        mismatchedRoundsData: sortedMismatched.map(batch => ({
          round: batch.round,
          wrongMetrics: batch.wrongMetrics,
          wrongCount: batch.wrongCount,
          gainLossInfo: {
            iv: {
              isCorrect: batch.gainLoss.Gain_Gap_Ratio < 0.001,
              Gain_Gap_Ratio: batch.gainLoss.Gain_Gap_Ratio.toFixed(3) + '%',
              selectedNode: batch.gainLoss.ivSelectsNode,
              selectedRate: batch.gainLoss.P_best_Iv.toFixed(2) + '%',
              gain: batch.gainLoss.Gain_Iv.toFixed(2) + '%',
              gainGap: batch.gainLoss.Gain_Gap_Iv.toFixed(2) + '%'
            },
            qv: {
              isCorrect: batch.gainLoss.Gain_Gap_Ratio_Qv < 0.001,
              Gain_Gap_Ratio: batch.gainLoss.Gain_Gap_Ratio_Qv.toFixed(3) + '%',
              selectedNode: batch.gainLoss.qvSelectsNode,
              selectedRate: batch.gainLoss.P_best_Qv.toFixed(2) + '%',
              gain: batch.gainLoss.Gain_Qv.toFixed(2) + '%',
              gainGap: batch.gainLoss.Gain_Gap_Qv.toFixed(2) + '%'
            },
            qv1: {
              isCorrect: batch.gainLoss.Gain_Gap_Ratio_Qv1 < 0.001,
              Gain_Gap_Ratio: batch.gainLoss.Gain_Gap_Ratio_Qv1.toFixed(3) + '%',
              selectedNode: batch.gainLoss.qv1SelectsNode,
              selectedRate: batch.gainLoss.P_best_Qv1.toFixed(2) + '%',
              gain: batch.gainLoss.Gain_Qv1.toFixed(2) + '%',
              gainGap: batch.gainLoss.Gain_Gap_Qv1.toFixed(2) + '%',
              tiebreakerTriggered: batch.gainLoss.qv1TiebreakerTriggered,
              selectionSameAsQv: batch.gainLoss.qv1SelectionSameAsQv,
              // 🔍 详细诊断信息
              diagnosis: batch.gainLoss.qv1Diagnosis ? {
                top1_node: batch.gainLoss.qv1Diagnosis.top1_node,
                top2_node: batch.gainLoss.qv1Diagnosis.top2_node,
                top1_Qv: (batch.gainLoss.qv1Diagnosis.top1_Qv_raw || 0).toFixed(2) + '%',
                top2_Qv: (batch.gainLoss.qv1Diagnosis.top2_Qv_raw || 0).toFixed(2) + '%',
                top1_Qv_normalized: batch.gainLoss.qv1Diagnosis.top1_Qv_01?.toFixed(6),
                top2_Qv_normalized: batch.gainLoss.qv1Diagnosis.top2_Qv_01?.toFixed(6),
                logit_top1: batch.gainLoss.qv1Diagnosis.logit_top1?.toFixed(6),
                logit_top2: batch.gainLoss.qv1Diagnosis.logit_top2?.toFixed(6),
                logit_diff: batch.gainLoss.qv1Diagnosis.logit_diff?.toFixed(6),
                epsilon_r: batch.gainLoss.qv1Diagnosis.epsilon_r,
                trigger: batch.gainLoss.qv1Diagnosis.trigger,
                lambda: batch.gainLoss.qv1Diagnosis.lambda
              } : null
            },
            qw: {
              isCorrect: batch.gainLoss.Gain_Gap_Ratio_Qw < 0.001,
              Gain_Gap_Ratio: batch.gainLoss.Gain_Gap_Ratio_Qw.toFixed(3) + '%',
              selectedNode: batch.gainLoss.qwSelectsNode,
              selectedRate: batch.gainLoss.P_best_Qw.toFixed(2) + '%',
              gain: batch.gainLoss.Gain_Qw.toFixed(2) + '%',
              gainGap: batch.gainLoss.Gain_Gap_Qw.toFixed(2) + '%'
            },
            q2: {  // ✅ 新增 Q_2
              isCorrect: batch.gainLoss.Gain_Gap_Ratio_Q2 < 0.001,
              Gain_Gap_Ratio: batch.gainLoss.Gain_Gap_Ratio_Q2.toFixed(3) + '%',
              selectedNode: batch.gainLoss.q2SelectsNode,
              selectedRate: batch.gainLoss.P_best_Q2.toFixed(2) + '%',
              gain: batch.gainLoss.Gain_Q2.toFixed(2) + '%',
              gainGap: batch.gainLoss.Gain_Gap_Q2.toFixed(2) + '%'
            },
            q3: {  // ✅ 新增 Q_3
              isCorrect: batch.gainLoss.Gain_Gap_Ratio_Q3 < 0.001,
              Gain_Gap_Ratio: batch.gainLoss.Gain_Gap_Ratio_Q3.toFixed(3) + '%',
              selectedNode: batch.gainLoss.q3SelectsNode,
              selectedRate: batch.gainLoss.P_best_Q3.toFixed(2) + '%',
              gain: batch.gainLoss.Gain_Q3.toFixed(2) + '%',
              gainGap: batch.gainLoss.Gain_Gap_Q3.toFixed(2) + '%'
            },
            theoreticalBestNode: batch.gainLoss.optimalNode,
            theoreticalBestRate: batch.gainLoss.P_best_Theory.toFixed(2) + '%',
            averageRate: batch.gainLoss.P_avg.toFixed(2) + '%',
            theoreticalGain: batch.gainLoss.Gain_Theory.toFixed(2) + '%'
          },
          reliabilityMatrix: batch.reliabilityMatrix,
          allNodes: batch.results.map((r, idx) => {
            const diag = batch.gainLoss.qv1Diagnosis
            const isTop1 = diag && idx === diag.top1_node
            const isTop2 = diag && idx === diag.top2_node
            
            return {
              nodeId: r.proposerId,
              theoreticalSuccessRate: r.theoreticalSuccessRate.toFixed(2) + '%',
              I_v: r.metrics?.I_v?.toFixed(2) + '%' || 'N/A',
              Q_v: r.metrics?.Q_pp?.toFixed(2) + '%' || 'N/A',
              Q_v1: r.metrics?.Q_v1?.toFixed(2) + '%' || 'N/A',
              Q_w: r.metrics?.Q_w?.toFixed(2) + '%' || 'N/A',
              Q_2: r.metrics?.Q_2?.toFixed(2) + '%' || 'N/A',
              Q_3: r.metrics?.Q_3?.toFixed(2) + '%' || 'N/A',
              // 🔍 Q_v1 诊断信息（仅对 Top2 节点显示）
              qv1_diag: (isTop1 || isTop2) ? {
                isTop1: isTop1,
                isTop2: isTop2,
                Qv_raw: r.metrics?.Q_pp?.toFixed(2) + '%',
                Qw_raw: r.metrics?.Q_w?.toFixed(2) + '%',
                logit_value: isTop1 ? diag.logit_top1?.toFixed(6) : (isTop2 ? diag.logit_top2?.toFixed(6) : null)
              } : null,
              isTheoryBest: idx === batch.gainLoss.optimalNode,
              isIvSelected: idx === batch.gainLoss.ivSelectsNode,
              isQvSelected: idx === batch.gainLoss.qvSelectsNode,
              isQv1Selected: idx === batch.gainLoss.qv1SelectsNode,
              isQwSelected: idx === batch.gainLoss.qwSelectsNode,
              isQ2Selected: idx === batch.gainLoss.q2SelectsNode,
              isQ3Selected: idx === batch.gainLoss.q3SelectsNode
            }
          })
        }))
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `mismatched-rounds-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success(`Exported ${totalMismatched} mismatched rounds successfully!`)
      console.log(`\n=== 导出不匹配轮次 ===`)
      console.log(`  - 总轮次: ${batchExperimentResults.value.length}`)
      console.log(`  - 两者都对: ${bothPerfect.length}`)
      console.log(`  - 不匹配总数: ${totalMismatched}`)
      console.log(`    • 两者都错: ${bothMismatched.length}`)
      console.log(`    • 仅I(v)错: ${ivMismatchedOnly.length}`)
      console.log(`    • 仅Q(v)错: ${qvMismatchedOnly.length}`)
      console.log(`  - 总不匹配率: ${((totalMismatched / batchExperimentResults.value.length) * 100).toFixed(1)}%`)
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
      showPrimaryMatrixEditor,  // ✅ Primary Selection 页面的矩阵编辑器
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
      primarySelectionConfig,  // ✅ Primary Selection 页面的独立配置
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
      Refresh,
      onReliabilityMatrixUpdate,
      onProposerIdUpdate,
      onRandomRangeUpdate,
      onPrimaryReliabilityMatrixUpdate,  // ✅ Primary Selection 页面的矩阵更新处理
      onPrimaryProposerIdUpdate,  // ✅ Primary Selection 页面的主节点更新处理
      onPrimaryRandomRangeUpdate,  // ✅ Primary Selection 页面的随机范围更新处理
      // All Proposers Experiment
      allProposersRunning,
      currentProposerIndex,
      allProposersResults,
      allProposersChartContainer,
      runAllProposersExperiment,
      exportAllProposersResults,
      exportBatchExperimentResults,
      exportMismatchedRounds,
      // Batch Random Experiments
      batchExperimentRunning,
      batchExperimentRounds,
      currentBatchRound,
      batchExperimentResults,
      gainLossStatsDisplay,
      gainLossStatsHTML,
      runBatchRandomExperiments,
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
  --total-radio: 3;
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

.radio-container input:nth-of-type(3):checked ~ .glider-container .glider {
  transform: translateY(200%);
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

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.stat-card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 10px;
}

.stat-card-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-row span:first-child {
  font-size: 14px;
  opacity: 0.9;
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