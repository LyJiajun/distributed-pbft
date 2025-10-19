# 共识统计修复

## 问题描述

用户反馈了两个关于共识统计显示的问题：

1. **节点数量统计问题**：没有包含主节点（提议者）
2. **选项显示问题**：第一个和第二个选项都显示相同的文本"吃火锅吗"，应该分别显示"选项A"和"选项B"

## 修复内容

### 1. 节点数量统计修复

#### 问题分析
- 原来的统计逻辑：`expected_nodes = config['nodeCount'] - 1`（除了提议者）
- 导致显示：`2/2`（准备阶段参与），但实际上应该包含所有节点

#### 修复方案
```python
# 修复前
expected_nodes = config['nodeCount'] - 1  # 除了提议者

# 修复后
expected_nodes = config['nodeCount']  # 包含所有节点（包括提议者）

# 准备阶段：除了提议者
if len(unique_prepare_nodes) < expected_nodes - 1:
    # 准备阶段需要 expected_nodes - 1 个节点

# 提交阶段：包含所有节点
elif len(unique_commit_nodes) < expected_nodes:
    # 提交阶段需要 expected_nodes 个节点
```

#### 统计逻辑
- **准备阶段**：期望节点数 = 总节点数 - 1（除了提议者）
- **提交阶段**：期望节点数 = 总节点数（包含所有节点）

### 2. 选项显示修复

#### 问题分析
- 原来的显示：两个选项都显示 `{{ sessionConfig.proposalContent || '选择A' }}`
- 导致两个选项显示相同的文本

#### 修复方案
```html
<!-- 修复前 -->
<div class="consensus-stat-label">{{ sessionConfig.proposalContent || '选择A' }} (节点)</div>
<div class="consensus-stat-label">{{ sessionConfig.proposalContent || '选择B' }} (节点)</div>

<!-- 修复后 -->
<div class="consensus-stat-label">选项A (节点)</div>
<div class="consensus-stat-label">选项B (节点)</div>
```

### 3. 后端数据结构增强

#### 新增字段
```python
consensus_result = {
    "stats": {
        "truth": truth_votes,
        "falsehood": falsehood_votes,
        "rejected": rejected_votes,
        "prepare_nodes": len(unique_prepare_nodes),
        "commit_nodes": len(unique_commit_nodes),
        "expected_nodes": expected_nodes,
        "expected_prepare_nodes": expected_nodes - 1,  # 新增：准备阶段期望节点数
        "total_messages": len(prepare_messages) + len(commit_messages)
    }
}
```

### 4. 前端显示优化

#### 准备阶段参与显示
```html
<!-- 修复前 -->
<div class="consensus-stat-number">{{ consensusResult.stats.prepare_nodes }}/{{ consensusResult.stats.expected_nodes }}</div>

<!-- 修复后 -->
<div class="consensus-stat-number">{{ consensusResult.stats.prepare_nodes }}/{{ consensusResult.stats.expected_prepare_nodes || consensusResult.stats.expected_nodes - 1 }}</div>
```

## 修复效果

### 1. 节点统计正确性
- ✅ 准备阶段：显示正确的期望节点数（除了提议者）
- ✅ 提交阶段：显示正确的期望节点数（包含所有节点）
- ✅ 统计逻辑符合PBFT算法要求

### 2. 选项显示清晰性
- ✅ 选项A：明确显示"选项A (节点)"
- ✅ 选项B：明确显示"选项B (节点)"
- ✅ 避免混淆，提高用户体验

### 3. 数据一致性
- ✅ 后端统计逻辑与前端显示一致
- ✅ 不同阶段的节点统计逻辑正确
- ✅ 符合PBFT算法的角色分工

## 测试验证

### 测试场景1：3节点系统
- 总节点数：3（包含提议者）
- 准备阶段期望：2（除了提议者）
- 提交阶段期望：3（包含所有节点）

### 测试场景2：5节点系统
- 总节点数：5（包含提议者）
- 准备阶段期望：4（除了提议者）
- 提交阶段期望：5（包含所有节点）

### 测试场景3：选项显示
- 选项A：显示"选项A (节点)"
- 选项B：显示"选项B (节点)"
- 拒绝：显示"拒绝 (节点)"

## 技术细节

### 1. PBFT算法要求
- **准备阶段**：提议者不发送准备消息，其他节点发送
- **提交阶段**：所有节点（包括提议者）都可以发送提交消息
- **统计逻辑**：需要准确反映不同阶段的参与要求

### 2. 用户体验优化
- **清晰标识**：选项A和选项B明确区分
- **准确统计**：节点数量统计符合算法逻辑
- **直观显示**：用户能够清楚理解共识结果

### 3. 代码维护性
- **逻辑分离**：不同阶段的统计逻辑独立
- **数据一致性**：前后端数据结构统一
- **扩展性**：支持不同节点数量的系统

## 总结

这次修复解决了共识统计显示的两个关键问题：

1. **统计准确性**：节点数量统计现在正确包含主节点，符合PBFT算法要求
2. **显示清晰性**：选项A和选项B现在明确区分，避免用户混淆

修复后的系统提供了更准确、更清晰的共识结果展示，提升了用户体验和系统的可信度。





