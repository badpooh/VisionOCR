import time
from datetime import datetime, timezone, timedelta

from function.func_connection import ConnectionManager
from function.func_touch import TouchManager

from config.a7300 import ConfigMap as ConfigMapA7300
from config.a3700n import ConfigMap as ConfigMapA3700N
from models import config as app_config


# ----------------------------------------------------------------------------
# Setup 디폴트값 — setup_initialization 이 적용하는 값과 일치해야 한다.
# verify_setup_defaults() 가 이 값을 기준으로 변경 후 다른 셀이 보존됐는지 검증.
#
# Base = A7300. A3700N 등 다른 제품은 overrides 만 명시.
# get_setup_defaults(product) 가 base + overrides 머지해서 반환.
# ----------------------------------------------------------------------------
SETUP_DEFAULTS = {
    'A7300': {
        'addr_wiring': 0,
        'addr_reference_voltage': 1900,
        'addr_vt_primary_ll_voltage': 1900,
        'addr_vt_secondary_ll_voltage': 1900,
        'addr_min_measured_secondary_ln_voltage': 5,
        'addr_reference_voltage_mode': 0,
        'addr_sliding_reference_voltage_type': 0,
        'addr_rotating_sequence': 1,
        'addr_ct_primary_current': 50,
        'addr_ct_secondary_current': 5,
        'addr_reference_current': 50,
        'addr_min_measured_current': 5,
        'addr_tdd_reference': 1,
        'addr_nominal_tdd_current': 0,
        'addr_sub_interval_time': 1,           # 초기화 값 15, Demo Test 위해 1
        'addr_num_of_sub_interval': 1,
        'addr_demand_power_type': 0,
        'addr_demand_sync_mode': 0,
        'addr_thermal_response_index': 90,
        'addr_phase_power_calculation': 1,
        'addr_total_power_calculation': 0,
        'addr_pf_sign': 1,
        'addr_pf_value_at_no_load': 1,
        'addr_reactive_power_sign': 1,
    },
    # A3700N: A7300 base 위에 다음 항목만 다르게.
    'A3700N': {
        # A3700N 은 1배 스케일 (A7300 은 10배 스케일이라 380V 표시에 3800 입력)
        'addr_reference_voltage': 380,
        'addr_vt_primary_ll_voltage': 380,          # alias of pt_primary_voltage
        'addr_vt_secondary_ll_voltage': 380,        # alias of pt_secondary_voltage (range 1-999)
        'addr_min_measured_current': 20,
    },
}


def get_setup_defaults(product):
    """product 의 디폴트값 dict 반환 (A7300 base + product overrides 머지)."""
    base = SETUP_DEFAULTS.get('A7300', {})
    overrides = SETUP_DEFAULTS.get(product, {}) if product != 'A7300' else {}
    return {**base, **overrides}


