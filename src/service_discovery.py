import time
import json
import logging
from typing import Dict, List, Optional
import requests
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceNode:
    name: str
    host: str
    port: int
    health_endpoint: str
    last_health_check: float
    healthy: bool = True
    retry_count: int = 0

class ServiceDiscovery:
    def __init__(self, health_check_interval: int = 30):
        self.services: Dict[str, List[ServiceNode]] = {}
        self.health_check_interval = health_check_interval
        self.max_retries = 3
    
    def register_service(self, name: str, host: str, port: int, 
                        health_endpoint: str = '/health') -> None:
        if name not in self.services:
            self.services[name] = []
            
        service = ServiceNode(
            name=name,
            host=host,
            port=port,
            health_endpoint=health_endpoint,
            last_health_check=time.time()
        )
        self.services[name].append(service)
        logger.info(f'Registered service {name} at {host}:{port}')

    def deregister_service(self, name: str, host: str, port: int) -> None:
        if name in self.services:
            self.services[name] = [s for s in self.services[name] 
                                 if not (s.host == host and s.port == port)]
            logger.info(f'Deregistered service {name} at {host}:{port}')

    def get_healthy_service(self, name: str) -> Optional[ServiceNode]:
        if name not in self.services:
            return None
            
        healthy_services = [s for s in self.services[name] if s.healthy]
        if not healthy_services:
            return None
            
        # Simple round-robin selection among healthy services
        return healthy_services[int(time.time()) % len(healthy_services)]

    def check_service_health(self, service: ServiceNode) -> bool:
        try:
            url = f'http://{service.host}:{service.port}{service.health_endpoint}'
            response = requests.get(url, timeout=5)
            healthy = response.status_code == 200
            
            if healthy:
                service.retry_count = 0
                service.healthy = True
            else:
                self._handle_unhealthy_service(service)
                
            service.last_health_check = time.time()
            return healthy
            
        except requests.exceptions.RequestException:
            self._handle_unhealthy_service(service)
            return False

    def _handle_unhealthy_service(self, service: ServiceNode) -> None:
        service.retry_count += 1
        if service.retry_count >= self.max_retries:
            service.healthy = False
            logger.warning(f'Service {service.name} at {service.host}:{service.port} '
                         f'marked as unhealthy after {self.max_retries} retries')
            self._trigger_recovery(service)

    def _trigger_recovery(self, service: ServiceNode) -> None:
        logger.info(f'Attempting recovery for service {service.name} at '
                   f'{service.host}:{service.port}')
        # Here you would implement service recovery logic
        # For example: restart container, notify admin, scale new instance, etc.

    def health_check_loop(self) -> None:
        while True:
            for service_list in self.services.values():
                for service in service_list:
                    if (time.time() - service.last_health_check) >= self.health_check_interval:
                        self.check_service_health(service)
            time.sleep(1)

    def get_service_status(self) -> Dict:
        status = {}
        for service_name, service_list in self.services.items():
            status[service_name] = [
                {
                    'host': s.host,
                    'port': s.port,
                    'healthy': s.healthy,
                    'last_check': s.last_health_check,
                    'retry_count': s.retry_count
                } for s in service_list
            ]
        return status