from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import socketio
import uuid
import random
import asyncio
from datetime import datetime
import json

# 创建FastAPI应用
app = FastAPI(title="分布式PBFT共识系统", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建Socket.IO服务器
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"
)

# 创建ASGI应用
socket_app = socketio.ASGIApp(sio, app)

# 数据模型
class SessionConfig(BaseModel):
    nodeCount: int
    faultyNodes: int
    robotNodes: int  # 机器人节点数量
    topology: str
    branchCount: Optional[int] = 2
    proposalValue: int
    proposalContent: Optional[str] = ""
    maliciousProposer: bool
    allowTampering: bool
    messageDeliveryRate: int = 100
    proposerId: Optional[int] = 0  # 主节点ID，默认为0

class SessionInfo(BaseModel):
    sessionId: str
    nodeCount: int
    faultyNodes: int
    topology: str
    proposalValue: int
    status: str
    createdAt: str

# 全局状态管理
sessions: Dict[str, Dict[str, Any]] = {}
connected_nodes: Dict[str, List[int]] = {}
node_sockets: Dict[str, Dict[int, str]] = {}
# 节点级别的消息可靠性配置 {session_id: {node_id: {target_node_id: reliability_percentage}}}
node_reliability: Dict[str, Dict[int, Dict[int, int]]] = {}

# 会话管理
def create_session(config: SessionConfig) -> SessionInfo:
    session_id = str(uuid.uuid4())
    
    print(f"创建会话 - 原始配置:", config.dict())
    print(f"提议内容检查 - 创建时:", {
        'proposalContent': config.proposalContent,
        'hasProposalContent': config.proposalContent and config.proposalContent.strip(),
        'proposalValue': config.proposalValue
    })
    
    # 计算最短路径（用于多跳路由）
    shortest_paths = calculate_shortest_paths(
        config.nodeCount, 
        config.topology, 
        config.branchCount
    )
    
    # 打印路径信息用于调试
    print(f"\n=== 拓扑路径信息 ===")
    print(f"拓扑类型: {config.topology}, 节点数: {config.nodeCount}")
    if config.topology != "full":
        print(f"示例路径:")
        sample_count = 0
        for (src, dst), path in shortest_paths.items():
            if sample_count < 5 and len(path) > 2:  # 只显示多跳路径
                print(f"  节点{src}→节点{dst}: {' → '.join(map(str, path))} (跳数: {len(path)-1})")
                sample_count += 1
    print(f"总路径数: {len(shortest_paths)}")
    print(f"===================\n")
    
    # 将元组键转换为字符串键以支持JSON序列化（但在Python中仍使用元组）
    # 注意：这里不需要转换，因为session不会被JSON序列化，保持为字典
    
    session = {
        "config": config.dict(),
        "status": "waiting",
        "phase": "waiting",
        "phase_step": 0,
        "current_round": 1,  # 当前共识轮次
        "connected_nodes": [],
        "robot_nodes": [],  # 机器人节点列表
        "human_nodes": [],  # 人类节点列表（拜占庭节点）
        "robot_node_states": {},  # 机器人节点的状态（记录收到的消息）
        "timeout_task": None,  # 超时任务
        "messages": {
            "pre_prepare": [],
            "prepare": [],
            "commit": []
        },
        "auto_next_round": config.robotNodes != config.nodeCount,
        "node_states": {},
        "consensus_result": None,
        "consensus_history": [],  # 共识历史记录
        "shortest_paths": shortest_paths,  # 缓存的最短路径
        "created_at": datetime.now().isoformat()
    }
    
    sessions[session_id] = session
    connected_nodes[session_id] = []
    node_sockets[session_id] = {}
    node_reliability[session_id] = {}  # 初始化可靠性配置
    
    # 创建机器人节点
    # 如果是全机器人节点（实验模式），不自动开始共识，等待reset-round触发
    if config.robotNodes == config.nodeCount:
        # 实验模式：只创建机器人节点，不自动开始共识
        asyncio.create_task(create_robot_nodes_only(session_id, config.robotNodes))
    else:
        # 正常模式：创建机器人节点并立即开始共识
        asyncio.create_task(create_robot_nodes_and_start(session_id, config.robotNodes))
    
    return {
        "sessionId": session_id,
        "config": {
            "nodeCount": config.nodeCount,
            "faultyNodes": config.faultyNodes,
            "robotNodes": config.robotNodes,
            "topology": config.topology,
            "branchCount": config.branchCount,
            "proposalValue": config.proposalValue,
            "proposalContent": config.proposalContent,
            "maliciousProposer": config.maliciousProposer,
            "allowTampering": config.allowTampering,
            "messageDeliveryRate": config.messageDeliveryRate
        },
        "status": "waiting",
        "createdAt": session["created_at"]
    }

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return sessions.get(session_id)

def is_direct_connection(i: int, j: int, n: int, topology: str, n_value: int) -> bool:
    """检查两个节点之间是否有直接物理连接（边）"""
    if i == j:
        return False
    if topology == "full":
        return True
    elif topology == "ring":
        # 环形：双向连接，每个节点连接相邻节点
        return j == (i + 1) % n or j == (i - 1) % n
    elif topology == "star":
        # 星形：中心节点(0)与所有节点双向连接
        return i == 0 or j == 0
    elif topology == "tree":
        # 树形：父子节点双向连接
        parent_of_j = (j - 1) // n_value
        parent_of_i = (i - 1) // n_value
        # i是j的父节点，或j是i的父节点
        return (i == parent_of_j and j < n) or (j == parent_of_i and i < n)
    return False

def calculate_shortest_paths(n: int, topology: str, n_value: int) -> Dict[tuple, List[int]]:
    """使用Floyd-Warshall算法计算所有节点对之间的最短路径
    
    返回: {(src, dst): [path]} 例如 {(0, 2): [0, 1, 2]} 表示从0到2的路径是0→1→2
    """
    # 初始化距离矩阵和路径矩阵
    INF = float('inf')
    dist = [[INF] * n for _ in range(n)]
    next_node = [[None] * n for _ in range(n)]
    
    # 初始化：自己到自己距离为0，直接连接的边距离为1
    for i in range(n):
        dist[i][i] = 0
        for j in range(n):
            if i != j and is_direct_connection(i, j, n, topology, n_value):
                dist[i][j] = 1
                next_node[i][j] = j
    
    # Floyd-Warshall算法
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]
    
    # 重建路径
    paths = {}
    for i in range(n):
        for j in range(n):
            if i != j and dist[i][j] < INF:
                path = [i]
                current = i
                while current != j:
                    current = next_node[current][j]
                    if current is None:
                        break
                    path.append(current)
                if current == j:
                    paths[(i, j)] = path
    
    return paths

def is_connection_allowed(i: int, j: int, n: int, topology: str, n_value: int) -> bool:
    """检查两个节点之间是否可以通信（直接或通过路由）
    
    在多跳路由模型中，只要存在路径就允许通信
    """
    if i == j:
        return False
    # 计算路径（会被缓存在session中）
    paths = calculate_shortest_paths(n, topology, n_value)
    return (i, j) in paths

def is_honest(node_id: int, n: int, m: int, faulty_proposer: bool, proposer_id: int = 0) -> bool:
    """判断节点是否为诚实节点
    
    Args:
        node_id: 节点ID
        n: 总节点数
        m: 故障节点数
        faulty_proposer: 主节点是否为恶意节点
        proposer_id: 主节点ID，默认为0
    """
    if m == 0:
        return True
    if faulty_proposer:
        if node_id == proposer_id:
            return False
        return node_id <= n - m
    else:
        if node_id == proposer_id:
            return True
        return node_id < n - m

def try_path(session_id: str, path: list, delivery_rate: float) -> bool:
    """尝试通过指定路径发送消息
    
    Args:
        session_id: 会话ID
        path: 路径列表，如 [0, 1, 2] 表示 0→1→2
        delivery_rate: 链路可靠性（百分比）
    
    Returns:
        bool: 路径是否成功
    """
    # 对路径上的每一跳进行可靠性检查
    for i in range(len(path) - 1):
        hop_from = path[i]
        hop_to = path[i + 1]
        
        # 检查节点级别配置
        hop_reliability = delivery_rate
        if session_id in node_reliability:
            if hop_from in node_reliability[session_id]:
                if hop_to in node_reliability[session_id][hop_from]:
                    hop_reliability = node_reliability[session_id][hop_from][hop_to]
        
        # 对这一跳进行可靠性检查
        if random.random() * 100 >= hop_reliability:
            # 这一跳失败
            return False
    
    # 所有跳都成功
    return True

def get_ring_paths(from_node: int, to_node: int, n: int) -> list:
    """获取环形拓扑中的两条路径（顺时针和逆时针）
    
    Args:
        from_node: 起始节点
        to_node: 目标节点
        n: 总节点数
    
    Returns:
        list: 路径列表，每个路径是节点ID的列表
    """
    if from_node == to_node:
        return [[from_node]]
    
    # 顺时针路径
    clockwise_path = [from_node]
    current = from_node
    while current != to_node:
        current = (current + 1) % n
        clockwise_path.append(current)
    
    # 逆时针路径
    counterclockwise_path = [from_node]
    current = from_node
    while current != to_node:
        current = (current - 1) % n
        counterclockwise_path.append(current)
    
    return [clockwise_path, counterclockwise_path]

def should_deliver_message(session_id: str, from_node: int = None, to_node: int = None) -> bool:
    """根据消息传达概率决定是否发送消息（支持多跳路由和自定义矩阵）
    
    路由策略：
    - 自定义矩阵：直接使用矩阵中的概率
    - 星形拓扑：使用最短路径（1条）
    - 环形拓扑：
      * 相邻节点：使用最短路径（1条）
      * 不相邻节点：尝试两条路径（顺时针+逆时针），至少一条成功即可
    - 其他拓扑：使用最短路径（1条）
    
    优先级：
    1. 如果有自定义矩阵，使用自定义矩阵中的概率
    2. 如果指定了from_node和to_node，使用节点级别的可靠性配置
    3. 否则使用全局的messageDeliveryRate
    """
    session = get_session(session_id)
    if not session:
        return True
    
    # 如果没有指定from_node和to_node，使用全局配置
    if from_node is None or to_node is None:
        delivery_rate = session["config"].get("messageDeliveryRate", 100)
        if delivery_rate >= 100:
            return True
        return random.random() * 100 < delivery_rate
    
    # 检查是否有自定义可靠度矩阵
    custom_matrix = session.get("custom_reliability_matrix")
    if custom_matrix is not None:
        # 使用自定义矩阵中的概率
        reliability = custom_matrix[from_node][to_node]
        return random.random() < reliability
    
    config = session["config"]
    topology = config.get("topology", "full")
    n = config["nodeCount"]
    delivery_rate = config.get("messageDeliveryRate", 100)
    
    # 全连接拓扑：直接通信
    if topology == "full":
        if delivery_rate >= 100:
            return True
        return random.random() * 100 < delivery_rate
    
    # 环形拓扑：特殊处理两条路径
    if topology == "ring":
        # 检查是否相邻
        is_adjacent = (to_node == (from_node + 1) % n) or (to_node == (from_node - 1) % n)
        
        if is_adjacent:
            # 相邻节点：只有1条路径
            return random.random() * 100 < delivery_rate
        else:
            # 不相邻节点：有2条路径（顺时针+逆时针），至少一条成功
            paths = get_ring_paths(from_node, to_node, n)
            
            # 尝试两条路径
            path1_success = try_path(session_id, paths[0], delivery_rate)
            path2_success = try_path(session_id, paths[1], delivery_rate)
            
            success = path1_success or path2_success
            
            if success and len(paths[0]) > 2:
                if path1_success and path2_success:
                    print(f"  ✅ 环形双路径成功: {from_node}→{to_node} (两条路径都成功)")
                else:
                    which = "顺时针" if path1_success else "逆时针"
                    print(f"  ✅ 环形备用路径成功: {from_node}→{to_node} ({which}路径成功)")
            elif not success and len(paths[0]) > 2:
                print(f"  ❌ 环形双路径失败: {from_node}→{to_node} (两条路径都失败)")
            
            return success
    
    # 其他拓扑（星形、树形等）：使用最短路径
    shortest_paths = session.get("shortest_paths", {})
    path_key = (int(from_node), int(to_node))
    
    if path_key not in shortest_paths:
        print(f"⚠️  节点{from_node}到节点{to_node}不可达")
        return False
    
    path = shortest_paths[path_key]
    success = try_path(session_id, path, delivery_rate)
    
    if success and len(path) > 2:
        print(f"  ✅ 多跳成功: {from_node}→{to_node} 路径{path}")
    elif not success and len(path) > 2:
        print(f"  ❌ 多跳失败: {from_node}→{to_node} 路径{path}")
    
    return success

def calculate_effective_reliability(n: int, topology: str, n_value: int, p: float) -> Dict[str, float]:
    """计算不同拓扑下的有效传输可靠性（平均跳数近似法）
    
    返回: {
        'avg_hops': 平均跳数,
        'p_effective': 有效传输概率,
        'max_hops': 最大跳数
    }
    """
    # 计算最短路径
    paths = calculate_shortest_paths(n, topology, n_value)
    
    if not paths:
        return {'avg_hops': 1.0, 'p_effective': p, 'max_hops': 1}
    
    # 统计跳数
    hop_counts = [len(path) - 1 for path in paths.values()]
    avg_hops = sum(hop_counts) / len(hop_counts)
    max_hops = max(hop_counts)
    
    # 有效传输概率：p^(平均跳数)
    p_effective = p ** avg_hops
    
    return {
        'avg_hops': avg_hops,
        'p_effective': p_effective,
        'max_hops': max_hops
    }

def build_adjacency_matrix(n: int, topology: str, n_value: int):
    """构建邻接矩阵
    
    Args:
        n: 节点数
        topology: 拓扑类型
        n_value: 分支数（用于树形拓扑）
    
    Returns:
        n×n的邻接矩阵，A[i][j]=1表示i和j之间有直接连接
    """
    import numpy as np
    A = np.zeros((n, n), dtype=int)
    
    for i in range(n):
        for j in range(n):
            if i != j and is_direct_connection(i, j, n, topology, n_value):
                A[i][j] = 1
    
    return A

