#!/usr/bin/env python3
"""
Socket.IO客户端测试脚本
用于测试消息传递功能
"""

import socketio
import asyncio
import time
import json

# 创建Socket.IO客户端
sio = socketio.AsyncClient()

# 测试配置
SESSION_ID = "f48cc330-e340-45e5-9720-deed01dc3a78"  # 使用之前创建的会话ID
NODE_ID = 0

@sio.event
async def connect():
    print(f"✅ 节点 {NODE_ID} 连接成功")
    
@sio.event
async def disconnect():
    print(f"❌ 节点 {NODE_ID} 连接断开")

@sio.event
async def session_config(data):
    print(f"📋 收到会话配置: {data}")

@sio.event
async def message_received(data):
    print(f"📨 收到消息: {data}")

@sio.event
async def connected_nodes(data):
    print(f"🌐 已连接节点: {data}")

@sio.event
async def phase_update(data):
    print(f"🔄 阶段更新: {data}")

async def main():
    try:
        # 连接到服务器
        await sio.connect(
            'http://127.0.0.1:8000',
            headers={
                'sessionId': SESSION_ID,
                'nodeId': str(NODE_ID)
            }
        )
        
        print(f"🔗 正在连接到会话 {SESSION_ID}，节点 {NODE_ID}")
        
        # 等待连接建立
        await asyncio.sleep(2)
        
        # 发送测试消息
        test_message = {
            'sessionId': SESSION_ID,
            'nodeId': NODE_ID,
            'type': 'test',
            'value': 1,
            'target': 'all',
            'customContent': f'来自节点{NODE_ID}的测试消息'
        }
        
        print(f"📤 发送测试消息: {test_message}")
        await sio.emit('send_message', test_message)
        
        # 等待消息处理
        await asyncio.sleep(3)
        
        # 发送Ping消息
        ping_message = {
            'sessionId': SESSION_ID,
            'nodeId': NODE_ID
        }
        
        print(f"🏓 发送Ping消息: {ping_message}")
        await sio.emit('ping', ping_message)
        
        # 等待响应
        await asyncio.sleep(3)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 