import asyncio
import threading
import time
import signal
import sys
import atexit
import functools
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class ProcessInfo:
    name: str
    thread: threading.Thread
    running: bool = True
    start_time: float = 0
    output_count: int = 0


# Global registry for tracking processes
_processes: Dict[str, ProcessInfo] = {}
_lock = threading.Lock()


def continuous_process(func):
    """Mark a function as a continuous process"""
    func._is_continuous = True
    return func


def _run_continuous_function(func, name, output_callback=None):
    """Run a function continuously in a loop"""
    output_callback = output_callback or (lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {name}: {msg}"))
    count = 0

    while True:
        try:
            with _lock:
                if name not in _processes or not _processes[name].running:
                    break

            count += 1
            result = func()
            if result:
                output_callback(str(result))
                with _lock:
                    if name in _processes:
                        _processes[name].output_count += 1

            time.sleep(1)  # Wait 1 second between calls

        except Exception as e:
            output_callback(f"Error: {e}")
            time.sleep(2)  # Wait longer after error


def start_background_processes(output_callback=None):
    """Decorator to start background processes before running main function"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            instance = args[0] if args and hasattr(args[0], func.__name__) else None

            if instance:
                # Find all continuous process methods
                continuous_methods = []
                for attr_name in dir(instance):
                    if not attr_name.startswith('_'):
                        attr = getattr(instance, attr_name)
                        if hasattr(attr, '_is_continuous') and attr._is_continuous:
                            continuous_methods.append((attr_name, attr))

                # Start each continuous process in its own thread
                for method_name, method in continuous_methods:
                    process_name = f"{instance.__class__.__name__}_{method_name}"

                    def make_runner(method_func, proc_name):
                        def runner():
                            _run_continuous_function(method_func, proc_name, output_callback)

                        return runner

                    thread = threading.Thread(
                        target=make_runner(method, process_name),
                        daemon=True,
                        name=process_name
                    )

                    with _lock:
                        _processes[process_name] = ProcessInfo(
                            name=process_name,
                            thread=thread,
                            start_time=time.time()
                        )

                    thread.start()
                    print(f"Started background process: {process_name}")

            # Run the main function
            try:
                return func(*args, **kwargs)
            finally:
                # Stop all background processes when main function exits
                stop_all_processes()

        return wrapper

    return decorator


def start_servers(output_callback=None):
    """Decorator to start blocking server processes in separate threads"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            instance = args[0] if args and hasattr(args[0], func.__name__) else None

            # Run the setup function first to get server configurations
            server_configs = func(*args, **kwargs)

            # Start each server in its own thread
            if server_configs:
                for config in server_configs:
                    server_name = config.get('name', 'unknown_server')
                    server_func = config.get('func')
                    server_args = config.get('args', ())

                    if server_func:
                        def make_server_runner(func, name, args):
                            def runner():
                                try:
                                    print(f"Starting server: {name}")
                                    func(*args)
                                except Exception as e:
                                    print(f"Server {name} error: {e}")

                            return runner

                        thread = threading.Thread(
                            target=make_server_runner(server_func, server_name, server_args),
                            daemon=True,
                            name=f"server_{server_name}"
                        )

                        with _lock:
                            _processes[f"server_{server_name}"] = ProcessInfo(
                                name=f"server_{server_name}",
                                thread=thread,
                                start_time=time.time()
                            )

                        thread.start()
                        time.sleep(0.5)  # Give server time to start
                        print(f"Started server: {server_name}")

            return server_configs

        return wrapper

    return decorator


def stop_all_processes():
    """Stop all running background processes"""
    with _lock:
        for process_info in _processes.values():
            process_info.running = False
        print(f"Stopped {len(_processes)} background processes")
        _processes.clear()


def get_process_status():
    """Get status of all running processes"""
    with _lock:
        status = {}
        for name, info in _processes.items():
            runtime = time.time() - info.start_time
            status[name] = {
                'name': name,
                'running': info.running,
                'runtime': f"{runtime:.1f}s",
                'output_count': info.output_count,
                'thread_alive': info.thread.is_alive()
            }
        return status


def print_process_status():
    """Print current process status"""
    status = get_process_status()
    if not status:
        print("No active processes")
        return

    print("\n=== Process Status ===")
    for name, info in status.items():
        print(f"Process: {info['name']}")
        print(f"  Running: {info['running']}")
        print(f"  Runtime: {info['runtime']}")
        print(f"  Outputs: {info['output_count']}")
        print(f"  Thread Alive: {info['thread_alive']}")
        print()


# Cleanup on exit
def _cleanup():
    stop_all_processes()


atexit.register(_cleanup)


# Simple signal handlers
def _signal_handler(signum, frame):
    print(f"Received signal {signum}, stopping processes...")
    stop_all_processes()
    sys.exit(0)


if sys.platform != 'win32':
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

# Test example
if __name__ == "__main__":
    class TestServer:
        def __init__(self, name):
            self.name = name
            self.counter = 0

        @continuous_process
        def health_check(self):
            self.counter += 1
            return f"Health check #{self.counter} - All systems OK"

        @continuous_process
        def monitor_cpu(self):
            import random
            cpu = random.randint(10, 90)
            return f"CPU usage: {cpu}%"

        @start_background_processes()
        def run(self):
            print(f"Starting {self.name} main server...")

            # Simulate main server work
            for i in range(10):
                print(f"Main server work step {i + 1}/10")
                time.sleep(2)

            print("Main server finished")


    # Test it
    server = TestServer("TestServer")
    server.run()