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
    topology: str
    branchCount: Optional[int] = 2
    proposalValue: int
    maliciousProposer: bool
    allowTampering: bool

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
    
    session = {
        "config": config.dict(),
        "status": "waiting",
        "phase": "waiting",
        "phase_step": 0,
        "connected_nodes": [],
        "messages": {
            "pre_prepare": [],
            "prepare": [],
            "commit": []
        },
        "node_states": {},
        "consensus_result": None,
        "created_at": datetime.now().isoformat()
    }
    
    sessions[session_id] = session
    connected_nodes[session_id] = []
    node_sockets[session_id] = {}
    
    return {
        "sessionId": session_id,
        "config": {
            "nodeCount": config.nodeCount,
            "faultyNodes": config.faultyNodes,
            "topology": config.topology,
            "branchCount": config.branchCount,
            "proposalValue": config.proposalValue,
            "maliciousProposer": config.maliciousProposer,
            "allowTampering": config.allowTampering
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
        
        # 发送会话配置
        await sio.emit('session_config', sessions[session_id]["config"], room=sid)
        
        # 发送当前阶段信息
        await sio.emit('phase_update', {
            "phase": sessions[session_id]["phase"],
            "step": sessions[session_id]["phase_step"],
            "isMyTurn": False
        }, room=sid)
        
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
        "timestamp": datetime.now().isoformat(),
        "tampered": False
    }
    
    session["messages"]["prepare"].append(message)
    
    # 广播给所有节点
    await sio.emit('message_received', message, room=session_id)
    
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
        "timestamp": datetime.now().isoformat(),
        "tampered": False
    }
    
    session["messages"]["commit"].append(message)
    
    # 广播给所有节点
    await sio.emit('message_received', message, room=session_id)
    
    # 检查提交阶段是否完成
    await check_commit_phase(session_id)

@sio.event
async def send_message(sid, data):
    """处理自定义消息"""
    session_id = data.get('sessionId')
    node_id = data.get('nodeId')
    message_type = data.get('type')
    value = data.get('value')
    target = data.get('target')
    custom_content = data.get('customContent', '')
    
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
        "tampered": False,
        "customContent": custom_content
    }
    
    # 根据消息类型存储到相应的消息列表
    if message_type == "prepare":
        session["messages"]["prepare"].append(message)
    elif message_type == "commit":
        session["messages"]["commit"].append(message)
    else:
        # 自定义消息或其他类型
        if "custom" not in session["messages"]:
            session["messages"]["custom"] = []
        session["messages"]["custom"].append(message)
    
    # 广播给所有节点
    await sio.emit('message_received', message, room=session_id)
    
    # 如果是准备或提交消息，检查阶段完成情况
    if message_type == "prepare":
        await check_prepare_phase(session_id)
    elif message_type == "commit":
        await check_commit_phase(session_id)
    
    print(f"节点 {node_id} 发送自定义消息: {message_type} 到 {target}")

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
    """开始共识过程"""
    session = get_session(session_id)
    if not session:
        return
    
    session["status"] = "running"
    session["phase"] = "pre_prepare"
    session["phase_step"] = 0
    
    config = session["config"]
    
    # 发送预准备消息
    pre_prepare_message = {
        "from": 0,  # 提议者
        "to": "all",
        "type": "pre_prepare",
        "value": config["proposalValue"],
        "phase": "pre_prepare",
        "timestamp": datetime.now().isoformat(),
        "tampered": config["maliciousProposer"] and random.random() < 0.5
    }
    
    session["messages"]["pre_prepare"].append(pre_prepare_message)
    
    # 广播预准备消息
    await sio.emit('message_received', pre_prepare_message, room=session_id)
    
    # 更新阶段
    await sio.emit('phase_update', {
        "phase": "pre_prepare",
        "step": 0,
        "isMyTurn": False
    }, room=session_id)
    
    # 延迟后进入准备阶段
    await asyncio.sleep(3)
    await start_prepare_phase(session_id)

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
    
    # 检查是否收到足够的准备消息
    if len(prepare_messages) >= config["nodeCount"] - 1:  # 除了提议者
        await start_commit_phase(session_id)

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

async def check_commit_phase(session_id: str):
    """检查提交阶段是否完成"""
    session = get_session(session_id)
    if not session:
        return
    
    config = session["config"]
    commit_messages = session["messages"]["commit"]
    
    # 检查是否收到足够的提交消息
    if len(commit_messages) >= config["nodeCount"] - 1:  # 除了提议者
        await finalize_consensus(session_id)

async def finalize_consensus(session_id: str):
    """完成共识"""
    session = get_session(session_id)
    if not session:
        return
    
    session["phase"] = "completed"
    session["phase_step"] = 3
    session["status"] = "completed"
    
    config = session["config"]
    
    # 计算共识结果
    prepare_messages = session["messages"]["prepare"]
    commit_messages = session["messages"]["commit"]
    
    # 统计投票结果
    truth_votes = 0
    falsehood_votes = 0
    rejected_votes = 0
    
    for msg in prepare_messages + commit_messages:
        if msg["value"] == 0:
            truth_votes += 1
        elif msg["value"] == 1:
            falsehood_votes += 1
        else:
            rejected_votes += 1
    
    # 判断共识结果
    total_votes = truth_votes + falsehood_votes + rejected_votes
    if total_votes == 0:
        consensus_status = "无诚实节点"
        consensus_description = "没有节点参与共识"
    elif truth_votes + falsehood_votes == 0:
        consensus_status = "拒绝提议"
        consensus_description = "所有节点都拒绝了提议"
    elif truth_votes > 0 and falsehood_votes == 0:
        consensus_status = "共识成功"
        consensus_description = f"所有节点都接受了值 0"
    elif falsehood_votes > 0 and truth_votes == 0:
        consensus_status = "共识成功"
        consensus_description = f"所有节点都接受了值 1"
    else:
        consensus_status = "共识失败"
        consensus_description = "节点间存在分歧，共识失败"
    
    consensus_result = {
        "status": consensus_status,
        "description": consensus_description,
        "stats": {
            "truth": truth_votes,
            "falsehood": falsehood_votes,
            "rejected": rejected_votes
        }
    }
    
    session["consensus_result"] = consensus_result
    
    # 广播共识结果
    await sio.emit('consensus_result', consensus_result, room=session_id)
    
    # 更新阶段
    await sio.emit('phase_update', {
        "phase": "completed",
        "step": 3,
        "isMyTurn": False
    }, room=session_id)
    
    print(f"会话 {session_id} 共识完成: {consensus_status}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="127.0.0.1", port=8000) 