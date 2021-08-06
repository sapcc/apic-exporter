import logging

from prometheus_client.core import CounterMetricFamily, Summary
import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_mcp_faults_processing_seconds',
                       'Time spent processing request')


class ApicMCPCollector(BaseCollector.BaseCollector):
    def describe(self):
        yield CounterMetricFamily('network_apic_mcp_fault_counter',
                                  'Counter for MCP Faults')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('Collecting APIC MCP Fault metrics ...')

        c_mcp_faults = CounterMetricFamily(
            'network_apic_mcp_fault_counter',
            'Counter for MCP Faults',
            labels=['apicHost', 'fault_summary', 'fault_desc', 'fault_lifecyle'])

        metric_counter = 0
        query = "/api/node/class/faultInst.json?query-target-filter=or(eq(faultInst.code,\"F2533\"),eq(faultInst.code,\"F2534\"))"
        for host in self.hosts: 
            fetched_data = self.connection.getRequest(host, query)
            if not self.connection.isDataValid(fetched_data):
                LOG.warning(
                    "Skipping apic host %s, %s did not return anything", host, query)
                continue

            if len(fetched_data['imdata']) == 0:
                # Add Empty Counter to have the metric show up in Prometheus.
                # Otherwise they only show when something is wrong and we dont know if it is actually working
                c_mcp_faults.add_metric(labels=[host, '', '', ''], value=0)
                metric_counter += 1
                break  # Each host produces the same metrics.
            count = int(fetched_data['totalCount'])
            for x in range(0, int(count)):
                if (fetched_data['imdata'][x]['faultInst']['attributes']['lc'] =='raised') or (fetched_data['imdata'][x]['faultInst']['attributes']['lc'] =='soaking'):
                    fault_lifecyle = fetched_data['imdata'][x]['faultInst']['attributes']['lc']
                    fault_summary = fetched_data['imdata'][x]['faultInst']['attributes']['dn']
                    fault_desc = fetched_data['imdata'][x]['faultInst']['attributes']['descr']

                    LOG.debug("host: %s, ip: %s", fault_lifecyle, fault_summary, fault_desc)
                    metric_counter += 1

                    c_mcp_faults.add_metric(labels=[host, fault_summary, fault_desc, fault_lifecyle], value=1)
            break  # Each host produces the same metrics.

        yield c_mcp_faults

        LOG.info('Collected %s APIC MCP Fault metrics', metric_counter)
