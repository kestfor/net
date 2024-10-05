package socks5

import (
	"encoding/binary"
	"fmt"
	"io"
)

const (
	NO_AUTH           = uint8(0)
	GSSAPI            = uint8(1)
	USERNAME_PASSWORD = uint8(2)
	NO_ACCEPTABLE     = uint8(0xff)
	USER_AUTH_VERSION = uint8(0x1)
	SUCCESS           = uint8(0)
	FAILURE           = uint8(0x1)
)

type ClientGreetingHeader struct {
	version                  uint8
	numberOfSupportedMethods uint8
}

type ServerChoice struct {
	version    uint8
	authMethod uint8
}

type PassAuthData struct {
	version        uint8
	usernameLength uint8
	username       []byte
	passwordLength uint8
	password       []byte
}

type Credentials interface {
	Valid(username, password string) bool
}

type StaticCredentials struct {
	Username string
	Password string
}

func (cr *StaticCredentials) Valid(username, password string) bool {
	return cr.Username == username && cr.Password == password
}

type Authenticator interface {
	Authenticate(reader io.Reader, writer io.Writer) error
	Code() uint8
}

type NoAuthAuthenticator struct{}

func (auth *NoAuthAuthenticator) Code() uint8 {
	return NO_AUTH
}

func (auth *NoAuthAuthenticator) Authenticate(reader io.Reader, writer io.Writer) error {
	return binary.Write(writer, binary.BigEndian, ServerChoice{version: SOCKS_VERSION, authMethod: NO_AUTH})
}

type UsernamePasswordAuthenticator struct {
	credentials Credentials
}

func (auth *UsernamePasswordAuthenticator) Code() uint8 {
	return USERNAME_PASSWORD
}

func (auth *UsernamePasswordAuthenticator) Authenticate(reader io.Reader, writer io.Writer) error {
	var data []byte

	if _, err := io.ReadAtLeast(reader, data, 1); err != nil {
		return err
	}

	version := data[0]

	if version != USER_AUTH_VERSION {
		return fmt.Errorf("unsupported auth version: %v", data[0])
	}

	userNameLength := int(data[1])
	userName := make([]byte, userNameLength)

	if _, err := io.ReadAtLeast(reader, userName, userNameLength); err != nil {
		return err
	}

	if _, err := reader.Read(data[:1]); err != nil {
		return err
	}

	passwordLength := int(data[0])

	password := make([]byte, passwordLength)
	if _, err := io.ReadAtLeast(reader, password, passwordLength); err != nil {
		return err
	}

	if auth.credentials.Valid(string(userName), string(password)) {
		return binary.Write(writer, binary.BigEndian, []byte{USER_AUTH_VERSION, SUCCESS})
	} else {
		return binary.Write(writer, binary.BigEndian, []byte{USER_AUTH_VERSION, FAILURE})
	}

}

func noAcceptableAuth(conn io.Writer) error {
	_, err := conn.Write([]byte{SOCKS_VERSION, NO_ACCEPTABLE})
	if err != nil {
		return err
	}
	return fmt.Errorf("no supported authentication mechanism")
}

func readMethods(reader io.Reader) ([]byte, error) {
	data := make([]byte, 1)
	if _, err := io.ReadAtLeast(reader, data, 1); err != nil {
		return nil, err
	}

	num := int(data[0])
	methods := make([]byte, num)
	if _, err := io.ReadAtLeast(reader, methods, num); err != nil {
		return nil, err
	}
	return methods, nil
}
