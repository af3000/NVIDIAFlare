# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import threading
from concurrent import futures
from typing import Any, Dict, List, Union

import grpc

from nvflare.fuel.f3.comm_config import CommConfigurator
from nvflare.fuel.f3.comm_error import CommError
from nvflare.fuel.f3.connection import Connection
from nvflare.fuel.f3.drivers.driver import ConnectorInfo
from nvflare.fuel.f3.drivers.grpc.streamer_pb2_grpc import (
    StreamerServicer,
    StreamerStub,
    add_StreamerServicer_to_server,
)
from nvflare.fuel.utils.obj_utils import get_logger
from nvflare.security.logging import secure_format_exception

from .base_driver import BaseDriver
from .driver_params import DriverCap, DriverParams
from .grpc.qq import QQ
from .grpc.utils import get_grpc_server_credentials, get_grpc_client_credentials
from .grpc.streamer_pb2 import Frame
from .net_utils import MAX_FRAME_SIZE, get_address, get_tcp_urls, ssl_required

GRPC_DEFAULT_OPTIONS = [
    ("grpc.max_send_message_length", MAX_FRAME_SIZE),
    ("grpc.max_receive_message_length", MAX_FRAME_SIZE),
]


class StreamConnection(Connection):

    seq_num = 0

    def __init__(self, oq: QQ, connector: ConnectorInfo, conn_props: dict, side: str, context=None, channel=None):
        super().__init__(connector)
        self.side = side
        self.oq = oq
        self.closing = False
        self.conn_props = conn_props
        self.context = context  # for server side
        self.channel = channel  # for client side
        self.lock = threading.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_conn_properties(self) -> dict:
        return self.conn_props

    def close(self):
        self.closing = True
        with self.lock:
            self.oq.close()
            if self.context:
                self.context.abort(grpc.StatusCode.CANCELLED, "service closed")
                self.context = None
            if self.channel:
                self.channel.close()
                self.channel = None

    def send_frame(self, frame: Union[bytes, bytearray, memoryview]):
        try:
            StreamConnection.seq_num += 1
            seq = StreamConnection.seq_num
            self.logger.debug(f"{self.side}: queued frame #{seq}")
            self.oq.append(Frame(seq=seq, data=bytes(frame)))
        except BaseException as ex:
            raise CommError(CommError.ERROR, f"Error sending frame: {ex}")

    def read_loop(self, msg_iter, q: QQ):
        ct = threading.current_thread()
        self.logger.debug(f"{self.side}: started read_loop in thread {ct.name}")
        try:
            for f in msg_iter:
                if self.closing:
                    break

                assert isinstance(f, Frame)
                self.logger.debug(f"{self.side} in {ct.name}: incoming frame #{f.seq}")
                if self.frame_receiver:
                    self.frame_receiver.process_frame(f.data)
                else:
                    self.logger.error(f"{self.side}: Frame receiver not registered for connection: {self.name}")
        except Exception as ex:
            if not self.closing:
                self.logger.debug(f"{self.side}: exception {type(ex)} in read_loop")
        if q:
            self.logger.debug(f"{self.side}: closing queue")
            q.close()
        self.logger.debug(f"{self.side} in {ct.name}: done read_loop")

    def generate_output(self):
        ct = threading.current_thread()
        self.logger.debug(f"{self.side}: generate_output in thread {ct.name}")
        for i in self.oq:
            assert isinstance(i, Frame)
            self.logger.debug(f"{self.side}: outgoing frame #{i.seq}")
            yield i
        self.logger.debug(f"{self.side}: done generate_output in thread {ct.name}")


class Servicer(StreamerServicer):
    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger(self.__class__.__name__)

    def Stream(self, request_iterator, context):
        connection = None
        oq = QQ()
        t = None
        ct = threading.current_thread()
        conn_props = {
            DriverParams.PEER_ADDR.value: context.peer(),
            DriverParams.LOCAL_ADDR.value: get_address(self.server.connector.params),
        }
        cn_names = context.auth_context().get("x509_common_name")
        if cn_names:
            conn_props[DriverParams.PEER_CN.value] = cn_names[0].decode("utf-8")

        try:
            self.logger.debug(f"SERVER started Stream CB in thread {ct.name}")
            connection = StreamConnection(oq, self.server.connector, conn_props, "SERVER", context=context)
            self.logger.debug(f"SERVER created connection in thread {ct.name}")
            self.server.driver.add_connection(connection)
            self.logger.debug(f"SERVER created read_loop thread in thread {ct.name}")
            t = threading.Thread(target=connection.read_loop, args=(request_iterator, oq))
            t.start()

            # DO NOT use connection.generate_output()!
            self.logger.debug(f"SERVER: generate_output in thread {ct.name}")
            for i in oq:
                assert isinstance(i, Frame)
                self.logger.debug(f"SERVER: outgoing frame #{i.seq}")
                yield i
            self.logger.debug(f"SERVER: done generate_output in thread {ct.name}")

        except BaseException as ex:
            self.logger.error(f"Connection closed due to error: {ex}")
        finally:
            if t is not None:
                t.join()
            if connection:
                self.logger.debug(f"SERVER: closing connection {connection.name}")
                self.server.driver.close_connection(connection)
            self.logger.debug(f"SERVER: cleanly finished Stream CB in thread {ct.name}")


