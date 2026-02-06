"""
Docker-based sandbox for safe code execution.

Provides isolated container environment for running untrusted code
without risking the host system.
"""
import os
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    import docker
    from docker.errors import DockerException, ImageNotFound, ContainerError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None
    DockerException = Exception
    ImageNotFound = Exception
    ContainerError = Exception


@dataclass
class SandboxResult:
    """Result from sandbox execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    timed_out: bool = False
    error: Optional[str] = None


class DockerSandbox:
    """
    Manages Docker containers for safe code execution.

    Features:
    - Ephemeral containers (destroyed after use)
    - Resource limits (CPU, memory, timeout)
    - Workspace mounting for file access
    - Output capture
    - Non-root execution
    """

    def __init__(
        self,
        image: str = "coding-agent-sandbox:latest",
        memory_limit: str = "512m",
        cpu_quota: int = 100000,  # 1 CPU
        timeout: int = 300,
        workspace_path: Optional[Path] = None,
        network_disabled: bool = False,
        enable_validation: bool = True
    ):
        """
        Initialize Docker sandbox.

        Args:
            image: Docker image to use
            memory_limit: Memory limit (e.g., "512m", "1g")
            cpu_quota: CPU quota in microseconds (100000 = 1 CPU)
            timeout: Execution timeout in seconds
            workspace_path: Path to mount as /workspace
            network_disabled: Disable network access
            enable_validation: Enable security validation
        """
        if not DOCKER_AVAILABLE:
            raise ImportError(
                "Docker SDK not installed. Install with: pip install docker"
            )

        self.image = image
        self.memory_limit = memory_limit
        self.cpu_quota = cpu_quota
        self.timeout = timeout
        self.workspace_path = workspace_path
        self.network_disabled = network_disabled
        self.enable_validation = enable_validation

        # Initialize security validator
        if enable_validation:
            from core.security import get_validator
            self.validator = get_validator(
                strict_mode=True,
                allow_network=not network_disabled
            )
        else:
            self.validator = None

        # Initialize Docker client
        try:
            self.client = docker.from_env()
            self.client.ping()
        except DockerException as e:
            raise RuntimeError(
                f"Docker is not available or not running: {e}\n"
                "Please ensure Docker is installed and running."
            )

        # Verify image exists
        self._ensure_image_exists()

    def _ensure_image_exists(self):
        """Ensure the sandbox image exists, build if necessary."""
        try:
            self.client.images.get(self.image)
        except ImageNotFound:
            print(f"⚠ Image {self.image} not found. Building...")
            self._build_image()

    def _build_image(self):
        """Build the sandbox image from Dockerfile."""
        sandbox_dir = Path(__file__).parent.parent / "sandbox"
        if not sandbox_dir.exists():
            raise FileNotFoundError(
                f"Sandbox directory not found: {sandbox_dir}\n"
                "Please create sandbox/Dockerfile first."
            )

        print(f"Building Docker image from {sandbox_dir}...")
        try:
            image, build_logs = self.client.images.build(
                path=str(sandbox_dir),
                tag=self.image,
                rm=True,
                forcerm=True
            )
            print(f"✓ Image built successfully: {self.image}")
        except DockerException as e:
            raise RuntimeError(f"Failed to build Docker image: {e}")

    def execute_python(
        self,
        code: str,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Execute Python code in sandbox.

        Args:
            code: Python code to execute
            timeout: Optional timeout override

        Returns:
            SandboxResult with output and status
        """
        # Validate code if validation enabled
        if self.validator:
            is_valid, error = self.validator.validate_python_code(code)
            if not is_valid:
                return SandboxResult(
                    stdout="",
                    stderr=f"Security validation failed: {error}",
                    exit_code=-1,
                    execution_time=0.0,
                    error=error
                )

        return self.execute_command(
            ["python3", "-c", code],
            timeout=timeout
        )

    def execute_command(
        self,
        command: List[str],
        timeout: Optional[int] = None,
        working_dir: str = "/workspace",
        environment: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        """
        Execute arbitrary command in sandbox with security validation.

        Args:
            command: Command and arguments as list
            timeout: Optional timeout override
            working_dir: Working directory in container
            environment: Environment variables

        Returns:
            SandboxResult with output and status
        """
        # Validate command if validation enabled
        if self.validator:
            is_valid, error = self.validator.validate_command(command)
            if not is_valid:
                return SandboxResult(
                    stdout="",
                    stderr=f"Security validation failed: {error}",
                    exit_code=-1,
                    execution_time=0.0,
                    error=error
                )

        timeout = timeout or self.timeout
        start_time = time.time()

        # Prepare volumes
        volumes = {}
        if self.workspace_path:
            volumes[str(self.workspace_path)] = {
                'bind': '/workspace',
                'mode': 'rw'
            }

        # Prepare network mode
        network_mode = 'none' if self.network_disabled else 'bridge'

        # Prepare environment
        env = environment or {}

        try:
            # Create and start container
            container = self.client.containers.run(
                self.image,
                command=command,
                detach=True,
                remove=False,  # We'll remove it manually
                mem_limit=self.memory_limit,
                cpu_quota=self.cpu_quota,
                volumes=volumes,
                working_dir=working_dir,
                environment=env,
                network_mode=network_mode,
                user="sandbox"  # Run as non-root user
            )

            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result['StatusCode']
                timed_out = False
            except Exception:
                # Timeout occurred
                container.stop(timeout=1)
                exit_code = -1
                timed_out = True

            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')

            # Clean up
            container.remove(force=True)

            execution_time = time.time() - start_time

            return SandboxResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time=execution_time,
                timed_out=timed_out
            )

        except ContainerError as e:
            execution_time = time.time() - start_time
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=e.exit_status,
                execution_time=execution_time,
                error=f"Container error: {e}"
            )

        except DockerException as e:
            execution_time = time.time() - start_time
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                error=f"Docker error: {e}"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                error=f"Unexpected error: {e}"
            )

    def execute_file(
        self,
        file_path: Path,
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Execute a Python file in sandbox.

        Args:
            file_path: Path to Python file (must be in workspace)
            args: Optional command-line arguments
            timeout: Optional timeout override

        Returns:
            SandboxResult with output and status
        """
        if self.workspace_path:
            # Make path relative to workspace
            try:
                rel_path = file_path.relative_to(self.workspace_path)
            except ValueError:
                return SandboxResult(
                    stdout="",
                    stderr=f"File must be in workspace: {file_path}",
                    exit_code=-1,
                    execution_time=0.0,
                    error="File not in workspace"
                )

            container_path = f"/workspace/{rel_path}"
        else:
            container_path = str(file_path)

        command = ["python3", container_path]
        if args:
            command.extend(args)

        return self.execute_command(command, timeout=timeout)

    def run_tests(
        self,
        test_path: str = "tests",
        pytest_args: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Run pytest tests in sandbox.

        Args:
            test_path: Path to tests directory/file
            pytest_args: Additional pytest arguments
            timeout: Optional timeout override

        Returns:
            SandboxResult with test output
        """
        command = ["pytest", test_path, "-v"]
        if pytest_args:
            command.extend(pytest_args)

        return self.execute_command(command, timeout=timeout or 120)

    def cleanup_containers(self):
        """Clean up any orphaned containers."""
        try:
            # Remove stopped containers
            containers = self.client.containers.list(
                all=True,
                filters={'ancestor': self.image}
            )
            for container in containers:
                if container.status != 'running':
                    container.remove(force=True)
        except DockerException:
            pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        self.cleanup_containers()


class FallbackSandbox:
    """
    Fallback sandbox that executes directly on host.
    Used when Docker is not available.

    WARNING: This provides NO isolation or security!
    Only use for development/testing.
    """

    def __init__(self, workspace_path: Optional[Path] = None, **kwargs):
        """Initialize fallback sandbox."""
        self.workspace_path = workspace_path
        print("⚠ WARNING: Using fallback sandbox (no isolation)")
        print("  Install Docker for secure execution")

    def execute_python(self, code: str, timeout: Optional[int] = None) -> SandboxResult:
        """Execute Python code directly (UNSAFE)."""
        import subprocess

        timeout = timeout or 300
        start_time = time.time()

        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_path
            )

            execution_time = time.time() - start_time

            return SandboxResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                stdout="",
                stderr="Execution timed out",
                exit_code=-1,
                execution_time=timeout,
                timed_out=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                error=str(e)
            )

    def execute_command(
        self,
        command: List[str],
        timeout: Optional[int] = None,
        **kwargs
    ) -> SandboxResult:
        """Execute command directly (UNSAFE)."""
        import subprocess

        timeout = timeout or 300
        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_path
            )

            execution_time = time.time() - start_time

            return SandboxResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                stdout="",
                stderr="Execution timed out",
                exit_code=-1,
                execution_time=timeout,
                timed_out=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                error=str(e)
            )

    def run_tests(self, test_path: str = "tests", **kwargs) -> SandboxResult:
        """Run tests directly (UNSAFE)."""
        return self.execute_command(["pytest", test_path, "-v"])

    def cleanup_containers(self):
        """No-op for fallback."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def get_sandbox(
    workspace_path: Optional[Path] = None,
    use_docker: bool = True,
    **kwargs
) -> DockerSandbox | FallbackSandbox:
    """
    Get appropriate sandbox instance.

    Args:
        workspace_path: Path to workspace directory
        use_docker: Whether to use Docker (falls back if unavailable)
        **kwargs: Additional sandbox configuration

    Returns:
        DockerSandbox if Docker available, FallbackSandbox otherwise
    """
    if use_docker and DOCKER_AVAILABLE:
        try:
            return DockerSandbox(workspace_path=workspace_path, **kwargs)
        except RuntimeError as e:
            print(f"⚠ Docker not available: {e}")
            print("  Falling back to direct execution (UNSAFE)")
            return FallbackSandbox(workspace_path=workspace_path)
    else:
        return FallbackSandbox(workspace_path=workspace_path)