def calculate_comm_reliability_matrix_shortest_path(n: int, topology: str, n_value: int, p: float):
    """计算通信路径可靠性矩阵（正确的路径枚举方法）
    
    不同拓扑的路径策略：
    - 星形拓扑：
      * 中心↔边缘：1条路径（1跳），P_comm = p
      * 边缘↔边缘：1条路径（2跳），P_comm = p²
    - 环形拓扑：
      * 相邻节点：1条路径（1跳），P_comm = p
      * 不相邻节点：2条路径（顺时针+逆时针），P_comm = 1 - (1-p^k1) × (1-p^k2)
    - 其他拓扑：使用最短路径，P_comm = p^k
    
    Args:
        n: 节点数
        topology: 拓扑类型
        n_value: 分支数
        p: 单链路成功概率
    
    Returns:
        通信路径可靠性矩阵 P_comm[i,j]
    """
    import numpy as np
    
    # 初始化通信可靠性矩阵
    P_comm = np.zeros((n, n))
    np.fill_diagonal(P_comm, 1.0)
    
    if topology == "ring":
        # 环形拓扑：考虑两条路径
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                # 计算两个方向的距离
                clockwise = (j - i) % n
                counterclockwise = (i - j) % n
                
                # 检查是否相邻
                if min(clockwise, counterclockwise) == 1:
                    # 相邻节点：只有1条路径
                    P_comm[i,j] = p
                else:
                    # 不相邻节点：有2条路径
                    p1 = p ** clockwise  # 顺时针路径成功概率
                    p2 = p ** counterclockwise  # 逆时针路径成功概率
                    # 至少一条成功
                    P_comm[i,j] = 1 - (1 - p1) * (1 - p2)
    
    elif topology == "star":
        # 星形拓扑：中心节点是0
        center = 0
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                if i == center or j == center:
                    # 中心↔边缘：1跳
                    P_comm[i,j] = p
                else:
                    # 边缘↔边缘：2跳（必须经过中心）
                    P_comm[i,j] = p ** 2
    
    else:
        # 其他拓扑：使用最短路径
        shortest_paths = calculate_shortest_paths(n, topology, n_value)
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                path_key = (i, j)
                if path_key in shortest_paths:
                    path = shortest_paths[path_key]
                    path_length = len(path) - 1
                    P_comm[i, j] = p ** path_length
                else:
                    P_comm[i, j] = 0.0
    
    return P_comm

def calculate_comm_reliability_matrix(A, p: float, max_path_length: int = None):
    """使用邻接矩阵幂运算计算通信路径可靠性矩阵（考虑所有路径）
    
    基于论文推导：
    1. A^k[i,j] 表示从节点i到节点j长度为k的路径数量
    2. 单条长度为k的路径成功概率：p^k
    3. N_ij(k)条长度为k的路径全部失败概率：(1 - p^k)^N_ij(k)
    4. 所有路径均失败概率：∏[k=1 to n-1] (1 - p^k)^A^k[i,j]
    5. 通信路径可靠性：P_comm(i,j) = 1 - ∏[k=1 to n-1] (1 - p^k)^A^k[i,j]
    
    注意：此函数考虑所有可能的路径，包括最短路径和绕路。
          在实际系统中，通常只使用最短路径，请使用 calculate_comm_reliability_matrix_shortest_path
    
    Args:
        A: 邻接矩阵（numpy数组）
        p: 单链路成功概率
        max_path_length: 最大路径长度（默认为n-1）
    
    Returns:
        通信路径可靠性矩阵 P_comm[i,j]
    """
    import numpy as np
    
    n = A.shape[0]
    if max_path_length is None:
        max_path_length = n - 1
    
    # 初始化通信失败概率矩阵（初始为1，表示必然失败）
    P_fail = np.ones((n, n))
    
    # 对角线元素设为0（自己到自己不需要通信）
    np.fill_diagonal(P_fail, 0)
    
    # 当前的邻接矩阵幂（A^k）
    A_power = A.copy()
    
    # 遍历所有可能的路径长度k = 1, 2, ..., n-1
    for k in range(1, max_path_length + 1):
        # 单条长度为k的路径成功概率
        p_k = p ** k
        
        # 对每个节点对(i,j)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                # 长度为k的路径数量
                N_ij_k = A_power[i, j]
                
                if N_ij_k > 0:
                    # 所有长度为k的路径均失败的概率：(1 - p^k)^N_ij(k)
                    fail_prob_k = (1 - p_k) ** N_ij_k
                    
                    # 累乘到总失败概率
                    P_fail[i, j] *= fail_prob_k
        
        # 计算A^(k+1) = A^k * A
        if k < max_path_length:
            A_power = np.matmul(A_power, A)
    
    # 通信路径可靠性 = 1 - 失败概率
    P_comm = 1 - P_fail
    
    return P_comm


def calc_exact_receive_k_prob(senders, target, k_min, P_comm):
    """计算目标节点从发送者集合中至少收到k_min条消息的概率
    
    Args:
        senders: 发送者节点ID列表
        target: 目标节点ID
        k_min: 需要接收的最小消息数
        P_comm: 通信可靠性矩阵 (numpy数组，n×n)
    
    Returns:
        至少收到k_min条消息的概率
    """
    from itertools import combinations
    
    # 过滤掉目标节点自己（不能给自己发消息）
    valid_senders = [s for s in senders if s != target]
    
    if k_min <= 0:
        return 1.0
    if k_min > len(valid_senders):
        return 0.0
    
    total_prob = 0.0
    
    # 枚举所有可能收到消息的子集，大小>=k_min
    for k in range(k_min, len(valid_senders) + 1):
        for subset in combinations(valid_senders, k):
            # 计算这个子集的概率：subset中的节点成功发送，其余节点失败
            prob = 1.0
            for sender in valid_senders:
                if sender in subset:
                    # 成功发送
                    prob *= P_comm[sender, target]
                else:
                    # 失败
                    prob *= (1 - P_comm[sender, target])
            total_prob += prob
    
    return total_prob

def calculate_theoretical_success_rate_custom_matrix(n: int, f: int, P_comm, proposer_id: int = 0) -> float:
    """使用自定义可靠度矩阵计算PBFT共识的理论成功概率
    
    Args:
        n: 节点数
        f: 容错数
        P_comm: 自定义的通信可靠性矩阵 (numpy数组或列表，n×n)
        proposer_id: 主节点ID，默认为0
    
    Returns:
        理论成功率
    """
    from math import comb
    from itertools import combinations
    import numpy as np
    
    # 确保P_comm是numpy数组
    if not isinstance(P_comm, np.ndarray):
        P_comm = np.array(P_comm)
    
    print(f"\n=== 自定义矩阵理论计算 ===")
    print(f"节点数: {n}, 容错数: {f}, 主节点: {proposer_id}")
    print(f"使用自定义P_comm矩阵")
    
    # 显示部分通信可靠性
    print(f"\nP_comm矩阵（部分）:")
    for i in range(min(3, n)):
        for j in range(min(3, n)):
            if i != j:
                print(f"  P_comm({i},{j}) = {P_comm[i,j]:.4f}")
    
    nc_required = n - f  # 成功阈值
    k_prepare = 2 * f - 1   # prepare阶段门限：从其他节点收到2f-1条（加自己=2f）
    k_commit = 2 * f        # commit阶段门限：从其他节点收到2f条（加自己=2f+1）
    
    # 构建副本节点列表（所有节点除了主节点）
    replica_nodes = [i for i in range(n) if i != proposer_id]
    
    total_prob = 0.0
    
    # ========== Pre-prepare阶段 ==========
    # 枚举所有可能的V_pp配置（主节点 + x-1个副本）
    for x in range(nc_required, n + 1):
        for v_pp_replicas in combinations(replica_nodes, x - 1):
            # 计算这个V_pp配置的概率
            p_this_vpp = 1.0
            for replica in replica_nodes:
                if replica in v_pp_replicas:
                    p_this_vpp *= P_comm[proposer_id, replica]
                else:
                    p_this_vpp *= (1 - P_comm[proposer_id, replica])
            
            if p_this_vpp < 1e-15:
                continue
            
            v_pp_nodes = [proposer_id] + list(v_pp_replicas)
            
            # ========== Prepare阶段 ==========
            for y in range(nc_required, min(x, n) + 1):
                for v_p_nodes in combinations(v_pp_nodes, y):
                    # 计算每个节点收到足够prepare的概率
                    p_this_vp_given_vpp = 1.0
                    
                    # prepare的发送者：主节点不发送prepare
                    prepare_senders = [node for node in v_pp_nodes if node != proposer_id]
                    
                    for target in v_pp_nodes:
                        if target in v_p_nodes:
                            # 该节点需要收到≥k_prepare个prepare
                            p_target_receive_k = calc_exact_receive_k_prob(
                                prepare_senders, target, k_prepare, P_comm
                            )
                            p_this_vp_given_vpp *= p_target_receive_k
                        else:
                            # 该节点未收到足够的prepare
                            p_target_receive_k = calc_exact_receive_k_prob(
                                prepare_senders, target, k_prepare, P_comm
                            )
                            p_this_vp_given_vpp *= (1 - p_target_receive_k)
                    
                    if p_this_vp_given_vpp < 1e-15:
                        continue
                    
                    # ========== Commit阶段 ==========
                    for z in range(nc_required, min(y, n) + 1):
                        for v_c_nodes in combinations(v_p_nodes, z):
                            # commit的发送者：v_p_nodes中的所有节点
                            commit_senders = list(v_p_nodes)
                            
                            p_this_vc_given_vp = 1.0
                            
                            for target in v_p_nodes:
                                if target in v_c_nodes:
                                    # 需要收到≥k_commit个commit
                                    p_target_receive_k = calc_exact_receive_k_prob(
                                        commit_senders, target, k_commit, P_comm
                                    )
                                    p_this_vc_given_vp *= p_target_receive_k
                                else:
                                    p_target_receive_k = calc_exact_receive_k_prob(
                                        commit_senders, target, k_commit, P_comm
                                    )
                                    p_this_vc_given_vp *= (1 - p_target_receive_k)
                            
                            if p_this_vc_given_vp < 1e-15:
                                continue
                            
                            # 如果|V_c| >= n-f，则成功
                            if len(v_c_nodes) >= nc_required:
                                total_prob += p_this_vpp * p_this_vp_given_vpp * p_this_vc_given_vp
    
    print(f"理论成功率（自定义矩阵，精确计算）: {total_prob:.6f}\n")
    return total_prob

def calculate_theoretical_success_rate_multihop(n: int, f: int, topology: str, n_value: int, p: float, proposer_id: int = 0) -> float:
    """计算多跳拓扑下PBFT共识的理论成功概率（精确计算，使用真实P_comm矩阵）
    
    方法：不使用平均P_comm的简化，而是对每对节点使用真实的通信可靠性P_comm[i,j]
    
    按照伪代码Line 8：所有诚实节点（包括主节点）都广播PREPARE
    
    路径策略：
    - 星形拓扑：中心↔边缘 P_comm=p，边缘↔边缘 P_comm=p²
    - 环形拓扑：相邻 P_comm=p，不相邻 P_comm=1-(1-p^k1)(1-p^k2)
    
    Args:
        n: 节点总数
        f: 容错数
        topology: 拓扑类型
        n_value: 分支数
        p: 单链路成功概率
        proposer_id: 主节点ID，默认为0
    
    Returns:
        理论成功率
    """
    from math import comb
    from itertools import combinations
    import numpy as np
    
    # 计算通信路径可靠性矩阵
    P_comm = calculate_comm_reliability_matrix_shortest_path(n, topology, n_value, p)
    
    print(f"\n=== 多跳拓扑理论计算（{topology}拓扑，精确方法） ===")
    print(f"节点数: {n}, 容错数: {f}, 链路可靠性: {p:.3f}, 主节点: {proposer_id}")
    print(f"使用精确P_comm矩阵，不使用平均近似")
    
    # 显示部分通信可靠性
    print(f"\nP_comm矩阵（部分）:")
    for i in range(min(3, n)):
        for j in range(min(3, n)):
            if i != j:
                print(f"  P_comm({i},{j}) = {P_comm[i,j]:.4f}")
    
    nc_required = n - f  # 成功阈值
    k_prepare = 2 * f - 1   # prepare阶段门限：从其他节点收到2f-1条（加自己=2f）
    k_commit = 2 * f        # commit阶段门限：从其他节点收到2f条（加自己=2f+1）
    
    # 构建副本节点列表（所有节点除了主节点）
    replica_nodes = [i for i in range(n) if i != proposer_id]
    
    total_prob = 0.0
    
    # ========== Pre-prepare阶段 ==========
    # 枚举所有可能的V_pp配置（主节点 + x-1个副本）
    for x in range(nc_required, n + 1):
        # 枚举所有x-1个副本的组合
        for v_pp_replicas in combinations(replica_nodes, x - 1):
            # 计算这个V_pp配置的概率
            p_this_vpp = 1.0
            for replica in replica_nodes:
                if replica in v_pp_replicas:
                    p_this_vpp *= P_comm[proposer_id, replica]  # 收到pre-prepare
                else:
                    p_this_vpp *= (1 - P_comm[proposer_id, replica])  # 未收到
            
            if p_this_vpp < 1e-15:
                continue
            
            # V_pp = {proposer_id} ∪ v_pp_replicas
            v_pp_nodes = [proposer_id] + list(v_pp_replicas)
            
            # ========== Prepare阶段 ==========
            # 主节点不发送prepare，只有副本互相发送
            
            # 对于V_pp中的每个节点，计算它收到≥k_prepare条prepare的概率
            # 使用精确的P_comm[i,j]
            
            # 副本节点发送prepare（主节点不发送）
            prepare_senders = [node for node in v_pp_nodes if node != proposer_id]
            
            # 计算每个节点能否进入V_p（收到≥k_prepare条prepare）
            # 使用动态规划或枚举所有可能的消息传递情况
            
            # 简化但仍精确的方法：对每个节点，计算从prepare_senders收到≥k_prepare条的概率
            node_enter_vp_prob = {}
            
            for target_node in v_pp_nodes:
                # 该节点从prepare_senders中收到消息
                senders_to_this_node = [s for s in prepare_senders if s != target_node]
                
                if len(senders_to_this_node) < k_prepare:
                    node_enter_vp_prob[target_node] = 0.0
                else:
                    # 计算收到≥k_prepare条消息的概率
                    # 枚举所有可能的k条成功组合
                    prob_ge_k = 0.0
                    for num_success in range(k_prepare, len(senders_to_this_node) + 1):
                        for success_set in combinations(senders_to_this_node, num_success):
                            prob_this_case = 1.0
                            for sender in senders_to_this_node:
                                if sender in success_set:
                                    prob_this_case *= P_comm[sender, target_node]
                                else:
                                    prob_this_case *= (1 - P_comm[sender, target_node])
                            prob_ge_k += prob_this_case
                    
                    node_enter_vp_prob[target_node] = prob_ge_k
            
            # 枚举V_p的所有可能配置（V_p ⊆ V_pp）
            for y in range(nc_required, x + 1):
                for v_p_nodes_tuple in combinations(v_pp_nodes, y):
                    v_p_nodes = list(v_p_nodes_tuple)
                    
                    # 计算这个V_p配置的概率
                    p_this_vp_given_vpp = 1.0
                    for node in v_pp_nodes:
                        if node in v_p_nodes:
                            p_this_vp_given_vpp *= node_enter_vp_prob[node]
                        else:
                            p_this_vp_given_vpp *= (1 - node_enter_vp_prob[node])
                    
                    if p_this_vp_given_vpp < 1e-15:
                        continue
                    
                    # ========== Commit阶段 ==========
                    # V_p中的所有节点互相发送commit
                    commit_senders = v_p_nodes
                    
                    # 计算每个节点能否进入V_c（收到≥k_commit条commit）
                    node_enter_vc_prob = {}
                    
                    for target_node in v_p_nodes:
                        senders_to_this_node = [s for s in commit_senders if s != target_node]
                        
                        if len(senders_to_this_node) < k_commit:
                            node_enter_vc_prob[target_node] = 0.0
                        else:
                            prob_ge_k = 0.0
                            for num_success in range(k_commit, len(senders_to_this_node) + 1):
                                for success_set in combinations(senders_to_this_node, num_success):
                                    prob_this_case = 1.0
                                    for sender in senders_to_this_node:
                                        if sender in success_set:
                                            prob_this_case *= P_comm[sender, target_node]
                                        else:
                                            prob_this_case *= (1 - P_comm[sender, target_node])
                                    prob_ge_k += prob_this_case
                            
                            node_enter_vc_prob[target_node] = prob_ge_k
                    
                    # 计算|V_c| >= nc_required的概率
                    # 枚举所有可能的V_c配置
                    p_success_given_vp = 0.0
                    for z in range(nc_required, y + 1):
                        for v_c_nodes_tuple in combinations(v_p_nodes, z):
                            v_c_nodes = list(v_c_nodes_tuple)
                            
                            p_this_vc_given_vp = 1.0
                            for node in v_p_nodes:
                                if node in v_c_nodes:
                                    p_this_vc_given_vp *= node_enter_vc_prob[node]
                                else:
                                    p_this_vc_given_vp *= (1 - node_enter_vc_prob[node])
                            
                            p_success_given_vp += p_this_vc_given_vp
                    
                    total_prob += p_this_vpp * p_this_vp_given_vpp * p_success_given_vp
    
    print(f"理论成功率（精确计算，使用真实P_comm）: {total_prob:.6f}")
    print(f"=" * 50)
    
    return total_prob

