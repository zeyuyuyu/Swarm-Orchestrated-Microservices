import time
import requests
import logging

logger = logging.getLogger(__name__)

class ServiceDiscovery:
    def __init__(self, service_registry_url, heartbeat_interval=10):
        self.service_registry_url = service_registry_url
        self.heartbeat_interval = heartbeat_interval
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
            self.services[service_name] = {
                'url': service_url,
                'healthy': True
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Error registering service {service_name}: {e}')

    def deregister_service(self, service_name):
        try:
            response = requests.delete(f'{self.service_registry_url}/{service_name}')
            response.raise_for_status()
            logger.info(f'Deregistered service: {service_name}')
            del self.services[service_name]
        except requests.exceptions.RequestException as e:
            logger.error(f'Error deregistering service {service_name}: {e}')

    def monitor_services(self):
        while True:
            for service_name, service_info in self.services.items():
                try:
                    response = requests.get(service_info['url'])
                    response.raise_for_status()
                    if not service_info['healthy']:
                        logger.info(f'Service {service_name} is now healthy')
                        service_info['healthy'] = True
                except requests.exceptions.RequestException:
                    if service_info['healthy']:
                        logger.warning(f'Service {service_name} is now unhealthy')
                        service_info['healthy'] = False
                        self.self_heal(service_name)
            time.sleep(self.heartbeat_interval)

    def self_heal(self, service_name):
        logger.info(f'Attempting to self-heal service {service_name}')
        try:
            # Implement your self-healing logic here
            # e.g., restart the service, scale up replicas, etc.
            pass
        except Exception as e:
            logger.error(f'Self-healing failed for service {service_name}: {e}')
