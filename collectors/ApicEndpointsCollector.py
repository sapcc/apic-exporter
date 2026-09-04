import logging
import re
from typing import Dict, List

from prometheus_client.core import GaugeMetricFamily, Summary
import BaseCollector

LOG = logging.getLogger('apic_exporter.exporter')
REQUEST_TIME = Summary('apic_endpoints_processing_seconds', 'Time spent processing request')


class ApicEndpointsCollector(BaseCollector.BaseCollector):
    """Collects the total number of client endpoints (fvCEp) per VRF.
    The VRFs to report on are provided via configuration ("vrf_dns")
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self.vrf_dns: List[str] = config.get('vrf_dns') or []
        if not self.vrf_dns:
            LOG.warning('ApicEndpointsCollector: no "vrf_dns" configured; no endpoint metrics will be produced')

    def describe(self):
        yield GaugeMetricFamily('network_apic_endpoints_total',
                                'Total number of endpoints (fvCEp) per VRF')

    @REQUEST_TIME.time()
    def collect(self):
        LOG.debug('collecting apic endpoint count metrics ...')

        g_ep = GaugeMetricFamily('network_apic_endpoints_total',
                                 'Total number of endpoints (fvCEp) per VRF',
                                 labels=['apicHost', 'tenant', 'vrf'])

        metric_counter = 0
        for host in self.hosts:
            host_failed = False
            for vrf_dn in self.vrf_dns:
                query = '/api/class/fvCEp.json' + \
                        '?query-target-filter=eq(fvCEp.vrfDn,"' + vrf_dn + '")' + \
                        '&rsp-subtree-include=count'
                fetched_data = self.query_host(host, query)
                if fetched_data is None:
                    LOG.warning(f'skipping apic host {host}, {query} did not return anything')
                    host_failed = True
                    break

                count = fetched_data['imdata'][0]['moCount']['attributes']['count']
                tenant, vrf = self._parse_vrf_dn(vrf_dn)
                g_ep.add_metric(labels=[host, tenant, vrf], value=float(count))
                metric_counter += 1
                LOG.debug(f'host: {host}, vrf: {vrf_dn}, endpoint count: {count}')

            if host_failed:
                continue  # try the next host

            break  # Each host produces the same metrics

        yield g_ep

        LOG.info(f'collected {metric_counter} apic endpoint count metrics')

    @staticmethod
    def _parse_vrf_dn(vrf_dn: str):
        """'uni/tn-common/ctx-test' -> ('common', 'test')"""
        match = re.match(r'uni/tn-(?P<tenant>[^/]+)/ctx-(?P<vrf>.+)', vrf_dn)
        if match:
            return match.group('tenant'), match.group('vrf')
        return '', vrf_dn
