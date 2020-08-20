import logging

from prometheus_client.core import GaugeMetricFamily, Summary
import BaseCollector

LOG          = logging.getLogger('apic_exporter.exporter')
# Create a metric to track time spent and requests made.
# https://github.com/prometheus/client_python/issues/82
#REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request', ('collector'))
#COLLECT_TIME = REQUEST_TIME.labels('apichealth')

class ApicHealthCollector (BaseCollector.BaseCollector):

    def describe(self):
        yield GaugeMetricFamily('network_apic_accessible', 'APIC accessibility')

        yield GaugeMetricFamily('network_apic_cpu_usage_percent', 'APIC CPU utilization')

        yield GaugeMetricFamily('network_apic_max_memory_allocation_bytes', 'APIC maximum memory allocated')

        yield GaugeMetricFamily('network_apic_free_memory_bytes', 'APIC maximum amount of available memory')

#    @COLLECT_TIME.time()
    def collect(self):
        LOG.info('Collecting APIC health metrics ...')

        g_cpu  = GaugeMetricFamily('network_apic_cpu_usage_percent', 'APIC CPU utilization', labels=['apicHost'])
        g_aloc = GaugeMetricFamily('network_apic_max_memory_allocation_kb', 'APIC maximum memory allocated', labels=['apicHost'])
        g_free = GaugeMetricFamily('network_apic_free_memory_kb', 'APIC maximum amount of available memory', labels=['apicHost'])

        query = '/api/node/class/procEntity.json?'
        for host in self.hosts:
            fetched_data   = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.error("Skipping apic host %s, %s did not return anything", host, query)
                continue

            g_cpu.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['cpuPct'])
            g_aloc.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['maxMemAlloc'])
            g_free.add_metric(labels=[host], value=fetched_data['imdata'][0]['procEntity']['attributes']['memFree'])

        yield g_cpu
        yield g_aloc
        yield g_free