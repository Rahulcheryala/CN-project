from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import struct
import pickle
import cv2
import json
import threading
import socket
import base64
from Crypto.PublicKey import RSA


clientsData = {}
isStreaming = False


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


def recv_message_large(conn):
    try:
        data = conn.recv(65536).decode()
        return data
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None


def send_message_raw(client_socket, message):
    try:
        client_socket.sendall(message)
    except Exception as e:
        print("Error while sending message:", e)


def cipher_encrypt(message, public_key_obj):
    cipher_text = public_key_obj.encrypt(
        message.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return cipher_text


def encrypt_message(message, public_key):
    # since the dictionary stores a decoded version of the public key
    public_key = public_key.encode()
    public_key_obj = serialization.load_pem_public_key(public_key)
    ciphertext = cipher_encrypt(message, public_key_obj)
    return ciphertext


def cipher_decrypt(ciphertext, private_key_obj):
    plaintext = private_key_obj.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext.decode()


def decrypt_message(ciphertext, private_key):
    private_key_obj = serialization.load_pem_private_key(
        private_key,
        password=None
    )
    plaintext = cipher_decrypt(ciphertext, private_key_obj)
    return plaintext


def watch(client_socket):
    # print("Insider")
    data = b""
    payloadSize = struct.calcsize("Q")

    while True:
        # key2 = cv2.waitKey(1)
        # if key2 == 27:
        #     break
        while len(data) < payloadSize:
            packet = client_socket.recv(4*1024)
            if not packet:
                break
            data += packet

        packed_msg_size = data[:payloadSize]
        data = data[payloadSize:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += client_socket.recv(4*1024)

        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data)
        frame = cv2.resize(frame, (1080, 720))
        cv2.imshow("Receiving From Server", frame)
        key = cv2.waitKey(1)
        if key == 13:
            break


def process_response(server_response, clientName, private_key, client_socket):
    identifier = server_response.get("identifier")
    data = server_response.get("data")
    from_client = server_response.get("from")

    # Process response based on identifier
    if identifier == "Client_Details":
        for key, value in data.items():
            if key != clientName:
                print(f"\n>> {key} Joined The Chat \n")
                clientsData[key] = value
    elif identifier == "encryptedMessage":
        decrypt_and_print(from_client, data, clientName, private_key)
    elif identifier == "Video Status":
        watch_video(data, client_socket)


def decrypt_and_print(from_client, encryptedMessage, clientName, private_key):
    if from_client != clientName:
        encrypted_message = base64.b64decode(encryptedMessage)
        decryptedMessage = decrypt_message(encrypted_message, private_key)
        print(">>> Decrypted Message:", decryptedMessage)
        print()


def watch_video(videos, client_socket):
    while True:
        message = input("Select a video to watch (1 or 2): ")
        if message not in ('1', '2'):
            print("Invalid input. Please select either '1' or '2'.")
        else:
            print("Selected video", message)
            send_message(client_socket, message)
            watch(client_socket)
            print("Watched")
            global isStreaming
            isStreaming = False
            break


def MessageFromServer(client_socket, clientName, private_key):
    global clientsData
    while True:
        try:
            server_response = recv_message_large(client_socket)
            server_response = json.loads(server_response)

            identifier = server_response.get("identifier")
            Client = server_response.get("data")
            if identifier == "Exiting":
                afkClient = Client
                if afkClient == clientName:
                    print("Disconnecting from server ...")
                    print("Disconnected.")
                    break
                else:
                    print(f"{afkClient} Left The Chat")
                    del clientsData[afkClient]
            else:
                # Process server response based on identifier using ternary operator functions
                process_response(server_response, clientName,
                                 private_key, client_socket)

        except Exception as e:
            print("Error :", e)


def main():

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 8005))

    clientName = input("Enter your name : ")
    key = RSA.generate(2048)
    public_key = key.publickey().export_key()
    private_key = key.export_key()

    client_name = recv_message(client_socket)
    send_message(client_socket, clientName)

    client_publicKey = recv_message(client_socket)
    client_socket.send(public_key)

    print("Public key :\n", public_key.decode())
    print()

    client_thread = threading.Thread(target=MessageFromServer, args=(
        client_socket, clientName, private_key))
    client_thread.start()

    while True:
        try:
            Client_input = input(
                "Enter any one of the following options : \n\n1. Connect To Other Clients\n2. Stream a Video (1 or 2)\n3. QUIT\n\n> ")

            if Client_input == "1":
                messageToClient = "CN is fantastic."
                selected_client = None
                while selected_client not in clientsData:

                    available_clients = []
                    for name, key in clientsData.items():
                        if name != clientName:
                            available_clients.append(name)

                    if not available_clients:
                        print("No available clients.\n")
                        break
                    else:
                        print("Available Clients:")
                        for client in available_clients:
                            print(client)

                        selected_client = input(
                            "To whom do you want to send a message: ")
                        if selected_client not in available_clients:
                            print("Invalid input. Please select a valid client.\n")
                        else:
                            print("\nMessage sent to", selected_client)
                            print()
                            break

                if selected_client in clientsData:
                    selected_public_key = clientsData[selected_client]
                    encryptedMessage = encrypt_message(
                        messageToClient, selected_public_key)

                    send_message(client_socket, "1")
                    send_message_raw(client_socket, encryptedMessage)

            if Client_input == "2":
                global isStreaming
                send_message(client_socket, "2")
                isStreaming = True
                while True:
                    if (not isStreaming):
                        break

            if Client_input == "3":
                send_message(client_socket, "3")
                client_thread.join()
                client_socket.close()
                break

        except KeyboardInterrupt as e:
            print("Error in the except block:", e)
            print()


if __name__ == "__main__":
    main()
