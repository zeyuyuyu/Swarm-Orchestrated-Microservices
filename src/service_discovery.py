import socket
import time
import json
import threading
from typing import Dict, List, Optional
import logging

class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, List[Dict]] = {}
        self._lock = threading.Lock()
        self._health_check_interval = 30  # seconds
        self._start_health_checker()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def register_service(self, service_name: str, host: str, port: int, metadata: Optional[Dict] = None) -> bool:
        """Register a new service instance"""
        with self._lock:
            if service_name not in self._services:
                self._services[service_name] = []
            
            service_info = {
                'host': host,
                'port': port,
                'metadata': metadata or {},
                'last_check': time.time(),
                'healthy': True
            }
            
            self._services[service_name].append(service_info)
            self.logger.info(f'Registered new service: {service_name} at {host}:{port}')
            return True

    def get_service(self, service_name: str) -> Optional[Dict]:
        """Get a healthy service instance using round-robin selection"""
        with self._lock:
            if service_name not in self._services:
                return None
            
            # Filter healthy instances
            healthy_instances = [
                instance for instance in self._services[service_name]
                if instance['healthy']
            ]
            
            if not healthy_instances:
                return None
            
            # Round-robin selection
            instance = healthy_instances[0]
            self._services[service_name].append(
                self._services[service_name].pop(0)
            )
            
            return {
                'host': instance['host'],
                'port': instance['port'],
                'metadata': instance['metadata']
            }

    def _health_check(self) -> None:
        """Perform health check on all registered services"""
        while True:
            with self._lock:
                for service_name, instances in self._services.items():
                    for instance in instances:
                        healthy = self._check_instance_health(
                            instance['host'],
                            instance['port']
                        )
                        
                        instance['healthy'] = healthy
                        instance['last_check'] = time.time()
                        
                        if not healthy:
                            self.logger.warning(
                                f'Service {service_name} at {instance["host"]}:{instance["port"]} '
                                f'is unhealthy'
                            )
                        
            time.sleep(self._health_check_interval)

    def _check_instance_health(self, host: str, port: int) -> bool:
        """Check if a service instance is healthy using TCP connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def _start_health_checker(self) -> None:
        """Start the health checker in a background thread"""
        health_thread = threading.Thread(
            target=self._health_check,
            daemon=True
        )
        health_thread.start()

    def deregister_service(self, service_name: str, host: str, port: int) -> bool:
        """Deregister a service instance"""
        with self._lock:
            if service_name not in self._services:
                return False
            
            self._services[service_name] = [
                instance for instance in self._services[service_name]
                if not (instance['host'] == host and instance['port'] == port)
            ]
            
            self.logger.info(f'Deregistered service: {service_name} at {host}:{port}')
            return True

    def get_all_services(self) -> Dict[str, List[Dict]]:
        """Get all registered services and their status"""
        with self._lock:
            return {
                name: [
                    {
                        'host': instance['host'],
                        'port': instance['port'],
                        'metadata': instance['metadata'],
                        'healthy': instance['healthy'],
                        'last_check': instance['last_check']
                    }
                    for instance in instances
                ]
                for name, instances in self._services.items()
            }