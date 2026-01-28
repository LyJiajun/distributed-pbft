<template>
  <div class="topology-editor">
    <div class="editor-header">
      <h4>Topology Communication Reliability Configuration</h4>
      <div class="header-controls">
        <div class="random-range-control">
          <span class="range-label">Random Range:</span>
          <el-input-number
            v-model="randomMinReliability"
            :min="0"
            :max="100"
            :step="5"
            size="small"
            controls-position="right"
            style="width: 100px;"
          />
          <span style="margin: 0 5px;">~</span>
          <el-input-number
            v-model="randomMaxReliability"
            :min="0"
            :max="100"
            :step="5"
            size="small"
            controls-position="right"
            style="width: 100px;"
          />
          <span style="margin-left: 5px; color: #909399;">%</span>
        </div>
        <div class="header-buttons">
          <el-button size="small" @click="randomizeReliability" type="warning">
            <el-icon><Refresh /></el-icon>
            Randomize
          </el-button>
          <el-button size="small" @click="resetAllReliability">Reset to {{ defaultReliability }}%</el-button>
        </div>
      </div>
    </div>
    
    <div class="info-bar">
      <el-alert type="info" :closable="false" show-icon>
        <template #default>
          <span><strong>Tip:</strong> Click percentage on edge to edit reliability, click node to switch primary node (Current Primary: <strong style="color: #f6d365;">Node {{ proposerId }}</strong>)</span>
        </template>
      </el-alert>
    </div>
    
    <div class="canvas-wrapper" style="position: relative;">
      <canvas ref="canvas" width="1200" height="800" @click="handleCanvasClick"></canvas>
      
      <!-- 内联编辑输入框 - 波浪效果 -->
      <div
        v-if="editingLabel"
        class="wave-group"
        :style="{
          position: 'absolute',
          left: editingLabel.x + 'px',
          top: editingLabel.y + 'px',
          transform: 'translate(-50%, -50%)',
          zIndex: 1000
        }"
      >
        <input
          ref="inlineInput"
          v-model="editingLabel.value"
          type="number"
          class="input"
          required
          @blur="saveInlineEdit"
          @keyup.enter="saveInlineEdit"
          @keyup.esc="cancelInlineEdit"
        />
        <span class="bar"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  nodeCount: {
    type: Number,
    default: 6
  },
  topology: {
    type: String,
    default: 'full'
  },
  defaultReliability: {
    type: Number,
    default: 80
  },
  initialMatrix: {
    type: Array,
    default: null
  },
  proposerId: {
    type: Number,
    default: 0
  },
  randomMin: {
    type: Number,
    default: 50
  },
  randomMax: {
    type: Number,
    default: 100
  },
  branchCount: {
    type: Number,
    default: 2
  }
})

const emit = defineEmits(['update:reliabilityMatrix', 'update:proposerId', 'update:randomRange'])

const canvas = ref(null)
const ctx = ref(null)

// 直连边的可靠度矩阵 [from][to] = reliability (0-1) - 用户编辑
const directReliabilityMatrix = ref([])

// 端到端可靠度矩阵（包括多跳路径）- 计算得到，发送给后端
const reliabilityMatrix = ref([])

// 节点位置缓存
const nodePositions = ref([])

// 边的位置信息（用于点击检测）
const edges = ref([])

// 文字标签位置信息（用于点击检测）
const labels = ref([])

// 内联编辑相关
const editingLabel = ref(null)
const inlineInput = ref(null)

// 随机范围设置（从 props 初始化）
const randomMinReliability = ref(props.randomMin)
const randomMaxReliability = ref(props.randomMax)

