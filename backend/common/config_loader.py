"""
Configuration loading utilities.

Provides functions to load server configurations, API keys, and setup Flask apps.
"""

import json
import os
from flask_cors import CORS
from dotenv import load_dotenv


def load_server_config(config_file, fallback_port=8080):
    """
    Load server configuration from JSON file.

    Args:
        config_file (str): Path to config JSON file
        fallback_port (int): Fallback port if config not found

    Returns:
        dict: Configuration dictionary
    """
    try:
        # Try multiple locations
        config_paths = [
            config_file,
            os.path.join('backend', 'config', config_file),
            os.path.join('..', config_file)
        ]

        for path in config_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"[Config] Loaded config from: {path}")
                return config

        # Fallback config
        print(f"[Config] Warning: {config_file} not found, using defaults")
        return {
            'server': {
                'host': '0.0.0.0',
                'port': fallback_port,
                'debug': True
            }
        }

    except Exception as e:
        print(f"[Config] Error loading config: {str(e)}")
        return {
            'server': {
                'host': '0.0.0.0',
                'port': fallback_port,
                'debug': True
            }
        }


def load_env_config():
    """
    Load configuration from environment variables.

    Returns:
        dict: Configuration dictionary from .env file
    """
    load_dotenv()

    return {
        "server": {
            "host": os.getenv('SERVER_HOST', '0.0.0.0'),
            "port": int(os.getenv('SERVER_PORT', 8080)),
            "debug": os.getenv('DEBUG_MODE', 'true').lower() == 'true',
            "cors_origins": os.getenv('CORS_ORIGINS', '*')
        },
        "api": {
            "upbit_base_url": os.getenv('UPBIT_API_URL', "https://api.upbit.com"),
            "default_count": int(os.getenv('MAX_DATA_COUNT', 200)),
            "max_count": int(os.getenv('MAX_DATA_COUNT', 200))
        }
    }


def load_api_keys():
    """
    Load Upbit API keys from environment variables.

    Returns:
        tuple: (access_key, secret_key) or (None, None) if not found
    """
    load_dotenv()

    access_key = os.getenv('UPBIT_ACCESS_KEY', '')
    secret_key = os.getenv('UPBIT_SECRET_KEY', '')

    if access_key and secret_key:
        print("[Config] API keys loaded from environment")
        return access_key, secret_key
    else:
        print("[Config] Warning: API keys not found in environment")
        return None, None


def setup_cors(app, port, additional_origins=None):
    """
    Setup CORS for Flask app.

    Args:
        app: Flask application instance
        port (int): Server port for CORS origins
        additional_origins (list, optional): Additional origins to allow

    Returns:
        Flask app with CORS configured
    """
    origins = [
        f'http://localhost:{port}',
        f'http://127.0.0.1:{port}',
        'http://localhost:8080',
        'http://127.0.0.1:8080',
        'http://localhost:8081',
        'http://127.0.0.1:8081',
        'http://localhost:8082',
        'http://127.0.0.1:8082',
        '*'  # Allow all for development
    ]

    if additional_origins:
        origins.extend(additional_origins)

    CORS(app, origins=origins, supports_credentials=True)
    print(f"[Config] CORS configured for port {port}")

    return app


def get_config_path(filename):
    """
    Get full path to configuration file.

    Searches in multiple locations:
    1. Current directory
    2. backend/config/
    3. Parent directory

    Args:
        filename (str): Config filename

    Returns:
        str: Full path to config file or None if not found
    """
    search_paths = [
        filename,
        os.path.join('backend', 'config', filename),
        os.path.join('config', filename),
        os.path.join('..', filename)
    ]

    for path in search_paths:
        if os.path.exists(path):
            return os.path.abspath(path)

    return None


def save_config(config, config_file):
    """
    Save configuration to JSON file.

    Args:
        config (dict): Configuration dictionary
        config_file (str): Path to save config

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Try to save in backend/config/ first
        config_dir = os.path.join('backend', 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        save_path = os.path.join(config_dir, config_file)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"[Config] Saved config to: {save_path}")
        return True

    except Exception as e:
        print(f"[Config] Error saving config: {str(e)}")
        return False


def merge_configs(*configs):
    """
    Merge multiple configuration dictionaries.

    Later configs override earlier ones.

    Args:
        *configs: Variable number of config dicts

    Returns:
        dict: Merged configuration
    """
    merged = {}

    for config in configs:
        if config:
            for key, value in config.items():
                if isinstance(value, dict) and key in merged:
                    # Recursively merge nested dicts
                    merged[key] = {**merged[key], **value}
                else:
                    merged[key] = value

    return merged


def validate_config(config, required_keys):
    """
    Validate configuration has required keys.

    Args:
        config (dict): Configuration to validate
        required_keys (list): List of required key paths (e.g., ['server.host', 'server.port'])

    Returns:
        tuple: (is_valid, missing_keys)
    """
    missing = []

    for key_path in required_keys:
        keys = key_path.split('.')
        current = config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                missing.append(key_path)
                break

    return len(missing) == 0, missing