class ModbusLabels:

	A2700_SETUP_UNLOCK_ADDR = 50999
	A2700_CONTROL_UNLOCK_ADDR = 54999
	A2700_TEST_PARAMETER_ACCESS_ADDR = 55800
	A2700_TEST_EXIT_TIMEOUT_ADDR = 55801
	A2700_TEST_MODE_SETUP_ADDR = 55802
	A2700_TEST_MODE_CONTROL_ADDR = 55900

	touch_manager = TouchManager()

	def __init__(self):
		self.connect_manager = ConnectionManager()
		self.response = None

	# ------------------------------------------------------------
	# 제품별 라우팅 헬퍼
	# ------------------------------------------------------------
	def uses_native_modbus_ui(self) -> bool:
		"""펌웨어가 외부소스 인가 테스트 모드(가상 터치/캡처, Modbus UI 테스트
		레지스터 시퀀스) 를 지원하는가? 현재는 A7300 만 True.

		단일 소스: models/config.py.EXTERNAL_SOURCE_TEST_MODE_PRODUCTS
		추후 데모 모드 / 설정 모드 흐름이 분리되면 그쪽 set 으로 분기해야 함.
		"""
		try:
			return self.connect_manager.PRODUCT in app_config.EXTERNAL_SOURCE_TEST_MODE_PRODUCTS
		except AttributeError:
			return False

	def _is_error_response(self, response):
		return response is None or (hasattr(response, "isError") and response.isError())

	def _write_checked(self, address, value, label):
		self.response = self.connect_manager.setup_client.write_register(address, value)
		if self._is_error_response(self.response):
			raise RuntimeError(f"{label} write failed: addr={address}, value={value}, response={self.response}")
		return self.response

	def _unlock_a2700_remote(self):
		if self.connect_manager.setup_client is None:
			print("setup_client가 연결되어 있지 않습니다.")
			return False
		for address, values, label in (
			(self.A2700_SETUP_UNLOCK_ADDR, [2300, 0, 700, 1], "A2700 setup unlock"),
			(self.A2700_CONTROL_UNLOCK_ADDR, [2300, 0, 1600, 1], "A2700 control unlock"),
		):
			for value in values:
				self._write_checked(address, value, label)
				time.sleep(0.4)
		return True

	def _a2700_test_mode_setting(self, mode):
		self.touch_manager.uitest_mode_start()
		if not self._unlock_a2700_remote():
			return
		client = self.connect_manager.setup_client
		self.response = client.read_holding_registers(self.A2700_TEST_PARAMETER_ACCESS_ADDR, count=3)
		if self._is_error_response(self.response):
			raise RuntimeError(f"A2700 test parameter read failed: {self.response}")
		timeout_value = 10000 if mode else 1
		self._write_checked(self.A2700_TEST_EXIT_TIMEOUT_ADDR, timeout_value, "A2700 test exit timeout")
		self._write_checked(self.A2700_TEST_MODE_SETUP_ADDR, mode, "A2700 test mode setup")
		self._write_checked(self.A2700_TEST_PARAMETER_ACCESS_ADDR, 1, "A2700 test parameter apply")
		self._write_checked(self.A2700_TEST_MODE_CONTROL_ADDR, mode, "A2700 test mode control")
		print(
			"A2700 Demo mode setting Done (timeout=10000)"
			if mode else
			"A2700 Test Mode OFF (timeout=1)"
		)

	def test_mode_balance_setting(self):

		product = self.connect_manager.PRODUCT
		if product == "A2700":
			self._a2700_test_mode_setting(1)
			return

		if product == "A7300":
			self.touch_manager.uitest_mode_start()
			values = [2300, 0, 700, 1]
			values_control = [2300, 0, 1600, 1]
			if self.connect_manager.setup_client is not None:
				for value in values:
					self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_setup_lock.value[0], value)
				for value_control in values_control:
					self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_control_lock.value[0], value_control)
					time.sleep(0.6)
				self.response = self.connect_manager.setup_client.read_holding_registers(4000, count=3)
				self.response = self.connect_manager.setup_client.write_register(4002, 0)
				self.response = self.connect_manager.setup_client.write_register(4000, 1)
				self.response = self.connect_manager.setup_client.write_register(4001, 1)
				print("Demo mode setting Done")
			else:
				print("setup_client가 연결되어 있지 않습니다.")

		if product == "A3700N":
			self.touch_manager.uitest_mode_start()
			values_control = [2300, 0, 1600, 1]
			if self.connect_manager.setup_client is not None:
				for value_control in values_control:
					self.response = self.connect_manager.setup_client.write_register(ConfigMapA3700N.addr_control_lock.value[0], value_control)
					time.sleep(0.6)
				self.response = self.connect_manager.setup_client.read_holding_registers(4000, count=2)
				self.response = self.connect_manager.setup_client.write_register(4001, 0)
				self.response = self.connect_manager.setup_client.write_register(4000, 1)
				self.response = self.connect_manager.setup_client.write_register(8050, 1)
				print("Demo mode setting Done")
			else:
				print("setup_client가 연결되어 있지 않습니다.")

		return
	
	def test_mode_off(self):
		if self.connect_manager.PRODUCT == "A2700":
			self._a2700_test_mode_setting(0)
			return
		if not self.uses_native_modbus_ui():
			print(f"[{self.connect_manager.PRODUCT}] test_mode_off: "
			    	f"not applicable (bridge mode, no-op)")
			return
		self.touch_manager.uitest_mode_start()
		values = [2300, 0, 700, 1]
		values_control = [2300, 0, 1600, 1]
		if self.connect_manager.setup_client is not None:
			for value in values:
				self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_setup_lock.value[0], value)
			# time.sleep(0.6)
			for value_control in values_control:
				self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_control_lock.value[0], value_control)
				time.sleep(0.6)
			self.response = self.connect_manager.setup_client.read_holding_registers(4000, count=3)
			self.response = self.connect_manager.setup_client.write_register(4002, 60)
			self.response = self.connect_manager.setup_client.write_register(4000, 0)
			self.response = self.connect_manager.setup_client.write_register(4001, 1)
			print("Test Mode OFF")
		else:
			# print(self.response.isError())
			print("setup_client가 연결되어 있지 않습니다.")
		return 
	
	def read_float(self, address, aggre_selection):

		list_address = isinstance(address, list)
		address_values = address if list_address else [address]

		results = []

		# Aggregation selection 레지스터는 A7300 전용 의미(peak/avg 선택).
		# A3700N 은 같은 주소가 schedule slot 선택이라 semantics 가 달라서
		# 이 write 를 하면 의도치 않은 상태 변경이 발생할 수 있음 → 스킵.
		if self.uses_native_modbus_ui():
			### Aggregation selection -> display peak ###
			self.connect_manager.setup_client.read_holding_registers(**ConfigMapA7300.addr_aggregation_selection.value)
			self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_aggregation_selection.value['address'], aggre_selection)
			self.connect_manager.setup_client.read_holding_registers(**ConfigMapA7300.addr_aggregation_selection.value)
		
		for item in address_values:
			addr = item[0] if isinstance(item, (list, tuple)) else item
			response = self.connect_manager.setup_client.read_holding_registers(addr, count=2)
			
			if response.isError():
				print(f"Error reading registers for FLOAT32 at address {addr}")
				results.append(None)
				continue

			regs = response.registers

			float_value = self.connect_manager.setup_client.convert_from_registers(
				registers=regs,
				data_type=self.connect_manager.setup_client.DATATYPE.FLOAT32,  
				word_order="big",
			)
			results.append(float_value)
			
		if list_address:
			return results
		else:
			return results[0] if results else None
	
	def setup_initialization(self):
		"""제품-aware 초기화. A7300/A3700N 모두 동작.

		측정 setup 6000번대 주소가 매핑된 제품(A7300, A3700N)에서 동일한
		초기값 시퀀스를 쓴다. 매핑 없는 항목은 자동 skip.
		브릿지 제품군은 setup_client(Modbus 502)만 있으면 동작 — 터치는 불필요.
		"""
		from config.config_product import get_map_module
		product = self.connect_manager.PRODUCT or "A7300"
		try:
			cfg_map = get_map_module(product).ConfigMap
		except Exception as e:
			print(f"[setup_initialization] ConfigMap load failed ({product}): {e}")
			return

		if self.connect_manager.setup_client is None:
			print(f"[setup_initialization] setup_client = None — skip")
			return

		# A7300 전용: 가상 터치 모드 진입. 브릿지 제품군은 no-op.
		self.touch_manager.uitest_mode_start()

		client = self.connect_manager.setup_client
		values = [2300, 0, 700, 1]
		values_control = [2300, 0, 1600, 1]

		def value_32bit(value):
			return (value >> 16) & 0xFFFF, value & 0xFFFF

		def _addr(name):
			"""매핑 없으면 None."""
			try:
				return cfg_map[name].value
			except (KeyError, AttributeError):
				return None

		def _w16(name, v):
			a = _addr(name)
			if a is None:
				print(f"[init] {name} not mapped on {product} -> skip")
				return
			client.write_register(a[0], v)

		def _w32(name, v):
			a = _addr(name)
			if a is None:
				print(f"[init] {name} not mapped on {product} -> skip")
				return
			client.write_registers(a[0], [*value_32bit(v)])

		def _read_access(name):
			a = _addr(name)
			if a is None:
				return
			if isinstance(a, dict):
				client.read_holding_registers(**a)
			else:
				client.read_holding_registers(a[0], count=a[1])

		def _commit_access(name):
			a = _addr(name)
			if a is None:
				return
			if isinstance(a, dict):
				client.write_register(a['address'], 1)
			else:
				client.write_register(a[0], 1)

		# 제품별 디폴트값 dict
		defaults = get_setup_defaults(product)
		print(f"[init] defaults for {product}: "
		      f"reference_voltage={defaults['addr_reference_voltage']} "
		      f"vt_primary={defaults['addr_vt_primary_ll_voltage']} "
		      f"min_measured_current={defaults['addr_min_measured_current']}")

		# Lock 시퀀스
		a_setup = _addr('addr_setup_lock')
		if a_setup:
			for v in values:
				client.write_register(a_setup[0], v)
				time.sleep(0.6)
		else:
			print(f"[init] addr_setup_lock not mapped on {product} -> skip")
		a_ctrl = _addr('addr_control_lock')
		if a_ctrl:
			for v in values_control:
				client.write_register(a_ctrl[0], v)
				time.sleep(0.6)
		else:
			print(f"[init] addr_control_lock not mapped on {product} -> skip")

		### measurement setup ###
		# A3700N: Module ID = 0 (MCU) — A7300 에는 없는 단계
		is_a3700n = (product == "A3700N")
		if is_a3700n:
			a_mid = _addr('addr_module_id')
			if a_mid:
				try:
					client.write_register(a_mid[0], 0)
					print(f"[init] Module ID @ {a_mid[0]} = 0 (MCU)")
					time.sleep(0.3)
				except Exception as e:
					print(f"[init] Module ID write failed: {e}")
			else:
				print(f"[init] addr_module_id not mapped on A3700N -> skip")

		_read_access('addr_measurement_setup_access')
		_w16('addr_wiring', defaults['addr_wiring'])
		_w32('addr_reference_voltage', defaults['addr_reference_voltage'])
		_w32('addr_vt_primary_ll_voltage', defaults['addr_vt_primary_ll_voltage'])
		_w16('addr_vt_secondary_ll_voltage', defaults['addr_vt_secondary_ll_voltage'])
		_w16('addr_min_measured_secondary_ln_voltage', defaults['addr_min_measured_secondary_ln_voltage'])
		_w16('addr_reference_voltage_mode', defaults['addr_reference_voltage_mode'])

		_read_access('addr_sliding_reference_voltage_setup_access')
		_w16('addr_sliding_reference_voltage_type', defaults['addr_sliding_reference_voltage_type'])
		_commit_access('addr_sliding_reference_voltage_setup_access')

		_w16('addr_rotating_sequence', defaults['addr_rotating_sequence'])
		_w32('addr_ct_primary_current', defaults['addr_ct_primary_current'])
		_w16('addr_ct_secondary_current', defaults['addr_ct_secondary_current'])
		_w32('addr_reference_current', defaults['addr_reference_current'])
		_w16('addr_min_measured_current', defaults['addr_min_measured_current'])
		_w16('addr_tdd_reference', defaults['addr_tdd_reference'])
		_w32('addr_nominal_tdd_current', defaults['addr_nominal_tdd_current'])
		# 초기화 값은 15, Demo Test를 위해 1로 변경
		_w16('addr_sub_interval_time', defaults['addr_sub_interval_time'])
		_w16('addr_num_of_sub_interval', defaults['addr_num_of_sub_interval'])
		_w16('addr_demand_power_type', defaults['addr_demand_power_type'])
		_w16('addr_demand_sync_mode', defaults['addr_demand_sync_mode'])
		_w16('addr_thermal_response_index', defaults['addr_thermal_response_index'])
		_w16('addr_phase_power_calculation', defaults['addr_phase_power_calculation'])
		_w16('addr_total_power_calculation', defaults['addr_total_power_calculation'])
		_w16('addr_pf_sign', defaults['addr_pf_sign'])
		_w16('addr_pf_value_at_no_load', defaults['addr_pf_value_at_no_load'])
		_w16('addr_reactive_power_sign', defaults['addr_reactive_power_sign'])

		# Commit: A7300 은 1, A3700N 은 0(MCU 모듈 타입으로 적용)
		commit_val = 0 if is_a3700n else 1
		a_acc = _addr('addr_measurement_setup_access')
		if a_acc:
			try:
				if isinstance(a_acc, dict):
					client.write_register(a_acc['address'], commit_val)
				else:
					client.write_register(a_acc[0], commit_val)
				print(f"[init] measurement_setup_access commit = {commit_val}")
			except Exception as e:
				print(f"[init] commit failed: {e}")
		print(f"[setup_initialization] {product} done")

	def verify_setup_defaults(self, except_addr_tuple=None):
		"""setup_initialization 직후 SETUP_DEFAULTS 값들이 제대로 적용됐는지,
		또는 설정 변경 후에도 다른 셀이 디폴트값을 유지하는지 검증.

		Args:
		    except_addr_tuple: 변경한 항목의 ConfigMap value (예: (6002, 1) 또는
		                       {'address': 6001, 'count': 1}). 같은 주소를 가진
		                       모든 alias가 비교에서 제외된다.

		Returns:
		    (ok: bool, mismatches: list of (name, expected, actual))
		"""
		# A2700 은 defaults_<product>.xlsx 단일 source 로 라우팅 — SETUP_DEFAULTS
		# dict + ConfigMap 하드코딩 양쪽에 베껴 적을 필요 없음. A7300/A3700N 은
		# 기존 하드코딩 경로 유지 (점진 마이그레이션 가능).
		product = self.connect_manager.PRODUCT or "A7300"
		if product == "A2700":
			return self._verify_setup_defaults_from_xlsx(
				product, except_addr_tuple
			)

		from config.config_product import get_map_module
		try:
			cfg_map = get_map_module(product).ConfigMap
		except Exception as e:
			print(f"[verify_setup_defaults] ConfigMap load failed: {e}")
			return False, [('LOAD_ERROR', None, str(e))]

		client = self.connect_manager.setup_client
		if client is None:
			print(f"[verify_setup_defaults] setup_client = None")
			return False, [('NO_CLIENT', None, None)]

		# except 의 실제 주소 추출
		def _addr_no(a):
			if a is None:
				return None
			if isinstance(a, tuple):
				return a[0]
			if isinstance(a, dict):
				return a.get('address')
			return None
		except_addr_no = _addr_no(except_addr_tuple)

		# A3700N: Module Setup (6003~6202) read 전에 access fetch 트리거 필수.
		# 6002 read하면 그 시점의 디바이스 값이 6003~6202 영역으로 fetch된다.
		# fetch 없이 직접 read하면 stale 값을 반환하므로 사용자 수동 변경을
		# 감지 못한다. A3700N은 Module ID + access read 시퀀스 필요.
		if product == "A3700N":
			try:
				a_mid = cfg_map['addr_module_id'].value if 'addr_module_id' in cfg_map.__members__ else None
				if a_mid:
					client.write_register(a_mid[0], 0)  # MCU 선택
					import time as _t
					_t.sleep(0.2)
			except Exception as e:
				print(f"[verify] Module ID set failed: {e}")
		try:
			a_acc = cfg_map['addr_measurement_setup_access'].value if 'addr_measurement_setup_access' in cfg_map.__members__ else None
			if a_acc:
				if isinstance(a_acc, dict):
					client.read_holding_registers(**a_acc)
				else:
					client.read_holding_registers(a_acc[0], count=a_acc[1])
				import time as _t
				_t.sleep(0.2)
				print(f"[verify] access fetch triggered on {product}")
		except Exception as e:
			print(f"[verify] access fetch failed: {e}")

		mismatches = []
		defaults = get_setup_defaults(product)
		for name, expected in defaults.items():
			try:
				a = cfg_map[name].value
			except (KeyError, AttributeError):
				# 매핑 없는 항목은 검증 skip
				continue

			a_no = _addr_no(a)
			# 변경한 항목 (alias 포함) 이면 skip
			if except_addr_no is not None and a_no == except_addr_no:
				continue

			# word_count 자동 결정
			if isinstance(a, tuple):
				word_count = a[1] if len(a) > 1 else 1
			elif isinstance(a, dict):
				word_count = a.get('count', 1)
			else:
				word_count = 1

			try:
				if word_count == 2:
					resp = client.read_holding_registers(a_no, count=2)
					if resp.isError():
						mismatches.append((name, expected, 'READ_ERROR'))
						continue
					regs = resp.registers
					actual = (regs[0] << 16) | regs[1]
				else:
					resp = client.read_holding_registers(a_no, count=1)
					if resp.isError():
						mismatches.append((name, expected, 'READ_ERROR'))
						continue
					actual = resp.registers[0]
			except Exception as e:
				mismatches.append((name, expected, f'EXC: {e}'))
				continue

			if actual != expected:
				mismatches.append((name, expected, actual))

		ok = (len(mismatches) == 0)
		if ok:
			print(f"[verify_setup_defaults] OK — 모든 항목 디폴트값 유지")
		else:
			print(f"[verify_setup_defaults] FAIL — {len(mismatches)} 항목 불일치:")
			for name, exp, act in mismatches:
				print(f"   {name:<40} expected={exp!r:<10} actual={act!r}")
		return ok, mismatches

	def _verify_setup_defaults_from_xlsx(self, product, except_addr_tuple=None):
		"""defaults_<product>.xlsx 의 모든 case 를 단일 source 로 사용해서 검증.

		각 case 의 (addr, value_type, target_value[0]) 가 곧 기댓값.
		access_addr 별로 그룹핑해서 wide FC3 read 한 번 → setup buffer 로딩 +
		변경된 값들 한꺼번에 비교. except_addr_tuple 의 시작주소와 같은 case 는
		"방금 우리가 바꾼 항목" 이라 비교 대상 제외.

		float 비교는 1e-3 tolerance, 그 외엔 정수 일치 비교.
		"""
		from setup_test.setup_xlsx_loader import load_defaults_cases
		from collections import defaultdict

		client = self.connect_manager.setup_client
		if client is None:
			print(f"[verify_xlsx] setup_client = None")
			return False, [('NO_CLIENT', None, None)]

		try:
			cases = load_defaults_cases(product)
		except FileNotFoundError as e:
			print(f"[verify_xlsx] {e}")
			return False, [('NO_XLSX', None, str(e))]

		def _addr_no(a):
			if a is None: return None
			if isinstance(a, tuple): return a[0]
			if isinstance(a, dict): return a.get('address')
			return None
		except_addr_no = _addr_no(except_addr_tuple)

		# 그룹핑 — apply_defaults 와 동일 패턴
		groups = defaultdict(list)
		for c in cases:
			if c.get('addr') is None or c.get('access_addr') is None:
				continue
			if not c.get('target_value'):
				continue
			groups[c['access_addr'][0]].append(c)

		mismatches = []
		total_checked = 0

		for acc_addr, group_cases in groups.items():
			# wide read 범위 — 그룹 내 max(addr+words) 까지
			max_end = acc_addr + 1
			for c in group_cases:
				a = c['addr']
				max_end = max(max_end, a[0] + a[1])
			count = max_end - acc_addr

			try:
				rr = client.read_holding_registers(acc_addr, count=count)
				if rr is None or (hasattr(rr, 'isError') and rr.isError()):
					for c in group_cases:
						mismatches.append((c['name'], None, 'READ_ERROR'))
					continue
				regs = list(rr.registers)
			except Exception as e:
				for c in group_cases:
					mismatches.append((c['name'], None, f'EXC: {e}'))
				continue

			# 각 case 비교
			for c in group_cases:
				a = c['addr']
				# 변경한 항목이면 skip
				if except_addr_no is not None and a[0] == except_addr_no:
					continue
				offset = a[0] - acc_addr
				words_n = a[1]
				if offset + words_n > len(regs):
					mismatches.append((c['name'], None, 'SHORT_READ'))
					continue
				actual_words = regs[offset:offset + words_n]

				types = c.get('value_type') or ['uint16']
				t = (types[0] or 'uint16').lower()
				expected = c['target_value'][0]

				try:
					actual = self._decode_words(actual_words, t, client)
				except Exception as e:
					mismatches.append((c['name'], expected, f'DECODE_EXC: {e}'))
					continue

				total_checked += 1
				if t == 'float':
					if abs(float(actual) - float(expected)) > 1e-3:
						mismatches.append((c['name'], expected, actual))
				else:
					if int(actual) != int(expected):
						mismatches.append((c['name'], expected, actual))

		ok = (len(mismatches) == 0)
		if ok:
			print(f"[verify_xlsx] OK — {total_checked} cases 디폴트값 유지")
		else:
			print(f"[verify_xlsx] FAIL — {len(mismatches)} 항목 불일치 / "
			      f"{total_checked} 검사:")
			for name, exp, act in mismatches[:20]:
				print(f"   {name:<28} expected={exp!r:<10} actual={act!r}")
		return ok, mismatches

	@staticmethod
	def _decode_words(words, value_type, client):
		"""register words list → 원본 값. setup_runner._encode_value 의 역변환."""
		t = (value_type or 'uint16').lower()
		w = [int(x) & 0xFFFF for x in words]
		if t == 'uint16':
			return w[0]
		if t == 'int16':
			v = w[0]
			return v - 0x10000 if v >= 0x8000 else v
		if t == 'uint32':
			return (w[0] << 16) | w[1]
		if t == 'int32':
			v = (w[0] << 16) | w[1]
			return v - 0x100000000 if v >= 0x80000000 else v
		if t == 'uint64':
			return (w[0] << 48) | (w[1] << 32) | (w[2] << 16) | w[3]
		if t == 'int64':
			v = (w[0] << 48) | (w[1] << 32) | (w[2] << 16) | w[3]
			return v - 0x10000000000000000 if v >= 0x8000000000000000 else v
		if t == 'float':
			return client.convert_from_registers(
				w, client.DATATYPE.FLOAT32, word_order='big'
			)
		return w[0]

			# ### meter event setup ###
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_dip_setup_access.value, 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_3phase_dip_setup_access.value, 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_swell_setup_access.value, 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_semi_event_setup_access.value, 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_itic_event_setup_access.value, 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_iec_event_setup_access.value, 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_dip.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_dip_threshold.value[0], 900)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_dip_hysteresis.value[0], 20)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_3phase_dip.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_dip_setup_access.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_3phase_dip_setup_access.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_swell.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_swell_threshold.value[0], 1100)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_swell_hysteresis.value[0], 20)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_swell_setup_access.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_semi.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_semi_event_setup_access.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_itic.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_itic_event_setup_access.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_iec.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_iec_event_setup_access.value[0], 1)

			# ### meter network setup ###
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_dhcp_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_dhcp.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_dhcp_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_rs485_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_device_address.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_bit_rate.value[0], 3)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_parity.value[0], 2)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_stop_bit.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_rs485_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_modbus_timeout_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_modbus_timeout.value[0], 600)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_modbus_timeout_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_rstp_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_rstp.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_rstp_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_storm_control_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_storm_control.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_storm_control_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_rs485_map_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_rs485_map.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_rs485_map_setup_access.value[0], 1)

			# ### meter control setup ###
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_meter_test_mode.value[0], 0)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_meter_demo_mode_timeout_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_meter_demo_mode_timeout.value[0], 60)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_meter_demo_mode_timeout_setup_access.value[0], 1)

			# ### meter system setup / local time 제외 ###
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_description_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_installation_year.value[0], 1970)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_installation_month.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_installation_day.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_description_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_locale_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_timezone_offset.value[0], 540)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_temperature_unit.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_energy_unit.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_date_display_format.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_locale_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_summer_time_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_summer_time.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_start_month.value[0], 3)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_start_nth_weekday.value[0], 2)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_start_weekday.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_start_minute.value[0], 120)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_end_month.value[0], 11)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_end_nth_weekday.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_end_weekday.value[0], 0)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_end_minute.value[0], 120)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_summer_time_offset.value[0], 60)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_summer_time_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_ntp_setup_access.value)
			# # self.connect_manager.setup_client.write_register(ecm.addr_ntp_ip.value[0], 0A0A0A01) 값 변경 필요
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_sync_mode.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_sync_period.value[0], 600)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_sync_max_drift.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_ntp_setup_access.value[0], 1)
			# self.connect_manager.setup_client.read_holding_registers(*ConfigMap.addr_lcd_buzzer_setup_access.value)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_lcd_backlight_timeout.value[0], 300)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_lcd_backlight_low_level.value[0], 10)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_buzzer_for_button.value[0], 1)
			# self.connect_manager.setup_client.write_register(ConfigMap.addr_lcd_buzzer_setup_access.value[0], 1)
	
	def setup_target_initialize(self, access_addr, target_addr, bit16=None, bit32=None):
		self.touch_manager.uitest_mode_start()
		values = [2300, 0, 700, 1]
		values_control = [2300, 0, 1600, 1]

		def value_32bit(value):
			return (value >> 16) & 0xFFFF, value & 0xFFFF

		if self.connect_manager.setup_client:
			for value in values:
				self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_setup_lock.value[0], value)
				time.sleep(0.6)
			for value_control in values_control:
				self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_control_lock.value[0], value_control)
				time.sleep(0.6)
			
			### measurement setup ###
			address, words = target_addr.value
			if access_addr:
				self.connect_manager.setup_client.read_holding_registers(*access_addr.value)
			if words == 1:
				self.connect_manager.setup_client.write_register(target_addr.value[0], bit16)
			elif words == 2:
				self.connect_manager.setup_client.write_registers(target_addr.value[0], [*value_32bit(bit32)])
			else:
				print('words error?')
				return
			if access_addr:
				self.connect_manager.setup_client.write_register(access_addr.value[0], 1)
																									
	def system_time_read(self):
		# 디바이스의 시스템 시각을 datetime 으로 반환.
		# A7300/A3700N 모두 같은 멤버 이름(addr_system_time_*) 으로 ConfigMap
		# 에 등록되어 있어 product-aware 하게 주소만 다르게 read 한다.
		# setup_client 가 없으면 None.
		if self.connect_manager.setup_client is None:
			print("setup_client가 연결되어 있지 않습니다.")
			return

		from config.config_product import get_map_module
		product = self.connect_manager.PRODUCT or "A7300"
		if product == "A2700":
			# Accura 2700m Modbus Map:
			# doc 51121 System time, WCNT=4, UINT64.
			# Project config/workbooks use wire address = doc address - 1.
			response = self.connect_manager.setup_client.read_holding_registers(
				51120, count=4
			)
			if response is None or (hasattr(response, "isError") and response.isError()):
				print("Modbus error:", response)
				return
			regs = list(getattr(response, "registers", []) or [])
			if len(regs) < 4:
				print(f"[A2700] system time read short: {len(regs)} < 4")
				return
			sec_value = ((regs[0] & 0xFFFF) << 16) | (regs[1] & 0xFFFF)
			usec_value = ((regs[2] & 0xFFFF) << 16) | (regs[3] & 0xFFFF)
			dt_object = datetime.fromtimestamp(sec_value)
			print(
				f"[{product}] Unix Time: {sec_value}, "
				f"current time: {dt_object}.{usec_value:06d}"
			)
			return dt_object
		try:
			cfg_map = get_map_module(product).ConfigMap
			access_addr = cfg_map.addr_system_time_setup_access.value
			sec_addr = cfg_map.addr_system_time_sec.value
			usec_addr = cfg_map.addr_system_time_usec.value
		except Exception as e:
			print(f"[system_time_read] ConfigMap load failed ({product}): {e}")
			return

		self.connect_manager.setup_client.read_holding_registers(access_addr[0], count=access_addr[1])
		response = self.connect_manager.setup_client.read_holding_registers(sec_addr[0], count=sec_addr[1])
		if response.isError():
			print("Modbus error:", response)
			return

		regs = response.registers

		sec_value = self.connect_manager.setup_client.convert_from_registers(
			registers=regs,
			data_type=self.connect_manager.setup_client.DATATYPE.UINT32,
			word_order="big",
		)
		dt_object = datetime.fromtimestamp(sec_value)

		response = self.connect_manager.setup_client.read_holding_registers(usec_addr[0], count=usec_addr[1])
		if response.isError():
			print("Modbus error:", response)
			return dt_object

		regs = response.registers

		msec_value = self.connect_manager.setup_client.convert_from_registers(
			registers=regs,
			data_type=self.connect_manager.setup_client.DATATYPE.UINT32,
			word_order="big",
		)

		print(f"[{product}] Unix Time: {sec_value}, 현재 시간: {dt_object}.{msec_value:06d}")

		return dt_object

	def reset_max_min_only(self):
		"""제품 무관 Modbus reset 트리거. 시각 read 는 안 함 — 호출자가
		필요하면 system_time_read() 따로 호출.

		A7300/A3700N 모두 ConfigMap 의 addr_control_lock + addr_reset_max_min
		을 사용 (주소만 다름). setup_client 가 없으면 False 리턴.
		"""
		if self.connect_manager.setup_client is None:
			print("setup_client가 연결되어 있지 않습니다.")
			return False

		from config.config_product import get_map_module
		product = self.connect_manager.PRODUCT or "A7300"
		try:
			cfg_map = get_map_module(product).ConfigMap
			ctrl_addr = cfg_map.addr_control_lock.value
			reset_addr = cfg_map.addr_reset_max_min.value
		except Exception as e:
			print(f"[reset_max_min_only] ConfigMap load failed ({product}): {e}")
			return False

		client = self.connect_manager.setup_client
		values_control = [2300, 0, 1600, 1]
		try:
			for v in values_control:
				client.write_register(ctrl_addr[0], v)
				time.sleep(0.6)
			client.write_register(reset_addr[0], 1)
		except Exception as e:
			print(f"[{product}] reset_max_min_only failed: {e}")
			return False
		print(f"[{product}] Max/Min Reset (modbus)")
		return True

	def reset_max_min(self):
		if not self.uses_native_modbus_ui():
			print(f"[{self.connect_manager.PRODUCT}] reset_max_min: "
			      f"not applicable (bridge mode, no-op)")
			return datetime.now()
		self.touch_manager.uitest_mode_start()
		values_control = [2300, 0, 1600, 1]
		if self.connect_manager.setup_client:
			self.response = self.connect_manager.setup_client.read_holding_registers(3060, count=1)
			for value_control in values_control:
				self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_control_lock.value[0], value_control)
				time.sleep(0.6)
			self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_reset_max_min.value[0], 1)
			print("Max/Min Reset")
		else:
			print(self.response.isError())

		response = self.connect_manager.setup_client.read_holding_registers(3061, count=2)

		regs = response.registers

		unix_timestamp = self.connect_manager.setup_client.convert_from_registers(
			registers=regs,
			data_type=self.connect_manager.setup_client.DATATYPE.UINT32,  
			word_order="big",
		)

		utc_time = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
		kst_time = utc_time + timedelta(minutes=540)
		reset_time = kst_time
		print(kst_time)
		return reset_time
	
	def reset_demand(self):
		if not self.uses_native_modbus_ui():
			print(f"[{self.connect_manager.PRODUCT}] reset_demand: "
			      f"not applicable (bridge mode, no-op)")
			return
		self.touch_manager.uitest_mode_start()
		values_control = [2300, 0, 1600, 1]
		if self.connect_manager.setup_client:
			for value_control in values_control:
				self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_control_lock.value[0], value_control)
				time.sleep(0.6)
			self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_reset_demand.value[0], 1)
			print("Max/Min Reset")
		else:
			print(self.response.isError())
	
	def reset_demand_peak(self):
		if not self.uses_native_modbus_ui():
			print(f"[{self.connect_manager.PRODUCT}] reset_demand_peak: "
			      f"not applicable (bridge mode, no-op)")
			self.reset_time = datetime.now()
			return self.reset_time
		self.touch_manager.uitest_mode_start()
		values_control = [2300, 0, 1600, 1]
		if self.connect_manager.setup_client:
			for value_control in values_control:
				self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_control_lock.value[0], value_control)
				time.sleep(0.6)
			self.response = self.connect_manager.setup_client.write_register(ConfigMapA7300.addr_reset_demand_peak.value[0], 1)
			print("Max/Min Reset")
		else:
			print(self.response.isError())
		self.reset_time = datetime.now()
		return self.reset_time
