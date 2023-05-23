import logging
from typing import Dict, List

from prometheus_client.core import GaugeMetricFamily

from Collector import Collector

LOG = logging.getLogger('apic_exporter.exporter')


class ApicInterfacesCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_interfaces', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_physcial_interface_reset_counter',
                                'APIC physical interface reset counter')

    def get_query(self) -> str:
        return '/api/node/class/ethpmPhysIf.json?query-target-filter=gt(ethpmPhysIf.resetCtr,"0")'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        LOG.debug('collecting apic interface metrics ...')

        g = GaugeMetricFamily('network_apic_physcial_interface_reset_counter',
                              'APIC physical interface reset counter',
                              labels=['apicHost', 'interfaceID'])

        # physical interface reset counter
        for item in data['imdata']:
            g.add_metric(labels=[host, item['ethpmPhysIf']['attributes']['dn']],
                         value=item['ethpmPhysIf']['attributes']['resetCtr'])
        return [g]
