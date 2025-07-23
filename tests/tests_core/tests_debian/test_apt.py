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
	",".join([
		"ret_code",
		"expected",
		"hide_stdout",
		"hide_stderr",
	]),
	(
		(1, False, False, True),
		(0, True, False, True),
		(1, False, True, False),
		(0, True, True, False),
		(1, False, False, False),
		(0, True, False, False),
		(1, False, True, True),
		(0, True, True, True),
	)
)
def test_dpkg_deb_is_installed(
	mocker: MockerFixture,
	ret_code: int,
	expected: bool,
	hide_stdout: bool,
	hide_stderr: bool,
):
	expected_stdout = subprocess.DEVNULL if hide_stdout else subprocess.PIPE
	expected_stderr = subprocess.DEVNULL if hide_stderr else subprocess.STDOUT
	m_call = mocker.patch("subprocess.call", return_value = ret_code)

	assert dpkg_deb_is_installed(
		pkg="mock-pkg",
		hide_stdout=hide_stdout,
		hide_stderr=hide_stderr,
	) is expected
	m_call.assert_called_once_with(
		["dpkg","-l", "mock-pkg"],
		stdout=expected_stdout,
		stderr=expected_stderr,
	)

class TestAptUpdate:
	def test_success(self, mocker: MockerFixture):
		m_subprocess_call = mocker.patch("subprocess.call", return_value=0)

		# Execution
		apt_update()

		m_subprocess_call.assert_called_once_with(
			["apt-get", "update", "-y"]
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

class TestAptInstall:
	def test_no_packages(self, mocker: MockerFixture):
		m_print_c = mocker.patch(f"{MODULE_PATH}.print_c")
		assert not apt_install(packages=[])
		m_print_c.assert_called_once()
	
	@pytest.mark.parametrize(
		"bad_value",
		(
			[1,2,3],
			{"some", "set"},
			{"some": "dict"},
		),
	)
	def test_raises_type_error(self, bad_value):
		with pytest.raises(TypeError, match="must be of type list"):
			apt_install(packages=bad_value)

	@pytest.mark.parametrize(
		",".join([
			"packages",
			"installed_packages",
			"expected_packages",
			"expected_args",
			"force_yes",
		]),
		(
			(
				["mock-pkg-1", "mock-pkg-2", "mock-pkg-3"],
				[],
				["mock-pkg-1", "mock-pkg-2", "mock-pkg-3"],
				["apt-get","install"],
				False
			),
			(
				["mock-pkg-1", "mock-pkg-2", "mock-pkg-3"],
				["mock-pkg-1"],
				["mock-pkg-2", "mock-pkg-3"],
				["apt-get","install"],
				False
			),
			(
				["mock-pkg-1", "mock-pkg-2", "mock-pkg-3"],
				["mock-pkg-1", "mock-pkg-2", "mock-pkg-3"],
				[],
				["apt-get","install"],
				False
			),
		),
	)
	def test_success(
		self,
		mocker: MockerFixture,
		packages: list[str],
		installed_packages: list[str],
		expected_packages: list[str],
		expected_args: list[str],
		force_yes: bool
	):
		# Mocking
		m_apt_update = mocker.patch(f"{MODULE_PATH}.apt_update")
		m_is_installed = mocker.patch(
			f"{MODULE_PATH}.dpkg_deb_is_installed",
			side_effect=[
				True if v in installed_packages else False
				for v in packages
			]
		)
		m_sp_call = mocker.patch(
			"subprocess.call",
			return_value=True
		)

		# Execution
		apt_install(packages=packages, force_yes=force_yes)

		# Assertions
		m_apt_update.assert_called_once()
		if expected_packages:
			m_sp_call.assert_called_once_with(expected_args + expected_packages)
		else:
			m_sp_call.assert_not_called()
		assert m_is_installed.call_count == len(packages)

		

class TestAptDistUpgrade:
	...

class TestAptAutoClean:
	...

class TestAptAutoRemove:
	...

class TestAptSearch:
	...
