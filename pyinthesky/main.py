from .base import Connection as _ConnectionBase
import six

class Connection(_ConnectionBase):

    def connect(self):
        from .methods import bind_service_methods
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

    # Browse(ObjectID, BrowseFlag, Filter, StartingIndex, RequestedCount, SortCriteria)
    def get_recordings(self, user_only=True):

        # Using Browse('BrowseDirectChildren', ObjectID=0), you can determine the valid
        # object ID's to use, which are:
        #   3 - "pvr"
        #   6 - "recycle"
        #   10 - "remote"
        from .xmlutils import text_to_etree, simple_elements_dict
        i = 0
        while True:
            res_dict = self.Browse('3', 'BrowseDirectChildren', '*', i, 25, '')
            res_etree = text_to_etree(res_dict['Result'])
            for item_node in res_etree.getroot().getchildren():
                rec = Recording(self, simple_elements_dict(item_node))
                if user_only and rec.attributes['bookingDiskQuotaName'] != 'user':
                    continue
                yield rec
            if res_dict['NumberReturned'] < 25:
                break
            i += 25

    def count_recordings(self):
        return self.Browse('3', 'BrowseDirectChildren', '*', 1, 0, '')['TotalMatches']

    def get_disk_space_info(self):
        d = self.Browse('3', 'BrowseMetadata', '*', 25, 0, '')

        from .xmlutils import text_to_etree, simple_elements_dict
        attrnode = text_to_etree(d['Result']).getroot().getchildren()[0]
        attrs = treat_attributes(simple_elements_dict(attrnode))

        kb_used = attrs['quotaInfo.usedSize']
        kb_max = attrs['quotaInfo.maxSize']
        return dict(

            # Values in KB.
            kb_used = kb_used,
            kb_max = kb_max,
            kb_free = kb_max - kb_used,

            # Values in MB.
            mb_used = kb_used / 1024,
            mb_max = kb_max / 1024,
            mb_free = (kb_max - kb_used) / 1024,

            # Values in GB.
            gb_used = kb_used / 1048576.0,
            gb_max = kb_max / 1048576.0,
            gb_free = (kb_max - kb_used) / 1048576.0,

            # Percentages.
            perc_used = (float(kb_used) / kb_max) * 100,
            perc_free = (float(kb_max - kb_used) / kb_max) * 100,
        )

    # XXX: Need a __str__ and a __repr__

def treat_attributes(attrdict):
    res = {}
    for key, value in attrdict.items():

        # Drop X_ prefix.
        if key.startswith('X_'):
            key = key[2:]

        # Things that look like integers, will become integers.
        if value.isdigit():
            value = int(value)

        # Flags are obviously booleans.
        if key.startswith('flags.'):
            value = bool(value)

        # As well as any type of "isXXX" value.
        lkey = key.split('.')[-1]
        if lkey.startswith('is') and lkey[2].isupper():
            value = bool(value)

        # If it looks like a ISO8601 datetime, and the key seems to
        # imply a datetime, then convert it as such.
        import iso8601
        if key.endswith('Time') and ':' in value and '-' in value \
            and 'T' in value:
            value = iso8601.parse_date(value)

        res[key] = value

    return res

@six.python_2_unicode_compatible
class Recording(object):

    def __init__(self, connection, attributes):
        self.connection = connection
        self.attributes = treat_attributes(attributes)
        #for name, value in simple_elements_dict.items():
        #    setattr(self, name, value)

    @property
    def schedtime_text(self):
        if 'scheduledStartTime' not in self.attributes:
            return ''
        startdate = self.attributes['scheduledStartTime']
        return startdate.strftime('%Y-%m-%d %H:%M')

    def __repr__(self):
        schedtime = self.schedtime_text
        tmpl = '<Recording "{title}" ({channelName})'
        if schedtime:
            tmpl += ' at {0}'
        tmpl += '>'
        return tmpl.format(schedtime, **self.attributes)

    def __str__(self):
        schedtime = self.schedtime_text
        tmpl = u'{title}" ({channelName})'
        if schedtime:
            tmpl += u' [{0}]'
        tmpl += u' - "{description}"'
        return tmpl.format(schedtime, **self.attributes)
