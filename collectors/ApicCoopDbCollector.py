from Collector import Collector
import logging
from prometheus_client.core import GaugeMetricFamily
from typing import List, Dict

LOG = logging.getLogger('apic_exporter.exporter')


class ApicCoopDbCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_coop', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_coop_records_total', 'APIC COOP DB entries')

    def get_query(self) -> str:
        return '/api/node/class/fabricNode.json?query-target-filter=eq(fabricNode.role,"spine")'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        """Collect the number of entries in the coop db for all spines"""
        g_coop_db = GaugeMetricFamily('network_apic_coop_records_total',
                                      'APIC COOP DB entries',
                                      labels=['apicHost', 'spineDn'])

        for spine in data['imdata']:
            spine_attributes = spine['fabricNode']['attributes']
            query_coop_count = '/api/node/mo/' + \
                               spine_attributes['dn'] + \
                               '/sys/coop/inst/dom-overlay-1.json' + \
                               '?query-target=subtree&target-subtree-class=coopEpRec&rsp-subtree-include=count'
            fetched_data = self.query_host(host, query_coop_count)
            if fetched_data is None:
                return None
            fetched_count = fetched_data['imdata'][0]['moCount']['attributes']['count']
            g_coop_db.add_metric(labels=[host, spine_attributes['dn']], value=fetched_count)

        return [g_coop_db]