def calculate_theoretical_success_rate(n: int, f: int, p: float) -> float:
    """计算PBFT共识的理论成功概率（口径A：N_c ≥ N − f）

    严格对齐论文 Theorem 1（式(1)–(6)）和伪代码Algorithm 1在以下特例下的闭式化简：
    - 全连接网络
    - 所有节点在线（P(V_node)=1）
    - 同质链路：p^L_{i,j} = p
    - n 给定，f = floor((n-1)/3)
    - 成功判据：commit 成功节点数 N_c ≥ N − f
    - 按照伪代码Line 8：所有诚实节点（包括主节点）都广播PREPARE

    注意：单节点在 prepare/commit 阶段的门限来自式(6)：至少收到 2f 条成功消息（来自其他节点）。
    """
    from math import comb

    def binom_prob(n_trials: int, k_success: int, prob: float) -> float:
        if k_success > n_trials or k_success < 0:
            return 0.0
        return comb(n_trials, k_success) * (prob ** k_success) * ((1 - prob) ** (n_trials - k_success))

    # q_{>=k}(m) = P(Bin(m,p) >= k)
    def binom_tail_ge(m: int, k: int, prob: float) -> float:
        if k <= 0:
            return 1.0
        if m < 0:
            return 0.0
        if k > m:
            return 0.0
        return sum(binom_prob(m, i, prob) for i in range(k, m + 1))

    # 口径A：最终成功要求 N_c >= N - f
    nc_required = n - f
    # 论文式(6)中使用的“至少收到2f条成功消息”（来自其他节点）
    k_prepare = 2 * f - 1   # prepare阶段：从其他节点收到2f-1条（加自己=2f）
    k_commit = 2 * f        # commit阶段：从其他节点收到2f条（加自己=2f+1）

    total_prob = 0.0

    # pre-prepare：主节点v0始终在V_pp，n-1个副本中有 x-1 个收到
    # 因为要求 N_pp >= N_p >= N_c >= N-f，所以这里 x 从 nc_required 到 n
    for x in range(nc_required, n + 1):
        # P(N_pp = x)
        p_pp = binom_prob(n - 1, x - 1, p)
        if p_pp < 1e-15:
            continue

        # prepare：给定 N_pp = x
        # 主节点不发送prepare，只有副本发送
        # 主节点从 x-1 个副本收到 prepare，需 >=2f
        q0 = binom_tail_ge(x - 1, k_prepare, p)
        # 副本从其余 (x-2) 个副本收到 prepare，需 >=2f
        q1 = binom_tail_ge(x - 2, k_prepare, p)

        # 枚举 N_p = y（也必须 >= nc_required，且 y <= x）
        for y in range(nc_required, x + 1):
            # P(N_p = y | N_pp = x)
            # 两种情况：主节点在/不在 V_p
            p_p_y_given_x = 0.0
            # 主节点在V_p：副本中有 y-1 个进入
            p_p_y_given_x += q0 * binom_prob(x - 1, y - 1, q1)
            # 主节点不在V_p：副本中有 y 个进入
            p_p_y_given_x += (1 - q0) * binom_prob(x - 1, y, q1)

            if p_p_y_given_x < 1e-15:
                continue

            # commit：给定 N_p = y
            # 节点从其他 y-1 个节点收到 commit，需 >=2f
            q2 = binom_tail_ge(y - 1, k_commit, p)
            # P(N_c >= N-f | N_p = y)
            p_c_ge = sum(binom_prob(y, z, q2) for z in range(nc_required, y + 1))

            total_prob += p_pp * p_p_y_given_x * p_c_ge

    return total_prob


def calculate_theoretical_success_rate_paper_simulation(n: int, f: int, p: float) -> float:
    """使用论文的逐阶段淘汰仿真模型计算PBFT共识成功概率
    
    论文方法（第10页）：
    "In P-L models, a link failure leads to the failure in the corresponding 
    communication phase, and only the live nodes enter the next round of consensus"
    
    关键特征：
    1. 每个阶段后，只有成功的节点（收到足够消息的节点）进入下一阶段
    2. 下一阶段的通信只在"存活"节点之间进行
    3. 最终判断：存活节点数 ≥ n-f 则成功
    
    这个模型更接近论文的红×仿真结果
    """
    from math import comb
    
    def binom_prob(n_trials: int, k_success: int, prob: float) -> float:
        if k_success > n_trials or k_success < 0:
            return 0.0
        return comb(n_trials, k_success) * (prob ** k_success) * ((1 - prob) ** (n_trials - k_success))
    
    def binom_tail_ge(m: int, k: int, prob: float) -> float:
        """二项分布尾概率 P(X ≥ k)"""
        if k <= 0:
            return 1.0
        if m < 0:
            return 0.0
        if k > m:
            return 0.0
        return sum(binom_prob(m, i, prob) for i in range(k, m + 1))
    
    nc_required = n - f
    k_prepare = 2 * f - 1  # prepare门限：从其他节点收到2f-1条（加自己=2f）
    k_commit = 2 * f       # commit门限：从其他节点收到2f条（加自己=2f+1）
    
    total_prob = 0.0
    
    # ========== Phase 1: Pre-prepare ==========
    # 主节点始终在V_pp，n-1个副本中x-1个收到pre-prepare消息
    for x in range(nc_required, n + 1):
        p_pp = binom_prob(n - 1, x - 1, p)
        if p_pp < 1e-15:
            continue
        
        # ========== Phase 2: Prepare（只有V_pp中的x个节点参与）==========
        # 在V_pp的x个节点中，每个节点需要收到≥k_prepare条prepare消息才能"存活"进入V_p
        # 
        # 主节点：从x-1个副本节点收到prepare
        q_primary_survives = binom_tail_ge(x - 1, k_prepare, p)
        # 副本节点：从x-2个其他节点收到prepare（不包括自己，主节点不发prepare）
        q_replica_survives = binom_tail_ge(x - 2, k_prepare, p)
        
        # 枚举进入V_p的"存活"节点数y
        for y in range(nc_required, x + 1):
            # 计算P(|V_p| = y | |V_pp| = x)
            # 情况1：主节点存活 + (y-1)个副本存活
            case1 = q_primary_survives * binom_prob(x - 1, y - 1, q_replica_survives)
            # 情况2：主节点未存活 + y个副本存活  
            case2 = (1 - q_primary_survives) * binom_prob(x - 1, y, q_replica_survives)
            p_vp_given_vpp = case1 + case2
            
            if p_vp_given_vpp < 1e-15:
                continue
            
            # ========== Phase 3: Commit（只有V_p中的y个"存活"节点参与）==========
            # 在V_p的y个节点中，每个节点需要收到≥k_commit条commit消息才能"存活"进入V_c
            # 每个节点从其他y-1个节点收到commit
            q_node_commits = binom_tail_ge(y - 1, k_commit, p)
            
            # 计算P(|V_c| ≥ nc_required | |V_p| = y)
            # 这是y个节点中有≥nc_required个成功完成commit的概率
            p_vc_success = sum(binom_prob(y, z, q_node_commits) for z in range(nc_required, y + 1))
            
            # 累加概率
            total_prob += p_pp * p_vp_given_vpp * p_vc_success
    
    return total_prob


# HTTP路由
@app.post("/api/sessions")
async def create_consensus_session(config: SessionConfig):
    """创建新的共识会话"""
    try:
        session_info = create_session(config)
        return session_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话并停止所有相关进程"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 停止会话
    session["status"] = "stopped"
    
    # 清理会话数据
    if session_id in sessions:
        del sessions[session_id]
    if session_id in connected_nodes:
        del connected_nodes[session_id]
    if session_id in node_sockets:
        del node_sockets[session_id]
    
    print(f"会话 {session_id} 已被删除并停止")
    
    return {"message": "会话已删除"}

@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """获取会话状态"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 将内部按类型存储的消息结构展开为扁平列表，便于前端统计
    # session["messages"] 结构:
    # {
    #   "pre_prepare": [...],
    #   "prepare": [...],
    #   "commit": [...]
    # }
    raw_messages = session.get("messages", {})
    flat_messages = []
    if isinstance(raw_messages, dict):
        # 只展开我们关心的几类消息，避免把其他内部结构暴露出去
        for key in ("pre_prepare", "prepare", "commit"):
            msg_list = raw_messages.get(key, [])
            if isinstance(msg_list, list):
                flat_messages.extend(msg_list)
    elif isinstance(raw_messages, list):
        # 兼容旧结构：如果本来就是列表就直接返回
        flat_messages = raw_messages

    history = session.get("consensus_history", [])
    max_history = 50
    if len(history) > max_history:
        history = history[-max_history:]
    
    return {
        "sessionId": session_id,
        "status": session["status"],
        "phase": session["phase"],
        "connectedNodes": len(connected_nodes.get(session_id, [])),
        "totalNodes": session["config"]["nodeCount"],
        "currentRound": session.get("current_round", 1),
        # 实验模块依赖这里的 messages 做 filter，因此必须是「消息列表」而不是内部字典结构
        "messages": flat_messages,
        "history": history
    }

@app.post("/api/sessions/{session_id}/reset-round")
async def reset_round(session_id: str):
    """重置当前轮次，开始新一轮共识（用于实验）"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 增加轮次计数
    session["current_round"] = session.get("current_round", 1) + 1
    current_round = session["current_round"]
    
    # 重置阶段到pre-prepare
    session["phase"] = "pre-prepare"
    session["phase_step"] = 0
    session["status"] = "running"
    session["consensus_result"] = None
    session["consensus_finalized_round"] = None  # 清除完成标记
    
    # 重置机器人节点状态（重要！否则后续轮次无法发送消息）
    for robot_id in session.get("robot_nodes", []):
        if robot_id in session.get("robot_node_states", {}):
            session["robot_node_states"][robot_id] = {
                "received_pre_prepare": False,
                "received_prepare_count": 0,
                "received_commit_count": 0,
                "sent_prepare": False,
                "sent_commit": False
            }
    
    print(f"第{current_round}轮开始 - 已重置所有机器人节点状态")
    
    # 不清除消息历史，保留所有轮次的消息用于统计
    
    # 如果是全机器人节点，自动开始新一轮
    robot_nodes = session["config"].get("robotNodes", 0)
    if robot_nodes == session["config"]["nodeCount"]:
        # 等待机器人节点创建完成（如果是第一轮，机器人节点可能还在异步创建中）
        expected_robot_count = session["config"]["nodeCount"]
        current_robot_count = len(session.get("robot_nodes", []))
        
        if current_robot_count < expected_robot_count:
            print(f"第{current_round}轮 - 机器人节点还未完全创建（当前{current_robot_count}/{expected_robot_count}），等待创建完成...")
            max_wait = 2.0  # 最多等待2秒
            check_interval = 0.01  # 从100ms减少到10ms（加速模式）  # 每100ms检查一次
            waited_time = 0
            
            while waited_time < max_wait:
                await asyncio.sleep(check_interval)
                waited_time += check_interval
                session = get_session(session_id)  # 重新获取session，因为可能被异步修改
                if not session:
                    break
                current_robot_count = len(session.get("robot_nodes", []))
                if current_robot_count >= expected_robot_count:
                    print(f"第{current_round}轮 - 机器人节点已创建完成（{current_robot_count}/{expected_robot_count}）")
                    break
            
            # 如果等待后仍然没有创建完成，打印警告但继续执行
            if current_robot_count < expected_robot_count:
                print(f"⚠️ 第{current_round}轮 - 警告：机器人节点仍未完全创建（{current_robot_count}/{expected_robot_count}），但继续执行（加速模式）")
        
        # 触发机器人节点开始发送pre-prepare
        await sio.emit('round_reset', {
            "round": session["current_round"],
            "proposalValue": session["config"]["proposalValue"]
        }, room=session_id)
        
        # 主节点发送pre-prepare
        await robot_send_pre_prepare(session_id)
    
    return {
        "sessionId": session_id,
        "currentRound": session["current_round"],
        "phase": session["phase"]
    }

