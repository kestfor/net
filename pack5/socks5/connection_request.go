package socks5

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"strings"
)

const (
	TCP_IP_STREAM      = uint8(1)
	TCP_IP_PORT_BIND   = uint8(2)
	UDP_PORT_ASSOCIATE = uint8(3)

	IPV4_ADDR   = uint8(1)
	IPV6_ADDR   = uint8(4)
	DOMAIN_NAME = uint8(3)
)

const (
	REQUEST_GRANTED                        = uint8(iota)
	GENERAL_FAILURE                        = uint8(iota)
	CONNECTION_NOT_ALLOWED_BY_RULESET      = uint8(iota)
	NETWORK_UNREACHABLE                    = uint8(iota)
	HOST_UNREACHABLE                       = uint8(iota)
	CONNECTION_REFUSED_BY_DESTINATION_HOST = uint8(iota)
	TTL_EXPIRED                            = uint8(iota)
	COMMAND_NOT_SUPPORTED                  = uint8(iota)
	ADDRESS_TYPE_NOT_SUPPORTED             = uint8(iota)
)

type AddrSpec struct {
	IP         net.IP
	Port       uint16
	DomainName string
}

type Request struct {
	SourceAddr      net.Addr
	DestinationAddr net.Addr
	Command         uint8
}

func readAddrSpec(reader io.Reader) (*AddrSpec, error) {
	res := &AddrSpec{}
	addrType := make([]byte, 1)
	if _, err := reader.Read(addrType); err != nil {
		return nil, err
	}
	switch addrType[0] {
	case IPV4_ADDR:
		address := make([]byte, 4)
		if _, err := io.ReadAtLeast(reader, address, 4); err != nil {
			return nil, err
		}
		res.IP = address
		break
	case IPV6_ADDR:
		address := make([]byte, 16)
		res.IP = address
		break
	case DOMAIN_NAME:
		if _, err := reader.Read(addrType); err != nil {
			return nil, err
		}

		length := int(addrType[0])
		name := make([]byte, length)

		if _, err := io.ReadAtLeast(reader, name, length); err != nil {
			return nil, err
		}

		res.DomainName = string(name)

		break
	default:
		return nil, fmt.Errorf("unsupported address type")
	}

	port := []byte{0, 0}
	if _, err := io.ReadAtLeast(reader, port, 2); err != nil {
		return nil, err
	}
	res.Port = binary.BigEndian.Uint16(port)
	return res, nil
}

func NewRequest(conn net.Conn) (*Request, error) {

	version := make([]byte, 1)

	if _, err := io.ReadAtLeast(conn, version, 1); err != nil {
		return nil, err
	}

	if version[0] != SOCKS_VERSION {
		sendReply(conn, GENERAL_FAILURE, nil)
		return nil, fmt.Errorf("not supported socks version")
	}

	data := make([]byte, 2)
	if _, err := io.ReadAtLeast(conn, data, 2); err != nil {
		return nil, err
	}

	command := data[0]

	addrSpec, err := readAddrSpec(conn)
	if err != nil {
		sendReply(conn, ADDRESS_TYPE_NOT_SUPPORTED, nil)
		return nil, err
	}

	if addrSpec.DomainName != "" {
		DNSResolver{}.Resolve(addrSpec.DomainName)
		addr, err := DNSResolver{}.Resolve(addrSpec.DomainName)
		if err != nil {
			sendReply(conn, HOST_UNREACHABLE, nil)
			return nil, err
		}
		addrSpec.IP = addr.IP
	}

	source := conn.RemoteAddr().(*net.TCPAddr)
	dest := net.TCPAddr{IP: addrSpec.IP, Port: int(addrSpec.Port)}
	return &Request{SourceAddr: source, DestinationAddr: &dest, Command: command}, nil
}

func sendReply(writer io.Writer, status uint8, addr *AddrSpec) error {
	version := SOCKS_VERSION
	var addrType uint8
	var addrBody []byte
	addrPort := make([]byte, 2)
	switch {
	case addr.DomainName != "":
		addrType = DOMAIN_NAME
		addrBody = []byte(addr.DomainName)
		break

	case addr.IP.To4() != nil:
		addrType = IPV4_ADDR
		addrBody = addr.IP.To4()
		break

	case addr.IP.To16() != nil:
		addrType = IPV6_ADDR
		addrBody = addr.IP.To16()
		break

	default:
		return fmt.Errorf("failed to format address: %v", addr)
	}

	if _, err := binary.Encode(addrPort, binary.BigEndian, addr.Port); err != nil {
		return fmt.Errorf("failed to encode port: %v", err)
	}

	answer := make([]byte, 6+len(addrBody))
	answer[0] = version
	answer[1] = status
	answer[2] = 0
	answer[3] = addrType
	copy(answer[4:], addrBody)
	copy(answer[4+len(addrBody):], addrPort)
	_, err := writer.Write(answer)
	return err
}

func handleRequest(conn net.Conn, request *Request) error {
	switch request.Command {
	case TCP_IP_STREAM:
		return handleTCPStream(conn, request)
	case TCP_IP_PORT_BIND:
		if err := sendReply(conn, COMMAND_NOT_SUPPORTED, nil); err != nil {
			return fmt.Errorf("failed to send reply: %v", err)
		}
		return fmt.Errorf("tcp ip port bind currently not supported")
	case UDP_PORT_ASSOCIATE:
		if err := sendReply(conn, COMMAND_NOT_SUPPORTED, nil); err != nil {
			return fmt.Errorf("failed to send reply: %v", err)
		}
		return fmt.Errorf("udp port associtae currently not supported")
	default:
		if err := sendReply(conn, COMMAND_NOT_SUPPORTED, nil); err != nil {
			return fmt.Errorf("failed to send reply: %v", err)
		}
		return fmt.Errorf("unsupported command: %v", request.Command)
	}
}

func handleTCPStream(conn net.Conn, request *Request) error {

	target, err := net.Dial("tcp", request.DestinationAddr.String())
	if err != nil {
		msg := err.Error()
		status := HOST_UNREACHABLE
		if strings.Contains(msg, "refused") {
			status = CONNECTION_REFUSED_BY_DESTINATION_HOST
		} else if strings.Contains(msg, "network is unreachable") {
			status = NETWORK_UNREACHABLE
		}
		if err := sendReply(conn, status, nil); err != nil {
			return fmt.Errorf("failed to send reply: %v", err)
		}
		return fmt.Errorf("failed to connect to target host: %v", err)
	}
	defer target.Close()
	local := target.LocalAddr().(*net.TCPAddr)
	bind := AddrSpec{IP: local.IP, Port: uint16(local.Port)}

	if err := sendReply(conn, SUCCESS, &bind); err != nil {
		return fmt.Errorf("failed to send reply: %v", err)
	}

	errChannels := make(chan error, 2)
	go startProxy(conn, target, errChannels)
	go startProxy(target, conn, errChannels)

	for i := 0; i < 2; i++ {
		e := <-errChannels
		if e != nil {
			return e
		}
	}
	return nil
}

func startProxy(destination net.Conn, source net.Conn, errChannels chan error) {
	_, err := io.Copy(destination, source)

	if tcpConn, ok := destination.(interface{ CloseWrite() error }); ok {
		tcpConn.CloseWrite()
	}

	errChannels <- err
}
