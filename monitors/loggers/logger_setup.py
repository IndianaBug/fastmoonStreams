import logging
import logging.config
import os

class LoggerSetup:
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup()

    def _setup(self):
        # Determine the path to the configuration file
        config_path = os.path.join(os.path.dirname(__file__), 'config/logging.conf')
        logging.config.fileConfig(config_path)
        self.logger = logging.getLogger('appLogger')
        
    def get_logger(self):
        return self.logger
