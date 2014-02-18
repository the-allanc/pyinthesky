from .base import Connection as _ConnectionBase
from .methods import method_sig_wrapper as mkfunc
from functools import partial

class Connection(_ConnectionBase):
    
    def connect(self):
        _ConnectionBase.connect(self)
        self.method_registry = {}
        for device in self.devices.values():
            for service in device.services.values():
                self._connect_service(service)
                for m, f in service.method_registry.items():
                    setattr(self, m, f)
                    self.method_registry[m] = f
                
    def _connect_service(self, service):
        service.connect()
        service.method_registry = {}
        for methname, (in_args, out_args) in service.methods.items():
            target = partial(service.invoke, methname)
            f = mkfunc(target, methname, in_args.argument_order, in_args.argument_defaults)
            service.method_registry[methname] = f
            setattr(service, methname, f)
