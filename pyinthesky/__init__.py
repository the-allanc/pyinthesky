from .base import locate
from .main import Connection

SERVICE_TYPES = {
    'urn:schemas-nds-com:device:SkyControl:2': True,
    'urn:schemas-nds-com:device:SkyServe:2': True,
    'urn:schemas-nds-com:device:SkyRemote:2': False,
}
