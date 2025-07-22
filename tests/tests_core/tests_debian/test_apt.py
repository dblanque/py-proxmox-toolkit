########################### Standard Pytest Imports ############################
import pytest
from pytest_mock import MockerFixture
################################################################################
from core.debian.apt import apt_update
from core.format.colors import bcolors

MODULE_PATH = "core.debian.apt"

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

	@pytest.mark.parametrize(
		"bad_extras",
		(
			[False],
			[b"bytes"],
			[1234, 2345]
		)
	)
	def test_raises_type_error(self, mocker: MockerFixture, bad_extras):
		m_subprocess_call = mocker.patch("subprocess.call")

		# Execution
		with pytest.raises(TypeError):
			apt_update(extra_args=bad_extras) # type: ignore

		m_subprocess_call.assert_not_called()

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
