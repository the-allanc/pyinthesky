def encode(protocol, **headers):
    lines = [protocol]
    lines.extend(['%s: %s' % kv for kv in headers.items()])
    return ('\r\n'.join(lines) + '\r\n\r\n').encode('ascii')

def decode(data):
    res = {}
    for dataline in data.decode('ascii').splitlines()[1:]:
        line_parts = dataline.split(':', 1)
        # This is to deal with headers with no value.
        if len(line_parts) < 2:
            line_parts = (line_parts[0], '')
        res[line_parts[0].strip().upper()] = line_parts[1].strip()
    return res

MCAST_IP = "239.255.255.250"
MCAST_PORT = 1900
MCAST_IP_PORT = MCAST_IP + ':' + str(MCAST_PORT)

# Create a socket to send a multicast request.
def make_socket():
    import struct
    import socket
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_IP), socket.INADDR_ANY)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(0.2)
    return sock

def service_search(sock, service_type=None, host=None, timeout=10, logger=None, search_every=2):

    if not logger:
        import logging
        logger = logging.getLogger('pyinthesky.minissdp')

    # Search for the service.
    msgparts = dict(HOST=MCAST_IP_PORT, MAN='"ssdp:discover"', MX='3')
    if service_type:
        msgparts['ST'] = service_type
    msg = encode('M-SEARCH * HTTP/1.1', **msgparts)

    # Figure out how long we can run for.
    import time
    now = time.time()
    give_up_by = now + timeout

    # We keep on trying every <search_every> seconds.
    while now < give_up_by:

        # Search for services.
        sock.sendto(msg, (MCAST_IP, MCAST_PORT))
        next_broadcast = time.time() + search_every

        # And listen for responses on the socket until we get
        # matches.
        import socket
        while now < next_broadcast:
            try:
                data = sock.recv(1024)
            except socket.timeout:
                now = time.time()
                continue

            for data_prefix, servkey in [
                (b'HTTP/1.1 200 OK', 'ST'),
                (b'NOTIFY * HTTP/1.1', 'NT')
            ]:
                if data[:len(data_prefix)] == data_prefix:
                    break
            else:
                continue

            resp = decode(data)
            resp_servtype = resp[servkey]

            # Didn't match particular service.
            if service_type not in (resp_servtype, None):
                continue

            # Perform a host check if we need to.
            location = resp['LOCATION']
            if host:
                import urlparse
                urlobj = urlparse.urlparse(location)
                if host not in (urlobj.netloc, urlobj.hostname):
                    continue

            yield resp_servtype, location

def search(service_types=None, host=None, timeout=5, logger=None,
    resources_only=False):
    if not logger:
        import logging
        logger = logging.getLogger('pyinthesky.minissdp')

    if service_types is None:
        from pyinthesky import SERVICE_TYPES
        service_types = SERVICE_TYPES

    if not isinstance(service_types, dict):
        service_types = dict.fromkeys(service_types, True)

    import contextlib
    with contextlib.closing(make_socket()) as sock:
        for (service_type, required) in service_types.items():
            for res in service_search(sock, service_type, host, timeout, logger):
                yield res[1] if resources_only else res
                break
            else:
                # If it's required, complain. If not, just skip.
                if required:
                    from requests import Timeout
                    err = 'unable to find service of type "%s" within %s seconds'
                    raise Timeout(err % (service_type, timeout))
