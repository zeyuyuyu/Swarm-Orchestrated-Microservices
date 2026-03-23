import requests
import time
import logging

logger = logging.getLogger(__name__)

class ServiceDiscovery:
    def __init__(self, service_registry_url):
        self.service_registry_url = service_registry_url
        self.services = {}

    def register_service(self, service_name, service_url):
        payload = {
            'service_name': service_name,
            'service_url': service_url
        }
        try:
            response = requests.post(self.service_registry_url, json=payload)
            response.raise_for_status()
            logger.info(f'Registered service: {service_name}')
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to register service {service_name}: {e}')

    def discover_services(self):
        try:
            response = requests.get(self.service_registry_url)
            response.raise_for_status()
            self.services = response.json()
            logger.info(f'Discovered services: {self.services}')
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to discover services: {e}')

    def monitor_services(self):
        while True:
            for service_name, service_url in self.services.items():
                try:
                    response = requests.get(f'{service_url}/health')
                    response.raise_for_status()
                    logger.info(f'Service {service_name} is healthy')
                except requests.exceptions.RequestException as e:
                    logger.error(f'Service {service_name} is unhealthy: {e}')
                    self.self_heal(service_name, service_url)
            time.sleep(60)  # Check service health every minute

    def self_heal(self, service_name, service_url):
        try:
            # Implement self-healing logic here, e.g., restart the service, scale up, etc.
            logger.info(f'Attempting to self-heal service {service_name}')
        except Exception as e:
            logger.error(f'Failed to self-heal service {service_name}: {e}')
