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

# 会话管理
def create_session(config: SessionConfig) -> SessionInfo:
    session_id = str(uuid.uuid4())
    
    print(f"创建会话 - 原始配置:", config.dict())
    print(f"提议内容检查 - 创建时:", {
        'proposalContent': config.proposalContent,
        'hasProposalContent': config.proposalContent and config.proposalContent.strip(),
        'proposalValue': config.proposalValue
    })
    
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
        "node_states": {},
        "consensus_result": None,
        "consensus_history": [],  # 共识历史记录
        "created_at": datetime.now().isoformat()
    }
    
    sessions[session_id] = session
    connected_nodes[session_id] = []
    node_sockets[session_id] = {}
    
    # 创建机器人节点并立即开始共识
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

def is_connection_allowed(i: int, j: int, n: int, topology: str, n_value: int) -> bool:
    """检查两个节点之间是否允许连接"""
    if i == j:
        return False
    if topology == "full":
        return True
    elif topology == "ring":
        return j == (i + 1) % n or j == (i - 1) % n
    elif topology == "star":
        return i == 0 or j == 0
    elif topology == "tree":
        parent = (j - 1) // n_value
        return i == parent and j < n
    return False

def is_honest(node_id: int, n: int, m: int, faulty_proposer: bool) -> bool:
    """判断节点是否为诚实节点"""
    if m == 0:
        return True
    if faulty_proposer:
        if node_id == 0:
            return False
        return node_id <= n - m
    else:
        if node_id == 0:
            return True
        return node_id < n - m

