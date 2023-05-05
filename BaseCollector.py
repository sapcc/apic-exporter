from abc import ABC, abstractmethod
from modules.Connection import Connection, TIMEOUT
import logging
from typing import Dict, List

LOG = logging.getLogger('apic_exporter.exporter')


class BaseCollector(ABC):

    def __init__(self, config: Dict):
        self.hosts: List[str] = config['apic_hosts'].split(',')
        self.__connection = Connection(self.hosts, config['apic_user'], config['apic_password'])

    @abstractmethod
    def describe(self):
        pass

    @abstractmethod
    def collect(self):
        pass

    def query_host(self, host: str, query: str, timeout: int = TIMEOUT) -> Dict:
        """Executes the query against a specific APIC host
           Returns the fetched data or None if fetched data is invalid
        """
        fetched_data = self.__connection.getRequest(host, query, timeout)
        if fetched_data is None:
            return None
        if not self.__connection.isDataValid(fetched_data):
            LOG.warning(f'apic host {host}, {query} did not return anything')
            return None
        return fetched_data

    def reset_unavailable_hosts(self):
        """Reset the list of unavailable hosts. Move the previously unavailable host to the end of the list"""
        unresponsive_hosts = self.__connection.get_unresponsive_hosts()
        for host in unresponsive_hosts:
            self.hosts.remove(host)
            self.hosts.append(host)
        self.__connection.reset_unavailable_hosts()
