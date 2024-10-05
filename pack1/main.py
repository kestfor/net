from application import Application

multicast_group_IPv4 = '224.0.0.1'
multicast_group_IPv6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
port = 10000


def main():
    app = Application(multicast_group_IPv4, port)
    try:
        app.start()
    except KeyboardInterrupt:
        app.close()


if __name__ == '__main__':
    main()