// 从直连矩阵计算端到端通信可靠度（考虑多跳路径）
const calculateEndToEndMatrix = () => {
  const n = props.nodeCount
  const topo = props.topology
  const endToEndMatrix = Array(n).fill(0).map(() => Array(n).fill(0))
  
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i === j) {
        endToEndMatrix[i][j] = 1
        continue
      }
      
      if (topo === 'full') {
        // 全连接：直连
        endToEndMatrix[i][j] = directReliabilityMatrix.value[i][j]
      } else if (topo === 'ring') {
        // 环形拓扑：计算顺时针和逆时针两条路径
        const clockwise = (j - i + n) % n
        const counterclockwise = (i - j + n) % n
        
        if (Math.min(clockwise, counterclockwise) === 1) {
          // 相邻节点：直连
          endToEndMatrix[i][j] = directReliabilityMatrix.value[i][j]
        } else {
          // 不相邻节点：2条路径，计算每条路径的可靠度
          // 顺时针路径
          let p1 = 1
          for (let step = 0; step < clockwise; step++) {
            const from = (i + step) % n
            const to = (i + step + 1) % n
            p1 *= directReliabilityMatrix.value[from][to]
          }
          
          // 逆时针路径
          let p2 = 1
          for (let step = 0; step < counterclockwise; step++) {
            const from = (i - step + n) % n
            const to = (i - step - 1 + n) % n
            p2 *= directReliabilityMatrix.value[from][to]
          }
          
          // 至少一条成功
          endToEndMatrix[i][j] = 1 - (1 - p1) * (1 - p2)
        }
      } else if (topo === 'star') {
        // 星形拓扑：中心节点是0
        const center = 0
        if (i === center || j === center) {
          // 中心↔边缘：直连
          endToEndMatrix[i][j] = directReliabilityMatrix.value[i][j]
        } else {
          // 边缘↔边缘：2跳（通过中心）
          const p1 = directReliabilityMatrix.value[i][center]
          const p2 = directReliabilityMatrix.value[center][j]
          endToEndMatrix[i][j] = p1 * p2
        }
      } else if (topo === 'tree') {
        // 树形拓扑：使用BFS计算最短路径并累乘可靠度
        const visited = new Array(n).fill(false)
        const queue = [{ node: i, prob: 1 }]
        visited[i] = true
        
        while (queue.length > 0) {
          const { node, prob } = queue.shift()
          if (node === j) {
            endToEndMatrix[i][j] = prob
            break
          }
          
          // 添加邻居节点
          for (let k = 0; k < n; k++) {
            if (!visited[k] && hasConnection(node, k)) {
              visited[k] = true
              const edgeProb = directReliabilityMatrix.value[node][k]
              queue.push({ node: k, prob: prob * edgeProb })
            }
          }
        }
      }
    }
  }
  
  return endToEndMatrix
}

// 初始化可靠度矩阵
const initReliabilityMatrix = () => {
  const n = props.nodeCount
  
  // 如果传入了初始矩阵且大小匹配，尝试还原直连矩阵
  if (props.initialMatrix && props.initialMatrix.length === n) {
    // 假设传入的是端到端矩阵，我们需要提取直连边
    const directMatrix = Array(n).fill(0).map(() => Array(n).fill(0))
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i === j) {
          directMatrix[i][j] = 1
        } else if (hasConnection(i, j)) {
          // 对于直连边，从端到端矩阵中提取
          directMatrix[i][j] = props.initialMatrix[i][j]
        }
      }
    }
    directReliabilityMatrix.value = directMatrix
    reliabilityMatrix.value = calculateEndToEndMatrix()
    console.log(`[TopologyEditor] Restored from existing matrix (${n}x${n})`)
    emitMatrix()
    return
  }
  
  // 否则创建新矩阵
  console.log(`[TopologyEditor] Initializing new matrix for topology: ${props.topology}, nodes: ${n}, defaultReliability: ${props.defaultReliability}%`)
  const directMatrix = Array(n).fill(0).map(() => Array(n).fill(0))
  const p = props.defaultReliability / 100
  let directConnectionCount = 0
  
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i === j) {
        directMatrix[i][j] = 1
      } else if (hasConnection(i, j)) {
        // 只设置直连边的可靠度
        directMatrix[i][j] = p
        directConnectionCount++
      }
    }
  }
  
  directReliabilityMatrix.value = directMatrix
  reliabilityMatrix.value = calculateEndToEndMatrix()
  
  console.log(`[TopologyEditor] Direct edges initialized: ${directConnectionCount}, end-to-end matrix calculated`)
  
  emitMatrix()
}

// 判断是否有连接
const hasConnection = (i, j) => {
  const n = props.nodeCount
  const topo = props.topology
  const nValue = props.branchCount
  
  if (topo === 'full') {
    return true
  } else if (topo === 'ring') {
    return (j === (i + 1) % n) || (i === (j + 1) % n)
  } else if (topo === 'star') {
    return i === 0 || j === 0
  } else if (topo === 'tree') {
    // 树形：父子节点双向连接
    const parentOfJ = Math.floor((j - 1) / nValue)
    const parentOfI = Math.floor((i - 1) / nValue)
    // i是j的父节点，或j是i的父节点
    return (i === parentOfJ && j < n) || (j === parentOfI && i < n)
  }
  return false
}

