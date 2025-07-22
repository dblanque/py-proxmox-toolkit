########################### Standard Pytest Imports ############################
import pytest
from pytest_mock import MockerFixture

################################################################################
import subprocess
from scripts.setup.microcode import (
	get_cpu_vendor,
	get_cpu_vendor_json,
	SUPPORTED_CPU_VENDORS,
)
from typing import Protocol

MODULE_PATH = "scripts.setup.microcode"
lscpu_amd_ryzen_3700x = """
Architecture:             x86_64
  CPU op-mode(s):         32-bit, 64-bit
  Address sizes:          48 bits physical, 48 bits virtual
  Byte Order:             Little Endian
CPU(s):                   16
  On-line CPU(s) list:    0-15
Vendor ID:                AuthenticAMD
  Model name:             AMD Ryzen 7 3700X 8-Core Processor
    CPU family:           23
    Model:                113
    Thread(s) per core:   2
    Core(s) per socket:   8
    Socket(s):            1
    Stepping:             0
    BogoMIPS:             7186.53
    Flags:                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse s
                          se2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl tsc_reliable no
                          nstop_tsc cpuid extd_apicid tsc_known_freq pni pclmulqdq ssse3 fma cx16 sse4_1 sse4_2 movbe po
                          pcnt aes xsave avx f16c rdrand hypervisor lahf_lm cmp_legacy svm cr8_legacy abm sse4a misalign
                          sse 3dnowprefetch osvw topoext perfctr_core ssbd ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bm
                          i2 rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 clzero xsaveerptr arat npt n
                          rip_save tsc_scale vmcb_clean flushbyasid decodeassists pausefilter pfthreshold v_vmsave_vmloa
                          d umip rdpid
Virtualization features:
  Virtualization:         AMD-V
  Hypervisor vendor:      Microsoft
  Virtualization type:    full
Caches (sum of all):
  L1d:                    256 KiB (8 instances)
  L1i:                    256 KiB (8 instances)
  L2:                     4 MiB (8 instances)
  L3:                     16 MiB (1 instance)
NUMA:
  NUMA node(s):           1
  NUMA node0 CPU(s):      0-15
Vulnerabilities:
  Gather data sampling:   Not affected
  Itlb multihit:          Not affected
  L1tf:                   Not affected
  Mds:                    Not affected
  Meltdown:               Not affected
  Mmio stale data:        Not affected
  Reg file data sampling: Not affected
  Retbleed:               Mitigation; untrained return thunk; SMT enabled with STIBP protection
  Spec rstack overflow:   Vulnerable: Safe RET, no microcode
  Spec store bypass:      Mitigation; Speculative Store Bypass disabled via prctl
  Spectre v1:             Mitigation; usercopy/swapgs barriers and __user pointer sanitization
  Spectre v2:             Mitigation; Retpolines; IBPB conditional; STIBP always-on; RSB filling; PBRSB-eIBRS Not affect
                          ed; BHI Not affected
  Srbds:                  Not affected
  Tsx async abort:        Not affected
"""

