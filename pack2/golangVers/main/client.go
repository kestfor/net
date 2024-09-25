package main

import (
	. "../file"
	"fmt"
)

func main() {
	f := NewFileSender("192.168.0.187", 1100, "C:\\Users\\anzhi\\netPacks\\packs\\pack2\\golangVers\\тест")
	for err := f.Send(); err == nil; err = f.Send() {

	}
	f.Close()
	fmt.Println("here")
	fmt.Println(f.Response())
}
