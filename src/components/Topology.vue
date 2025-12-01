<template>
  <div class="canvas-container">
    <canvas ref="canvas" width="600" height="600"></canvas>
    <!-- 最终共识结果显示区域 -->
    <div class="consensus-result" v-if="finalConsensus">
      <h3>最终共识结果</h3>
      <p>{{ finalConsensus }}</p>
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
      // 基础步数100，除以速度系数（默认速度1x对应100步）
      const speed = props.animationSpeed || 1;
      const steps = Math.round(100 / speed);
      
      const animations = messages
        .filter((msg) => msg.dst !== null)
        .map((msg) => {
          return {
            msg,
            start: nodePositions.value[msg.src],
            end: nodePositions.value[msg.dst],
            frame: 0,
            steps: steps // 根据速度动态计算动画步数
          };
        });

      const animateStep = () => {
        ctx.value.clearRect(0, 0, 600, 600);
        drawTopology();
        let stillAnimating = false;
        animations.forEach((anim) => {
          if (anim.frame < anim.steps) {
            stillAnimating = true;
            const progress = anim.frame / anim.steps;
            const x = anim.start.x + (anim.end.x - anim.start.x) * progress;
            const y = anim.start.y + (anim.end.y - anim.start.y) * progress;
            // 根据消息的 value 决定移动圆点的颜色：
            // 与proposalValue相同时使用绿色（正确），不同时使用红色（拜占庭攻击）
            const expectedValue = props.proposalValue ?? props.simulationResult?.proposalValue ?? 0;
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
              simulationResult.consensus || "共识结果已达成";
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
