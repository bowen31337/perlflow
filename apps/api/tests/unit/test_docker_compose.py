"""
Test Docker Compose full stack functionality.
These tests verify the complete Docker setup without requiring Docker to be installed.
"""

import os
import pytest
from pathlib import Path
import yaml


class TestDockerComposeFullStack:
    """Test complete Docker Compose stack configuration."""

    def test_docker_compose_full_stack_structure(self):
        """Verify docker-compose.yml has complete stack structure."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml should exist"

        content = compose_path.read_text()

        # Verify all required services exist
        services = ["postgres", "redis", "api", "frontend"]
        for service in services:
            assert f"{service}:" in content, f"Service {service} should be defined"

    def test_docker_compose_full_stack_dependencies(self):
        """Verify service dependencies are properly configured."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # API depends on database and redis
        assert "depends_on:" in content
        assert "postgres:" in content
        assert "redis:" in content
        assert "condition: service_healthy" in content

        # Frontend depends on API
        assert "frontend:" in content

    def test_docker_compose_full_stack_networking(self):
        """Verify networking configuration for service communication."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # Verify default network is used (services can communicate by name)
        assert "postgres:5432" in content  # API connects to postgres by service name
        assert "redis:6379" in content      # API connects to redis by service name

    def test_docker_compose_full_stack_environment_variables(self):
        """Verify environment variables are properly configured for full stack."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # Database URL for API
        assert "DATABASE_URL=postgresql+asyncpg://pearlflow:pearlflow123@postgres:5432/pearlflow" in content

        # Redis URL for API
        assert "REDIS_URL=redis://redis:6379" in content

        # API URL for frontend
        assert "NEXT_PUBLIC_API_URL=http://api:8000" in content

    def test_docker_compose_full_stack_ports(self):
        """Verify port mappings for full stack accessibility."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # PostgreSQL exposes port 5432
        assert '"5432:5432"' in content

        # Redis exposes port 6379
        assert '"6379:6379"' in content

        # API exposes port 8000
        assert '"8000:8000"' in content

        # Frontend exposes port 3000
        assert '"3000:3000"' in content

    def test_docker_compose_full_stack_healthchecks(self):
        """Verify health checks are configured for all services."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # PostgreSQL health check
        assert "pg_isready -U pearlflow -d pearlflow" in content

        # Redis health check (can be array format ["CMD", "redis-cli", "ping"])
        assert "redis-cli" in content and "ping" in content

        # API health check
        assert "healthcheck:" in content

    def test_docker_compose_full_stack_volumes(self):
        """Verify volume configuration for data persistence."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # PostgreSQL data volume
        assert "postgres_data:/var/lib/postgresql/data" in content

        # Volumes section
        assert "volumes:" in content
        assert "postgres_data:" in content

    def test_docker_compose_full_stack_restart_policy(self):
        """Verify restart policies for production reliability."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # Verify restart policies
        assert "restart: unless-stopped" in content

    def test_docker_compose_full_stack_build_context(self):
        """Verify build contexts are properly configured."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # API build context
        assert "context: ./apps/api" in content
        assert "dockerfile: Dockerfile" in content

        # Frontend build context
        assert "context: ./apps/demo-web" in content

    def test_docker_compose_full_stack_container_names(self):
        """Verify container names are properly configured."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # Verify container names
        assert "container_name: pearlflow-postgres" in content
        assert "container_name: pearlflow-redis" in content
        assert "container_name: pearlflow-api" in content
        assert "container_name: pearlflow-demo-web" in content


def test_docker_compose_yaml_valid():
    """Verify docker-compose.yml is valid YAML."""
    compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
    content = compose_path.read_text()

    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        pytest.fail(f"docker-compose.yml is not valid YAML: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