// 计算节点位置
const calculateNodePositions = () => {
  const n = props.nodeCount
  const cx = 600  // 居中于1200宽的canvas
  const cy = 400  // 居中于800高的canvas
  const radius = 280  // 更大的半径
  const positions = []
  
  for (let i = 0; i < n; i++) {
    const angle = (i / n) * 2 * Math.PI - Math.PI / 2
    positions.push({
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle)
    })
  }
  
  nodePositions.value = positions
}

// 根据可靠度获取颜色
const getColorByReliability = (reliability) => {
  if (reliability >= 0.8) return '#67C23A'
  if (reliability >= 0.5) return '#E6A23C'
  return '#F56C6C'
}

// 绘制单向半箭头（用于双向显示）
const drawHalfArrow = (c, fromX, fromY, toX, toY, color, reliability, isTop) => {
  const headlen = 15
  const angle = Math.atan2(toY - fromY, toX - fromX)
  
  // 计算垂直角度（用于后面判断箭头翼的方向）
  const perpAngle = angle + Math.PI / 2
  
  // 计算连线向量
  const dx = toX - fromX
  const dy = toY - fromY
  const len = Math.sqrt(dx * dx + dy * dy)
  
  // 计算垂直向量（用于文字和箭头偏移）
  // 使用固定的规则：计算连线的垂直向量，总是选择一个一致的方向
  let perpX = -dy / len
  let perpY = dx / len
  
  // 统一规则：确保垂直向量指向"上"或"左上"
  // 优先考虑 Y 方向，如果 Y 接近 0 则考虑 X 方向
  if (Math.abs(perpY) > 0.1) {
    // Y 分量明显，确保指向上（perpY < 0）
    if (perpY > 0) {
      perpX = -perpX
      perpY = -perpY
    }
  } else {
    // Y 分量很小（接近水平线），确保 X 分量指向左（perpX < 0）
    if (perpX > 0) {
      perpX = -perpX
      perpY = -perpY
    }
  }
  
  // 缩短线段，避免覆盖节点
  const nodeRadius = 30
  const ratio1 = nodeRadius / len
  const ratio2 = (len - nodeRadius) / len
  
  // 计算完整线段的起点和终点（避免覆盖节点）
  const fullStartX = fromX + dx * ratio1
  const fullStartY = fromY + dy * ratio1
  const fullEndX = fromX + dx * ratio2
  const fullEndY = fromY + dy * ratio2
  
  // 只绘制靠近目标节点的一半
  // 线段从中点开始，到终点结束（靠近 toX, toY 的一半）
  const midX = (fullStartX + fullEndX) / 2
  const midY = (fullStartY + fullEndY) / 2
  
  const startX = midX
  const startY = midY
  const endX = fullEndX
  const endY = fullEndY
  
  // 绘制线段（只有一半）
  c.beginPath()
  c.moveTo(startX, startY)
  c.lineTo(endX, endY)
  c.strokeStyle = color
  c.lineWidth = 2.5
  if (reliability < 0.3) {
    c.setLineDash([5, 5])
  } else {
    c.setLineDash([])
  }
  c.stroke()
  c.setLineDash([])
  
  // 绘制半箭头头部（只有一半，像 ﹀ 或 ﹁）
  // 箭头尖端在线上
  const arrowTipX = endX
  const arrowTipY = endY
  
  // 箭头的两个翼，但只在一侧（上或下）
  const wing1Angle = angle - Math.PI / 6
  const wing2Angle = angle + Math.PI / 6
  
  // 计算两个翼的端点，但只延伸到线的一侧
  const wing1X = arrowTipX - headlen * Math.cos(wing1Angle)
  const wing1Y = arrowTipY - headlen * Math.sin(wing1Angle)
  const wing2X = arrowTipX - headlen * Math.cos(wing2Angle)
  const wing2Y = arrowTipY - headlen * Math.sin(wing2Angle)
  
  // 使用固定的垂直向量判断翼的位置（与文字标签使用相同的判断方式）
  // 计算每个翼相对于箭头尖端的位置，然后用 perpX, perpY 判断它在哪一侧
  const wing1Offset = perpX * (wing1X - arrowTipX) + perpY * (wing1Y - arrowTipY)
  const wing2Offset = perpX * (wing2X - arrowTipX) + perpY * (wing2Y - arrowTipY)
  
  c.beginPath()
  c.moveTo(arrowTipX, arrowTipY)
  
  if (isTop) {
    // 上半箭头：只绘制在 perpX,perpY 方向的翼
    if (wing1Offset > 0) {
      c.lineTo(wing1X, wing1Y)
    }
    if (wing2Offset > 0) {
      c.lineTo(wing2X, wing2Y)
    }
  } else {
    // 下半箭头：只绘制在 -perpX,-perpY 方向的翼
    if (wing1Offset < 0) {
      c.lineTo(wing1X, wing1Y)
    }
    if (wing2Offset < 0) {
      c.lineTo(wing2X, wing2Y)
    }
  }
  
  c.strokeStyle = color
  c.lineWidth = 2.5
  c.stroke()
  
  // 绘制标签（平行于箭头，显示在箭头线上方，与箭头在同一侧）
  // 标签位于实际绘制的线段（一半线段）的中点
  const labelMidX = (startX + endX) / 2
  const labelMidY = (startY + endY) / 2
  
  // 计算沿箭头方向的单位向量
  const arrowDirX = dx / len
  const arrowDirY = dy / len
  
  // 文字偏移：1) 垂直方向偏移 2) 沿箭头方向偏移
  const textOffsetDist = 12  // 垂直偏移距离
  const textArrowOffset = 20  // 沿箭头方向偏移距离（减小，因为线段变短了）
  
  const textOffsetX = perpX * textOffsetDist * (isTop ? 1 : -1) + arrowDirX * textArrowOffset
  const textOffsetY = perpY * textOffsetDist * (isTop ? 1 : -1) + arrowDirY * textArrowOffset
  
  const text = `${Math.round(reliability * 100)}%`
  
  // 保存当前状态
  c.save()
  
  // 移动到文字位置（基于实际绘制线段的中点，再微调）
  c.translate(labelMidX + textOffsetX, labelMidY + textOffsetY)
  
  // 调整文字旋转角度，确保文字始终可读（不倒置）
  let textAngle = angle
  // 如果角度超出 -90° 到 90° 范围，旋转180°使文字正向
  if (textAngle > Math.PI / 2) {
    textAngle -= Math.PI
  } else if (textAngle < -Math.PI / 2) {
    textAngle += Math.PI
  }
  
  // 旋转文字使其平行于箭头且可读
  c.rotate(textAngle)
  
  // 设置字体和基线
  c.font = 'bold 16px Arial'
  c.textAlign = 'center'
  c.textBaseline = 'middle'
  
  // 绘制文字（黑色，无背景）
  c.fillStyle = '#333'
  c.fillText(text, 0, 0)
  
  // 恢复状态
  c.restore()
  
  // 返回标签位置信息（用于点击检测）
  const labelX = labelMidX + textOffsetX
  const labelY = labelMidY + textOffsetY
  return {
    x: labelX,
    y: labelY,
    text: text,
    reliability: reliability
  }
}

