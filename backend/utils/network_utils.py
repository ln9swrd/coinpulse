"""
Network Utilities Module

Provides network-related utility functions for port availability checking.
"""

import socket


def is_port_available(port, host='localhost', config=None):
    """
    Check if a port is available for use.

    Args:
        port (int): Port number to check
        host (str): Host to check on (default: 'localhost')
        config (dict): Optional configuration dictionary containing:
            - network.port_check_timeout: Timeout for port check

    Returns:
        bool: True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Get timeout from config or use default
            port_timeout = 1
            if config:
                port_timeout = config.get('network', {}).get('port_check_timeout', 1)
            
            s.settimeout(port_timeout)
            result = s.connect_ex((host, port))
            return result != 0
    except Exception:
        return False


def find_available_port(start_port=5000, max_attempts=100, host='localhost', config=None):
    """
    Find an available port starting from a given port number.

    Args:
        start_port (int): Port number to start searching from
        max_attempts (int): Maximum number of ports to try
        host (str): Host to check on (default: 'localhost')
        config (dict): Optional configuration dictionary

    Returns:
        int or None: Available port number, or None if no port found
    """
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port, host, config):
            return port
    return None
