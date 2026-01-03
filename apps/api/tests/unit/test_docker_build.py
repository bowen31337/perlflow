"""
Test Docker containerization for API service.
These tests verify Docker configuration without requiring Docker to be installed.
"""

import os
import pytest
from pathlib import Path


class TestDockerBuild:
    """Test Docker containerization setup."""

    def test_dockerfile_exists(self):
        """Verify API Dockerfile exists and has required content."""
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "API Dockerfile should exist"

        content = dockerfile_path.read_text()

        # Verify required sections exist
        required_sections = [
            "FROM python:3.11-slim",
            "uv sync --frozen --no-install-project",
            '"uvicorn", "src.main:app"',
            "EXPOSE 8000",
            "HEALTHCHECK"
        ]

        for section in required_sections:
            assert section in content, f"Dockerfile should contain: {section}"

    def test_dockerfile_multistage_build(self):
        """Verify Dockerfile uses multistage build for optimization."""
        dockerfile_path = Path("Dockerfile")
        content = dockerfile_path.read_text()

        # Verify builder and runtime stages
        assert "FROM python:3.11-slim as builder" in content
        assert "FROM python:3.11-slim as runtime" in content
        assert "COPY --from=builder" in content

    def test_dockerfile_security_practices(self):
        """Verify Dockerfile follows security best practices."""
        dockerfile_path = Path("Dockerfile")
        content = dockerfile_path.read_text()

        # Verify non-root user
        assert "USER pearlflow" in content
        assert "useradd -r -g pearlflow pearlflow" in content

        # Verify cleanup
        assert "rm -rf /var/lib/apt/lists/*" in content

    def test_dockerfile_healthcheck(self):
        """Verify Dockerfile includes health check."""
        dockerfile_path = Path("Dockerfile")
        content = dockerfile_path.read_text()

        assert "HEALTHCHECK" in content
        assert "curl -f http://localhost:8000/health" in content

    def test_pyproject_toml_for_docker(self):
        """Verify pyproject.toml is configured for Docker builds."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists()

        content = pyproject_path.read_text()

        # Verify uv is used as package manager
        assert "uv" in content


class TestDockerCompose:
    """Test Docker Compose configuration."""

    def test_docker_compose_file_exists(self):
        """Verify docker-compose.yml exists in root directory."""
        # From apps/api/tests/unit/test_docker_build.py, go up 5 levels to project root
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml should exist in root"

        content = compose_path.read_text()

        # Verify required services
        required_services = [
            "postgres:",
            "redis:",
            "api:",
            "frontend:"
        ]

        for service in required_services:
            assert service in content, f"Docker Compose should include {service}"

    def test_docker_compose_api_service(self):
        """Verify API service configuration in docker-compose.yml."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # Verify API service configuration
        api_config = """
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: pearlflow-api
    environment:
      - DATABASE_URL=postgresql+asyncpg://pearlflow:pearlflow123@postgres:5432/pearlflow
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
        """.strip()

        for line in api_config.split('\n'):
            if line.strip():
                assert line.strip() in content, f"API service should have: {line.strip()}"

    def test_docker_compose_postgres_service(self):
        """Verify PostgreSQL service configuration."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        # Verify PostgreSQL configuration
        postgres_config = """
    image: postgres:16-alpine
    container_name: pearlflow-postgres
    environment:
      POSTGRES_DB: pearlflow
      POSTGRES_USER: pearlflow
      POSTGRES_PASSWORD: pearlflow123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pearlflow -d pearlflow"]
        """.strip()

        for line in postgres_config.split('\n'):
            if line.strip():
                assert line.strip() in content, f"PostgreSQL service should have: {line.strip()}"

    def test_docker_compose_volumes(self):
        """Verify volume configuration for data persistence."""
        compose_path = Path(__file__).parent.parent.parent.parent.parent / "docker-compose.yml"
        content = compose_path.read_text()

        assert "volumes:" in content
        assert "postgres_data:" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
