package socks5

type Config struct {
	AuthMethods map[uint8]Authenticator
	Credentials Credentials
}

func NewConfig(credentials Credentials) *Config {
	methods := map[uint8]Authenticator{NO_AUTH: &NoAuthAuthenticator{}}
	if credentials != nil {
		methods[USERNAME_PASSWORD] = &UsernamePasswordAuthenticator{credentials: credentials}
	}
	return &Config{AuthMethods: methods, Credentials: credentials}
}
