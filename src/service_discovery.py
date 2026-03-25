import os
import requests
import time
import logging

logger = logging.getLogger(__name__)

class ServiceDiscovery:
    def __init__(self, registry_url, heartbeat_interval=10):
        self.registry_url = registry_url
        self.heartbeat_interval = heartbeat_interval
        self.services = {}

    def register_service(self, service_name, service_url, service_health_check):
        service_info = {
            'url': service_url,
            'health_check': service_health_check,
            'last_heartbeat': time.time()
        }
        self.services[service_name] = service_info
        self._send_heartbeat(service_name)
        logger.info(f'Registered service: {service_name}')

    def unregister_service(self, service_name):
        if service_name in self.services:
            del self.services[service_name]
            logger.info(f'Unregistered service: {service_name}')

    def get_service(self, service_name):
        if service_name in self.services:
            return self.services[service_name]['url']
        else:
            return None

    def monitor_services(self):
        while True:
            for service_name, service_info in self.services.items():
                if time.time() - service_info['last_heartbeat'] > self.heartbeat_interval:
                    if self._check_service_health(service_info['health_check']):
                        self._send_heartbeat(service_name)
                    else:
                        self.unregister_service(service_name)
                        logger.warning(f'Service {service_name} is unhealthy and has been unregistered.')
                        self._scale_service(service_name)
            time.sleep(self.heartbeat_interval)

    def _send_heartbeat(self, service_name):
        service_info = self.services[service_name]
        try:
            requests.post(self.registry_url, json={'service_name': service_name, 'service_url': service_info['url']})
            service_info['last_heartbeat'] = time.time()
            logger.debug(f'Sent heartbeat for service: {service_name}')
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to send heartbeat for service {service_name}: {e}')

    def _check_service_health(self, health_check):
        try:
            response = requests.get(health_check)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _scale_service(self, service_name):
        # Implement dynamic scaling logic here
        pass
