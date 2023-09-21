# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
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
import io
import os.path
import struct
import uuid
from typing import Any, BinaryIO

from nvflare.fuel.utils.config_service import ConfigService
from nvflare.fuel.utils.fobs.datum import Datum, DatumManager, DatumType
from nvflare.fuel.utils.fobs.fobs import deserialize, serialize

HEADER_STRUCT = struct.Struct(">BQ")  # marker(1), size(8)
HEADER_LEN = HEADER_STRUCT.size

MARKER_MAIN = 101
MARKER_DATUM_BLOB = 102
MARKER_DATUM_FILE = 103

DATUM_ID_LEN = 16
MAX_BYTES_PER_READ = 1024 * 1024  # 1MB

DATUM_DIR_CONFIG_VAR = "datum_dir"
DEFAULT_DATUM_DIR = "/tmp/nvflare/datums"


class _Header:
    def __init__(self, marker, size: int):
        self.marker = marker
        self.size = size

    @classmethod
    def from_bytes(cls, buffer: bytes):
        if len(buffer) < HEADER_LEN:
            raise ValueError("Header too short")

        marker, size = HEADER_STRUCT.unpack_from(buffer, 0)
        return _Header(marker, size)

    def to_bytes(self):
        return HEADER_STRUCT.pack(self.marker, self.size)


def _write_datum_header(stream: BinaryIO, marker, datum_id: str, value_size: int):
    datum_uuid = uuid.UUID(datum_id)
    datum_id_bytes = datum_uuid.bytes
    if len(datum_id_bytes) != DATUM_ID_LEN:
        raise RuntimeError(f"program error: datum ID length should be {DATUM_ID_LEN} but got {len(datum_id_bytes)}")
    header = _Header(marker, len(datum_id_bytes) + value_size)
    stream.write(header.to_bytes())
    stream.write(datum_id_bytes)


def dump_to_stream(obj: Any, stream: BinaryIO, max_value_size=None):
    """
    Encode the specified object to a stream of bytes. If the object contains any datums, they will be included
    into the result.

    Args:
        obj:
        stream:
        max_value_size: max size of bytes value allowed. If a value exceeds this, it will be converted to datum.

    Returns:

    """
    mgr = DatumManager(max_value_size)
    main_body = serialize(obj, mgr)
    header = _Header(MARKER_MAIN, len(main_body))
    stream.write(header.to_bytes())
    stream.write(main_body)

    datums = mgr.get_datums()
    for datum_id, datum in datums.items():
        if datum.app_data:
            c, p = datum.app_data
            if datum.datum_type == DatumType.BLOB:
                c[p] = datum.value
            else:
                # file datum - app provided
                c[p] = datum

        if datum.datum_type == DatumType.BLOB:
            _write_datum_header(stream, MARKER_DATUM_BLOB, datum_id, len(datum.value))
            stream.write(datum.value)
        else:
            # file type:
            file_path = datum.value
            if not os.path.exists(file_path):
                raise RuntimeError(f"{file_path} does not exist")

            if not os.path.isfile(file_path):
                raise RuntimeError(f"{file_path} is not a valid file")

            file_size = os.path.getsize(file_path)
            _write_datum_header(stream, MARKER_DATUM_FILE, datum_id, file_size)
            with open(file_path, "rb") as f:
                while True:
                    bytes_read = f.read(MAX_BYTES_PER_READ)
                    if not bytes_read:
                        break
                    stream.write(bytes_read)


def _get_datum_id(stream: BinaryIO, header: _Header):
    # get datum_id:
    if header.size < DATUM_ID_LEN:
        raise RuntimeError(f"not enough data for datum ID: expect {DATUM_ID_LEN} bytes but got {header.size}")

    uuid_bytes = stream.read(DATUM_ID_LEN)
    if not uuid_bytes:
        raise RuntimeError(f"cannot get {DATUM_ID_LEN} for datum ID")

    if len(uuid_bytes) != DATUM_ID_LEN:
        raise RuntimeError(f"expect {DATUM_ID_LEN} bytes for datum ID but got {len(uuid_bytes)}")

    header.size -= DATUM_ID_LEN
    uuid_str = uuid_bytes.hex()  # this str version does not have "-" between parts
    return str(uuid.UUID(uuid_str))  # this str version has "-" between parts


def _get_one_section(stream: BinaryIO, expect_datum: bool):
    buf = stream.read(HEADER_LEN)
    if not buf:
        return None, None, None

    if len(buf) != HEADER_LEN:
        raise RuntimeError(f"cannot get {HEADER_LEN} header bytes")

    header = _Header.from_bytes(buf)
    if header.size <= 0:
        raise RuntimeError(f"invalid size {header.size}")

    if expect_datum:
        if header.marker not in (MARKER_DATUM_BLOB, MARKER_DATUM_FILE):
            raise RuntimeError(f"expect datum but got {header.marker}")
    else:
        if header.marker != MARKER_MAIN:
            raise RuntimeError(f"expect main but got {header.marker}")

    datum_id = None
    if expect_datum:
        datum_id = _get_datum_id(stream, header)

    data = stream.read(header.size)
    if not data:
        raise RuntimeError(f"cannot get {header.size} data bytes")

    if len(data) != header.size:
        raise RuntimeError(f"expect {header.size} bytes but got {len(data)}")

    return header, datum_id, data


def _get_datum_dir():
    dir_name = ConfigService.get_str_var(name=DATUM_DIR_CONFIG_VAR, default=DEFAULT_DATUM_DIR)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    return dir_name


def load_from_stream(stream: BinaryIO):
    mgr = DatumManager()

    # get main body
    header, _, main_body = _get_one_section(stream, expect_datum=False)
    if not header:
        raise RuntimeError("invalid lobs content: missing main body")

    # try to get datums
    while True:
        header, datum_id, body = _get_one_section(stream, expect_datum=True)
        if not header:
            # all done
            break

        if header.marker == MARKER_DATUM_BLOB:
            datum = Datum.blob_datum(body)
        else:
            # put the value in a file
            datum_dir = _get_datum_dir()
            file_path = os.path.join(datum_dir, f"{datum_id}.bin")
            with open(file_path, "wb") as f:
                f.write(body)
            datum = Datum.file_datum(file_path)

        datum.datum_id = datum_id
        mgr.datums[datum_id] = datum
    return deserialize(main_body, mgr)


def dump_to_bytes(obj: Any, max_value_size=None):
    bio = io.BytesIO()
    dump_to_stream(obj, bio, max_value_size)
    return bio.getvalue()


def load_from_bytes(data: bytes) -> Any:
    return load_from_stream(io.BytesIO(data))


def dump_to_file(obj: Any, file_path: str, max_value_size=None):
    with open(file_path, "wb") as f:
        dump_to_stream(obj, f, max_value_size)


def load_from_file(file_path: str) -> Any:
    with open(file_path, "rb") as f:
        return load_from_stream(f)
