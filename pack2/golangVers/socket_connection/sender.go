package socket_connection

import (
	"net"
	"strconv"
)

type Sender interface {
	Close() error
	Send([]byte) error
	Response() []byte
}

type SocketSender struct {
	address string
	port    int
	socket  net.Conn
}

func NewSocketSender(address string, port int) *SocketSender {
	res := &SocketSender{address: address, port: port}
	var err error
	res.socket, err = net.Dial("tcp", address+":"+strconv.Itoa(res.port))
	if err != nil {
		panic(err)
	}
	return res
}

func (s *SocketSender) Close() error {
	return s.socket.Close()
}

func (s *SocketSender) Send(data []byte) error {
	sent, err := s.socket.Write(data)
	for sent != len(data) {
		if err != nil {
			return err
		}
		var nowSent = 0
		nowSent, err = s.socket.Write(data[sent:])
		sent += nowSent
	}
	return err
}

func (s *SocketSender) Response() []byte {
	data := make([]byte, 10)
	_, err := s.socket.Read(data)
	if err != nil {
		panic(err)
	}
	return data
}
