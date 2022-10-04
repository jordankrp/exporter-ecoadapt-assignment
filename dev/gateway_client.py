###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

# This client application reads the voltage and frequency from the Eco-Adapt sensor and sends it to the backend server every second.

import asyncio
import logging
from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
from ecoadapt import run_sync_client
from random import randrange

# configure the client logging
FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.INFO)

class MyClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))
        return None

    def onConnecting(self, transport_details):
        print("Connecting; transport details: {}".format(transport_details))
        return None  # ask for defaults

    def onOpen(self):
        print("WebSocket connection open.")

        """
        def hello():
            self.sendMessage("Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.loop.call_later(1, hello)

        # start sending messages every second ..
        hello()
        """
        def generate_register_data(register, length):
            # Generates random register data
            # With hardware connected:
            # resp = client.read_input_registers(register, length, unit=UNIT)
            # output_array = resp.registers

            output_array = []
            if register == 0:
                output_array = [514]
            elif register == 1:
                output_array = [2]
            elif register == 2:
                output_array = [30, 44285, 17639]
            elif register == 244:
                for i in range(length):
                    output_array.append(0)
            elif register == 352 or register == 388 or register == 424:
                for i in range(int(length/2)):
                    output_array.append(randrange(15000, 55000))
                for j in range(int(length/2)):
                    output_array.append(0)
            else:
                output_array = [0]
            return output_array

        def ecoadapt_mock_data():
            # Reads registers and length of each register and generates random data

            read_registers = [
                (0, 1),
                (1, 1),
                (2, 3),
                (244, 12),
                (352, 12),
                (388, 12),
                (424, 12),
            ]

            output_string = ""
            for r in read_registers:
                output_string += f"\n{r}: ReadRegisterResponse ({r[1]}): {generate_register_data(r[0], r[1])}"
            return output_string

        def send_ecoadapt_data():
            # The client (Raspberry Pi bridge / gateway) sends the Eco-Adapt data to the backend server
            # as an encoded WebSocket message every 1s
            self.sendMessage("Hello from client".encode('utf-8'))
            self.sendMessage(ecoadapt_mock_data().encode('utf-8'))
            self.factory.loop.call_later(1, send_ecoadapt_data)
        
        # start sending messages every second ...
        send_ecoadapt_data()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':
    factory = WebSocketClientFactory("ws://127.0.0.1:9000")
    factory.protocol = MyClientProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, '127.0.0.1', 9000)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()