# global import
from datetime import datetime
from .apstra_session import CkApstraSession
from .apstra_blueprint import CkApstraBlueprint, CkEnum, IpLinkEnum
from .generic_system import GsCsvKeys, add_generic_systems
from .connectivity_template import CtCsvKeys, import_ip_link_ct
from .util import prep_logging, deep_copy

data_dict = {
    'blueprint': {
        'BP_NAME': {
            'dci': {
                'DCI_NAME': {
                    'esi_mac_msb': 2,
                    'interconnect': {},
                    'ott': {},
                },
            },
            'catalog': {
                'logical_device': {
                    'LD_NAME': {
                        'panels': [],
                    },
                },
                'interface_map': {
                    'IM_NAME': {
                        'logical_device': 'LD_NAME',
                        'device_profile': 'DP_NAME',
                    },
                },
            },
            'physical': {
                'node': {
                    'NODE_NAME': {
                        'old_labe': 'NODE_NAME',
                        'label': 'NODE_NAME',
                        'tags': [],
                        'role': 'leaf',  ## spine, leaf, generic_system, super_spine
                        'external': False,
                        'deploy_mode': None,
                        'interface_map': 'IM_NAME',
                        'device_profile': 'DP_NAME',
                        'hostname': 'HOSTNAME',
                        'asn': 65000,
                        'loopback_ipv4': '1.2.3.4/32',
                        'loopback_ipv6': '2001:db8::1/128',
                    },
                },
            },
        },
    },
    'resources': {},
}