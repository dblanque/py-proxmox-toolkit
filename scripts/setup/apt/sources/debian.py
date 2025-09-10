SRC_DEB_LISTS_FILENAME = "/etc/apt/sources.list"
SRC_DEB_LISTS = """# Debian Repository Sources
deb https://deb.debian.org/debian {0} main non-free-firmware
deb-src https://deb.debian.org/debian {0} main non-free-firmware

deb https://deb.debian.org/debian {0}-updates main non-free-firmware
deb-src https://deb.debian.org/debian {0}-updates main non-free-firmware

deb https://security.debian.org/debian-security {0}-security main non-free-firmware
deb-src https://security.debian.org/debian-security {0}-security main non-free-firmware
"""

SRC_DEB_SOURCES_FILENAME = "/etc/apt/sources.list.d/debian.sources"
SRC_DEB_SOURCES = """
Types: deb deb-src
URIs: http://deb.debian.org/debian
Suites: {0} {0}-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb deb-src
URIs: https://security.debian.org/debian-security
Suites: {0}-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
"""

DEB_FILENAMES = {
	"bookworm": SRC_DEB_LISTS_FILENAME,
	"trixie": SRC_DEB_SOURCES_FILENAME,
}

DEB_LISTS = {
	"bookworm": SRC_DEB_LISTS,
	"trixie": SRC_DEB_SOURCES,
}
