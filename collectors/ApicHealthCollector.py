import logging
import BaseCollector
from prometheus_client.core import GaugeMetricFamily, Summary
from typing import List, Dict

LOG = logging.getLogger('apic_exporter.exporter')
TIMEOUT = 5
REQUEST_TIME = Summary('apic_health_processing_seconds', 'Time spent processing request')


class ApicHealthCollector(BaseCollector.BaseCollector):

    def __init__(self, config: Dict):
        super().__init__(config)
        self.__metric_counter = 0

    def describe(self):
        yield GaugeMetricFamily('network_apic_accessible', 'APIC controller accessibility')

        yield GaugeMetricFamily('network_apic_cpu_usage_percent', 'APIC CPU utilization')

        yield GaugeMetricFamily('network_apic_max_memory_allocation_bytes', 'APIC maximum memory allocated')

        yield GaugeMetricFamily('network_apic_free_memory_bytes', 'APIC maximum amount of available memory')

    def collect_apic_accessible(self) -> GaugeMetricFamily:
        """Collect the availability of APIC hosts and flag unavailable hosts"""

        g_access = GaugeMetricFamily('network_apic_accessible', 'APIC controller accessibility', labels=['apicHost'])

        for host in self.hosts:
            query = f'/api/node/class/topSystem.json?query-target-filter=eq(topSystem.oobMgmtAddr,\"{host}\")'
            fetched_data = self.query_host(host, query, TIMEOUT)
            if fetched_data is None:
                g_access.add_metric(labels=[host], value=0)
            else:
                g_access.add_metric(labels=[host], value=1)
            self.__metric_counter += 1
        return g_access

    def collect_apic_utilization(self) -> List[GaugeMetricFamily]:
        """Collect the APIC CPU Usage, Memory Allocation and available memory"""

        g_cpu = GaugeMetricFamily('network_apic_cpu_usage_percent', 'APIC CPU utilization', labels=['apicHost'])
        g_aloc = GaugeMetricFamily('network_apic_max_memory_allocation_kb',
                                   'APIC maximum memory allocated',
                                   labels=['apicHost'])
        g_free = GaugeMetricFamily('network_apic_free_memory_kb',
                                   'APIC maximum amount of available memory',
                                   labels=['apicHost'])

        metrics: List[GaugeMetricFamily] = [g_cpu, g_aloc, g_free]

        query = '/api/node/class/procEntity.json?'
        for host in self.hosts:
            fetched_data = self.query_host(host, query)
            if fetched_data is None:
                LOG.debug(f'skipping apic host {host}, {query} did not return anything')
                continue

            g_cpu.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['cpuPct'])
            g_aloc.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['maxMemAlloc'])
            g_free.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['memFree'])
            self.__metric_counter += 3

        return metrics

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('collecting apic health metrics ...')

        self.reset_unavailable_hosts()

        self.__metric_counter = 0

        metrics: List[GaugeMetricFamily] = []

        metrics.append(self.collect_apic_accessible())
        metrics.extend(self.collect_apic_utilization())

        for metric in metrics:
            yield metric

        LOG.info(f'collected {self.__metric_counter} apic health metrics')
