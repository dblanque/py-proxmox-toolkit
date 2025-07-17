SRC_DEB_BOOKWORM_SYNTAX = """# Debian Repository Sources
deb http://deb.debian.org/debian {0} main
deb-src http://deb.debian.org/debian {0} main

deb http://deb.debian.org/debian-security/ {0}-security main
deb-src http://deb.debian.org/debian-security/ {0}-security main

deb http://deb.debian.org/debian {0}-updates main
deb-src http://deb.debian.org/debian {0}-updates main

deb http://ftp.debian.org/debian/ {0} main contrib non-free non-free-firmware
deb http://security.debian.org/ {0}-security main contrib non-free non-free-firmware
"""

DEB_LISTS = {"bookworm": SRC_DEB_BOOKWORM_SYNTAX}