lscpu_amd_ryzen_2600 = """
Architecture:             x86_64
  CPU op-mode(s):         32-bit, 64-bit
  Address sizes:          43 bits physical, 48 bits virtual
  Byte Order:             Little Endian
CPU(s):                   12
  On-line CPU(s) list:    0-11
Vendor ID:                AuthenticAMD
  BIOS Vendor ID:         Advanced Micro Devices, Inc.
  Model name:             AMD Ryzen 5 2600 Six-Core Processor
    BIOS Model name:      AMD Ryzen 5 2600 Six-Core Processor             Unknown CPU @ 3.4GHz
    BIOS CPU family:      107
    CPU family:           23
    Model:                8
    Thread(s) per core:   2
    Core(s) per socket:   6
    Socket(s):            1
    Stepping:             2
    BogoMIPS:             6787.19
    Flags:                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse s
                          se2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl nonstop_tsc cpu
                          id extd_apicid aperfmperf rapl pni pclmulqdq monitor ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt
                           aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dn
                          owprefetch osvw skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb hw
                          _pstate ssbd ibpb vmmcall fsgsbase bmi1 avx2 smep bmi2 rdseed adx smap clflushopt sha_ni xsave
                          opt xsavec xgetbv1 clzero irperf xsaveerptr arat npt lbrv svm_lock nrip_save tsc_scale vmcb_cl
                          ean flushbyasid decodeassists pausefilter pfthreshold avic v_vmsave_vmload vgif overflow_recov
                           succor smca sev sev_es
Virtualization features:
  Virtualization:         AMD-V
Caches (sum of all):
  L1d:                    192 KiB (6 instances)
  L1i:                    384 KiB (6 instances)
  L2:                     3 MiB (6 instances)
  L3:                     16 MiB (2 instances)
NUMA:
  NUMA node(s):           1
  NUMA node0 CPU(s):      0-11
Vulnerabilities:
  Gather data sampling:   Not affected
  Itlb multihit:          Not affected
  L1tf:                   Not affected
  Mds:                    Not affected
  Meltdown:               Not affected
  Mmio stale data:        Not affected
  Reg file data sampling: Not affected
  Retbleed:               Mitigation; untrained return thunk; SMT vulnerable
  Spec rstack overflow:   Mitigation; Safe RET
  Spec store bypass:      Mitigation; Speculative Store Bypass disabled via prctl
  Spectre v1:             Mitigation; usercopy/swapgs barriers and __user pointer sanitization
  Spectre v2:             Mitigation; Retpolines; IBPB conditional; STIBP disabled; RSB filling; PBRSB-eIBRS Not affecte
                          d; BHI Not affected
  Srbds:                  Not affected
  Tsx async abort:        Not affected
"""

lscpu_intel_xeon_e5_2690 = """
Architecture:          x86_64
CPU op-mode(s):        32-bit, 64-bit
Byte Order:            Little Endian
CPU(s):                56
On-line CPU(s) list:   0-55
Thread(s) per core:    2
Core(s) per socket:    14
Socket(s):             2
NUMA node(s):          2
Vendor ID:             GenuineIntel
CPU family:            6
Model:                 79
Model name:            Intel(R) Xeon(R) CPU E5-2690 v4 @ 2.60GHz
Stepping:              1
CPU MHz:               2600.000
CPU max MHz:           2600.0000
CPU min MHz:           1200.0000
BogoMIPS:              5201.37
Virtualization:        VT-x
Hypervisor vendor:     vertical
Virtualization type:   full
L1d cache:             32K
L1i cache:             32K
L2 cache:              256K
L3 cache:              35840K
NUMA node0 CPU(s):     0-13,28-41
NUMA node1 CPU(s):     14-27,42-55
"""


class LscpuMocker(Protocol):
	def __call__(
		self,
		varname: str,
	) -> bytes: ...


@pytest.fixture
def get_lscpu_result() -> LscpuMocker:
	def maker(varname: str) -> bytes:
		block: str = globals()[varname]
		return block.lstrip().encode("utf-8")

	return maker


