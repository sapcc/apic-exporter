import yaml
import logging
import os
import sys
import time
import click
import importlib
import pkgutil

from prometheus_client.core import REGISTRY
from prometheus_client import start_http_server

LOG = logging.getLogger('apic_exporter.exporter')


def run_prometheus_server(port, collectors):
    start_http_server(int(port))
    for c in collectors:
        REGISTRY.register(c)
    while True:
        time.sleep(1)


def get_config(config_file):
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                config = yaml.load(f, Loader=yaml.Loader)
        except IOError as e:
            LOG.error(f'could not open configuration file: {str(e)}')
            exit(1)
        # check if collectors are defined
        if 'collectors' not in config:
            LOG.info("Collectors not defined in config. Using defaults")
            config['collectors'] = get_default_collectors()
        elif len(config['collectors']) == 0:
            LOG.error("Empty list of collectors")
            exit(1)

        # load apic password from environment
        pw = os.getenv('APIC_PASSWORD')
        if pw is None:
            LOG.error("envvar 'APIC_PASSWORD' not set")
            exit(1)
        if 'aci' in config:
            config['aci']['apic_password'] = pw
        else:
            LOG.error("section 'aci' missing in config")
            exit(1)

        return config
    else:
        LOG.error(f'config file does not exist: {config_file}')
        exit(1)


def get_default_collectors():
    return [name for _, name, _ in pkgutil.iter_modules(['collectors'])]


def initialize_collector_by_name(class_name, config):
    try:
        class_module = importlib.import_module(f'collectors.{class_name}')
    except ModuleNotFoundError as e:
        LOG.error(f'no collector {class_name} defined: {e}')
        return None

    try:
        return class_module.__getattribute__(class_name)(config)
    except AttributeError as e:
        LOG.error(f'unable to initialize {class_name}: {e}')
        return None


@click.command()
@click.option("-p", "--port", metavar="<port>", default=9102, help="specify exporter serving port")
@click.option("-c", "--config", metavar="<config>", help="path to rest config")
@click.version_option()
@click.help_option()
def main(port, config):

    if not config:
        raise click.ClickException("Missing APIC config yaml --config")

    config_obj = get_config(config)
    exporter_config = config_obj['exporter']
    apic_config = config_obj['aci']

    collectors = list(map(lambda c: initialize_collector_by_name(c, apic_config), config_obj['collectors']))

    level = logging.getLevelName("INFO")
    if exporter_config['log_level']:
        level = logging.getLevelName(exporter_config['log_level'].upper())

    format = '[%(asctime)s] [%(levelname)s] %(message)s'
    logging.basicConfig(stream=sys.stdout, format=format, level=level)

    LOG.info(f'starting apic Exporter on port={port} config={config}')
    LOG.info(f'apic exporter connects to apic hosts: {apic_config["apic_hosts"]}')

    run_prometheus_server(port, collectors)


if __name__ == '__main__':
    main()