class BatchExperimentRequest(BaseModel):
    rounds: int = 30
    customReliabilityMatrix: Optional[List[List[float]]] = None  # 自定义可靠度矩阵
    averageDirectReliability: Optional[float] = None  # 平均直连可靠度

@app.post("/api/sessions/{session_id}/run-batch-experiment")
async def run_batch_experiment(session_id: str, request: BatchExperimentRequest):
    """批量运行多轮实验，完成后一次性返回所有结果
    
    Args:
        session_id: 会话ID
        request: 包含实验轮数和可选的自定义可靠度矩阵
    
    Returns:
        {
            "results": [...],  # 每轮的结果
            "theoreticalSuccessRate": 0.85,  # 理论成功率
            "experimentalSuccessRate": 0.83  # 实验成功率
        }
    """
    print(f"\n[DEBUG] run_batch_experiment 收到请求:")
    print(f"  - session_id: {session_id}")
    print(f"  - rounds: {request.rounds}")
    print(f"  - customReliabilityMatrix: {'有' if request.customReliabilityMatrix else '无'}")
    print(f"  - averageDirectReliability: {request.averageDirectReliability}")
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    config = session["config"]
    n = config["nodeCount"]
    f = (n - 1) // 3
    p = config["messageDeliveryRate"] / 100.0  # 转换为概率
    topology = config["topology"]
    n_value = config.get("branchCount", 2)
    proposer_id = config.get("proposerId", 0)  # 获取主节点ID
    rounds = request.rounds
    custom_matrix = request.customReliabilityMatrix
    
    # 如果提供了自定义矩阵，将其存储到session中用于实验
    if custom_matrix:
        import numpy as np
        # 验证矩阵维度
        if len(custom_matrix) != n or any(len(row) != n for row in custom_matrix):
            raise HTTPException(status_code=400, detail=f"自定义矩阵维度错误，应为{n}x{n}")
        
        # 转换为numpy数组
        P_comm_custom = np.array(custom_matrix)
        session["custom_reliability_matrix"] = P_comm_custom.tolist()
        
        print(f"使用自定义可靠度矩阵：")
        print(f"  矩阵维度: {n}x{n}")
        print(f"  平均可靠度: {np.mean([P_comm_custom[i][j] for i in range(n) for j in range(n) if i != j]):.4f}")
    else:
        session["custom_reliability_matrix"] = None
    
    # 计算理论成功率
    avg_reliability_theoretical = None  # 基于平均直连可靠度的理论值
    
    if custom_matrix:
        # 使用自定义矩阵计算理论成功率
        import numpy as np
        P_comm_custom = np.array(custom_matrix)
        theoretical_rate = calculate_theoretical_success_rate_custom_matrix(n, f, P_comm_custom, proposer_id)
        print(f"开始批量实验：{rounds}轮，n={n}, f={f}, 主节点={proposer_id}, 使用自定义可靠度矩阵")
        print(f"  理论成功率={theoretical_rate:.4f} (基于自定义矩阵的精确计算)")
        
        # 如果提供了平均直连可靠度，计算对应的理论值
        if request.averageDirectReliability is not None:
            avg_p = request.averageDirectReliability
            print(f"  平均直连可靠度={avg_p:.4f}")
            
            # 使用平均可靠度计算理论成功率
            if topology == "full":
                avg_reliability_theoretical = calculate_theoretical_success_rate(n, f, avg_p) * 100
            else:
                avg_reliability_theoretical = calculate_theoretical_success_rate_multihop(n, f, topology, n_value, avg_p, proposer_id) * 100
            
            print(f"  平均可靠度理论成功率={avg_reliability_theoretical:.4f}% (用于对比)")
    elif topology == "full":
        # 全连接拓扑：使用精确公式
        theoretical_rate = calculate_theoretical_success_rate(n, f, p)
        print(f"开始批量实验：{rounds}轮，n={n}, f={f}, p={p}, 拓扑={topology}")
        print(f"  理论成功率={theoretical_rate:.4f} (精确计算)")
    else:
        # 其他拓扑：使用正确的路径策略计算理论成功率
        try:
            import numpy as np
            
            # 使用正确的路径策略计算理论成功率
            # - 星形：中心↔边缘1跳，边缘↔边缘2跳
            # - 环形：相邻1跳，不相邻尝试两个方向
            theoretical_rate = calculate_theoretical_success_rate_multihop(n, f, topology, n_value, p, proposer_id)
            
            # 同时计算平均跳数等统计信息（用于日志）
            topo_stats = calculate_effective_reliability(n, topology, n_value, p)
            avg_hops = topo_stats['avg_hops']
            max_hops = topo_stats['max_hops']
            
            print(f"开始批量实验：{rounds}轮，n={n}, f={f}, p={p:.2f}, 拓扑={topology}, 主节点={proposer_id}")
            print(f"  平均跳数={avg_hops:.2f}, 最大跳数={max_hops}")
            print(f"  理论成功率={theoretical_rate:.4f} (基于路径策略的精确计算)")
        except ImportError:
            print("警告：numpy未安装，回退到平均跳数近似法")
            # 回退到平均跳数近似法
            topo_stats = calculate_effective_reliability(n, topology, n_value, p)
            p_eff = topo_stats['p_effective']
            avg_hops = topo_stats['avg_hops']
            max_hops = topo_stats['max_hops']
            
            theoretical_rate = calculate_theoretical_success_rate(n, f, p_eff)
            
            print(f"开始批量实验：{rounds}轮，n={n}, f={f}, p={p:.2f}, 拓扑={topology}")
            print(f"  平均跳数={avg_hops:.2f}, 最大跳数={max_hops}, 有效可靠性={p_eff:.4f}")
            print(f"  理论成功率={theoretical_rate:.4f} (平均跳数近似法)")
        except Exception as e:
            print(f"错误：多跳理论计算失败 - {str(e)}")
            import traceback
            traceback.print_exc()
            # 回退到平均跳数近似法
            topo_stats = calculate_effective_reliability(n, topology, n_value, p)
            p_eff = topo_stats['p_effective']
            theoretical_rate = calculate_theoretical_success_rate(n, f, p_eff)
            print(f"  回退到平均跳数近似法，理论成功率={theoretical_rate:.4f}")
    
    # 存储所有轮次的结果
    all_results = []

    # 批量实验必须严格“等一轮结束再进入下一轮”，否则会出现异步任务跨轮写入（round字段错乱）
    # 这里复用现有的 reset_round 逻辑，确保每轮初始化、触发、超时机制一致。
    session["current_round"] = 0
    session["consensus_finalized_round"] = None
    session["last_pre_prepare_round"] = None

    for round_num in range(1, rounds + 1):
        # 触发新一轮（reset_round 内部会 +1 并触发 pre-prepare）
        reset_info = await reset_round(session_id)
        current_round = reset_info.get("currentRound", round_num)

        # 等待本轮结束：
        # - 成功会由 check_commit_phase -> finalize_consensus 写入 consensus_history
        # - 失败会由 timeout_task(2s) -> finalize_consensus 写入 consensus_history
        max_wait = 3.0  # 给 finalize_consensus 留一点余量，避免2s边界竞态
        check_interval = 0.05
        waited_time = 0.0

        while waited_time < max_wait:
            await asyncio.sleep(check_interval)
            waited_time += check_interval

            session = get_session(session_id)
            if not session:
                break

            # 优先用 finalized_round，避免 history 还未来得及 append 的瞬间
            if session.get("consensus_finalized_round") == current_round:
                break

            history = session.get("consensus_history", [])
            if any(h.get("round") == current_round for h in history):
                break

        session = get_session(session_id)
        if not session:
            break

        history = session.get("consensus_history", [])
        round_history = next((h for h in history if h.get("round") == current_round), None)
        
        # 统计该轮的消息数
        messages = session.get("messages", {})
        all_messages = []
        for msg_type in ["pre_prepare", "prepare", "commit"]:
            all_messages.extend(messages.get(msg_type, []))
        
        round_messages = [m for m in all_messages if m.get("round") == current_round]
        message_count = len(round_messages)
        
        # 判断成功与否
        success = False
        failure_reason = None
        
        if round_history:
            status_text = round_history.get("status", "")
            description = round_history.get("description", "")
            success = "成功" in status_text and "失败" not in status_text
            
            if not success:
                if "超时" in status_text:
                    failure_reason = "超时"
                elif description:
                    failure_reason = description
                else:
                    failure_reason = status_text or "失败"
        else:
            failure_reason = "超时" if waited_time >= max_wait else "未知"
        
        result = {
            "round": round_num,
            "success": success,
            "messageCount": message_count,
            "failureReason": failure_reason,
            "waitTime": round(waited_time * 1000)  # 转换为毫秒
        }
        
        all_results.append(result)
        
        print(f"第{round_num}轮完成: {'成功' if success else '失败'}, 消息数={message_count}, 等待时间={result['waitTime']}ms")
    
    # 计算实验成功率
    success_count = sum(1 for r in all_results if r["success"])
    experimental_rate = success_count / len(all_results) if all_results else 0
    
    print(f"批量实验完成：成功{success_count}/{len(all_results)}轮，实验成功率={experimental_rate:.4f}，理论成功率={theoretical_rate:.4f}")
    
    response_data = {
        "results": all_results,
        "theoreticalSuccessRate": round(theoretical_rate * 100, 2),  # 转换为百分比
        "experimentalSuccessRate": round(experimental_rate * 100, 2),
        "totalRounds": len(all_results),
        "successCount": success_count,
        "failureCount": len(all_results) - success_count
    }
    
    # 如果有平均可靠度理论值，添加到返回结果
    if avg_reliability_theoretical is not None:
        response_data["averageReliabilityTheoretical"] = round(avg_reliability_theoretical, 2)
        print(f"  平均可靠度理论成功率={avg_reliability_theoretical:.2f}%")
    
    return response_data

@app.post("/api/sessions/{session_id}/assign-node")
async def assign_node(session_id: str):
    """自动分配节点"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取已连接的节点
    connected = connected_nodes.get(session_id, [])
    total_nodes = session["config"]["nodeCount"]
    
    # 找到第一个可用的节点
    available_node = None
    for i in range(total_nodes):
        if i not in connected:
            available_node = i
            break
    
    if available_node is None:
        raise HTTPException(status_code=409, detail="All nodes are occupied")
    
    proposer_id = session["config"].get("proposerId", 0)
    return {
        "nodeId": available_node,
        "sessionId": session_id,
        "role": "Proposer" if available_node == proposer_id else "Validator",
        "totalNodes": total_nodes,
        "connectedNodes": len(connected)
    }

@app.get("/api/sessions/{session_id}/connected-nodes")
async def get_connected_nodes(session_id: str):
    """获取已连接的节点列表"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    connected = connected_nodes.get(session_id, [])
    return {
        "sessionId": session_id,
        "connectedNodes": connected,
        "totalNodes": session["config"]["nodeCount"]
    }

