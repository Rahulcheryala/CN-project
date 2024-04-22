# CN-project
Demo Video Link - https://drive.google.com/file/d/16O_hPmx-MpZE-t1JudLx5SO3yujoRp3C/view?usp=drive_link

# Client-Server Secure Communication and Video Streaming System

## Overview

This project implements a socket programming system where a server manages client connections, maintains client information securely, and facilitates secure communication and video streaming among clients.

## Features

### Client Connection Management:

- Clients can connect to the server, providing their name and generated public key.
- The server maintains a dictionary mapping client names to their public keys and broadcasts this information to all connected clients.
- Clients can disconnect by sending a 'QUIT' message to the server, which removes their entry from the dictionary and notifies other clients.

### Secure Communication Management:

- Clients can securely communicate with each other using public-key cryptography.
- The server broadcasts encrypted messages among clients, ensuring only the intended recipient can decrypt and read the message.

### Video Streaming Management:

- The server streams video files to clients without saving them locally.
- Clients can request a list of available videos and play a selected video file.

## Used Libraries

- OpenCV (for video streaming)
- PyCryptoDome (for RSA encryption)

## Usage

### Start the server:

```bash
python 210010012_server.py
```

### Start the client(s):

```bash
python 210010012_client.py
```

## Steps on the Client Side

1. First, the name of the client will be asked.

   ```
   Enter your name: rahul
   ```

2. The generated public key will be sent to the server, and the dictionary named `clientsData` will store the name and corresponding public key in the dictionary.

3. This dictionary will be broadcasted to every client in the connection.

4. The following options are provided for the client:

   Options:

   1. To Know Available clients and send Message
   2. Video Playback
   3. Quit (Exiting)

   - When the client types 1, they will know the available clients and they will be able to send messages to the available clients. If they type the wrong name, they will be asked to enter the name of the receiver again.
   - When the client types 2, they will be given the list of possible videos.
     ```
     Video_1 Video_2
     Enter the video to watch (1 or 2):
     ```
     If they type 1, video 1 will be played, and if they type 2, video 2 will be played with different resolutions.
   - When the client types 3, they will be removed from the list of clients' data at the server, and at the client level, their name will not be present in the available clients.

**Note**: There is one exception that when the video is playing, if another client tries to join the chat, this will cause a thread error. So please do not join when the video is being played. After the video completion, the clients will be able to join the chat.

Thank you.
