import logging
import re

from prometheus_client.core import CounterMetricFamily, Summary
import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_ips_processing_seconds', 'Time spent processing request')


class ApicIPsCollector(BaseCollector.BaseCollector):

    def describe(self):
        yield CounterMetricFamily('network_apic_duplicate_ip_counter', 'Counter for duplicate IPs')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('collecting apic IP metrics ...')

        c_dip = CounterMetricFamily('network_apic_duplicate_ip_counter',
                                    'Counter for duplicate IPs',
                                    labels=['apicHost', 'ip', 'mac', 'nodeId', 'tenant'])

        metric_counter = 0
        query = '/api/node/class/fvIp.json' + \
                '?rsp-subtree=full' + \
                '&rsp-subtree-class=fvReportingNode&query-target-filter=and(ne(fvIp.debugMACMessage,""))'
        for host in self.hosts:
            fetched_data = self.query_host(host, query)
            if fetched_data is None:
                continue

            if len(fetched_data['imdata']) == 0:
                # Add Empty Counter to have the metric show up in Prometheus.
                # Otherwise they only show when something is wrong and we dont know if it is actually working
                c_dip.add_metric(labels=[host, '', '', '', ''], value=0)
                metric_counter += 1
                break  # Each host produces the same metrics.

            for ip in fetched_data['imdata']:
                addr = ip['fvIp']['attributes']['addr']
                dn = ip['fvIp']['attributes']['dn']
                mac = re.search(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", dn).group()
                tenant = re.match(r"uni\/tn-(.+)\/ap.+", dn)[1]

                child_nodes = []
                if 'children' in ip['fvIp']:
                    for child in ip['fvIp']['children']:
                        node_id = child['fvReportingNode']['attributes']['id']
                        child_nodes.append(str(node_id))

                _nodeIds = 'None'
                if child_nodes:
                    _nodeIds = '+'.join(child_nodes)

                LOG.debug(f'host: {host}, ip: {addr}, mac: {mac}, nodes: {_nodeIds}')
                metric_counter += 1

                c_dip.add_metric(labels=[host, addr, mac, _nodeIds, tenant], value=1)
            break  # Each host produces the same metrics.

        yield c_dip

        LOG.info(f'collected {metric_counter} apic IP metrics')
