package main

import (
	. "../file"
	. "../socket_connection"
	"fmt"
)

const (
	addr = "192.168.0.187"
	port = 1100
)

func receive() {
	r := NewSocketReceiver(port)
	r.Listen()
	s, err := r.Accept()
	if err != nil {
		panic(err)
	}
	fmt.Println("got new connection", s.RemoteAddr())
	data := make([]byte, 4096)
	file := NewFileReceiver(s, "C:\\Users\\anzhi\\netPacks\\packs\\pack2\\golangVers\\main\\uploads")
	for err := file.Write(data); err == nil; err = file.Write(data) {
	}
	fmt.Println(err)
	fmt.Println("here")
	fmt.Println(s.Write([]byte("ok")))
}

func send() {
	fmt.Println("send")
	s := NewSocketSender(addr, port)
	if err := s.Send([]byte("тест")); err != nil {
		panic(err)
	}
}

func main() {
	receive()
	//f := NewFileSender(addr, port, "C:\\Users\\anzhi\\netPacks\\packs\\pack2\\golangVers\\тест")
	//fmt.Println(f.Send())

}
