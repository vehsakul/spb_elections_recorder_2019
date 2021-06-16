import logging
import logging.config

import yaml


def init_logging(dev=True):
    log_config_file = 'logconf.dev.yml' if dev else 'logconf.prod.yml'
    with open(log_config_file, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)

    logging.config.dictConfig(config)