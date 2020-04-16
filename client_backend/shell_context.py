"""Shell Context

Provides contextual information about the shell environment
"""

# No /usr/local by default :)
# Variables will be set by shell on startup
VERSION = "0.0"
PATH = "/usr/sbin:/usr/bin:/sbin:/bin"
USER = 99 # Default user is nobody (if in rdbsh will change to root)
HOME = "/" # Default home directory is empty
PWD = HOME
__status__ = 0 # For getting errorcodes of previous commands