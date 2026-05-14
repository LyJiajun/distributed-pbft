<template>
  <div class="canvas-container">
    <canvas ref="canvas" width="600" height="600"></canvas>
    <!-- 最终共识结果显示区域 -->
    <div class="consensus-result" v-if="finalConsensus">
      <h3>Final Consensus Result</h3>
      <p :style="{ color: finalConsensus.includes('Succeeded') ? '#22c55e' : '#ef4444', fontWeight: 'bold' }">{{ finalConsensus }}</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from "vue";

export default {
  props: ["topologyType", "nodeCount", "byzantineNodes", "simulationResult", "proposalValue", "animationSpeed"],
  setup(props) {
    const canvas = ref(null);
    const ctx = ref(null);
    const nodeRadius = 20;
    const finalConsensus = ref("");

    // 使用 computed 缓存节点位置，只有 props.nodeCount 改变时才重新计算
    const nodePositions = computed(() => {
      const cx = 300,
        cy = 300,
        radius = 200;
      const positions = [];
      for (let i = 0; i < props.nodeCount; i++) {
        const angle = (i / props.nodeCount) * (2 * Math.PI);
        positions.push({
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle)
        });
      }
      return positions;
    });

    // 使用 computed 缓存节点颜色，只有 props.nodeCount 或 props.byzantineNodes 改变时才重新计算
    const nodeColors = computed(() => {
      const colors = Array(props.nodeCount).fill("green");
      for (let i = 0; i < props.byzantineNodes && i < props.nodeCount; i++) {
        colors[props.nodeCount - 1 - i] = "red";
      }
      return colors;
    });

    const drawNodes = () => {
      nodePositions.value.forEach((pos, i) => {
        ctx.value.beginPath();
        ctx.value.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2);
        ctx.value.fillStyle = nodeColors.value[i];
        ctx.value.fill();
        ctx.value.stroke();
        ctx.value.fillStyle = "white";
        ctx.value.font = "14px Arial";
        ctx.value.fillText(i, pos.x - 5, pos.y + 5);
      });
    };

    const drawLine = (p1, p2) => {
      ctx.value.beginPath();
      ctx.value.moveTo(p1.x, p1.y);
      ctx.value.lineTo(p2.x, p2.y);
      ctx.value.strokeStyle = "#aaa";
      ctx.value.stroke();
    };

    // 绘制拓扑结构时直接使用缓存的节点位置和颜色，避免重复计算
    const drawTopology = () => {
      if (!ctx.value) return;
      ctx.value.clearRect(0, 0, 600, 600);
      const positions = nodePositions.value;

      if (props.topologyType === "full") {
        for (let i = 0; i < positions.length; i++) {
          for (let j = i + 1; j < positions.length; j++) {
            drawLine(positions[i], positions[j]);
          }
        }
      } else if (props.topologyType === "ring") {
        for (let i = 0; i < positions.length; i++) {
          drawLine(positions[i], positions[(i + 1) % positions.length]);
        }
      } else if (props.topologyType === "star") {
        for (let i = 1; i < positions.length; i++) {
          drawLine(positions[0], positions[i]);
        }
      } else if (props.topologyType === "tree") {
        for (let i = 0; i < positions.length; i++) {
          const leftChild = 2 * i + 1;
          const rightChild = 2 * i + 2;
          if (leftChild < positions.length)
            drawLine(positions[i], positions[leftChild]);
          if (rightChild < positions.length)
            drawLine(positions[i], positions[rightChild]);
        }
      }
      drawNodes();
    };

    // 单个阶段内所有消息动画同时播放的处理函数
    const animatePhase = (messages, doneCallback) => {
      // 根据animationSpeed计算步数：速度越快，步数越少
      const speed = props.animationSpeed || 1;
      const stepsPerHop = Math.round(80 / speed); // 每一跳的步数（75%速度）

      const animations = messages
        .filter((msg) => msg.dst !== null)
        .map((msg) => {
          // 构建路径上的坐标点序列
          const path = msg.path || [msg.src, msg.dst];
          const waypoints = path.map(nodeId => nodePositions.value[nodeId]);
          // 每个小球速度略有不同，避免完全重叠
          const speedVariation = 0.85 + Math.random() * 0.25; // 0.85 ~ 1.10
          const actualStepsPerHop = Math.round(stepsPerHop * speedVariation);
          // 随机延迟几帧出发，进一步错开
          const delay = Math.floor(Math.random() * Math.round(stepsPerHop * 0.3));
          const totalSteps = actualStepsPerHop * (waypoints.length - 1) + delay;
          return {
            msg,
            waypoints,
            frame: 0,
            totalSteps,
            stepsPerHop: actualStepsPerHop,
            delay
          };
        });

      const animateStep = () => {
        ctx.value.clearRect(0, 0, 600, 600);
        drawTopology();
        let stillAnimating = false;
        const expectedValue = props.proposalValue ?? props.simulationResult?.proposalValue ?? 0;

        animations.forEach((anim) => {
          if (anim.frame < anim.totalSteps) {
            stillAnimating = true;
            // 延迟期间不绘制
            const effectiveFrame = anim.frame - anim.delay;
            if (effectiveFrame < 0) {
              anim.frame++;
              return;
            }
            // 计算当前在路径的哪一段
            const segIndex = Math.min(
              Math.floor(effectiveFrame / anim.stepsPerHop),
              anim.waypoints.length - 2
            );
            const segProgress = (effectiveFrame - segIndex * anim.stepsPerHop) / anim.stepsPerHop;
            const from = anim.waypoints[segIndex];
            const to = anim.waypoints[segIndex + 1];
            const x = from.x + (to.x - from.x) * segProgress;
            const y = from.y + (to.y - from.y) * segProgress;

            const dotColor = (anim.msg.value === expectedValue ||
                            anim.msg.value === expectedValue.toString())
                ? "green"
                : "red";
            ctx.value.beginPath();
            ctx.value.arc(x, y, 10, 0, Math.PI * 2);
            ctx.value.fillStyle = dotColor;
            ctx.value.fill();
            anim.frame++;
          }
        });
        if (stillAnimating) {
          requestAnimationFrame(animateStep);
        } else {
          if (doneCallback) doneCallback();
        }
      };
      animateStep();
    };

    const startAnimation = () => {
      const simulationResult = props.simulationResult;
      if (!simulationResult) return;

      const prePrepareMessages = simulationResult.pre_prepare;
      const prepareMessages = simulationResult.prepare.flat();
      const commitMessages = simulationResult.commit.flat();

      animatePhase(prePrepareMessages, () => {
        animatePhase(prepareMessages, () => {
          animatePhase(commitMessages, () => {
            finalConsensus.value =
              simulationResult.consensus || "Consensus reached";
          });
        });
      });
    };

    onMounted(() => {
      ctx.value = canvas.value.getContext("2d");
      drawTopology();
    });

    watch(
      () => props.simulationResult,
      (newResult) => {
        if (newResult) {
          startAnimation();
        }
      }
    );

    return { canvas, startAnimation, finalConsensus };
  }
};
</script>

<style>
.canvas-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.consensus-result {
  margin-top: 20px;
  text-align: center;
  font-size: 16px;
  color: #333;
}
</style>
