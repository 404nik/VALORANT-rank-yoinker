import json
import logging
import traceback
from websocket_server import WebsocketServer

from src.constants import version

logging.getLogger('websocket_server.websocket_server').disabled = True

# websocket.enableTrace(True)


class QuietWebsocketServer(WebsocketServer):
    """A WebsocketServer that drops malformed connections quietly.

    Anything that opens the port without a WebSocket upgrade -- a browser
    pointed at https:// instead of ws://, a LAN port scanner, a half-open
    probe -- trips an AssertionError inside websocket_server's handshake.
    socketserver's default handle_error prints that traceback straight to
    stderr, which tears through the rendered table. Send it to the log
    instead; a bad client is not something the user needs to see.
    """

    log = None  # assigned by Server.start_server

    def handle_error(self, request, client_address):
        if callable(self.log):
            self.log(
                f"server: dropped malformed connection from {client_address[0]}: "
                f"{traceback.format_exc().strip()}"
            )


class Server:
    def __init__(self, log, Error):
        self.Error = Error
        self.log = log
        self.lastMessages = {}

    def start_server(self):
        port = None
        try:
            # print(self.lastMessage)
            with open("config.json", "r") as conf:
                port = json.load(conf)["port"]
            self.server = QuietWebsocketServer(host="0.0.0.0", port=port)
            self.server.log = self.log
            # server = websocket.WebSocketApp("wss://localhost:1100", on_open=on_open, on_message=on_message, on_close=on_close)
            self.server.set_fn_new_client(self.handle_new_client)
            self.server.run_forever(threaded=True)
        except Exception as e:
            self.Error.PortError(port)

    def handle_new_client(self, client, server):
        self.send_payload("version",{
            "core": version
        })
        for key in self.lastMessages:
            if key not in ["chat","version"]:
                self.send_message(self.lastMessages[key])

    def send_message(self, message):
        self.server.send_message_to_all(message)

    def send_payload(self, type, payload):
        payload["type"] = type
        msg_str = json.dumps(payload)
        self.lastMessages[type] = msg_str
        self.server.send_message_to_all(msg_str)