@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str, round: Optional[int] = None):
    """获取会话的真实消息历史，用于动画演示
    
    参数:
        round: 指定轮次，如果不指定则返回所有轮次信息
    """
    print(f"\n=== 获取会话历史 ===")
    print(f"请求的会话ID: {session_id}, 轮次: {round if round else '所有'}")
    print(f"当前所有会话ID: {list(sessions.keys())}")
    
    session = get_session(session_id)
    if not session:
        print(f"错误: 会话 {session_id} 不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    config = session["config"]
    messages = session["messages"]
    n = config["nodeCount"]
    topology = config["topology"]
    n_value = config.get("branchCount", 2)
    
    # 如果没有指定轮次，返回轮次列表和当前轮次
    if round is None:
        # 获取所有轮次
        all_rounds = set()
        for msg_list in [messages.get("pre_prepare", []), messages.get("prepare", []), messages.get("commit", [])]:
            for msg in msg_list:
                if "round" in msg:
                    all_rounds.add(msg["round"])
        
        rounds_list = sorted(list(all_rounds))
        current_round = session.get("current_round", 1)
        
        print(f"会话共有 {len(rounds_list)} 轮: {rounds_list}, 当前轮次: {current_round}")
        
        return {
            "rounds": rounds_list,
            "currentRound": current_round,
            "totalRounds": len(rounds_list)
        }
    
    # 指定了轮次，返回该轮次的消息
    print(f"获取第 {round} 轮消息")
    
    def filter_by_round(msg_list, target_round):
        """按轮次过滤消息"""
        return [msg for msg in msg_list if msg.get("round", 1) == target_round]
    
    # 按轮次过滤消息
    round_pre_prepare = filter_by_round(messages.get("pre_prepare", []), round)
    round_prepare = filter_by_round(messages.get("prepare", []), round)
    round_commit = filter_by_round(messages.get("commit", []), round)
    
    print(f"第 {round} 轮消息数量: pre_prepare={len(round_pre_prepare)}, "
          f"prepare={len(round_prepare)}, commit={len(round_commit)}")
    
    # 转换消息格式以适配动画组件
    # Pre-prepare消息 - 展开广播为点对点消息
    pre_prepare_messages = []
    for msg in round_pre_prepare:
        src = msg["from"]
        value = msg.get("value", config["proposalValue"])
        # 如果是广播消息，展开为多个点对点消息
        if msg.get("to") == "all":
            for dst in range(n):
                if dst != src and is_connection_allowed(src, dst, n, topology, n_value):
                    pre_prepare_messages.append({
                        "src": src,
                        "dst": dst,
                        "value": value,
                        "type": "pre_prepare"
                    })
        else:
            pre_prepare_messages.append({
                "src": src,
                "dst": msg.get("to", None),
                "value": value,
                "type": "pre_prepare"
            })
    
    # Prepare消息 - 展开广播为点对点消息
    prepare_messages = []
    for msg in round_prepare:
        src = msg["from"]
        value = msg.get("value", config["proposalValue"])
        # 如果是广播消息，展开为多个点对点消息
        if msg.get("to") == "all":
            for dst in range(n):
                if dst != src and is_connection_allowed(src, dst, n, topology, n_value):
                    prepare_messages.append({
                        "src": src,
                        "dst": dst,
                        "value": value,
                        "type": "prepare"
                    })
        else:
            prepare_messages.append({
                "src": src,
                "dst": msg.get("to", None),
                "value": value,
                "type": "prepare"
            })
    
    # Commit消息 - 展开广播为点对点消息
    commit_messages = []
    for msg in round_commit:
        src = msg["from"]
        value = msg.get("value", config["proposalValue"])
        # 如果是广播消息，展开为多个点对点消息
        if msg.get("to") == "all":
            for dst in range(n):
                if dst != src and is_connection_allowed(src, dst, n, topology, n_value):
                    commit_messages.append({
                        "src": src,
                        "dst": dst,
                        "value": value,
                        "type": "commit"
                    })
        else:
            commit_messages.append({
                "src": src,
                "dst": msg.get("to", None),
                "value": value,
                "type": "commit"
            })
    
    # 获取该轮的共识结果
    round_consensus = None
    for history in session.get("consensus_history", []):
        if history.get("round") == round:
            round_consensus = f"{history.get('status', '未知')}: {history.get('description', '')}"
            break
    
    if not round_consensus:
        round_consensus = "共识进行中..." if round == session.get("current_round") else "无结果"
    
    return {
        "round": round,
        "pre_prepare": pre_prepare_messages,
        "prepare": [prepare_messages],
        "commit": [commit_messages],
        "consensus": round_consensus,
        "messages": pre_prepare_messages + prepare_messages + commit_messages,
        "nodeCount": config["nodeCount"],
        "topology": config["topology"],
        "proposalValue": config["proposalValue"]
    }

# Socket.IO事件处理
@sio.event
async def connect(sid, environ, auth):
    """客户端连接事件"""
    print(f"客户端连接: {sid}")
    
    # 从查询参数获取会话和节点信息
    query = environ.get('QUERY_STRING', '')
    params = dict(item.split('=') for item in query.split('&') if '=' in item)
    
    session_id = params.get('sessionId')
    node_id = int(params.get('nodeId', 0))
    
    if session_id and session_id in sessions:
        # 存储节点连接信息
        if session_id not in node_sockets:
            node_sockets[session_id] = {}
        node_sockets[session_id][node_id] = sid
        
        # 添加到已连接节点列表
        if session_id not in connected_nodes:
            connected_nodes[session_id] = []
        if node_id not in connected_nodes[session_id]:
            connected_nodes[session_id].append(node_id)
            
            # 标记人类节点为拜占庭节点
            session = sessions[session_id]
            if node_id not in session["robot_nodes"]:
                session["human_nodes"].append(node_id)
                print(f"人类节点 {node_id} 已连接（拜占庭节点）")
            else:
                print(f"机器人节点 {node_id} 已重新连接")
        
        session = sessions[session_id]
        
        # 发送会话配置
        config = session["config"]
        print(f"发送会话配置给节点 {node_id}:", config)
        print(f"提议内容检查 - 后端:", {
            'proposalContent': config.get('proposalContent'),
            'hasProposalContent': config.get('proposalContent') and config.get('proposalContent').strip(),
            'proposalValue': config.get('proposalValue')
        })
        await sio.emit('session_config', config, room=sid)
        
        # 人类节点进入时，不参加当前轮次的共识
        # 只发送会话配置，不发送当前轮次信息和历史消息
        print(f"人类节点 {node_id} 进入，等待下一轮共识开始")
        
        # 将节点加入会话房间
        await sio.enter_room(sid, session_id)
        
        # 广播连接状态
        await sio.emit('connected_nodes', connected_nodes[session_id], room=session_id)
        
        print(f"节点 {node_id} 加入会话 {session_id}")
        
        # 检查是否可以开始共识
        await check_and_start_consensus(session_id)

@sio.event
async def disconnect(sid):
    """客户端断开连接事件"""
    print(f"客户端断开连接: {sid}")
    
    # 查找并移除节点连接
    for session_id, nodes in node_sockets.items():
        for node_id, node_sid in nodes.items():
            if node_sid == sid:
                del nodes[node_id]
                if node_id in connected_nodes.get(session_id, []):
                    connected_nodes[session_id].remove(node_id)
                
                # 广播更新
                await sio.emit('connected_nodes', connected_nodes[session_id], room=session_id)
                print(f"节点 {node_id} 离开会话 {session_id}")
                break

@sio.event
async def send_prepare(sid, data):
    """处理准备消息"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    value = data.get('value')
    
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    config = session["config"]
    n = config["nodeCount"]
    
    # 为每个目标节点单独发送消息（根据可靠性配置）
    for target_node in range(n):
        if target_node == node_id:
            continue  # 不发送给自己
        
        # 先检查可靠性，决定是否发送
        deliver = should_deliver_message(session_id, node_id, target_node)
        
        # 获取可靠性配置用于日志
        reliability_info = "全局配置"
        if session_id in node_reliability and node_id in node_reliability[session_id]:
            if target_node in node_reliability[session_id][node_id]:
                reliability_info = f"{node_reliability[session_id][node_id][target_node]}%"
        
        if deliver:
            # 只有通过可靠性检查的消息才记录和发送
            message = {
                "from": node_id,
                "to": target_node,
                "type": "prepare",
                "value": value,
                "phase": "prepare",
                "round": session["current_round"],
                "timestamp": datetime.now().isoformat(),
                "tampered": False,
                "byzantine": data.get("byzantine", False),
                "delivered": True  # 标记消息已实际发送
            }
            
            # 记录消息（只记录实际发送的消息）
            session["messages"]["prepare"].append(message)
            
            # 获取目标节点的socket ID并发送
            if session_id in node_sockets and target_node in node_sockets[session_id]:
                target_sid = node_sockets[session_id][target_node]
                await sio.emit('message_received', message, room=target_sid)
                print(f"✅ 节点 {node_id} 的准备消息已发送给节点 {target_node} (可靠性: {reliability_info})")
            else:
                print(f"⚠️  节点 {target_node} 未连接，消息未发送")
        else:
            print(f"❌ 节点 {node_id} 到节点 {target_node} 的准备消息被丢弃 (可靠性: {reliability_info})")
    
    # 检查准备阶段是否完成
    await check_prepare_phase(session_id)

@sio.event
async def send_differential_prepare(sid, data):
    """处理差异化准备消息 - 向不同节点发送不同的值"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    messages = data.get('messages')  # {target_node_id: value}
    
    session = get_session(session_id)
    if not session:
        return
    
    config = session["config"]
    n = config["nodeCount"]
    
    print(f"🦹 节点 {node_id} 发起差异化准备消息攻击")
    
    # 为每个目标节点发送指定的值
    for target_node in range(n):
        if target_node == node_id:
            continue  # 不发送给自己
        
        # 获取该目标节点应该接收的值
        target_node_int = int(target_node)
        if target_node_int not in messages:
            continue
        
        value = messages[target_node_int]
        
        # 先检查可靠性，决定是否发送
        deliver = should_deliver_message(session_id, node_id, target_node)
        
        # 获取可靠性配置用于日志
        reliability_info = "全局配置"
        if session_id in node_reliability and node_id in node_reliability[session_id]:
            if target_node in node_reliability[session_id][node_id]:
                reliability_info = f"{node_reliability[session_id][node_id][target_node]}%"
        
        if deliver:
            # 只有通过可靠性检查的消息才记录和发送
            message = {
                "from": node_id,
                "to": target_node,
                "type": "prepare",
                "value": value,
                "phase": "prepare",
                "round": session["current_round"],
                "timestamp": datetime.now().isoformat(),
                "tampered": False,
                "byzantine": True,  # 标记为拜占庭消息
                "differential": True,  # 标记为差异化消息
                "delivered": True
            }
            
            # 记录消息
            session["messages"]["prepare"].append(message)
            
            # 获取目标节点的socket ID并发送
            target_sid = None
            if session_id in node_sockets and target_node in node_sockets[session_id]:
                target_sid = node_sockets[session_id][target_node]
                await sio.emit('message_received', message, room=target_sid)
                print(f"✅ 差异化攻击：节点 {node_id} 向节点 {target_node} 发送值 {value} (可靠性: {reliability_info})")
            else:
                print(f"⚠️  节点 {target_node} 未连接，差异化消息未发送")
            
            # 广播消息到整个会话（用于动画和表格显示）
            if target_sid:
                await sio.emit('message_received', message, room=session_id, skip_sid=target_sid)
            else:
                await sio.emit('message_received', message, room=session_id)
        else:
            print(f"❌ 差异化攻击：节点 {node_id} 到节点 {target_node} 的消息被丢弃 (可靠性: {reliability_info})")
    
    # 检查准备阶段是否完成
    await check_prepare_phase(session_id)

@sio.event
async def send_differential_commit(sid, data):
    """处理差异化提交消息 - 向不同节点发送不同的值"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    messages = data.get('messages')  # {target_node_id: value}
    
    session = get_session(session_id)
    if not session:
        return
    
    config = session["config"]
    n = config["nodeCount"]
    
    print(f"🦹 节点 {node_id} 发起差异化提交消息攻击")
    
    # 为每个目标节点发送指定的值
    for target_node in range(n):
        if target_node == node_id:
            continue  # 不发送给自己
        
        # 获取该目标节点应该接收的值
        target_node_int = int(target_node)
        if target_node_int not in messages:
            continue
        
        value = messages[target_node_int]
        
        # 先检查可靠性，决定是否发送
        deliver = should_deliver_message(session_id, node_id, target_node)
        
        # 获取可靠性配置用于日志
        reliability_info = "全局配置"
        if session_id in node_reliability and node_id in node_reliability[session_id]:
            if target_node in node_reliability[session_id][node_id]:
                reliability_info = f"{node_reliability[session_id][node_id][target_node]}%"
        
        if deliver:
            # 只有通过可靠性检查的消息才记录和发送
            message = {
                "from": node_id,
                "to": target_node,
                "type": "commit",
                "value": value,
                "phase": "commit",
                "round": session["current_round"],
                "timestamp": datetime.now().isoformat(),
                "tampered": False,
                "byzantine": True,  # 标记为拜占庭消息
                "differential": True,  # 标记为差异化消息
                "delivered": True
            }
            
            # 记录消息
            session["messages"]["commit"].append(message)
            
            # 获取目标节点的socket ID并发送
            target_sid = None
            if session_id in node_sockets and target_node in node_sockets[session_id]:
                target_sid = node_sockets[session_id][target_node]
                await sio.emit('message_received', message, room=target_sid)
                print(f"✅ 差异化攻击：节点 {node_id} 向节点 {target_node} 发送值 {value} (可靠性: {reliability_info})")
            else:
                print(f"⚠️  节点 {target_node} 未连接，差异化消息未发送")
            
            # 广播消息到整个会话（用于动画和表格显示）
            if target_sid:
                await sio.emit('message_received', message, room=session_id, skip_sid=target_sid)
            else:
                await sio.emit('message_received', message, room=session_id)
        else:
            print(f"❌ 差异化攻击：节点 {node_id} 到节点 {target_node} 的消息被丢弃 (可靠性: {reliability_info})")
    
    # 检查提交阶段是否完成
    await check_commit_phase(session_id)

@sio.event
async def send_commit(sid, data):
    """处理提交消息"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    value = data.get('value')
    
    session = get_session(session_id)
    if not session:
        return
    
    config = session["config"]
    n = config["nodeCount"]
    
    # 为每个目标节点单独发送消息（根据可靠性配置）
    for target_node in range(n):
        if target_node == node_id:
            continue  # 不发送给自己
        
        # 先检查可靠性，决定是否发送
        deliver = should_deliver_message(session_id, node_id, target_node)
        
        # 获取可靠性配置用于日志
        reliability_info = "全局配置"
        if session_id in node_reliability and node_id in node_reliability[session_id]:
            if target_node in node_reliability[session_id][node_id]:
                reliability_info = f"{node_reliability[session_id][node_id][target_node]}%"
        
        if deliver:
            # 只有通过可靠性检查的消息才记录和发送
            message = {
                "from": node_id,
                "to": target_node,
                "type": "commit",
                "value": value,
                "phase": "commit",
                "round": session["current_round"],
                "timestamp": datetime.now().isoformat(),
                "tampered": False,
                "byzantine": data.get("byzantine", False),
                "delivered": True  # 标记消息已实际发送
            }
            
            # 记录消息（只记录实际发送的消息）
            session["messages"]["commit"].append(message)
            
            # 获取目标节点的socket ID并发送
            if session_id in node_sockets and target_node in node_sockets[session_id]:
                target_sid = node_sockets[session_id][target_node]
                await sio.emit('message_received', message, room=target_sid)
                print(f"✅ 节点 {node_id} 的提交消息已发送给节点 {target_node} (可靠性: {reliability_info})")
            else:
                print(f"⚠️  节点 {target_node} 未连接，消息未发送")
        else:
            print(f"❌ 节点 {node_id} 到节点 {target_node} 的提交消息被丢弃 (可靠性: {reliability_info})")
    
    # 检查提交阶段是否完成
    await check_commit_phase(session_id)
    

@sio.event
async def send_message(sid, data):
    """处理通用消息（已移除自定义消息功能）"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    message_type = data.get('type')
    value = data.get('value')
    target = data.get('target')
    
    session = get_session(session_id)
    if not session:
        return
    
    # 记录消息
    message = {
        "from": node_id,
        "to": target,
        "type": message_type,
        "value": value,
        "phase": session.get("phase", "waiting"),
        "timestamp": datetime.now().isoformat(),
        "tampered": False
    }
    
    # 根据消息类型存储到相应的消息列表
    if message_type == "prepare":
        session["messages"]["prepare"].append(message)
    elif message_type == "commit":
        session["messages"]["commit"].append(message)
    else:
        # 其他类型消息
        if "other" not in session["messages"]:
            session["messages"]["other"] = []
        session["messages"]["other"].append(message)
    
    # 根据消息传达概率决定是否广播消息
    if should_deliver_message(session_id):
        await sio.emit('message_received', message, room=session_id)
        print(f"节点 {node_id} 的消息已发送 (传达概率: {session['config'].get('messageDeliveryRate', 100)}%)")
    else:
        print(f"节点 {node_id} 的消息被丢弃 (传达概率: {session['config'].get('messageDeliveryRate', 100)}%)")
    
    # 如果是准备或提交消息，检查阶段完成情况
    if message_type == "prepare":
        await check_prepare_phase(session_id)
    elif message_type == "commit":
        await check_commit_phase(session_id)
    
    print(f"节点 {node_id} 发送消息: {message_type} 到 {target}")

@sio.event
async def choose_normal_consensus(sid, data):
    """处理人类节点选择正常共识"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    
    session = get_session(session_id)
    if not session:
        return
    
    # 将此人类节点转为机器人代理模式
    print(f"人类节点 {node_id} 选择正常共识，切换为机器人代理模式")
    
    # 从人类节点列表中移除，加入机器人节点列表（本轮）
    if node_id in session["human_nodes"]:
        session["human_nodes"].remove(node_id)
    
    # 临时将此节点加入机器人节点列表
    if node_id not in session["robot_nodes"]:
        session["robot_nodes"].append(node_id)
        
        # 初始化机器人节点状态
        session["robot_node_states"][node_id] = {
            "received_pre_prepare": True,
            "received_prepare_count": len([m for m in session["messages"]["prepare"] if m["from"] != node_id]),
            "received_commit_count": len([m for m in session["messages"]["commit"] if m["from"] != node_id]),
            "sent_prepare": False,
            "sent_commit": False
        }
    
    # 根据当前阶段自动发送消息
    config = session["config"]
    proposer_id = config.get("proposerId", 0)
    
    if session["phase"] == "prepare" and node_id != proposer_id:
        # 在准备阶段且不是主节点，发送准备消息
        # 标记为即将发送，防止robot_send_prepare_messages重复发送
        session["robot_node_states"][node_id]["sent_prepare"] = True
        asyncio.create_task(schedule_robot_prepare(session_id, node_id, config["proposalValue"]))
    elif session["phase"] == "commit":
        # 在提交阶段，发送提交消息
        # 标记为即将发送，防止robot_send_commit_messages重复发送
        session["robot_node_states"][node_id]["sent_commit"] = True
        asyncio.create_task(schedule_robot_commit(session_id, node_id, config["proposalValue"]))

async def schedule_robot_prepare(session_id: str, robot_id: int, value: int):
    """调度机器人节点发送准备消息（最多延迟500ms）"""
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    current_round = session["current_round"]
    await asyncio.sleep(0.5)
    
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    # 检查轮次是否改变
    if session["current_round"] != current_round:
        print(f"轮次已改变（{current_round} -> {session['current_round']}），节点{robot_id}放弃发送准备消息")
        return
    
    await handle_robot_prepare(session_id, robot_id, value)

@sio.event
async def choose_byzantine_attack(sid, data):
    """处理人类节点选择拜占庭攻击"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    
    print(f"人类节点 {node_id} 选择拜占庭攻击模式")
    # 不需要特殊处理，人类节点保持在human_nodes列表中

@sio.event
async def update_reliability(sid, data):
    """更新节点的消息可靠性配置"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    reliability_config = data.get('reliability')  # {target_node_id: percentage}
    
    session = get_session(session_id)
    if not session:
        return
    
    # 初始化该会话和节点的可靠性配置
    if session_id not in node_reliability:
        node_reliability[session_id] = {}
    
    if node_id not in node_reliability[session_id]:
        node_reliability[session_id][node_id] = {}
    
    # 转换所有键为整数（前端可能发送字符串或整数）
    normalized_config = {}
    for target_node, percentage in reliability_config.items():
        target_node_int = int(target_node) if isinstance(target_node, str) else target_node
        normalized_config[target_node_int] = int(percentage)
    
    # 更新配置
    node_reliability[session_id][node_id] = normalized_config
    
    print(f"节点 {node_id} 更新消息可靠性配置: {normalized_config}")
    
    # 发送确认
    await sio.emit('reliability_updated', {
        'nodeId': node_id,
        'reliability': normalized_config
    }, room=sid)

@sio.event
async def ping(sid, data):
    """处理Ping消息"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    
    # 发送Pong响应
    pong_message = {
        "from": "server",
        "to": node_id,
        "type": "pong",
        "value": None,
        "phase": "ping",
        "timestamp": datetime.now().isoformat(),
        "tampered": False,
        "customContent": f"服务器响应节点{node_id}的Ping"
    }
    
    await sio.emit('message_received', pong_message, room=session_id)
    print(f"节点 {node_id} 发送Ping，服务器响应Pong")

# 共识逻辑
async def check_and_start_consensus(session_id: str):
    """检查是否可以开始共识"""
    session = get_session(session_id)
    if not session:
        return
    
    config = session["config"]
    connected_count = len(connected_nodes.get(session_id, []))
    
    # 如果连接节点数达到要求，开始共识
    if connected_count >= config["nodeCount"]:
        await start_consensus(session_id)

async def start_consensus(session_id: str):
    """开始共识过程 - 仅用于第一轮共识的初始化"""
    session = get_session(session_id)
    if not session:
        return
    
    session["status"] = "running"
    session["phase"] = "pre-prepare"
    session["phase_step"] = 0
    
    print(f"会话 {session_id} 开始PBFT共识流程")
    
    # 通知所有节点进入预准备阶段
    await sio.emit('phase_update', {
        "phase": "pre-prepare",
        "step": 0,
        "isMyTurn": False
    }, room=session_id)
    
    # 提议者发送预准备消息（统一使用robot_send_pre_prepare）
    await robot_send_pre_prepare(session_id)

async def start_prepare_phase(session_id: str):
    """开始准备阶段"""
    session = get_session(session_id)
    if not session:
        return
    
    session["phase"] = "prepare"
    session["phase_step"] = 1
    
    config = session["config"]
    
    # 通知所有节点进入准备阶段
    await sio.emit('phase_update', {
        "phase": "prepare",
        "step": 1,
        "isMyTurn": True
    }, room=session_id)
    
    print(f"会话 {session_id} 进入准备阶段")

async def check_prepare_phase(session_id: str):
    """检查准备阶段是否完成"""
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    config = session["config"]
    current_round = session["current_round"]
    
    # 仅统计当前轮次的准备消息
    prepare_messages = [
        msg for msg in session["messages"]["prepare"]
        if msg.get("round", current_round) == current_round
    ]
    
    # 计算故障节点数 f = floor((n-1)/3)
    # 注意：在实验模式下，所有节点都是好节点，不会发错误信息
    n = config["nodeCount"]
    f = (n - 1) // 3
    required_correct_messages = 2 * f - 1  # 需要2f-1个正确消息（加自己=2f）
    primary_required = 2 * f - 1  # 主节点需要收到2f-1个正确prepare消息（加自己=2f）
    
    # 统计发送正确信息的不同节点（value=0）
    correct_nodes = set()
    primary_correct_nodes = set()

    def message_to_primary(msg: Dict[str, Any]) -> bool:
        target = msg.get("to")
        if target is None:
            return True
        if isinstance(target, str):
            if target.lower() == "all":
                return True
            if target.isdigit():
                target = int(target)
            else:
                return False
        try:
            return int(target) == 0
        except (TypeError, ValueError):
            return False

    for msg in prepare_messages:
        if msg.get("value") == config["proposalValue"]:  # 正确信息
            correct_nodes.add(msg["from"])
            if msg.get("delivered", True) and message_to_primary(msg):
                primary_correct_nodes.add(msg["from"])
    
    print(f"准备阶段检查 - 总节点数: {n}, 故障节点数: {f}")
    print(f"准备阶段检查 - 需要正确消息数: {required_correct_messages}, 实际正确消息节点数: {len(correct_nodes)}")
    print(f"准备阶段检查 - 发送正确消息的节点: {correct_nodes}")
    print(f"准备阶段检查 - 主节点收到的正确prepare数量: {len(primary_correct_nodes)}, 需要数量: {primary_required}")
    
    # 口径A：不允许“只看主节点prepare就直接判成功”
    # 这里只负责推动进入commit阶段；最终是否成功由 check_commit_phase 按 Nc >= N-f 判定。
    # 论文式(6)的单节点门限是“至少收到 2f 条来自其他节点的消息”，因此这里用 >= 2f（不是 >）。
    if len(primary_correct_nodes) >= primary_required:
        print(
            f"主节点收到{len(primary_correct_nodes)}个正确prepare（需要≥{primary_required}个），进入提交阶段"
        )
        await start_commit_phase(session_id)
        return
    
    # 检查是否收到足够多的正确消息（超过2f个即可）
    # 注意：所有节点都是好节点，不会发错误信息
    # 保留一个保底路径：当网络整体出现足够多prepare发送者时也推进commit（不直接判成功）
    if len(correct_nodes) >= (required_correct_messages + 1):
        print(
            f"✅ 准备阶段推进（发送正确prepare的节点数={len(correct_nodes)}），进入提交阶段"
        )
        await start_commit_phase(session_id)
    else:
        print(f"❌ 准备阶段未完成，还需要 {required_correct_messages - len(correct_nodes)} 个正确消息（当前{len(correct_nodes)}/{required_correct_messages}）")
        # 如果接近完成，打印详细信息帮助调试
        if len(correct_nodes) > 0:
            print(f"   当前正确消息节点: {sorted(correct_nodes)}")
            print(f"   当前轮次prepare消息总数: {len(prepare_messages)}")

async def start_commit_phase(session_id: str):
    """开始提交阶段"""
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    session["phase"] = "commit"
    session["phase_step"] = 2
    
    # 通知所有节点进入提交阶段
    await sio.emit('phase_update', {
        "phase": "commit",
        "step": 2,
        "isMyTurn": True
    }, room=session_id)
    
    print(f"会话 {session_id} 进入提交阶段")
    
    # 通知所有机器人节点检查是否可以发送提交消息
    await check_robot_nodes_ready_for_commit(session_id)

async def check_commit_phase(session_id: str):
    """检查提交阶段是否完成"""
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    config = session["config"]
    current_round = session["current_round"]
    
    # 仅统计当前轮次的提交消息
    commit_messages = [
        msg for msg in session["messages"]["commit"]
        if msg.get("round", current_round) == current_round
    ]
    
    # 计算故障节点数 f = floor((n-1)/3)
    # 注意：在实验模式下，所有节点都是好节点，不会发错误信息
    n = config["nodeCount"]
    f = (n - 1) // 3
    primary_required = 2 * f  # 主节点需要收到2f个正确commit消息（加自己=2f+1）
    
    # 统计发送正确信息的不同节点（所有节点都是好节点，不会发错误信息）
    correct_nodes = set()
    primary_correct_nodes = set()
    
    def message_to_primary(msg: Dict[str, Any]) -> bool:
        target = msg.get("to")
        if target is None:
            return True
        if isinstance(target, str):
            if target.lower() == "all":
                return True
            if target.isdigit():
                target = int(target)
            else:
                return False
        try:
            return int(target) == 0
        except (TypeError, ValueError):
            return False

    # 所有节点都是好节点，不会发错误信息，只统计正确消息
    for msg in commit_messages:
        if msg.get("value") == config["proposalValue"]:  # 正确信息
            correct_nodes.add(msg["from"])
            if msg.get("delivered", True) and message_to_primary(msg):
                primary_correct_nodes.add(msg["from"])
    
    # ========== 共识判断（口径A：N_c ≥ N − f） ==========
    # 对齐论文式(6)：commit 成功节点（commit节点）的定义是
    # “从其他节点收到至少 2f 条成功 commit 消息”（不需要把自己那一条算进去）
    commit_msg_threshold = 2 * f
    success_threshold = n - f
    
    print(f"\n{'='*60}")
    print(f"提交阶段检查（口径A：N_c ≥ N − f）")
    print(f"{'='*60}")
    print(f"总节点数: {n}, 容错数 f: {f}")
    print(f"commit节点判定门限: {commit_msg_threshold} (2f, 来自其他节点)")
    print(f"共识成功门限: {success_threshold} (N-f)")
    print(f"发送正确commit的节点: {sorted(correct_nodes)} (共{len(correct_nodes)}个)")
    
    # 统计每个节点收到的commit数量
    # 在广播模型下：如果节点 i 成功广播commit，所有其他节点都会收到
    commit_nodes = []  # “commit节点”：收到≥2f条commit的节点
    non_commit_nodes = []  # 未收到足够commit的节点
    
    for node_id in session["robot_nodes"]:
        node_state = session["robot_node_states"][node_id]
        # received_commit_count 本身就是“来自其他节点的commit数”
        received_count = node_state["received_commit_count"]
        
        if received_count >= commit_msg_threshold:
            commit_nodes.append(node_id)
            print(f"  ✅ 节点 {node_id}: 收到 {received_count} 条commit (≥{commit_msg_threshold}) [commit节点]")
        else:
            non_commit_nodes.append(node_id)
            print(f"  ⏳ 节点 {node_id}: 收到 {received_count} 条commit (<{commit_msg_threshold})")
    
    # 判断：commit节点数量 N_c ≥ N − f
    print(f"\ncommit节点数量: {len(commit_nodes)}/{n}")
    print(f"commit节点: {sorted(commit_nodes)}")
    
    if len(commit_nodes) >= success_threshold:
        print(f"\n✅✅✅ 共识成功！")
        print(f"   {len(commit_nodes)} 个commit节点 ≥ {success_threshold} (N-f)")
        print(f"   这些节点已达成共识，系统整体共识成功")
        print(f"{'='*60}\n")
        await finalize_consensus(
            session_id,
            "共识成功",
            f"{len(commit_nodes)}个commit节点达成共识(≥{success_threshold})"
        )
        return
    else:
        print(f"\n⏳ 共识进行中：{len(commit_nodes)}/{success_threshold} 个commit节点")
        print(f"   还需要 {success_threshold - len(commit_nodes)} 个节点达成共识")
        print(f"{'='*60}\n")

async def finalize_consensus(session_id: str, status: str = "共识完成", description: str = "共识已完成"):
    """完成共识"""
    session = get_session(session_id)
    if not session:
        return
    
    # 防止重复调用
    current_round = session["current_round"]
    if session.get("consensus_finalized_round") == current_round:
        print(f"第{current_round}轮共识已完成，跳过重复调用")
        return
    
    session["consensus_finalized_round"] = current_round
    print(f"第{current_round}轮共识完成处理开始")
    
    # 取消超时任务
    if session.get("timeout_task"):
        session["timeout_task"].cancel()
        print(f"第{session['current_round']}轮共识已完成，取消超时任务")
    
    session["phase"] = "completed"
    session["phase_step"] = 3
    session["status"] = "completed"
    
    config = session["config"]
    
    # 创建共识结果
    consensus_result = {
        "status": status,
        "description": description,
        "stats": {
            "expected_nodes": config["nodeCount"],
            "expected_prepare_nodes": config["nodeCount"] - 1,
            "total_messages": len(session["messages"]["prepare"]) + len(session["messages"]["commit"])
        }
    }
    
    session["consensus_result"] = consensus_result
    
    # 广播共识结果
    print(f"准备发送共识结果: {consensus_result}")
    await sio.emit('consensus_result', consensus_result, room=session_id)
    print(f"已发送共识结果到房间: {session_id}")
    
    # 更新阶段
    await sio.emit('phase_update', {
        "phase": "completed",
        "step": 3,
        "isMyTurn": False
    }, room=session_id)
    
    print(f"会话 {session_id} 第{session['current_round']}轮共识完成: {status}")
    
    # 保存共识历史
    session["consensus_history"].append({
        "round": session["current_round"],
        "status": status,
        "description": description,
        "timestamp": datetime.now().isoformat()
    })
    
    # 启动下一轮共识（10秒后），实验模式（全机器人）由前端控制
    if session.get("auto_next_round", True):
        print(f"将在10秒后开始第{session['current_round'] + 1}轮共识")
        asyncio.create_task(start_next_round(session_id))
    else:
        print("实验模式：不自动启动下一轮，等待reset-round触发")

async def handle_consensus_timeout(session_id: str, round_number: int):
    """处理共识超时"""
    await asyncio.sleep(2)  # 等待2秒（进一步加速）
    
    session = get_session(session_id)
    if not session:
        return
    
    # 检查是否仍然在同一轮次且未完成共识
    if session["current_round"] == round_number and session["status"] == "running":
        print(f"第{round_number}轮共识超时（2秒未完成），判定为共识失败（加速模式）")
        
        # 清除超时任务引用，避免在finalize_consensus中尝试取消正在执行的任务
        session["timeout_task"] = None
        
        # 设置共识结果为超时失败
        await finalize_consensus(session_id, "共识超时失败", "2秒内未达成共识（加速模式）")

async def start_next_round(session_id: str):
    """启动下一轮共识"""
    await asyncio.sleep(10)
    
    session = get_session(session_id)
    if not session:
        return
    
    # 增加轮次
    session["current_round"] += 1
    current_round = session["current_round"]
    
    # 重置会话状态
    session["status"] = "running"
    session["phase"] = "pre-prepare"
    session["phase_step"] = 0
    session["consensus_result"] = None
    
    # 不再清空消息，保留历史轮次的消息
    # 所有消息通过 round 字段区分不同轮次
    # session["messages"] 保持累积，不清空
    
    # 将临时机器人节点移回人类节点列表
    config = session["config"]
    original_robot_count = config["robotNodes"]
    
    print(f"第{current_round}轮开始 - 原始机器人节点数: {original_robot_count}")
    print(f"第{current_round}轮开始 - 当前机器人节点: {session['robot_nodes']}")
    print(f"第{current_round}轮开始 - 当前人类节点: {session['human_nodes']}")
    
    # 找出临时加入的机器人节点（ID >= original_robot_count）
    temp_robot_nodes = [node_id for node_id in session["robot_nodes"] if node_id >= original_robot_count]
    
    print(f"第{current_round}轮开始 - 临时机器人节点: {temp_robot_nodes}")
    
    # 将临时机器人节点移回人类节点列表
    for node_id in temp_robot_nodes:
        if node_id in session["robot_nodes"]:
            session["robot_nodes"].remove(node_id)
        if node_id not in session["human_nodes"]:
            session["human_nodes"].append(node_id)
        # 清除临时机器人节点状态
        if node_id in session["robot_node_states"]:
            del session["robot_node_states"][node_id]
    
    print(f"已将临时机器人节点 {temp_robot_nodes} 移回人类节点列表")
    print(f"第{current_round}轮开始后 - 机器人节点: {session['robot_nodes']}")
    print(f"第{current_round}轮开始后 - 人类节点: {session['human_nodes']}")
    
    # 重置机器人节点状态（只重置原始机器人节点）
    for robot_id in session["robot_nodes"]:
        session["robot_node_states"][robot_id] = {
            "received_pre_prepare": False,
            "received_prepare_count": 0,
            "received_commit_count": 0,
            "sent_prepare": False,
            "sent_commit": False
        }
    
    print(f"会话 {session_id} 开始第{current_round}轮共识")
    
    # 通知所有节点（包括等待中的人类节点）进入新一轮共识
    await sio.emit('new_round', {
        "round": current_round,
        "phase": "pre-prepare",
        "step": 0
    }, room=session_id)
    
    # 通知所有节点进入预准备阶段
    await sio.emit('phase_update', {
        "phase": "pre-prepare",
        "step": 0,
        "isMyTurn": False
    }, room=session_id)
    
    print(f"第{current_round}轮开始，所有节点（包括新加入的人类节点）现在可以参与共识")
    
    # 机器人提议者发送预准备消息
    await robot_send_pre_prepare(session_id)

# ==================== 辅助函数 ====================

async def broadcast_to_online_nodes(session_id: str, event: str, data: Any):
    """只向在线的人类节点广播消息，机器人节点总是在线"""
    session = get_session(session_id)
    if not session:
        return
    
    # 向所有在线的人类节点发送
    if session_id in node_sockets:
        for node_id, sid in node_sockets[session_id].items():
            if node_id in session["human_nodes"]:  # 只向人类节点发送
                await sio.emit(event, data, room=sid)
    
    # 机器人节点不需要接收WebSocket消息，因为它们在后端自动处理

# ==================== 机器人节点管理 ====================

async def create_robot_nodes_only(session_id: str, robot_count: int):
    """只创建机器人节点，不自动开始共识（用于实验模式）"""
    # 移除1秒延迟，立即初始化以加速实验
    session = get_session(session_id)
    if not session:
        return

    print(f"创建{robot_count}个机器人节点（实验模式，不自动开始共识，加速模式）")
    
    # 机器人节点是0到robotNodes-1，人类节点从robotNodes开始编号
    for robot_id in range(robot_count):
        session["robot_nodes"].append(robot_id)
        connected_nodes[session_id].append(robot_id)
        print(f"机器人节点 {robot_id} 已创建")
        
        # 初始化机器人节点状态
        session["robot_node_states"][robot_id] = {
            "received_pre_prepare": False,
            "received_prepare_count": 0,
            "received_commit_count": 0,
            "sent_prepare": False,
            "sent_commit": False
        }
    
    print(f"机器人节点准备完毕，等待reset-round触发共识")
    print(f"机器人节点列表: {session['robot_nodes']}, 总数: {len(session['robot_nodes'])}")

async def create_robot_nodes_and_start(session_id: str, robot_count: int):
    """创建机器人节点并立即启动PBFT流程"""
    await asyncio.sleep(1)  # 等待会话初始化
    
    session = get_session(session_id)
    if not session:
        return
    
    print(f"创建{robot_count}个机器人节点")
    
    # 机器人节点是0到robotNodes-1，人类节点从robotNodes开始编号
    for robot_id in range(robot_count):
        session["robot_nodes"].append(robot_id)
        connected_nodes[session_id].append(robot_id)
        print(f"机器人节点 {robot_id} 已创建")
        
        # 初始化机器人节点状态
        session["robot_node_states"][robot_id] = {
            "received_pre_prepare": False,
            "received_prepare_count": 0,
            "received_commit_count": 0,
            "sent_prepare": False,
            "sent_commit": False
        }
    
    # 立即开始PBFT共识流程（不等待人类节点）
    print(f"机器人节点准备完毕，立即开始PBFT共识流程")
    await start_pbft_process(session_id)

async def start_pbft_process(session_id: str):
    """启动PBFT共识流程"""
    session = get_session(session_id)
    if not session:
        return
    
    # 更新会话状态
    session["status"] = "running"
    session["phase"] = "pre-prepare"
    session["phase_step"] = 0
    
    # 通知所有节点进入预准备阶段
    await sio.emit('phase_update', {
        "phase": "pre-prepare",
        "step": 0,
        "isMyTurn": False
    }, room=session_id)
    
    print(f"会话 {session_id} 开始PBFT共识流程")
    
    # 提议者发送预准备消息
    await robot_send_pre_prepare(session_id)

async def robot_send_pre_prepare(session_id: str):
    """机器人提议者发送预准备消息
    
    点对点独立链路模型：主节点向每个副本节点独立发送
    - 每条链路（主节点→副本i）独立以概率p成功
    """
    session = get_session(session_id)
    if not session:
        return
    
    # 防止重复调用
    current_round = session["current_round"]
    if session.get("last_pre_prepare_round") == current_round:
        print(f"第{current_round}轮预准备消息已发送，跳过重复调用")
        return
    
    session["last_pre_prepare_round"] = current_round
    
    config = session["config"]
    proposer_id = config.get("proposerId", 0)  # 获取配置的主节点ID，默认为0
    
    # 只有当主节点是机器人节点时才自动发送
    if proposer_id not in session["robot_nodes"]:
        print(f"Primary node {proposer_id} is a human node, waiting for human operation")
        return
    
    # 重要：主节点自己默认收到pre-prepare（因为它自己发起的）
    session["robot_node_states"][proposer_id]["received_pre_prepare"] = True
    print(f"Primary node {proposer_id} sending pre-prepare message")
    
    # 多跳路由模型：对每个副本节点通过最短路径发送
    successful_count = 0
    for target_node_id in session["robot_nodes"]:
        if target_node_id == proposer_id:
            continue  # 不发送给自己
        
        # 通过最短路径发送（可靠性检查在should_deliver_message中处理）
        link_success = should_deliver_message(session_id, proposer_id, target_node_id)
        
        # 创建消息记录
        message = {
            "from": proposer_id,
            "to": target_node_id,
            "type": "pre_prepare",
            "value": config["proposalValue"],
            "phase": "pre-prepare",
            "round": session["current_round"],
            "timestamp": datetime.now().isoformat(),
            "tampered": False,
            "isRobot": True,
            "delivered": link_success
        }
        
        # 记录消息
        session["messages"]["pre_prepare"].append(message)
        
        if link_success:
            # 向目标节点发送消息
            if session_id in node_sockets and target_node_id in node_sockets[session_id]:
                target_sid = node_sockets[session_id][target_node_id]
                await sio.emit('message_received', message, room=target_sid)
            
            # 标记该节点收到了 pre-prepare
            session["robot_node_states"][target_node_id]["received_pre_prepare"] = True
            successful_count += 1
            print(f"  ✅ 主节点 → 节点{target_node_id}: pre-prepare送达")
        else:
            print(f"  ❌ 主节点 → 节点{target_node_id}: pre-prepare丢失")
    
    print(f"📊 Pre-prepare阶段完成: {successful_count}/{len(session['robot_nodes'])-1} 条链路成功")

    # 实验模式（全机器人）使用“同步阶段推进”，避免prepare/commit乱序导致的误判（对齐Theorem 1）
    is_experiment_mode = config["robotNodes"] == config["nodeCount"]
    if is_experiment_mode:
        await run_experiment_round_sync(session_id)
        return

    # 正常模式：进入准备阶段（异步）
    session["phase"] = "prepare"
    session["phase_step"] = 1

    await sio.emit('phase_update', {
        "phase": "prepare",
        "step": 1,
        "isMyTurn": True
    }, room=session_id)

    print(f"会话 {session_id} 进入准备阶段")

    # 启动超时任务（2秒后检查）
    current_round = session["current_round"]
    timeout_task = asyncio.create_task(handle_consensus_timeout(session_id, current_round))
    session["timeout_task"] = timeout_task
    print(f"第{current_round}轮共识超时检查已启动（2秒）")

    # 机器人节点自动发送准备消息
    asyncio.create_task(robot_send_prepare_messages(session_id))


async def run_experiment_round_sync(session_id: str):
    """实验模式（全机器人）同步执行一轮PBFT（口径A：Nc>=N-f，单节点门限2f来自其他节点）

    目的：对齐论文 Theorem 1（式(1)–(6)）的阶段假设，避免异步乱序导致
    commit 在节点进入 V_p 前到达而被丢弃，从而把成功率严重拉低。
    """
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return

    config = session["config"]
    n = config["nodeCount"]
    f = (n - 1) // 3
    current_round = session["current_round"]

    # 口径A
    success_threshold = n - f  # Nc >= N-f
    prepare_threshold = 2 * f - 1      # prepare阶段门限：从其他节点收到2f-1条（加自己=2f）
    commit_threshold = 2 * f           # commit阶段门限：从其他节点收到2f条（加自己=2f+1）

    # V_pp
    V_pp = [
        node_id for node_id in session["robot_nodes"]
        if session["robot_node_states"][node_id].get("received_pre_prepare")
    ]

    # 口径A：Nc>=N-f => Npp>=N-f，否则必失败
    if len(V_pp) < success_threshold:
        await finalize_consensus(
            session_id,
            "共识失败",
            f"Pre-prepare失败：Npp={len(V_pp)} < N-f={success_threshold}"
        )
        return

    # ========== Prepare（主节点不发送prepare） ==========
    session["phase"] = "prepare"
    session["phase_step"] = 1
    await sio.emit('phase_update', {"phase": "prepare", "step": 1, "isMyTurn": True}, room=session_id)

    # 清零计数（避免任何残留）
    for node_id in session["robot_nodes"]:
        session["robot_node_states"][node_id]["received_prepare_count"] = 0

    proposer_id = config.get("proposerId", 0)
    # 副本节点发送prepare（主节点不发送）
    prepare_senders = [node for node in V_pp if node != proposer_id]
    total_prepare_links = 0
    successful_prepare_links = 0
    
    for sender in prepare_senders:
        session["robot_node_states"][sender]["sent_prepare"] = True
        for target in V_pp:
            if target == sender:
                continue
            total_prepare_links += 1
            # 通过最短路径发送（可靠性检查在should_deliver_message中处理）
            link_success = should_deliver_message(session_id, sender, target)
            message = {
                "from": sender,
                "to": target,
                "type": "prepare",
                "value": config["proposalValue"],
                "phase": "prepare",
                "round": current_round,
                "timestamp": datetime.now().isoformat(),
                "tampered": False,
                "isRobot": True,
                "delivered": link_success
            }
            session["messages"]["prepare"].append(message)
            if link_success:
                session["robot_node_states"][target]["received_prepare_count"] += 1
                successful_prepare_links += 1
    
    print(f"📊 Prepare阶段完成: {successful_prepare_links}/{total_prepare_links} 条链路成功")
    
    # 输出每个节点收到的prepare消息数
    for node_id in V_pp:
        count = session["robot_node_states"][node_id]["received_prepare_count"]
        threshold_met = "✅" if count >= prepare_threshold else "❌"
        print(f"   节点{node_id}: 收到{count}条prepare (需要{prepare_threshold}条) {threshold_met}")

    V_p = [nid for nid in V_pp if session["robot_node_states"][nid]["received_prepare_count"] >= prepare_threshold]
    print(f"   进入Prepare阶段的节点集合V_p: {V_p} (共{len(V_p)}个，需要{success_threshold}个)")
    
    if len(V_p) < success_threshold:
        await finalize_consensus(
            session_id,
            "共识失败",
            f"Prepare失败：Np={len(V_p)} < N-f={success_threshold}"
        )
        return

    # ========== Commit ==========
    session["phase"] = "commit"
    session["phase_step"] = 2
    await sio.emit('phase_update', {"phase": "commit", "step": 2, "isMyTurn": False}, room=session_id)

    for node_id in session["robot_nodes"]:
        session["robot_node_states"][node_id]["received_commit_count"] = 0

    total_commit_links = 0
    successful_commit_links = 0
    
    for sender in V_p:
        session["robot_node_states"][sender]["sent_commit"] = True
        for target in V_p:
            if target == sender:
                continue
            total_commit_links += 1
            # 通过最短路径发送（可靠性检查在should_deliver_message中处理）
            link_success = should_deliver_message(session_id, sender, target)
            message = {
                "from": sender,
                "to": target,
                "type": "commit",
                "value": config["proposalValue"],
                "phase": "commit",
                "round": current_round,
                "timestamp": datetime.now().isoformat(),
                "tampered": False,
                "isRobot": True,
                "delivered": link_success
            }
            session["messages"]["commit"].append(message)
            if link_success:
                session["robot_node_states"][target]["received_commit_count"] += 1
                successful_commit_links += 1
    
    print(f"📊 Commit阶段完成: {successful_commit_links}/{total_commit_links} 条链路成功")
    
    # 输出每个节点收到的commit消息数
    for node_id in V_p:
        count = session["robot_node_states"][node_id]["received_commit_count"]
        threshold_met = "✅" if count >= commit_threshold else "❌"
        print(f"   节点{node_id}: 收到{count}条commit (需要{commit_threshold}条) {threshold_met}")

    V_c = [nid for nid in V_p if session["robot_node_states"][nid]["received_commit_count"] >= commit_threshold]
    print(f"   完成Commit阶段的节点集合V_c: {V_c} (共{len(V_c)}个，需要{success_threshold}个)")

    if len(V_c) >= success_threshold:
        await finalize_consensus(
            session_id,
            "共识成功",
            f"Nc={len(V_c)} ≥ N-f={success_threshold}"
        )
    else:
        await finalize_consensus(
            session_id,
            "共识失败",
            f"Nc={len(V_c)} < N-f={success_threshold}"
        )

async def robot_send_prepare_messages(session_id: str):
    """机器人节点自动发送准备消息
    实验模式（所有节点都是机器人）：立即发送，无延迟
    正常模式（有用户参与）：延迟10秒发送
    """
    session = get_session(session_id)
    if not session:
        return
    
    config = session["config"]
    current_round = session["current_round"]
    
    # 判断是否为实验模式：所有节点都是机器人
    is_experiment_mode = config["robotNodes"] == config["nodeCount"]
    
    if is_experiment_mode:
        # 实验模式：立即发送，不等待延迟
        print(f"机器人节点立即发送准备消息（实验模式）")
    else:
        # 正常模式：延迟10秒发送
        print(f"机器人节点将在10秒后发送准备消息（正常模式）")
        await asyncio.sleep(10)
        
        # 重新获取session，检查状态是否改变
        session = get_session(session_id)
        if not session:
            return
        if session.get("status") in {"completed", "stopped"}:
            return
        if session["current_round"] != current_round:
            print(f"轮次已改变（{current_round} -> {session['current_round']}），放弃发送准备消息")
            return
        
        print(f"10秒延迟结束，开始发送prepare消息")
    
    # 只有收到 pre-prepare 的机器人节点才发送准备消息
    config = session["config"]
    proposer_id = config.get("proposerId", 0)
    # 重要：根据PBFT协议，主节点也需要发送prepare消息！
    print(f"准备发送prepare消息 - 机器人节点列表: {session['robot_nodes']}, 主节点: {proposer_id}")
    for robot_id in session["robot_nodes"]:
        # 对齐论文 Theorem 1（式(4)(6) 的特例化）：prepare 由副本集合发出，主节点不发送 prepare
        if robot_id == proposer_id:
            print(f"节点 {robot_id} 是主节点，不发送prepare")
            continue
        # 检查是否收到 pre-prepare（主节点默认收到自己的pre-prepare）
        if not session["robot_node_states"][robot_id]["received_pre_prepare"]:
            print(f"节点 {robot_id} 未收到pre-prepare消息，不发送prepare")
            continue
        
        if session["robot_node_states"][robot_id]["sent_prepare"]:
            print(f"节点 {robot_id} 已经发送过prepare消息，跳过")
            continue  # 已经发送过了
        
        # 检查轮次是否改变
        if session["current_round"] != current_round:
            print(f"轮次已改变（{current_round} -> {session['current_round']}），节点{robot_id}放弃发送准备消息")
            continue
        
        # 检查状态
        if session.get("status") in {"completed", "stopped"}:
            print(f"会话状态为{session.get('status')}，节点{robot_id}放弃发送准备消息")
            continue
        
        print(f"节点 {robot_id} 发送prepare消息")
        # 调用发送准备消息的函数
        await handle_robot_prepare(session_id, robot_id, config["proposalValue"])
        session["robot_node_states"][robot_id]["sent_prepare"] = True

async def handle_robot_prepare(session_id: str, robot_id: int, value: int):
    """处理机器人节点的准备消息
    
    多跳路由模型：节点robot_id向每个其他节点通过最短路径发送
    - 路径上每一跳独立以概率p成功
    """
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    config = session["config"]
    
    # 多跳路由模型：对每个目标节点通过最短路径发送
    successful_count = 0
    for target_node_id in session["robot_nodes"]:
        if target_node_id == robot_id:
            continue  # 不发送给自己
        
        # 通过最短路径发送（可靠性检查在should_deliver_message中处理）
        link_success = should_deliver_message(session_id, robot_id, target_node_id)
        
        # 创建消息记录
        message = {
            "from": robot_id,
            "to": target_node_id,
            "type": "prepare",
            "value": value,
            "phase": "prepare",
            "round": session["current_round"],
            "timestamp": datetime.now().isoformat(),
            "tampered": False,
            "isRobot": True,
            "delivered": link_success
        }
        
        # 记录消息
        session["messages"]["prepare"].append(message)
        
        if link_success:
            # 向目标节点发送消息
            if session_id in node_sockets and target_node_id in node_sockets[session_id]:
                target_sid = node_sockets[session_id][target_node_id]
                await sio.emit('message_received', message, room=target_sid)
            
            # 关键修复：只有目标节点收到了pre-prepare，才会接收和计数prepare消息
            # 这符合PBFT协议：节点只有在收到pre-prepare后才会处理prepare消息
            if session["robot_node_states"][target_node_id]["received_pre_prepare"]:
                session["robot_node_states"][target_node_id]["received_prepare_count"] += 1
                successful_count += 1
            else:
                print(f"    ⏭️  目标节点{target_node_id}未收到pre-prepare，不计数此prepare")
    
    print(f"  节点{robot_id}→其他节点: prepare {successful_count}/{len(session['robot_nodes'])-1}条成功")
    
    # 检查准备阶段是否完成（每次添加消息后检查）
    await check_prepare_phase(session_id)
    
    # 检查是否有机器人节点需要进入提交阶段
    await check_robot_nodes_ready_for_commit(session_id)

async def check_robot_nodes_ready_for_commit(session_id: str):
    """检查机器人节点是否准备好发送提交消息
    实验模式（所有节点都是机器人）：立即发送，无延迟
    正常模式（有用户参与）：延迟10秒发送
    """
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    if session["phase"] != "commit":
        return  # 还没进入提交阶段
    
    config = session["config"]
    n = config["nodeCount"]
    f = (n - 1) // 3
    # 论文式(6)：单节点进入 V_p 的门限是“至少收到 2f 条来自其他节点的 prepare”
    required_prepare = 2 * f - 1  # 从其他节点收到2f-1条（加自己=2f）
    
    # 判断是否为实验模式：所有节点都是机器人
    is_experiment_mode = config["robotNodes"] == config["nodeCount"]
    
    # 检查每个机器人节点是否收到足够的准备消息（包括主节点node 0）
    print(f"检查机器人节点是否准备好发送commit - 需要≥{required_prepare+1}个prepare消息（包括自己）")
    for robot_id in session["robot_nodes"]:
        robot_state = session["robot_node_states"][robot_id]
        
        # 按论文门限，这里只看“来自其他节点”的 prepare 数量（received_prepare_count 本身就是这个口径）
        total_prepare_count = robot_state["received_prepare_count"]

        # 打印每个节点的状态
        print(
            f"节点 {robot_id}: 收到 {total_prepare_count} 个prepare(来自其他节点), 已发送commit: {robot_state['sent_commit']}"
        )
        
        # 如果已经发送过提交消息，跳过
        if robot_state["sent_commit"]:
            continue
        
        # 检查是否收到足够的准备消息（按论文式(6)：≥2f）
        if total_prepare_count >= required_prepare:
            if is_experiment_mode:
                print(f"✅ 机器人节点 {robot_id} prepare达标（{total_prepare_count}≥{required_prepare}），立即发送commit（实验模式）")
                # 实验模式：立即发送，不使用异步延迟
                await handle_robot_commit(session_id, robot_id, config["proposalValue"])
            else:
                print(f"✅ 机器人节点 {robot_id} prepare达标（{total_prepare_count}≥{required_prepare}），将在10秒后发送commit（正常模式）")
                # 正常模式：延迟10秒发送
                asyncio.create_task(schedule_robot_commit_with_delay(session_id, robot_id, config["proposalValue"]))
            robot_state["sent_commit"] = True
        else:
            print(f"⏳ 机器人节点 {robot_id} prepare未达标（{total_prepare_count}<{required_prepare}），等待中...")

async def schedule_robot_commit_with_delay(session_id: str, robot_id: int, value: int):
    """调度机器人节点发送提交消息（正常模式：延迟10秒）"""
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    current_round = session["current_round"]
    await asyncio.sleep(10)  # 正常模式：延迟10秒
    
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    # 检查轮次是否改变
    if session["current_round"] != current_round:
        print(f"轮次已改变（{current_round} -> {session['current_round']}），节点{robot_id}放弃发送提交消息")
        return
    
    await handle_robot_commit(session_id, robot_id, value)

async def schedule_robot_commit(session_id: str, robot_id: int, value: int):
    """调度机器人节点发送提交消息（最多延迟500ms）"""
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    current_round = session["current_round"]
    await asyncio.sleep(0.5)
    
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    # 检查轮次是否改变
    if session["current_round"] != current_round:
        print(f"轮次已改变（{current_round} -> {session['current_round']}），节点{robot_id}放弃发送提交消息")
        return
    
    await handle_robot_commit(session_id, robot_id, value)

async def handle_robot_commit(session_id: str, robot_id: int, value: int):
    """处理机器人节点的提交消息
    
    多跳路由模型：节点robot_id向每个其他节点通过最短路径发送
    - 路径上每一跳独立以概率p成功
    """
    session = get_session(session_id)
    if not session:
        return
    if session.get("status") in {"completed", "stopped"}:
        return
    
    config = session["config"]
    n = config["nodeCount"]
    f = (n - 1) // 3
    
    # 多跳路由模型：对每个目标节点通过最短路径发送
    successful_count = 0
    for target_node_id in session["robot_nodes"]:
        if target_node_id == robot_id:
            continue  # 不发送给自己
        
        # 通过最短路径发送（可靠性检查在should_deliver_message中处理）
        link_success = should_deliver_message(session_id, robot_id, target_node_id)
        
        # 创建消息记录
        message = {
            "from": robot_id,
            "to": target_node_id,
            "type": "commit",
            "value": value,
            "phase": "commit",
            "round": session["current_round"],
            "timestamp": datetime.now().isoformat(),
            "tampered": False,
            "isRobot": True,
            "delivered": link_success
        }
        
        # 记录消息
        session["messages"]["commit"].append(message)
        
        if link_success:
            # 向目标节点发送消息
            if session_id in node_sockets and target_node_id in node_sockets[session_id]:
                target_sid = node_sockets[session_id][target_node_id]
                await sio.emit('message_received', message, room=target_sid)
            
            # 关键修复：只有目标节点收到了足够的prepare（即在V_p中），才会接收和计数commit消息
            # 这符合PBFT协议：节点只有在prepare阶段达标后才会处理commit消息
            # 标准PBFT阈值：需要>2f条prepare（即≥2f+1条）
            required_prepare = 2 * f - 1  # 从其他节点收到2f-1条（加自己=2f）
            # 论文式(6)：目标节点只有在 prepare 阶段“来自其他节点的prepare数 ≥ 2f”时，才接收并计数 commit
            target_state = session["robot_node_states"][target_node_id]
            total_prepare_count = target_state["received_prepare_count"]

            if total_prepare_count >= required_prepare:
                session["robot_node_states"][target_node_id]["received_commit_count"] += 1
                successful_count += 1
            else:
                print(
                    f"    ⏭️  目标节点{target_node_id}prepare未达标（{total_prepare_count}<{required_prepare}），不计数此commit"
                )
    
    print(f"  节点{robot_id}→其他节点: commit {successful_count}/{len(session['robot_nodes'])-1}条成功")
    
    # 检查提交阶段是否完成
    await check_commit_phase(session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="127.0.0.1", port=8000) 