import logging
from Collector import Collector
from prometheus_client.core import GaugeMetricFamily
from typing import Dict, List

LOG = logging.getLogger('apic_exporter.exporter')


class ApicSpinePortsCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_spine_ports', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_free_port_count', 'Total available free ports')

        yield GaugeMetricFamily('network_apic_used_port_count', 'Total in-use ports')

        yield GaugeMetricFamily('network_apic_down_port_count', 'In-use but down ports')

    def get_query(self) -> str:
        return '/api/node/class/fabricNode.json?' + \
               '&query-target-filter=eq(fabricNode.role,"spine")&order-by=fabricNode.id|asc'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:

        g_free_port = GaugeMetricFamily('network_apic_free_port_count',
                                        'Total available free ports',
                                        labels=['apicHost', 'Spine_id', 'pod_id'])

        g_used_port = GaugeMetricFamily('network_apic_used_port_count',
                                        'Total in-use ports',
                                        labels=['apicHost', 'Spine_id', 'pod_id'])

        g_down_port = GaugeMetricFamily('network_apic_down_port_count',
                                        'In-use but down ports',
                                        labels=['apicHost', 'Spine_id', 'pod_id'])

        count = data['totalCount']
        spine_dn_list = []
        for x in range(0, int(count)):
            dn = str(data['imdata'][x]['fabricNode']['attributes']['dn'])
            spine_dn_list.append(str(dn))

        # fetch physcal port from each spine
        for dn in spine_dn_list:
            query_url = f'/api/node/mo/{dn}/sys.json?rsp-subtree=full&rsp-subtree-class=ethpmPhysIf'
            free_port = []
            used_port = []
            down_port = []

            output = self.query_host(host, query_url)
            if output is None:
                continue

            for x in output['imdata']:
                pod_id = x['topSystem']['attributes']['podId']
                spine_id = x['topSystem']['attributes']['id']
                for port_dict in x['topSystem']['children']:
                    if (port_dict['l1PhysIf']['attributes']['adminSt'] == 'up' and
                            port_dict['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']['operSt'] == 'down'):
                        port_number = port_dict['l1PhysIf']['attributes']['id']
                        free_port.append(str(port_number))

                    elif (port_dict['l1PhysIf']['attributes']['adminSt'] == 'up' and
                          port_dict['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']['operSt'] == 'up'):
                        port_number = port_dict['l1PhysIf']['attributes']['id']
                        used_port.append(str(port_number))

                    elif port_dict['l1PhysIf']['attributes']['adminSt'] == 'down':
                        port_number = port_dict['l1PhysIf']['attributes']['id']
                        down_port.append(str(port_number))

            # Free Ports
            g_free_port.add_metric(labels=[host, spine_id, pod_id], value=len(free_port))

            # Used Ports
            g_used_port.add_metric(labels=[host, spine_id, pod_id], value=len(used_port))

            # Down ports
            g_down_port.add_metric(labels=[host, spine_id, pod_id], value=len(down_port))

        return [g_free_port, g_used_port, g_down_port]
