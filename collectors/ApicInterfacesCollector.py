import logging
import BaseCollector
from prometheus_client.core import GaugeMetricFamily, Summary

LOG = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_interfaces_processing_seconds', 'Time spent processing request')


class ApicInterfacesCollector(BaseCollector.BaseCollector):

    def describe(self):

        yield GaugeMetricFamily('network_apic_physcial_interface_reset_counter',
                                'APIC physical interface reset counter')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('collecting apic interface metrics ...')

        g = GaugeMetricFamily('network_apic_physcial_interface_reset_counter',
                              'APIC physical interface reset counter',
                              labels=['apicHost', 'interfaceID'])

        metric_counter = 0
        # query only reset counters > 0
        query = '/api/node/class/ethpmPhysIf.json?query-target-filter=gt(ethpmPhysIf.resetCtr,"0")'
        for host in self.hosts:
            fetched_data = self.query_host(host, query)
            if fetched_data is None:
                LOG.warning(f'skipping apic host {host}, {query} did not return anything')
                continue

            # physical interface reset counter
            for item in fetched_data['imdata']:
                g.add_metric(labels=[host, item['ethpmPhysIf']['attributes']['dn']],
                             value=item['ethpmPhysIf']['attributes']['resetCtr'])
                metric_counter += 1
            break  # Each host produces the same metrics.

        yield g

        LOG.info('collected %s apic interface metrics', metric_counter)
