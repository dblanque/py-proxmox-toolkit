SRC_DEB_BOOKWORM_SYNTAX = """# Debian Repository Sources
deb https://deb.debian.org/debian {0} main non-free-firmware non-free
deb-src https://deb.debian.org/debian {0} main non-free-firmware non-free

deb https://security.debian.org/debian-security {0}-security main non-free-firmware non-free
deb-src https://security.debian.org/debian-security {0}-security main non-free-firmware non-free

deb https://deb.debian.org/debian {0}-updates main non-free-firmware non-free
deb-src https://deb.debian.org/debian {0}-updates main non-free-firmware non-free
"""

DEB_LISTS = {"bookworm": SRC_DEB_BOOKWORM_SYNTAX}