class Server:
    def __init__(
        self,
        driver,
        connector,
        max_workers,
        options,
    ):
        self.driver = driver
        self.logger = get_logger(self)
        self.connector = connector
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers), options=options)
        servicer = Servicer(self)
        add_StreamerServicer_to_server(servicer, self.grpc_server)

        params = connector.params
        host = params.get(DriverParams.HOST.value)
        port = int(params.get(DriverParams.PORT.value))
        if not host:
            host = "0.0.0.0"

        addr = f"{host}:{port}"
        try:
            self.logger.debug(f"SERVER: connector params: {params}")
            secure = ssl_required(params)
            if secure:
                credentials = get_grpc_server_credentials(params)
                self.grpc_server.add_secure_port(addr, server_credentials=credentials)
                self.logger.info(f"added secure port at {addr}")
            else:
                self.grpc_server.add_insecure_port(addr)
                self.logger.info(f"added insecure port at {addr}")
        except Exception as ex:
            error = f"cannot listen on {addr}: {type(ex)}: {secure_format_exception(ex)}"
            self.logger.debug(error)

    def start(self):
        self.grpc_server.start()
        self.grpc_server.wait_for_termination()

    def shutdown(self):
        self.grpc_server.stop(grace=0.5)


class GrpcDriver(BaseDriver):
    def __init__(self):
        BaseDriver.__init__(self)
        self.server = None
        self.closing = False
        self.max_workers = 100
        self.options = GRPC_DEFAULT_OPTIONS
        self.logger = logging.getLogger(self.__class__.__name__)
        configurator = CommConfigurator()
        config = configurator.get_config()
        if config:
            my_params = config.get("grpc")
            if my_params:
                self.max_workers = my_params.get("max_workers", 100)
                self.options = my_params.get("options")
        self.logger.debug(f"GRPC Config: max_workers={self.max_workers}, options={self.options}")

    @staticmethod
    def supported_transports() -> List[str]:
        return ["grpc", "grpcs"]

    @staticmethod
    def capabilities() -> Dict[str, Any]:
        return {DriverCap.SEND_HEARTBEAT.value: True, DriverCap.SUPPORT_SSL.value: True}

    def listen(self, connector: ConnectorInfo):
        self.connector = connector
        self.server = Server(self, connector, max_workers=self.max_workers, options=self.options)
        self.server.start()

    def connect(self, connector: ConnectorInfo):
        self.logger.debug("CLIENT: trying connect ...")
        params = connector.params
        address = get_address(params)
        conn_props = {DriverParams.PEER_ADDR.value: address}

        secure = ssl_required(params)
        if secure:
            self.logger.info("CLIENT: creating secure channel")
            channel = grpc.secure_channel(
                address, options=self.options, credentials=get_grpc_client_credentials(params)
            )
        else:
            self.logger.info("CLIENT: creating insecure channel")
            channel = grpc.insecure_channel(address, options=self.options)

        self.logger.debug("CLIENT: created channel")
        stub = StreamerStub(channel)
        self.logger.debug("CLIENT: got stub")
        oq = QQ()
        connection = StreamConnection(oq, connector, conn_props, "CLIENT", channel=channel)
        self.add_connection(connection)
        self.logger.debug("CLIENT: added connection")
        try:
            received = stub.Stream(connection.generate_output())
            connection.read_loop(received, oq)
        except BaseException as ex:
            self.logger.debug(f"CLIENT: connection done: {type(ex)}")
        connection.close()
        self.logger.debug("CLIENT: finished connection")

    @staticmethod
    def get_urls(scheme: str, resources: dict) -> (str, str):
        secure = resources.get(DriverParams.SECURE)
        if secure:
            scheme = "grpcs"
        return get_tcp_urls(scheme, resources)

    def shutdown(self):
        if self.closing:
            return
        self.closing = True
        if self.server:
            self.server.shutdown()
        self.close_all()
