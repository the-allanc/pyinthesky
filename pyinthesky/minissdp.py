SERVICE_TYPES = ('urn:schemas-nds-com:device:SkyServe:2', 'urn:schemas-nds-com:device:SkyControl:2')




#data2 = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nST: urn:schemas-nds-com:device:SkyServe:2\r\nMAN: "ssdp:discover"\r\nMX: 3\r\n\r\n'
#data3 = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nST: urn:schemas-nds-com:device:SkyControl:2\r\nMAN: "ssdp:discover"\r\nMX: 3\r\n\r\n'

def encode(protocol, **headers):
    lines = [protocol]
    lines.extend(['%s: %s' % kv for kv in headers.items()])
    return '\r\n'.join(lines) + '\r\n\r\n'
    
def decode(data):
    return {k: v.upper() for (k, v) in 
        [l.split(': ', 1) for l in data.splitlines()[1:] if l]
    }

# Create a socket to send a multicast request.
MCAST_IP = "239.255.255.250"
MCAST_PORT = 1900
MCAST_IP_PORT = MCAST_IP + ':' + str(MCAST_PORT)

def search(host=None, service_types=None, timeout=5, logger=False, search_every=1):
    if logger is True:
        logger = logging.getLogger('pyinthesky.minissdp')
    if service_types is None:
        service_types = SERVICE_TYPES
        
    import struct
    import socket
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_IP), socket.INADDR_ANY)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    #sock.setblocking(False)
    sock.settimeout(0.2)
    
    import contextlib
    with contextlib.closing(sock) as sock:
        for service_type in service_types:
            yield _locate_service(host, service_type, sock, timeout, logger, search_every)
            
def _locate_service(host, service_type, sock, timeout, logger, search_every):

    import socket            

    # Search for the service.
    msg = encode('M-SEARCH * HTTP/1.1', HOST=MCAST_IP_PORT,
        ST=service_type, MAN='"ssdp: discover"', MX='3')
    
    # We keep broadcasting messages.
    import time
    now = time.time()
    give_up_by = now + timeout
    
    ok = False
    
    # We keep on trying every <search_every> seconds.
    while now < give_up_by:
        
        # Search for services.
        sock.sendto(msg, (MCAST_IP, MCAST_PORT))
        next_broadcast = time.time() + search_every
        
        # And listen for responses on the socket until we get
        # matches.
        while now < next_broadcast:
            try:
                data = sock.recv(1024)
            except socket.timeout:
                now = time.time()
                continue
            if not data.startswith('HTTP/1.1 200 OK'):
                continue
            resp = decode(data)
            if resp.get('ST') != service_type:
                continue
            return resp('ST'), resp['LOCATION']
            
    raise RuntimeError('could not find %s' % service_type)