// 绘制拓扑图
const drawTopology = () => {
  if (!ctx.value || !canvas.value) {
    return
  }
  
  const c = ctx.value
  const w = canvas.value.width
  const h = canvas.value.height
  
  // 清空画布
  c.clearRect(0, 0, w, h)
  
  // 重置边信息和标签信息
  edges.value = []
  labels.value = []
  
  const positions = nodePositions.value
  const n = props.nodeCount
  
  // 绘制边（避免重复，只绘制 i < j 的边对）
  // 只绘制物理直连边，而不是所有非零可靠度的节点对
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      // 检查是否有物理直连（而不是端到端可靠度>0）
      const hasPhysicalEdgeIJ = hasConnection(i, j)
      const hasPhysicalEdgeJI = hasConnection(j, i)
      
      if (hasPhysicalEdgeIJ || hasPhysicalEdgeJI) {
        const pos_i = positions[i]
        const pos_j = positions[j]
        
        // i -> j 方向（小节点 -> 大节点，因为外层循环保证 i < j）
        if (hasPhysicalEdgeIJ) {
          const reliability = directReliabilityMatrix.value[i][j]
          const color = getColorByReliability(reliability)
          
          // 强制规则：小节点 -> 大节点，始终在上方
          const isTop = true
          
          const labelInfo = drawHalfArrow(
            c,
            pos_i.x,
            pos_i.y,
            pos_j.x,
            pos_j.y,
            color,
            reliability,
            isTop
          )
          
          // 记录标签位置信息
          labels.value.push({
            ...labelInfo,
            from: i,
            to: j
          })
          
          edges.value.push({
            from: i,
            to: j,
            fromX: pos_i.x,
            fromY: pos_i.y,
            toX: pos_j.x,
            toY: pos_j.y,
            reliability,
            isTop: isTop
          })
        }
        
        // j -> i 方向（大节点 -> 小节点）
        if (hasPhysicalEdgeJI) {
          const reliability = directReliabilityMatrix.value[j][i]
          const color = getColorByReliability(reliability)
          
          // 强制规则：大节点 -> 小节点，始终在下方
          const isTop = false
          
          const labelInfo = drawHalfArrow(
            c,
            pos_j.x,
            pos_j.y,
            pos_i.x,
            pos_i.y,
            color,
            reliability,
            isTop
          )
          
          // 记录标签位置信息
          labels.value.push({
            ...labelInfo,
            from: j,
            to: i
          })
          
          edges.value.push({
            from: j,
            to: i,
            fromX: pos_j.x,
            fromY: pos_j.y,
            toX: pos_i.x,
            toY: pos_i.y,
            reliability,
            isTop: isTop
          })
        }
      }
    }
  }
  
  // 绘制节点
  positions.forEach((pos, i) => {
    c.beginPath()
    c.arc(pos.x, pos.y, 30, 0, Math.PI * 2)
    // 主节点用金黄色，其他节点用蓝色
    c.fillStyle = i === props.proposerId ? '#f6d365' : '#409EFF'
    c.fill()
    c.strokeStyle = i === props.proposerId ? '#e6a23c' : '#333'
    c.lineWidth = i === props.proposerId ? 3 : 2
    c.stroke()
    
    // 主节点添加标记
    if (i === props.proposerId) {
      c.font = 'bold 10px Arial'
      c.fillStyle = '#333'
      c.textAlign = 'center'
      c.fillText('PRIMARY', pos.x, pos.y - 45)
    }
    
    c.fillStyle = 'white'
    c.font = 'bold 20px Arial'
    c.textAlign = 'center'
    c.textBaseline = 'middle'
    c.fillText(i, pos.x, pos.y)
  })
}

