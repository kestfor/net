package socks5

import (
	"net"
)

type NameResolver interface {
	Resolve(name string) (net.IP, error)
}

type DNSResolver struct{}

func (r DNSResolver) Resolve(name string) (*net.IPAddr, error) {
	addr, err := net.ResolveIPAddr("ip", name)
	if err != nil {
		return nil, err
	}
	return addr, nil
}
