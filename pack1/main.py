from application import Application

multicast_group_IPv4 = '224.3.29.71'
multicast_group_IPv6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
port = 10000


def main():
    app = Application(multicast_group_IPv6, port)
    try:
        app.start()
    except KeyboardInterrupt:
        exit(0)


if __name__ == '__main__':
    main()
