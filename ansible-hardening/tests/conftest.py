"""
Pytest configuration and fixtures for Ansible Hardening Framework.
Author: Ruben Omar Ramírez Gutiérrez
"""

import os
import pytest
import yaml

@pytest.fixture(scope="session")
def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(scope="session")
def load_yaml():
    def _loader(rel_path):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        full_path = os.path.join(root, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Handle Jinja template comments if present
            return yaml.safe_load(content)
    return _loader
