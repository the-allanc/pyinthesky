from .base import Connection as _ConnectionBase
from .methods import bind_service_methods
from functools import partial

class Connection(_ConnectionBase):
    
    def connect(self):
        _ConnectionBase.connect(self)
        all_services = []
        for device in self.devices.values():
            services = device.services.values()
            for service in services:
                service.connect()
                bind_service_methods(service, bind_to_class=service.name + 'Service')
                setattr(self, service.name, service)
            bind_service_methods(device, services, bind_to_class=device.devtype + 'Device')
            all_services.extend(services)
            setattr(self, device.devtype, device)
        bind_service_methods(self, all_services, bind_to_class=True)

    # XXX: Need a __str__ and a __repr__
