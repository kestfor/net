package socket_connection

import (
	"net"
	"strconv"
)

type Receiver interface {
	Listen()
	Accept() (net.Conn, error)
}

type SocketReceiver struct {
	port   int
	socket net.Listener
}

func NewSocketReceiver(port int) *SocketReceiver {
	res := &SocketReceiver{port: port}
	return res
}

func (receiver *SocketReceiver) Listen() {
	var err error
	receiver.socket, err = net.Listen("tcp", "0.0.0.0:"+strconv.Itoa(receiver.port))
	if err != nil {
		panic(err)
	}
}

func (receiver *SocketReceiver) Accept() (net.Conn, error) {
	return receiver.socket.Accept()
}
