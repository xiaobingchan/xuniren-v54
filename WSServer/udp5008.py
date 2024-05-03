import sys
import asyncio
import websockets
import json

async def send_message_to_websocket(message):
    async with websockets.connect('ws://localhost:60002') as websocket:
        await websocket.send(message)  # 发送消息给服务器

def send_message(message):
    asyncio.run(send_message_to_websocket(message))


if __name__ == "__main__":
    import socket

    # 创建UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 绑定本地IP和端口
    server_address = ('0.0.0.0', 5008)
    server_socket.bind(server_address)

    print(f'Listening on {server_address[0]}:{server_address[1]}')

    while True:
        # 接收数据
        data, address = server_socket.recvfrom(4096)
        result=data.decode()
        send_message(result)

        # 可选: 发送响应
        # msg = b'Message received!'
        # server_socket.sendto(msg, address)
