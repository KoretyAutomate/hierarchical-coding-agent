"""
Security validation layer for safe code execution.

Provides:
- Command whitelisting/blacklisting
- Path traversal prevention
- Dangerous pattern detection
- Resource limit validation
"""
import re
from pathlib import Path
from typing import List, Optional, Set


class SecurityValidator:
    """
    Validates commands and code for security issues.

    Implements defense-in-depth with multiple layers of validation.
    """

    # Dangerous commands that should never be executed
    BLACKLIST_COMMANDS = {
        'rm', 'rmdir', 'del', 'format',
        'dd', 'mkfs',
        'shutdown', 'reboot', 'halt', 'poweroff',
        'nc', 'netcat', 'telnet',
        'wget', 'curl',  # Can download malicious code
        'chmod', 'chown', 'chgrp',  # Permission changes
        'su', 'sudo', 'doas',  # Privilege escalation
        'passwd',  # Password changes
        'useradd', 'userdel', 'usermod',  # User management
        'iptables', 'nft', 'ufw',  # Firewall changes
        'systemctl', 'service',  # Service management
        'crontab',  # Scheduled task manipulation
        'at',  # Scheduled execution
    }

    # Commands that are explicitly allowed
    WHITELIST_COMMANDS = {
        'python3', 'python', 'pip',
        'pytest', 'unittest',
        'git',
        'ls', 'cat', 'echo', 'grep', 'find', 'sed', 'awk',
        'mkdir', 'touch', 'cp', 'mv',
        'head', 'tail', 'wc', 'sort', 'uniq',
        'diff', 'patch',
        'tar', 'gzip', 'gunzip', 'zip', 'unzip',
    }

    # Dangerous Python patterns
    DANGEROUS_PATTERNS = [
        # System/OS manipulation
        r'os\.system\s*\(',
        r'subprocess\.call\s*\(',
        r'subprocess\.Popen\s*\(',
        r'eval\s*\(',
        r'exec\s*\(',
        r'compile\s*\(',
        r'__import__\s*\(',

        # File operations on sensitive paths
        r'open\s*\([\'"]/(etc|bin|boot|dev|proc|sys)',
        r'/etc/(passwd|shadow|sudoers)',

        # Network operations
        r'import\s+socket',
        r'from\s+socket',
        r'socket\.',
        r'import\s+urllib',
        r'from\s+urllib',
        r'urllib\.',
        r'import\s+requests',
        r'from\s+requests',
        r'requests\.',
        r'import\s+http',
        r'from\s+http',
        r'http\.client',

        # Code injection
        r'pickle\.loads\s*\(',
        r'marshal\.loads\s*\(',
        r'yaml\.load\s*\(',  # unsafe YAML loading

        # Shell escapes
        r'shell\s*=\s*True',
    ]

    def __init__(
        self,
        strict_mode: bool = True,
        allow_network: bool = False,
        custom_whitelist: Optional[Set[str]] = None,
        custom_blacklist: Optional[Set[str]] = None
    ):
        """
        Initialize security validator.

        Args:
            strict_mode: If True, only whitelisted commands allowed
            allow_network: Whether to allow network operations
            custom_whitelist: Additional commands to whitelist
            custom_blacklist: Additional commands to blacklist
        """
        self.strict_mode = strict_mode
        self.allow_network = allow_network

        # Build final whitelist and blacklist
        self.whitelist = self.WHITELIST_COMMANDS.copy()
        if custom_whitelist:
            self.whitelist.update(custom_whitelist)

        self.blacklist = self.BLACKLIST_COMMANDS.copy()
        if custom_blacklist:
            self.blacklist.update(custom_blacklist)

        # Compile dangerous patterns
        self.dangerous_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.DANGEROUS_PATTERNS
        ]

    def validate_command(self, command: List[str]) -> tuple[bool, Optional[str]]:
        """
        Validate a shell command.

        Args:
            command: Command as list of strings

        Returns:
            (is_valid, error_message)
        """
        if not command:
            return False, "Empty command"

        base_command = Path(command[0]).name

        # Check blacklist first (highest priority)
        if base_command in self.blacklist:
            return False, f"Blacklisted command: {base_command}"

        # In strict mode, must be whitelisted
        if self.strict_mode and base_command not in self.whitelist:
            return False, f"Command not in whitelist: {base_command}"

        # Check for path traversal in arguments
        for arg in command[1:]:
            if self._is_path_traversal(arg):
                return False, f"Potential path traversal detected: {arg}"

            # Check for command injection
            if self._is_command_injection(arg):
                return False, f"Potential command injection detected: {arg}"

        return True, None

    def validate_python_code(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate Python code for dangerous patterns.

        Args:
            code: Python code to validate

        Returns:
            (is_valid, error_message)
        """
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            match = pattern.search(code)
            if match:
                # Special handling for network operations
                if not self.allow_network and any(
                    net_pattern in pattern.pattern
                    for net_pattern in ['socket', 'urllib', 'requests', 'http']
                ):
                    return False, f"Network operations not allowed: {match.group()}"

                # Other dangerous patterns
                return False, f"Dangerous pattern detected: {match.group()}"

        # Check for excessive recursion depth
        if 'sys.setrecursionlimit' in code:
            return False, "Modifying recursion limit not allowed"

        return True, None

    def validate_file_path(
        self,
        file_path: Path,
        workspace_root: Path
    ) -> tuple[bool, Optional[str]]:
        """
        Validate file path is within workspace and safe.

        Args:
            file_path: Path to validate
            workspace_root: Workspace root directory

        Returns:
            (is_valid, error_message)
        """
        try:
            # Resolve to absolute path
            abs_path = file_path.resolve()
            abs_workspace = workspace_root.resolve()

            # Check if within workspace
            try:
                abs_path.relative_to(abs_workspace)
            except ValueError:
                return False, f"Path outside workspace: {file_path}"

            # Check for sensitive file names
            sensitive_patterns = [
                '.env', '.git', '.ssh', 'id_rsa', 'private_key',
                'credentials', 'secrets', 'password', 'token'
            ]

            path_str = str(abs_path).lower()
            for pattern in sensitive_patterns:
                if pattern in path_str:
                    return False, f"Access to sensitive file not allowed: {file_path}"

            return True, None

        except Exception as e:
            return False, f"Path validation error: {e}"

    def _is_path_traversal(self, path: str) -> bool:
        """Check if path contains traversal patterns."""
        traversal_patterns = ['../', '..\\', '%2e%2e', '....']
        return any(pattern in path.lower() for pattern in traversal_patterns)

    def _is_command_injection(self, arg: str) -> bool:
        """Check if argument contains command injection patterns."""
        injection_patterns = [
            ';', '|', '&', '&&', '||',
            '`', '$(',
            '\n', '\r',
        ]
        return any(pattern in arg for pattern in injection_patterns)

    def validate_resource_limits(
        self,
        memory_mb: int,
        timeout_seconds: int,
        max_memory: int = 1024,
        max_timeout: int = 600
    ) -> tuple[bool, Optional[str]]:
        """
        Validate resource limits are within acceptable bounds.

        Args:
            memory_mb: Requested memory in MB
            timeout_seconds: Requested timeout in seconds
            max_memory: Maximum allowed memory in MB
            max_timeout: Maximum allowed timeout in seconds

        Returns:
            (is_valid, error_message)
        """
        if memory_mb > max_memory:
            return False, f"Memory limit too high: {memory_mb}MB (max: {max_memory}MB)"

        if timeout_seconds > max_timeout:
            return False, f"Timeout too high: {timeout_seconds}s (max: {max_timeout}s)"

        if memory_mb <= 0:
            return False, "Memory limit must be positive"

        if timeout_seconds <= 0:
            return False, "Timeout must be positive"

        return True, None


# Global validator instance
_validator: Optional[SecurityValidator] = None


def get_validator(
    strict_mode: bool = True,
    allow_network: bool = False,
    **kwargs
) -> SecurityValidator:
    """
    Get security validator singleton.

    Args:
        strict_mode: If True, only whitelisted commands allowed
        allow_network: Whether to allow network operations
        **kwargs: Additional validator configuration

    Returns:
        SecurityValidator instance
    """
    global _validator

    if _validator is None:
        _validator = SecurityValidator(
            strict_mode=strict_mode,
            allow_network=allow_network,
            **kwargs
        )

    return _validator


def reset_validator():
    """Reset validator singleton (useful for testing)."""
    global _validator
    _validator = None
