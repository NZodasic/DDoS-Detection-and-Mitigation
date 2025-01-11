import socket
import threading
import os
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class SecureServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.clients = {}  # {client_address: session_key}
        self.agent_tokens = {  # Example token store
            "agent-123": {"active": False, "machine_id": None},
            "agent-456": {"active": False, "machine_id": None}
        }
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = server_socket.accept()
                threading.Thread(target=self.handle_client, args=(
                    client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        try:
            # Step 1: Send public key to the client
            public_key_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            client_socket.sendall(public_key_bytes)

            # Step 2: Receive agent token and machine ID
            data = json.loads(client_socket.recv(1024).decode())
            agent_token = data.get("token")
            machine_id = data.get("machine_id")

            if not self.authenticate_agent(agent_token, machine_id):
                print(f"Authentication failed for {client_address}")
                client_socket.close()
                return

            # Step 3: Receive and decrypt the session key
            encrypted_session_key = client_socket.recv(256)
            session_key = self.private_key.decrypt(
                encrypted_session_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                             algorithm=hashes.SHA256(), label=None)
            )
            print(f"Session key established with {client_address}")

            self.clients[client_address] = {
                "session_key": session_key, "token": agent_token}

            # Step 4: Secure communication loop
            while True:
                encrypted_message = client_socket.recv(1024)
                if not encrypted_message:
                    break
                message = self.decrypt_message(session_key, encrypted_message)
                print(f"Received from {client_address}: {message}")

                # Server-side commands
                response = self.handle_commands(agent_token, message)
                client_socket.sendall(
                    self.encrypt_message(session_key, response))
        except Exception as e:
            print(f"Error with client {client_address}: {e}")
        finally:
            print(f"Connection closed for {client_address}")
            self.clients.pop(client_address, None)
            client_socket.close()

    def authenticate_agent(self, token, machine_id):
        agent = self.agent_tokens.get(token)
        if not agent:
            return False

        if agent["active"]:
            return agent["machine_id"] == machine_id

        # Activate token and associate with machine ID
        self.agent_tokens[token] = {"active": True, "machine_id": machine_id}
        return True

    def handle_commands(self, token, message):
        command = json.loads(message)
        action = command.get("action")

        if action == "start":
            return json.dumps({"status": "success", "message": "Agent started"})
        elif action == "stop":
            return json.dumps({"status": "success", "message": "Agent stopped"})
        elif action == "update":
            return json.dumps({"status": "success", "message": "Agent update triggered"})
        else:
            return json.dumps({"status": "error", "message": "Unknown command"})

    def encrypt_message(self, key, plaintext):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(
            plaintext.encode()) + encryptor.finalize()
        return iv + ciphertext

    def decrypt_message(self, key, ciphertext):
        iv = ciphertext[:16]
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext[16:]) + decryptor.finalize()
        return plaintext.decode()


if __name__ == '__main__':
    server = SecureServer()
    server.start()
