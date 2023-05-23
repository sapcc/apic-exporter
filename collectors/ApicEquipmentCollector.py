import logging
import re
from collections import namedtuple
from typing import Dict, List

from Collector import Collector
from prometheus_client.core import GaugeMetricFamily

LOG = logging.getLogger('apic_exporter.exporter')


class ApicEquipmentCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_equipment', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_flash_readwrite', 'APIC flash is read and writeable')

    def get_query(self) -> str:
        return '/api/node/class/eqptFlash.json' + \
                '?rsp-subtree=full&query-target-filter=wcard(eqptFlash.model,\"Micron_M500IT\")'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        """Collect read-write status of flash equipment"""

        g_flash_rw = GaugeMetricFamily('network_apic_flash_readwrite',
                                       'APIC flash is read and writeable',
                                       labels=['apicHost', 'node', 'type', 'vendor', 'model'])

        eqpt_template = namedtuple("apic_equipment", ['type', 'vendor', 'model', 'nodeId', 'acc'])

        # get a list of all flash devices NOT in read-write mode
        flashes = [
            eqpt_template(type=d['eqptFlash']['attributes']['type'],
                          vendor=d['eqptFlash']['attributes']['vendor'],
                          model=d['eqptFlash']['attributes']['model'],
                          nodeId=self._parseNodeId(d['eqptFlash']['attributes']['dn']),
                          acc=d['eqptFlash']['attributes']['acc'])
            for d in data['imdata']
            if d['eqptFlash']['attributes']['model'].startswith('Micron_M500IT')
        ]

        for flash in flashes:
            if flash.acc == 'read-write':
                g_flash_rw.add_metric(labels=[host, flash.nodeId, flash.type, flash.vendor, flash.model], value=1)
            else:
                g_flash_rw.add_metric(labels=[host, flash.nodeId, flash.type, flash.vendor, flash.model], value=0)

        return [g_flash_rw]

    def _parseNodeId(self, dn):
        matchObj = re.match(u".+node-([0-9]*).+", dn)
        return matchObj.group(1) if matchObj is not None else ''
