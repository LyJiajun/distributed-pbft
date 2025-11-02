<template>
  <div class="pbft-table-container">
    <h2>PBFT Result</h2>
    <table v-if="filteredSimulationResult" class="pbft-table">
      <thead>
        <tr>
          <th>Node</th>
          <th>Pre-Prepare</th>
          <th>Prepare</th>
          <th>Commit</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="node in nodes" :key="node">
          <td>{{ node }}</td>
          <td>
            <div
              v-for="msg in getStageMessages('pre_prepare', node)"
              :key="msgKey(msg)"
              class="msg-line"
            >
              {{ msg.src }}->{{ msg.dst }}:
              <span :class="getValueClass(msg)">
                {{ formatValue(msg) }}
              </span>
            </div>
          </td>
          <td>
            <div
              v-for="msg in getStageMessages('prepare', node)"
              :key="msgKey(msg)"
              class="msg-line"
            >
              {{ msg.src }}->{{ msg.dst }}:
              <span :class="getValueClass(msg)">
                {{ formatValue(msg) }}
              </span>
            </div>
          </td>
          <td>
            <div
              v-for="msg in getStageMessages('commit', node)"
              :key="msgKey(msg)"
              class="msg-line"
            >
              {{ msg.src }}->{{ msg.dst }}:
              <span :class="getValueClass(msg)">
                {{ formatValue(msg) }}
              </span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="filteredSimulationResult?.consensus" class="consensus-result">
      <span :class="{ 'red-text': isReject, 'green-text': !isReject }">
        {{ filteredSimulationResult.consensus }}
      </span>
    </div>
  </div>
</template>

<script>
import { computed } from "vue";

export default {
  name: "PBFTTable",
  props: {
    filteredSimulationResult: { type: Object, default: null },
    nodeCount: { type: Number, default: 6 },
  },
  setup(props) {
    const nodes = computed(() => {
      return Array.from({ length: props.nodeCount }, (_, i) => i);
    });

    const getStageMessages = (stage, nodeIndex) => {
      if (!props.filteredSimulationResult || Object.keys(props.filteredSimulationResult).length === 0) {
        return [];
      }
      let msgs = [];
      if (stage === "pre_prepare") {
        msgs = props.filteredSimulationResult.pre_prepare || [];
      } else if (stage === "prepare") {
        msgs = (props.filteredSimulationResult.prepare || []).flat() || [];
      } else if (stage === "commit") {
        msgs = (props.filteredSimulationResult.commit || []).flat() || [];
      }
      return msgs.filter((m) => m && m.src === nodeIndex && m.dst !== null);
    };

    const msgKey = (msg) => {
      if (!msg) return "invalid-key";
      return `${msg.src}-${msg.dst ?? "null"}-${msg.value}`;
    };

    const referenceValue = computed(() => {
      const firstMatch = props.filteredSimulationResult?.messages?.find(msg => msg.dst === null);
      return firstMatch ? firstMatch.value : 0;
    });

    const formatValue = (msg) => {
      return msg.value === referenceValue.value ? "AGREE" : "ARBITRARY";
    };

    const getValueClass = (msg) => {
      return msg.value === referenceValue.value ? "truth-text" : "arbitrary-text";
    };

    const isReject = computed(() => {
      const consensusText = props.filteredSimulationResult?.consensus || "";
      return typeof consensusText === "string" && consensusText.toLowerCase().includes("reject");
    });

    return {
      nodes,
      getStageMessages,
      msgKey,
      formatValue,
      getValueClass,
      isReject,
    };
  },
};
</script>

<style scoped>
.pbft-table-container {
  width: 600px;
  margin: 0 auto;
}
.pbft-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  font-size: 14px;
}
.msg-line {
  white-space: nowrap;
}
.pbft-table th,
.pbft-table td {
  border: 1px solid #ccc;
  padding: 6px 8px;
  text-align: left;
}
.consensus-result {
  margin-top: 10px;
  font-weight: bold;
  text-align: center;
}
.truth-text {
  color: green;
  font-weight: bold;
}
.arbitrary-text {
  color: red;
  font-weight: bold;
}
.green-text {
  color: green;
}
.red-text {
  color: red;
}
</style>
