#  Copyright (c) 2021-2022, NVIDIA CORPORATION.  All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License

from typing import Optional


from nvflare.fuel.f3.drivers.driver import Driver
from nvflare.fuel.f3.endpoint import Endpoint, EndpointMonitor
from nvflare.fuel.f3.message import Message, MessageReceiver
from nvflare.fuel.f3.sfm.conn_manager import ConnManager, Mode


class Communicator:

    def __init__(self, local_endpoint: Endpoint):
        self.local_endpoint = local_endpoint
        self.monitors = []
        self.conn_manager = ConnManager(local_endpoint)

    def start(self):
        """Start the communicator and establishing all the connections

        Raises:
            CommError: If any error encountered while starting up
        """
        self.conn_manager.start()

    def stop(self):
        """Stop the communicator and shutdown all the connections

        Raises:
            CommError: If any error encountered while shutting down
        """
        self.conn_manager.stop()

    def register_monitor(self, monitor: EndpointMonitor):
        """Register a monitor for endpoint lifecycle changes

        This monitor is notified for any state changes of all the endpoints.
        Multiple monitors can be registered.

        Args:
            monitor: The class that receives the state change notification

        Raises:
            CommError: If any error happens while sending the request
        """
        self.conn_manager.add_endpoint_monitor(monitor)

    def get_endpoint(self, name: str) -> Optional[Endpoint]:
        """Find endpoint by name

        Args:
            name: Endpoint name

        Returns:
            The endpoint if found. None if not found

        """
        return self.conn_manager.find_endpoint(name)

    def send(self, endpoint: Endpoint, app_id: int, message: Message):
        """Send a message to endpoint for app_id, no response is expected

        Args:
            endpoint: An endpoint to send the request to
            app_id: Application ID
            message: Message to send

        Raises:
            CommError: If any error happens while sending the data
        """

        self.conn_manager.send_message(endpoint, app_id, message.headers, message.payload)

    def register_message_receiver(self, app_id: int, receiver: MessageReceiver):
        """Register a receiver to process FCI message for the app

         Args:
             app_id: Application ID
             receiver: The class to process the message

         Raises:
             CommError: If duplicate endpoint/app or responder is of wrong type
         """

        self.conn_manager.register_message_receiver(app_id, receiver)

    def add_listener(self, driver: Driver):
        """Add a connector using the driver

         Args:
             driver: The driver for the transport

         Raises:
             CommError: If any errors
         """

        self.conn_manager.add_transport(driver, Mode.PASSIVE)

    def add_connector(self, driver: Driver):
        """Add a connector using the driver

         Args:
             driver: The driver for the transport

         Raises:
             CommError: If any errors
         """

        self.conn_manager.add_transport(driver, Mode.ACTIVE)
