package socks5

import (
	"fmt"
	"io"
	"log"
	"net"
)

const (
	SOCKS_VERSION = uint8(0x5)
)

type Server struct {
	logger *log.Logger
	config *Config
}

func NewServer(config *Config) *Server {
	return &Server{logger: log.Default(), config: config}
}

func (server *Server) serve(listener net.Listener) error {
	for {
		conn, err := listener.Accept()
		if err != nil {
			return err
		}
		go server.handleNewConnection(conn)
	}

}

func (server *Server) ListenAndServe(address string) error {
	conn, err := net.Listen("tcp", address)
	if err != nil {
		return err
	}
	return server.serve(conn)
}

func (server *Server) authenticate(reader io.Reader, writer io.Writer) error {
	methods, err := readMethods(reader)
	if err != nil {
		return err
	}
	for _, method := range methods {
		auth, found := server.config.AuthMethods[method]
		if found {
			return auth.Authenticate(reader, writer)
		}
	}
	return noAcceptableAuth(writer)
}

func (server *Server) handleNewConnection(conn net.Conn) error {
	defer conn.Close()

	version := make([]byte, 1)

	if _, err := conn.Read(version); err != nil {
		server.logger.Printf("[ERR] failed to get: %v", int(version[0]))
		return err
	}

	if version[0] != SOCKS_VERSION {
		err := fmt.Errorf("unsupported SOCKS version: %v", version)
		server.logger.Printf("[ERR] unsuported socks version: %v", int(version[0]))
		return err
	}

	if err := server.authenticate(conn, conn); err != nil {
		err = fmt.Errorf("failed to authenticate: %v", err)
		server.logger.Printf("[ERR] socks: %v", err)
		return err
	}

	request, err := NewRequest(conn)
	if err != nil {
		server.logger.Printf("[ERR] failed to create request: %v", err)
		return err
	}

	if err := handleRequest(conn, request); err != nil {
		err = fmt.Errorf("failed to handle request: %v", err)
		server.logger.Printf("[ERR] socks: %v", err)
		return err
	}

	return nil
}