class TestGetCpuVendor:
	@pytest.mark.parametrize(
		"mock_lscpu_fixture, expected",
		(
			("lscpu_amd_ryzen_3700x", "AuthenticAMD"),
			("lscpu_amd_ryzen_2600", "AuthenticAMD"),
			("lscpu_intel_xeon_e5_2690", "GenuineIntel"),
		),
	)
	def test_transform(
		self,
		mocker: MockerFixture,
		mock_lscpu_fixture: str,
		expected: str,
		get_lscpu_result: LscpuMocker,
	):
		# Mock first Popen (lscpu)
		m_lscpu = mocker.MagicMock()
		m_lscpu.stdout = get_lscpu_result(mock_lscpu_fixture)

		# Mock second Popen (grep)
		grep_sp = subprocess.Popen(
			["grep", "-oP", r"Vendor ID:\s*\K\S+"],
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
		)
		grep_out, grep_err = grep_sp.communicate(
			input=get_lscpu_result(mock_lscpu_fixture)
		)

		m_grep = mocker.MagicMock()
		m_grep.stdout = grep_out

		head_sp = subprocess.check_output(["head", "-n", "1"], input=grep_out)

		m_popen = mocker.patch("subprocess.Popen", side_effect=(m_lscpu, m_grep))
		m_check_output = mocker.patch("subprocess.check_output", return_value=head_sp)
		result = get_cpu_vendor()
		assert m_popen.call_count == 2
		m_popen.assert_any_call(["lscpu"], stdout=subprocess.PIPE)
		m_popen.assert_any_call(
			["grep", "-oP", r"Vendor ID:\s*\K\S+"],
			stdin=m_lscpu.stdout,
			stdout=subprocess.PIPE,
		)
		m_check_output.assert_called_once_with(["head", "-n", "1"], stdin=m_grep.stdout)
		m_lscpu.wait.assert_called_once()
		m_grep.wait.assert_called_once()
		assert result == expected


class TestGetCpuVendorJson:
	@pytest.mark.parametrize(
		"mock_vendor",
		(
			"AuthenticAMD",
			"GenuineIntel",
		),
	)
	def test_logic(self, mocker: MockerFixture, mock_vendor: str):
		m_check_output_ret = mocker.Mock()
		m_check_output = mocker.patch(
			"subprocess.check_output",
			return_value=m_check_output_ret
		)
		m_lscpu_json_partial = {
			"lscpu": [
				{
					"field": "Vendor ID:",
					"data": mock_vendor,
				},
			]
		}
		m_json_loads = mocker.patch(
			"json.loads",
			return_value=m_lscpu_json_partial,
		)
		assert get_cpu_vendor_json() == mock_vendor
		m_check_output.assert_called_once_with(["lscpu", "--json"])
		m_json_loads.assert_called_once_with(m_check_output_ret)

	def test_returns_unknown(self, mocker: MockerFixture):
		m_check_output = mocker.patch(
			"subprocess.check_output",
			side_effect=Exception
		)
		m_json_loads = mocker.patch("json.loads")
		assert get_cpu_vendor_json() == "Unknown"
		m_check_output.assert_called_once_with(["lscpu", "--json"])
		m_json_loads.assert_not_called()

	def test_raises(self, mocker: MockerFixture):
		m_check_output = mocker.patch(
			"subprocess.check_output",
			side_effect=Exception
		)
		m_json_loads = mocker.patch("json.loads")
		with pytest.raises(Exception):
			get_cpu_vendor_json(raise_exception=True)
		m_check_output.assert_called_once_with(["lscpu", "--json"])
		m_json_loads.assert_not_called()

class TestSupportedVendors:
	@pytest.mark.parametrize(
		"vendor_name",
		(
			"AuthenticAMD",
			"GenuineIntel",
		),
	)
	def test_keys(self, vendor_name: str):
		assert vendor_name.lower() in set(SUPPORTED_CPU_VENDORS.keys())

	@pytest.mark.parametrize(
		"vendor_name, expected_keys",
		(
			(
				"AuthenticAMD",
				("label", "deb"),
			),
			(
				"GenuineIntel",
				("label", "deb", "supplementary_deb"),
			),
		),
	)
	def test_sub_keys(self, vendor_name: str, expected_keys: tuple):
		vendor = SUPPORTED_CPU_VENDORS[vendor_name.lower()]
		for k in expected_keys:
			assert k in vendor

	@pytest.mark.parametrize(
		"vendor_name, expected_deb_pkg",
		(
			("AuthenticAMD", "amd64-microcode"),
			("GenuineIntel", "intel-microcode"),
		),
	)
	def test_deb(self, vendor_name: str, expected_deb_pkg: str):
		assert SUPPORTED_CPU_VENDORS[
			vendor_name.lower()
		]["deb"] == expected_deb_pkg
