########################### Standard Pytest Imports ############################
import pytest
from pytest_mock import MockerFixture
################################################################################
import subprocess
from core.debian.apt import (
	make_apt_args,
	dpkg_deb_is_installed,
	apt_update,
	apt_install,
	apt_dist_upgrade,
	apt_autoclean,
	apt_autoremove,
	apt_search,
)
from core.format.colors import bcolors

MODULE_PATH = "core.debian.apt"

class TestMakeAptArgs:
	@pytest.mark.parametrize(
		"initial_args, extra_args, force_yes, expected",
		(
			(
				["apt-get", "update"],
				[],
				False,
				["apt-get", "update"]
			),
			(
				["apt-get", "update"],
				[],
				True,
				["apt-get", "update", "-y"]
			),
			(
				["apt-get", "dist-upgrade"],
				["--fix-broken", "--fix-missing"],
				False,
				[
					"apt-get",
					"dist-upgrade",
					"--fix-broken",
					"--fix-missing",
				]
			),
			(
				["apt-get", "dist-upgrade"],
				["--fix-broken", "--fix-missing"],
				True,
				[
					"apt-get",
					"dist-upgrade",
					"--fix-broken",
					"--fix-missing",
					"-y",
				]
			),
		),
		ids=[
			"APT Update (No force yes)",
			"APT Update (Force yes)",
			"APT Dist Upgrade (No force yes)",
			"APT Dist Upgrade (Force yes)",
		]
	)
	def test_success(
		self,
		initial_args,
		extra_args,
		force_yes,
		expected
	):
		assert make_apt_args(
			initial_args=initial_args,
			extra_args=extra_args,
			force_yes=force_yes
		) == expected

	def test_raises_no_args(self):
		with pytest.raises(ValueError, match="is required"):
			make_apt_args(initial_args=[])

	def test_raises_type_error(self):
		with pytest.raises(TypeError, match="initial_args must be"):
			make_apt_args(initial_args={"apt-get", "update"}) # type: ignore

	@pytest.mark.parametrize(
		"bad_value",
		(
			{"some_value"},
			{"key":"value"}
		)
	)
	def test_raises_bad_extra_type(self, bad_value):
		with pytest.raises(TypeError, match="extra_args must be of type list"):
			make_apt_args(
				initial_args=["apt-get", "update"],
				extra_args=bad_value
			) # type: ignore

	@pytest.mark.parametrize(
		"bad_values",
		(
			[1234, 5678],
			[{}],
			[None],
			[False]
		)
	)
	def test_raises_bad_extra_subtypes(self, bad_values):
		with pytest.raises(TypeError, match="elements in extra_args"):
			make_apt_args(
				initial_args=["apt-get", "update"],
				extra_args=bad_values
			) # type: ignore

@pytest.mark.parametrize(
	"ret_code, expected",
	(
		(1, False),
		(0, True),
	)
)
def test_dpkg_deb_is_installed(mocker: MockerFixture, ret_code: int, expected: bool):
	m_call = mocker.patch("subprocess.call", return_value = ret_code)
	assert dpkg_deb_is_installed(pkg="mock-pkg") is expected
	m_call.assert_called_once_with(
		["dpkg","-l", "mock-pkg"],
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL,
	)

class TestAptUpdate:
	def test_success_no_extras(self, mocker: MockerFixture):
		m_subprocess_call = mocker.patch("subprocess.call", return_value=0)

		# Execution
		apt_update()

		m_subprocess_call.assert_called_once_with(
			["apt-get", "update", "-y"]
		)

	def test_success_extras(self, mocker: MockerFixture):
		m_subprocess_call = mocker.patch("subprocess.call", return_value=0)

		# Execution
		apt_update(extra_args=["-h"])

		m_subprocess_call.assert_called_once_with(
			["apt-get", "update", "-h", "-y"]
		)

	def test_raises_retcode(self, mocker: MockerFixture):
		m_print_c = mocker.patch(f"{MODULE_PATH}.print_c")
		m_ret_code = 1
		m_subprocess_call = mocker.patch(
			"subprocess.call",
			return_value=m_ret_code
		)

		# Execution
		with pytest.raises(SystemExit) as e:
			apt_update() # type: ignore

		assert e.value.code == m_ret_code
		m_subprocess_call.assert_called_once()
		assert m_print_c.call_count == 2
		m_print_c.assert_any_call(
			bcolors.L_RED,
			"Could not do apt update (non-zero exit status %s)." % (
				str(m_ret_code)
			),
		)
