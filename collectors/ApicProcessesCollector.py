import logging
import re
from typing import Dict, List

from prometheus_client.core import GaugeMetricFamily

from Collector import Collector

LOG = logging.getLogger('apic_exporter.exporter')


class ApicProcessesCollector(Collector):

    def __init__(self, config: Dict):
        super().__init__('apic_processes', config)

    def describe(self):
        yield GaugeMetricFamily('network_apic_process_memory_used_min_kb', 'Minimum memory used by process')

        yield GaugeMetricFamily('network_apic_process_memory_used_max_kb', 'Maximum memory used by process')

        yield GaugeMetricFamily('network_apic_process_memory_used_avg_kb', 'Average memory used by process')

    def get_query(self) -> str:
        return '/api/node/class/fabricNode.json?'

    def get_metrics(self, host: str, data: Dict) -> List[GaugeMetricFamily]:
        LOG.debug('collecting apic processes metrics ...')

        g_mem_min = GaugeMetricFamily('network_apic_process_memory_used_min_kb',
                                      'Minimum memory used by process',
                                      labels=['apicHost', 'procName', 'nodeId', 'nodeRole'])

        g_mem_max = GaugeMetricFamily('network_apic_process_memory_used_max_kb',
                                      'Maximum memory used by process',
                                      labels=['apicHost', 'procName', 'nodeId', 'nodeRole'])

        g_mem_avg = GaugeMetricFamily('network_apic_process_memory_used_avg_kb',
                                      'Average memory used by process',
                                      labels=['apicHost', 'procName', 'nodeId', 'nodeRole'])

        # fetch nfm process id from each node
        for node in data['imdata']:
            node_dn = node['fabricNode']['attributes']['dn']
            node_role = node['fabricNode']['attributes']['role']
            LOG.debug(f'fetching process data for node {node_dn} {node_role}')

            proc_query = f'/api/node/class/{node_dn}/procProc.json?query-target-filter=eq(procProc.name,"nfm")'
            proc_data = self.query_host(host, proc_query)
            if proc_data is None:
                LOG.info(f'apic host {host} node {node_dn} has no nfm process')
                continue

            # fetch nfm process memory consumption per node
            if int(proc_data['totalCount']) > 0:
                proc_dn = proc_data['imdata'][0]['procProc']['attributes']['dn']
                proc_name = proc_data['imdata'][0]['procProc']['attributes']['name']
                mem_query = f'/api/node/mo/{proc_dn}/HDprocProcMem5min-0.json'
                mem_data = self.query_host(host, mem_query)
                if mem_data is None:
                    LOG.info(f'apic host {host} node {node_dn} process {proc_dn} has no memory data')
                    continue

                if int(mem_data['totalCount']) > 0:
                    node_id = self._parseNodeIdInProcDN(proc_dn)

                    LOG.debug("procName: %s, nodeId: %s, role: %s, MemUsedMin: %s, MemUsedMax: %s, MemUsedAvg: %s",
                              proc_name, node_id, node_role,
                              mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMin'],
                              mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMax'],
                              mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedAvg'])

                    # Min memory used
                    g_mem_min.add_metric(labels=[host, proc_name, node_id, node_role],
                                         value=mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMin'])

                    # Max memory used
                    g_mem_max.add_metric(labels=[host, proc_name, node_id, node_role],
                                         value=mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedMax'])

                    # Avg memory used
                    g_mem_avg.add_metric(labels=[host, proc_name, node_id, node_role],
                                         value=mem_data['imdata'][0]['procProcMemHist5min']['attributes']['usedAvg'])
        return [g_mem_min, g_mem_max, g_mem_avg]

    def _parseNodeIdInProcDN(self, procDn):
        nodeId = ''
        matchObj = re.match(u".+node-([0-9]*).+", procDn)
        if matchObj:
            nodeId = matchObj.group(1)
        return nodeId