def should_deliver_message(session_id: str) -> bool:
    """根据消息传达概率决定是否发送消息"""
    session = get_session(session_id)
    if not session:
        return True
    
    delivery_rate = session["config"].get("messageDeliveryRate", 100)
    if delivery_rate >= 100:
        return True
    
    # 生成随机数，如果小于传达概率则发送消息
    return random.random() * 100 < delivery_rate

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
    
    return {
        "sessionId": session_id,
        "status": session["status"],
        "phase": session["phase"],
        "connectedNodes": len(connected_nodes.get(session_id, [])),
        "totalNodes": session["config"]["nodeCount"]
    }

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
        raise HTTPException(status_code=409, detail="所有节点已被占用")
    
    return {
        "nodeId": available_node,
        "sessionId": session_id,
        "role": "提议者" if available_node == 0 else "验证者",
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
    
    # 记录消息
    message = {
        "from": node_id,
        "to": "all",
        "type": "prepare",
        "value": value,
        "phase": "prepare",
        "round": session["current_round"],  # 添加轮次信息
        "timestamp": datetime.now().isoformat(),
        "tampered": False,
        "byzantine": data.get("byzantine", False)  # 标记是否为拜占庭攻击消息
    }
    
    session["messages"]["prepare"].append(message)
    
    # 根据消息传达概率决定是否广播消息
    if should_deliver_message(session_id):
        await sio.emit('message_received', message, room=session_id)
        print(f"节点 {node_id} 的准备消息已发送 (传达概率: {session['config'].get('messageDeliveryRate', 100)}%)")
    else:
        print(f"节点 {node_id} 的准备消息被丢弃 (传达概率: {session['config'].get('messageDeliveryRate', 100)}%)")
    
    # 检查准备阶段是否完成
    await check_prepare_phase(session_id)

@sio.event
async def send_commit(sid, data):
    """处理提交消息"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    value = data.get('value')
    
    session = get_session(session_id)
    if not session:
        return
    
    # 记录消息
    message = {
        "from": node_id,
        "to": "all",
        "type": "commit",
        "value": value,
        "phase": "commit",
        "round": session["current_round"],  # 添加轮次信息
        "timestamp": datetime.now().isoformat(),
        "tampered": False,
        "byzantine": data.get("byzantine", False)  # 标记是否为拜占庭攻击消息
    }
    
    session["messages"]["commit"].append(message)
    
    # 根据消息传达概率决定是否广播消息
    if should_deliver_message(session_id):
        await sio.emit('message_received', message, room=session_id)
        print(f"节点 {node_id} 的确认消息已发送 (传达概率: {session['config'].get('messageDeliveryRate', 100)}%)")
    else:
        print(f"节点 {node_id} 的确认消息被丢弃 (传达概率: {session['config'].get('messageDeliveryRate', 100)}%)")
    

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
    
    if session["phase"] == "prepare" and node_id != 0:
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
    """调度机器人节点在10秒后发送准备消息"""
    session = get_session(session_id)
    if not session:
        return
    
    current_round = session["current_round"]
    await asyncio.sleep(10)
    
    session = get_session(session_id)
    if not session:
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
    
    config = session["config"]
    prepare_messages = session["messages"]["prepare"]
    
    # 计算故障节点数 f = floor((n-1)/3)
    n = config["nodeCount"]
    f = (n - 1) // 3
    required_correct_messages = 2 * f + 1  # 需要2f+1个正确消息
    
    # 统计发送正确信息的不同节点（value=0）
    correct_nodes = set()
    for msg in prepare_messages:
        if msg.get("value") == config["proposalValue"]:  # 正确信息
            correct_nodes.add(msg["from"])
    
    print(f"准备阶段检查 - 总节点数: {n}, 故障节点数: {f}")
    print(f"准备阶段检查 - 需要正确消息数: {required_correct_messages}, 实际正确消息节点数: {len(correct_nodes)}")
    print(f"准备阶段检查 - 发送正确消息的节点: {correct_nodes}")
    
    # 检查是否收到足够多的正确消息
    if len(correct_nodes) >= required_correct_messages:
        print(f"准备阶段完成（收到{len(correct_nodes)}个正确消息），进入提交阶段")
        await start_commit_phase(session_id)
    else:
        print(f"准备阶段未完成，还需要 {required_correct_messages - len(correct_nodes)} 个正确消息")

async def start_commit_phase(session_id: str):
    """开始提交阶段"""
    session = get_session(session_id)
    if not session:
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
    
    config = session["config"]
    commit_messages = session["messages"]["commit"]
    
    # 计算故障节点数 f = floor((n-1)/3)
    n = config["nodeCount"]
    f = (n - 1) // 3
    
    # 统计发送正确信息和错误信息的不同节点
    correct_nodes = set()
    error_nodes = set()
    
    for msg in commit_messages:
        if msg.get("value") == config["proposalValue"]:  # 正确信息
            correct_nodes.add(msg["from"])
        else:  # 错误信息
            error_nodes.add(msg["from"])
    
    print(f"提交阶段检查 - 总节点数: {n}, 故障节点数: {f}")
    print(f"提交阶段检查 - 发送正确消息的节点数: {len(correct_nodes)}")
    print(f"提交阶段检查 - 发送错误消息的节点数: {len(error_nodes)}")
    print(f"提交阶段检查 - 正确消息节点: {correct_nodes}")
    print(f"提交阶段检查 - 错误消息节点: {error_nodes}")
    print(f"提交阶段检查 - 需要正确消息数: {2*f+1}, 需要错误消息数: {f+1}")
    
    # 判断共识结果（基于正确/错误消息数量）
    if len(correct_nodes) >= 2 * f + 1:  # 包括自己，需要2f+1个正确消息
        print(f"共识成功 - 收到{len(correct_nodes)}个正确消息（需要{2*f+1}个）")
        print(f"发送共识结果: 共识成功")
        await finalize_consensus(session_id, "共识成功", f"收到{len(correct_nodes)}个正确消息")
    elif len(error_nodes) >= f + 1:  # 包括自己，需要f+1个错误消息
        print(f"共识失败 - 收到{len(error_nodes)}个错误消息（需要{f+1}个）")
        print(f"发送共识结果: 共识失败")
        await finalize_consensus(session_id, "共识失败", f"收到{len(error_nodes)}个错误消息")
    else:
        print(f"提交阶段等待中 - 正确消息:{len(correct_nodes)}, 错误消息:{len(error_nodes)}")

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
    
    # 启动下一轮共识（10秒后）
    print(f"将在10秒后开始第{session['current_round'] + 1}轮共识")
    asyncio.create_task(start_next_round(session_id))

async def handle_consensus_timeout(session_id: str, round_number: int):
    """处理共识超时"""
    await asyncio.sleep(40)  # 等待40秒
    
    session = get_session(session_id)
    if not session:
        return
    
    # 检查是否仍然在同一轮次且未完成共识
    if session["current_round"] == round_number and session["status"] == "running":
        print(f"第{round_number}轮共识超时（40秒未完成），判定为共识失败")
        
        # 清除超时任务引用，避免在finalize_consensus中尝试取消正在执行的任务
        session["timeout_task"] = None
        
        # 设置共识结果为超时失败
        await finalize_consensus(session_id, "共识超时失败", "40秒内未达成共识")

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
    """机器人提议者发送预准备消息"""
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
    proposer_id = 0  # 提议者总是节点0
    
    # 只有当节点0是机器人节点时才自动发送
    if proposer_id not in session["robot_nodes"]:
        print(f"提议者 {proposer_id} 是人类节点，等待人类操作")
        return
    
    # 发送预准备消息
    message = {
        "from": proposer_id,
        "to": "all",
        "type": "pre_prepare",
        "value": config["proposalValue"],
        "phase": "pre-prepare",
        "round": session["current_round"],  # 添加轮次信息
        "timestamp": datetime.now().isoformat(),
        "tampered": False,
        "isRobot": True
    }
    
    session["messages"]["pre_prepare"].append(message)
    
    # 广播消息
    await sio.emit('message_received', message, room=session_id)
    
    print(f"机器人提议者 {proposer_id} 发送了预准备消息: {config['proposalValue']}")
    
    # 进入准备阶段
    await asyncio.sleep(1)
    session["phase"] = "prepare"
    session["phase_step"] = 1
    
    await sio.emit('phase_update', {
        "phase": "prepare",
        "step": 1,
        "isMyTurn": True
    }, room=session_id)
    
    print(f"会话 {session_id} 进入准备阶段")
    
    # 启动超时任务（40秒后检查）
    current_round = session["current_round"]
    timeout_task = asyncio.create_task(handle_consensus_timeout(session_id, current_round))
    session["timeout_task"] = timeout_task
    print(f"第{current_round}轮共识超时检查已启动（40秒）")
    
    # 标记所有机器人节点已收到预准备消息
    for robot_id in session["robot_nodes"]:
        session["robot_node_states"][robot_id]["received_pre_prepare"] = True
    
    # 机器人节点自动发送准备消息（10秒后）
    asyncio.create_task(robot_send_prepare_messages(session_id))

async def robot_send_prepare_messages(session_id: str):
    """机器人节点自动发送准备消息"""
    session = get_session(session_id)
    if not session:
        return
    
    config = session["config"]
    current_round = session["current_round"]
    
    # 等待10秒后发送准备消息
    print(f"机器人节点将在10秒后发送准备消息")
    await asyncio.sleep(10)
    
    session = get_session(session_id)
    if not session:
        return
    
    # 检查轮次是否改变，如果改变则放弃发送
    if session["current_round"] != current_round:
        print(f"轮次已改变（{current_round} -> {session['current_round']}），放弃发送准备消息")
        return
    
    # 所有机器人验证者（除了节点0）发送准备消息
    for robot_id in session["robot_nodes"]:
        if robot_id == 0:  # 提议者不发送准备消息
            continue
        
        if session["robot_node_states"][robot_id]["sent_prepare"]:
            continue  # 已经发送过了
        
        # 调用发送准备消息的函数
        await handle_robot_prepare(session_id, robot_id, config["proposalValue"])
        session["robot_node_states"][robot_id]["sent_prepare"] = True

async def handle_robot_prepare(session_id: str, robot_id: int, value: int):
    """处理机器人节点的准备消息"""
    session = get_session(session_id)
    if not session:
        return
    
    message = {
        "from": robot_id,
        "to": "all",
        "type": "prepare",
        "value": value,
        "phase": "prepare",
        "round": session["current_round"],  # 添加轮次信息
        "timestamp": datetime.now().isoformat(),
        "tampered": False,
        "isRobot": True
    }
    
    session["messages"]["prepare"].append(message)
    
    # 广播消息
    if should_deliver_message(session_id):
        await sio.emit('message_received', message, room=session_id)
        print(f"机器人节点 {robot_id} 的准备消息已发送")
        
        # 所有机器人节点收到这条消息并更新状态
        for rid in session["robot_nodes"]:
            if rid != robot_id:
                session["robot_node_states"][rid]["received_prepare_count"] += 1
    
    # 检查准备阶段是否完成（每次添加消息后检查）
    await check_prepare_phase(session_id)
    
    # 检查是否有机器人节点需要进入提交阶段
    await check_robot_nodes_ready_for_commit(session_id)

async def check_robot_nodes_ready_for_commit(session_id: str):
    """检查机器人节点是否准备好发送提交消息"""
    session = get_session(session_id)
    if not session:
        return
    
    if session["phase"] != "commit":
        return  # 还没进入提交阶段
    
    config = session["config"]
    n = config["nodeCount"]
    f = (n - 1) // 3
    required_prepare = 2 * f  # 需要收到2f个准备消息
    
    # 检查每个机器人节点是否收到足够的准备消息
    for robot_id in session["robot_nodes"]:
        robot_state = session["robot_node_states"][robot_id]
        
        # 如果已经发送过提交消息，跳过
        if robot_state["sent_commit"]:
            continue
        
        # 检查是否收到足够的准备消息
        if robot_state["received_prepare_count"] >= required_prepare:
            print(f"机器人节点 {robot_id} 收到足够的准备消息，将在10秒后发送提交消息")
            asyncio.create_task(schedule_robot_commit(session_id, robot_id, config["proposalValue"]))
            robot_state["sent_commit"] = True  # 标记为已发送（虽然是异步的）

async def schedule_robot_commit(session_id: str, robot_id: int, value: int):
    """调度机器人节点在10秒后发送提交消息"""
    session = get_session(session_id)
    if not session:
        return
    
    current_round = session["current_round"]
    await asyncio.sleep(10)
    
    session = get_session(session_id)
    if not session:
        return
    
    # 检查轮次是否改变
    if session["current_round"] != current_round:
        print(f"轮次已改变（{current_round} -> {session['current_round']}），节点{robot_id}放弃发送提交消息")
        return
    
    await handle_robot_commit(session_id, robot_id, value)

async def handle_robot_commit(session_id: str, robot_id: int, value: int):
    """处理机器人节点的提交消息"""
    session = get_session(session_id)
    if not session:
        return
    
    message = {
        "from": robot_id,
        "to": "all",
        "type": "commit",
        "value": value,
        "phase": "commit",
        "round": session["current_round"],  # 添加轮次信息
        "timestamp": datetime.now().isoformat(),
        "tampered": False,
        "isRobot": True
    }
    
    session["messages"]["commit"].append(message)
    
    # 广播消息
    if should_deliver_message(session_id):
        await sio.emit('message_received', message, room=session_id)
        print(f"机器人节点 {robot_id} 的提交消息已发送")
        
        # 所有机器人节点收到这条消息并更新状态
        for rid in session["robot_nodes"]:
            if rid != robot_id:
                session["robot_node_states"][rid]["received_commit_count"] += 1
    
    # 检查提交阶段是否完成
    await check_commit_phase(session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="127.0.0.1", port=8000) 