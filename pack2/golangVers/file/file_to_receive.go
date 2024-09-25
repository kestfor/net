package file

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"os"
)

type FileReceiver interface {
	Write([]byte) error
	Close() error
}

type FileToReceive struct {
	path       string
	size       uint64
	dir        string
	headerRead bool
	receiver   net.Conn
	fileWriter *os.File
}

func NewFileReceiver(receiver net.Conn, dir string) *FileToReceive {
	res := &FileToReceive{dir: dir}
	res.receiver = receiver
	res.headerRead = false
	return res
}

func (r *FileToReceive) readHeader(buff []byte) int {
	r.size = binary.BigEndian.Uint64(buff[0:8])
	filenameLen := binary.BigEndian.Uint16(buff[8:10])
	r.path = r.dir + "/" + string(buff[10:10+filenameLen])
	file, err := os.Create(r.path)
	if err != nil {
		panic(err)
	}
	r.fileWriter = file
	return int(10 + filenameLen)
}

func (r *FileToReceive) Write(buff []byte) error {
	startInd := 0
	n, err := r.receiver.Read(buff)
	fmt.Println("got ", n, " bytes")
	if n == 0 {
		return io.EOF
	}
	if err != nil {
		return err
	}
	if !r.headerRead {
		startInd = r.readHeader(buff)
		r.headerRead = true
	}
	_, err = r.fileWriter.Write(buff[startInd:])
	return err
}
