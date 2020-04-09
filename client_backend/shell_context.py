"""Shell Context

Provides contextual information about the shell environment
"""

# No /usr/local by default :)
# Variables will be set by shell on startup
env = {
    "VERSION": "0.0",
    "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
    "USER": None,
    "HOME": None
}