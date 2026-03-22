import os
import time
import random
import multiprocessing as mp

from typing import Callable, Dict, List, Tuple

class TaskScheduler:
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.task_queue = mp.Queue()
        self.worker_processes = []
        self.start_workers()

    def start_workers(self):
        for _ in range(self.num_workers):
            worker = mp.Process(target=self.worker_loop)
            worker.start()
            self.worker_processes.append(worker)

    def worker_loop(self):
        while True:
            task, args = self.task_queue.get()
            task(*args)

    def submit_task(self, task: Callable, *args):
        self.task_queue.put((task, args))

    def shutdown(self):
        for worker in self.worker_processes:
            worker.terminate()

class MicroserviceManager:
    def __init__(self, services: Dict[str, Callable]):
        self.services = services
        self.scheduler = TaskScheduler(num_workers=len(services))

    def run_service(self, service_name: str, *args):
        self.scheduler.submit_task(self.services[service_name], *args)

    def shutdown(self):
        self.scheduler.shutdown()

# Example usage
def add(a: int, b: int) -> int:
    time.sleep(random.uniform(0.1, 1.0))  # Simulate processing time
    return a + b

def multiply(a: int, b: int) -> int:
    time.sleep(random.uniform(0.1, 1.0))
    return a * b

services = {
    'add': add,
    'multiply': multiply
}

manager = MicroserviceManager(services)

# Run some tasks
manager.run_service('add', 2, 3)
manager.run_service('multiply', 4, 5)
manager.run_service('add', 6, 7)

# Wait for tasks to complete
time.sleep(2)

manager.shutdown()
