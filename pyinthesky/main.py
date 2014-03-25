from .base import Connection as _ConnectionBase
from .methods import method_sig_wrapper as mkfunc, make_ambiguous_function as ambig
from functools import partial

class Connection(_ConnectionBase):
    
    def connect(self):
        _ConnectionBase.connect(self)

        # Build up method registries for the connection.
        conn_methods = {}

        for device in self.devices.values():
            
            # Build up method registries for the device too.
            dev_methods = {}
            
            # Process methods for each service.
            for service in device.services.values():
                self._connect_service(service)
                for m, f in service.method_registry.items():
                    
                    # Populate parent method registries.
                    dev_methods.setdefault(m, []).append(
                        [f, '.'.join(('device', service.name, m))])
                    conn_methods.setdefault(m, []).append(
                        [f, '.'.join(('conn', device.devtype, service.name, m))])
                        
                setattr(self, service.name, service)
                setattr(device, service.name, service)
                    
            # Bind aliases to device objects.
            for methname, methods in dev_methods.items():
                if len(methods) == 1:
                    setattr(device, methname, methods[0][0])
                else:
                    f = ambig(methname, [x[1] for x in methods])
                    setattr(device, methname, f)
                    
            setattr(self, device.devtype, device)
       
        # Bind aliases to this connection object.
        for methname, methods in conn_methods.items():
            if len(methods) == 1:
                setattr(self, methname, methods[0][0])
            else:
                f = ambig(methname, [x[1] for x in methods])
                setattr(self, methname, f)
                    
    def _connect_service(self, service):
        service.connect()
        service.method_registry = {}
        for methname, (in_args, out_args) in service.methods.items():
            target = partial(service.invoke, methname)
            f = mkfunc(target, methname, in_args.argument_order, in_args.argument_defaults)
            service.method_registry[methname] = f
            setattr(service, methname, f)

    # XXX: Need a __str__ and a __repr__