// 点击检测
const handleCanvasClick = (event) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // 首先检测是否点击了节点
  for (let i = 0; i < nodePositions.value.length; i++) {
    const pos = nodePositions.value[i]
    const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2)
    if (dist <= 30) {  // 节点半径
      // 切换主节点
      emit('update:proposerId', i)
      drawTopology()  // 重新绘制以更新主节点显示
      return
    }
  }
  
  // 检测是否点击了标签
  for (const label of labels.value) {
    if (isNearLabel(x, y, label)) {
      openInlineEdit(label, event)
      return
    }
  }
}

// 判断点是否在标签附近
const isNearLabel = (px, py, label) => {
  const threshold = 20  // 点击热区大小
  const dist = Math.sqrt((px - label.x) ** 2 + (py - label.y) ** 2)
  return dist < threshold
}

// 打开内联编辑
const openInlineEdit = (label, event) => {
  editingLabel.value = {
    from: label.from,
    to: label.to,
    value: Math.round(label.reliability * 100),
    x: label.x,  // 直接使用标签的坐标
    y: label.y
  }
  
  // 在下一帧聚焦并选中输入框
  nextTick(() => {
    if (inlineInput.value) {
      inlineInput.value.focus()
      inlineInput.value.select()
    }
  })
}

// 保存内联编辑
const saveInlineEdit = () => {
  if (!editingLabel.value) return
  
  const { from, to, value } = editingLabel.value
  const newValue = Math.max(0, Math.min(100, parseInt(value) || 0)) / 100
  
  // 更新直连矩阵
  directReliabilityMatrix.value[from][to] = newValue
  
  // 重新计算端到端矩阵
  reliabilityMatrix.value = calculateEndToEndMatrix()
  
  editingLabel.value = null
  
  drawTopology()
  emitMatrix()
}

