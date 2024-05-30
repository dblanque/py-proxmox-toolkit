
SRC_DEB_BOOKWORM_SYNTAX = """# Debian Repository Sources
deb http://deb.debian.org/debian {debian_distribution} main
deb-src http://deb.debian.org/debian {debian_distribution} main

deb http://deb.debian.org/debian-security/ {debian_distribution}-security main
deb-src http://deb.debian.org/debian-security/ {debian_distribution}-security main

deb http://deb.debian.org/debian {debian_distribution}-updates main
deb-src http://deb.debian.org/debian {debian_distribution}-updates main

deb http://ftp.us.debian.org/debian/ {debian_distribution} main contrib non-free non-free-firmware
deb http://security.debian.org/ {debian_distribution}-security main contrib non-free non-free-firmware
"""
