# bin struct - header + data
import os


# header
# first 8 bytes - size of file in bytes
# second 2 bytes - len of file_name in bytes (n)
# filename - n bytes

# data
# filedata other bytes

class File:
    _size_encoded_len = 8
    _filename_len_encoded_len = 2
    _byteorder = "big"
    _encoding = "utf-8"


class FileToSend(File):

    def __init__(self, filename: str, path: str):
        self._filename = filename
        self._path = path
        self._size = os.stat(self._path).st_size  # in bytes

    def _pack_info(self) -> bytes:
        size_encoded = self._size.to_bytes(self._size_encoded_len, self._byteorder)
        filename_encoded = bytes(self._filename, encoding=self._encoding)
        filename_len = len(filename_encoded)
        filename_len_encoded = filename_len.to_bytes(self._filename_len_encoded_len, self._byteorder)
        return size_encoded + filename_len_encoded + filename_encoded

    def raw_header(self) -> bytes:
        return self._pack_info()

    @property
    def path(self) -> str:
        return self._path


class FileToReceive(File):

    def __init__(self, raw_header: bytes):
        self._size = 0
        self._filename = ''
        self._raw_file_start_ind = 0
        self._remain = bytes()
        self._parse_header(raw_header)

    def _parse_header(self, raw_header: bytes):
        try:
            self._size = int.from_bytes(raw_header[:self._size_encoded_len], self._byteorder)
            filename_len = int.from_bytes(
                raw_header[self._size_encoded_len:self._filename_len_encoded_len + self._size_encoded_len],
                self._byteorder)
            self._raw_file_start_ind = self._filename_len_encoded_len + self._size_encoded_len + filename_len
            self._filename = raw_header[
                             self._filename_len_encoded_len + self._size_encoded_len:self._raw_file_start_ind].decode(
                self._encoding)

            self._remain = raw_header[self._raw_file_start_ind:]
        except Exception as e:
            raise RuntimeError("can't parse header")

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def size(self) -> int:
        return self._size

    def get_remain(self) -> bytes:
        return self._remain