// 取消内联编辑
const cancelInlineEdit = () => {
  editingLabel.value = null
}

// 重置所有可靠度
const resetAllReliability = () => {
  initReliabilityMatrix()
  drawTopology()
}

// 随机设置可靠度
const randomizeReliability = () => {
  const n = props.nodeCount
  const minVal = randomMinReliability.value
  const maxVal = randomMaxReliability.value
  
  // 确保最小值不大于最大值
  if (minVal > maxVal) {
    const temp = minVal
    randomMinReliability.value = maxVal
    randomMaxReliability.value = temp
  }
  
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i === j) {
        directReliabilityMatrix.value[i][j] = 1
      } else if (hasConnection(i, j)) {
        // 在自定义范围内随机生成可靠度，以 5% 为单位
        const min = Math.floor(randomMinReliability.value / 5)
        const max = Math.floor(randomMaxReliability.value / 5)
        const randomReliability = (Math.floor(Math.random() * (max - min + 1) + min) * 5) / 100
        directReliabilityMatrix.value[i][j] = randomReliability
      }
    }
  }
  
  // 重新计算端到端矩阵
  reliabilityMatrix.value = calculateEndToEndMatrix()
  
  drawTopology()
  emitMatrix()
}

// 发送矩阵更新事件
const emitMatrix = () => {
  emit('update:reliabilityMatrix', reliabilityMatrix.value)
}

// 监听节点数和拓扑结构变化（只有这些变化时才重新初始化）
watch(() => [props.nodeCount, props.topology, props.branchCount], () => {
  initReliabilityMatrix()
  calculateNodePositions()
  drawTopology()
})

// 监听默认可靠度变化（只重绘，不重新初始化矩阵）
watch(() => props.defaultReliability, () => {
  drawTopology()
})

// 监听主节点变化（重新绘制以更新显示）
watch(() => props.proposerId, () => {
  drawTopology()
})

// 监听随机范围变化，emit 给父组件
watch([randomMinReliability, randomMaxReliability], ([newMin, newMax]) => {
  emit('update:randomRange', { min: newMin, max: newMax })
})

// 监听 props 的随机范围变化（当对话框重新打开时同步）
watch(() => [props.randomMin, props.randomMax], ([newMin, newMax]) => {
  randomMinReliability.value = newMin
  randomMaxReliability.value = newMax
})

// 初始化
onMounted(() => {
  ctx.value = canvas.value.getContext('2d')
  initReliabilityMatrix()
  calculateNodePositions()
  drawTopology()
})
</script>

<style scoped>
.topology-editor {
  width: 100%;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.editor-header h4 {
  margin: 0;
  font-size: 18px;
  color: #606266;
  flex-shrink: 0;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.random-range-control {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
}

.range-label {
  font-size: 14px;
  color: #606266;
  margin-right: 5px;
  font-weight: 500;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.info-bar {
  margin-bottom: 20px;
}

.canvas-wrapper {
  position: relative;
  background: white;
  border-radius: 6px;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  min-height: 820px;
}

canvas {
  display: block;
  cursor: pointer;
}

/* 波浪效果输入框 */
.wave-group {
  position: relative;
}

.wave-group .input {
  font-size: 16px;
  font-weight: bold;
  padding: 8px 10px;
  display: block;
  width: 70px;
  border: none;
  border-bottom: 2px solid #515151;
  background: transparent;
  text-align: center;
}

.wave-group .input:focus {
  outline: none;
}

.wave-group .bar {
  position: relative;
  display: block;
  width: 70px;
}

.wave-group .bar:before,
.wave-group .bar:after {
  content: '';
  height: 2px;
  width: 0;
  bottom: 0px;
  position: absolute;
  background: #5264AE;
  transition: 0.2s ease all;
  -moz-transition: 0.2s ease all;
  -webkit-transition: 0.2s ease all;
}

.wave-group .bar:before {
  left: 50%;
}

.wave-group .bar:after {
  right: 50%;
}

.wave-group .input:focus ~ .bar:before,
.wave-group .input:focus ~ .bar:after {
  width: 50%;
}
</style>
