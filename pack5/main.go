package main

import (
	"fmt"
	"pack5/socks5"
)

func main() {
	config := socks5.NewConfig(nil)
	server := socks5.NewServer(config)
	err := server.ListenAndServe("0.0.0.0:8000")
	if err != nil {
		fmt.Println(err)
	}
}
