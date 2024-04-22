from http import client
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import struct
import pickle
import cv2
import threading
import socket
import json
import base64


clients = []
clientData = {}
videos = "1. Video_1	2. Video_2 : "


def send_message(conn, message):
    try:
        conn.sendall(message.encode())
    except Exception as e:
        print(f"Error sending message: {e}")


def recv_message(conn):
    try:
        data = conn.recv(1024).decode()
        return data
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None


def recv_encrypted_message(conn):
    try:
        data = conn.recv(1024)
        return data
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None


def Broadcast(clientName):
    Client_Info = {
        "identifier": "Client_Details",
        "data": clientData
    }
    client_info_json = json.dumps(Client_Info).encode()
    num_clients = len(clients)
    name = clientName
    i = 0
    while i < num_clients:
        clients[i].send(client_info_json)
        i += 1


def Peer_Communication(encryptedMessage, clientName):
    message = {
        "identifier": "encryptedMessage",
        "data": base64.b64encode(encryptedMessage).decode('utf-8'),
        "from": clientName
    }
    index = 0
    while index < len(clients):
        conn = clients[index]
        send_message(conn, json.dumps(message))
        index += 1


def stream(conn, reply):
    video_files = ["Video_240p.mp4", "Video_720p.mp4", "Video_1080p.mp4"]
    frame_counts = [0, 0, 0]
    starting_frame = 0

    if reply == "1":
        for video_path in video_files:
            vid = cv2.VideoCapture(video_path)
            total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
            print("Total Frames : ", total_frames)
            print("Starting @ : ", starting_frame)
            vid.set(cv2.CAP_PROP_POS_FRAMES, starting_frame)
            while vid.isOpened():
                ret, frame = vid.read()
                if not ret:
                    break
                a = pickle.dumps(frame)
                message = struct.pack("Q", len(a)) + a
                conn.sendall(message)
                frame_counts[video_files.index(video_path)] += 1
                if frame_counts[video_files.index(video_path)] >= total_frames // 3:
                    print("Ended @ : ",
                          frame_counts[video_files.index(video_path)])
                    starting_frame += frame_counts[video_files.index(
                        video_path)]
                    print("Starting @ : ", starting_frame)
                    break
            vid.release()
    elif reply == "2":
        print("Playing Video 2")


def handleOption1(client_socket, clientName):
    encrypted_message = recv_encrypted_message(client_socket)
    Peer_Communication(encrypted_message, clientName)


def handleOption2(client_socket):
    message = {
        "identifier": "Video Status",
        "videos": videos
    }
    send_message(client_socket, json.dumps(message))
    print("Sent")
    reply = recv_message(client_socket)
    print("Received ", reply)
    stream(client_socket, reply)
    print("Streamed")


def HandleClient(client_socket, clientName):
    global clientData
    global clients
    while True:
        Client_response = recv_message(client_socket)

        if Client_response == "1":
            handleOption1(client_socket, clientName)

        elif Client_response == "2":
            handleOption2(client_socket)

        elif Client_response == "3":
            message = {
                "identifier": "Exiting",
                "data": clientName
            }

            send_message(client_socket, json.dumps(message))
            clients[:] = [
                clientConn for clientConn in clients if clientConn != client_socket]
            print(f"{clientName} left the server.")

            for conn in clients:
                send_message(conn, json.dumps(message))
            del clientData[clientName]
            break

        else:
            invalid_message = "Invalid input. Please try again."
            send_message(client_socket, invalid_message.encode())

    return


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8005))
    server_socket.listen(5)
    print("Server listening on port 8005...")

    while True:
        try:
            client_socket, addr = server_socket.accept()
            clients.append(client_socket)

            # Prompt the client to enter their name
            send_message(client_socket, "Please enter your name: ")
            client_name = recv_message(client_socket)

            # Prompt the client to enter their public key
            send_message(client_socket, "Please enter your public key: ")
            client_key = recv_message(client_socket)

            # Add client name and public key to clientData dictionary
            clientData[client_name] = client_key

            # Print confirmation of new client connection
            print("New client {", client_name, "} joined into the server")
            # print("Public Key:", client_key)

            Broadcast(client_name)

            client_handler = threading.Thread(target=HandleClient, args=(
                client_socket, client_name))
            client_handler.start()

        except KeyboardInterrupt:
            print("Server Shutting Down...")
        # finally:
        #     server_socket.close()


if __name__ == "__main__":
    main()
