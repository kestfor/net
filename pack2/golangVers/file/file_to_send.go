package file

import (
	. "../socket_connection"
	"encoding/binary"
	"io"
	"os"
	"strings"
)

const buffSize int = 4096

type FileSender interface {
	Send() error
	Response() error
	Close() error
}

type FileToSend struct {
	path       string
	name       string
	size       uint64
	headerRead bool
	sender     *SocketSender
	fileReader *os.File
}

func getName(path string) string {
	index := strings.LastIndex(strings.ToLower(path), "\\")
	if index != -1 {
		return path[index+1:]
	} else {
		return path
	}
}

func NewFileSender(address string, port int, path string) *FileToSend {
	file, err := os.Open(path)
	info, err := os.Stat(path)
	if err != nil {
		panic(err)
	}
	res := &FileToSend{path: path, name: getName(path), size: uint64(info.Size())}
	res.sender = NewSocketSender(address, port)
	res.headerRead = false
	res.fileReader = file
	return res
}

func (f *FileToSend) getHeader() []byte {
	sizeEncoded := make([]byte, 8)
	binary.BigEndian.PutUint64(sizeEncoded, uint64(f.size))
	fileNameLength := len(f.name)
	fileNameLengthEncoded := make([]byte, 2)
	binary.BigEndian.PutUint16(fileNameLengthEncoded, uint16(fileNameLength))
	fileNameEncoded := []byte(f.name)
	res := append(sizeEncoded, fileNameLengthEncoded...)
	res = append(res, fileNameEncoded...)
	return res
}

func (f *FileToSend) Send() error {
	buff := make([]byte, buffSize)
	startInd := 0
	if f.headerRead == false {
		header := f.getHeader()
		for v := range header {
			buff[v] = header[v]
		}
		startInd = len(header)
		f.headerRead = true
	}
	n, err := f.fileReader.Read(buff[startInd:])
	if n == 0 {
		return io.EOF
	}
	if err != nil {
		return err
	}
	return f.sender.Send(buff)
}

func (f *FileToSend) Close() error {
	return f.fileReader.Close()
}

func (f *FileToSend) Response() []byte {
	return f.sender.Response()
}
