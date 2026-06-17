import time
import serial
from typing import Union, Tuple, Optional

class LCRClient:
    def __init__(self, port: str = "COM23", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        # According to the manual, valid terminators are \n, \r or \r\n
        self.terminator = "\n"

    def connect(self) -> None:
        """Open the port for communication with the LCR meter."""
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
            timeout=1.0
        )
        time.sleep(0.5)
        print(f"[*] Connected to {self.port} ({self.baudrate} baud).")

    def disconnect(self) -> None:
        """Close the connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[*] Connection closed.")

    def _execute(self, cmd: str, is_query: bool = False) -> str:
        """Internal method to send a command / query."""
        if not self.ser or not self.ser.is_open:
            raise ConnectionError("Port is not open. Call connect() first.")
        
        self.ser.reset_input_buffer()
        full_cmd = f"{cmd}{self.terminator}"
        self.ser.write(full_cmd.encode('ascii'))
        self.ser.flush()

        if is_query:
            resp = self.ser.readline()
            return resp.decode('ascii', errors='ignore').strip()
        return ""

    @staticmethod
    def _parse_nr3(value_str: str) -> Union[float, str]:
        """Parser for exponential data format (NR3).
        Converts '+1.2345E-03' to float, and leaves '----' as 'OL/Unset'.
        """
        v_clean = value_str.strip()
        if not v_clean or "---" in v_clean:
            return "OL/Unset"
        try:
            return float(v_clean)
        except ValueError:
            return v_clean

    # =========================================================================
    # GENERAL SYSTEM COMMANDS (IEEE 488)
    # =========================================================================

    def get_idn(self) -> str:
        """*IDN? - Query device identification.
        Returns: <manufacturer>, <model>, <serial number>, <firmware version>
        """
        return self._execute("*IDN?", is_query=True)

    def local_lockout(self) -> None:
        """*LLO - Local Lockout.
        Disables all physical buttons on the front panel, including the RMT button.
        (The POWER button remains active).
        """
        self._execute("*LLO", is_query=False)

    def go_to_local(self) -> None:
        """*GTL - Go to Local.
        Clears the keyboard lockout caused by the *LLO command.
        """
        self._execute("*GTL", is_query=False)

    # =========================================================================
    # FREQUENCY AND VOLTAGE SUBSYSTEM (FREQuency / VOLTage)
    # =========================================================================

    def set_frequency(self, freq: Union[int, str]) -> None:
        """FREQuency <value> - Set test frequency.
        Valid parameters: 100, 120, 1000, 10000, 100000 (or with Hz/kHz postfix)
        Example: client.set_frequency("1kHz") or client.set_frequency(100)
        """
        # Remove any spaces for syntax safety
        clean_freq = str(freq).replace(" ", "")
        self._execute(f"FREQuency {clean_freq}", is_query=False)

    def get_frequency(self) -> str:
        """FREQuency? - Query the current test frequency."""
        return self._execute("FREQuency?", is_query=True)

    def set_voltage_level(self, level: float) -> None:
        """VOLTage <value> - Set AC test signal amplitude.
        Valid parameters: 0.3, 0.6, 1.0
        """
        self._execute(f"VOLTage {level}", is_query=False)

    def get_voltage_level(self) -> str:
        """VOLTage? - Query the current test voltage level."""
        return self._execute("VOLTage?", is_query=True)

    # =========================================================================
    # MEASUREMENT FUNCTION SUBSYSTEM (FUNCtion)
    # =========================================================================

    def set_primary_parameter(self, param: str) -> None:
        """FUNCtion:impa <L|C|R|Z|DCR> - Select the primary measurement parameter.
        L - inductance, C - capacitance, R - resistance, Z - impedance, DCR - direct current resistance.
        """
        self._execute(f"FUNCtion:impa {param.upper()}", is_query=False)

    def get_primary_parameter(self) -> str:
        """FUNCtion:impa? - Query the current primary parameter."""
        return self._execute("FUNCtion:impa?", is_query=True)

    def set_secondary_parameter(self, param: str) -> None:
        """FUNCtion:impb <D|Q|THETA|ESR> - Select the secondary parameter.
        D - dissipation factor, Q - quality factor, THETA - phase angle, ESR - equivalent series resistance.
        (Has no effect in DCR mode).
        """
        self._execute(f"FUNCtion:impb {param.upper()}", is_query=False)

    def get_secondary_parameter(self) -> str:
        """FUNCtion:impb? - Query the current secondary parameter."""
        return self._execute("FUNCtion:impb?", is_query=True)

    def set_equivalent_mode(self, mode: str) -> None:
        """FUNCtion:EQUivalent <SERies|PAL> - Set measurement equivalent circuit mode.
        SERies - series, PAL (or PARallel) - parallel.
        """
        # Manual accepts SERies, parallel or PAL
        m = "SERies" if mode.upper().startswith("SER") else "PAL"
        self._execute(f"FUNCtion:EQUivalent {m}", is_query=False)

    def get_equivalent_mode(self) -> str:
        """FUNCtion:EQUivalent? - Query current equivalent circuit mode (Returns SER or PAL)."""
        return self._execute("FUNCtion:EQUivalent?", is_query=True)

    # =========================================================================
    # SORTING AND TOLERANCE SUBSYSTEM (CALCulate:TOLerance)
    # =========================================================================

    def set_tolerance_state(self, enabled: bool) -> None:
        """CALCulate:TOLerance:STATE <ON|OFF> - Enable/disable tolerance sorting mode."""
        state = "ON" if enabled else "OFF"
        self._execute(f"CALCulate:TOLerance:STATE {state}", is_query=False)

    def get_tolerance_state(self) -> str:
        """CALCulate:TOLerance:STATE? - Query the state of tolerance sorting mode."""
        return self._execute("CALCulate:TOLerance:STATE?", is_query=True)

    def get_tolerance_nominal(self) -> Union[float, str]:
        """CALCulate:TOLerance:NOMinal? - Query the stored nominal (reference) value."""
        resp = self._execute("CALCulate:TOLerance:NOMinal?", is_query=True)
        return self._parse_nr3(resp)

    def get_tolerance_percent_value(self) -> Union[float, str]:
        """CALCulate:TOLerance:VALUE? - Query the current deviation from nominal in percent."""
        resp = self._execute("CALCulate:TOLerance:VALUE?", is_query=True)
        return self._parse_nr3(resp)

    def set_tolerance_range(self, percent: int) -> None:
        """CALCulate:TOLerance:RANGE <1|5|10|20> - Set tolerance range in %."""
        if percent in [1, 5, 10, 20]:
            self._execute(f"CALCulate:TOLerance:RANGE {percent}", is_query=False)

    def get_tolerance_range(self) -> str:
        """CALCulate:TOLerance:RANGE? - Query the current sorting bin.
        Returns: BIN1 (for 1%), BIN2 (5%), BIN3 (10%), BIN4 (20%) or '----' if not set.
        """
        return self._execute("CALCulate:TOLerance:RANGE?", is_query=True)

    # =========================================================================
    # STATIC RECORDING SUBSYSTEM (CALCulate:RECording)
    # =========================================================================

    def set_recording_state(self, enabled: bool) -> None:
        """CALCulate:RECording:STATE <ON|OFF> - Enable/disable dynamic MAX/MIN/AVG recording."""
        state = "ON" if enabled else "OFF"
        self._execute(f"CALCulate:RECording:STATE {state}", is_query=False)

    def get_recording_state(self) -> str:
        """CALCulate:RECording:STATe? - Query the recording mode status."""
        return self._execute("CALCulate:RECording:STATe?", is_query=True)

    def _parse_rec_pair(self, resp_str: str) -> Tuple[Union[float, str], Union[float, str]]:
        """Helper parser for recording responses that return two comma-separated values."""
        if "," in resp_str:
            parts = resp_str.split(",")
            return self._parse_nr3(parts[0]), self._parse_nr3(parts[1])
        return self._parse_nr3(resp_str), "OL/Unset"

    def get_recording_max(self) -> Tuple[Union[float, str], Union[float, str]]:
        """CALCulate:RECording:MAXimum? - Query the maximum recorded values.
        Returns tuple: (Primary_parameter, Secondary_parameter)
        """
        resp = self._execute("CALCulate:RECording:MAXimum?", is_query=True)
        return self._parse_rec_pair(resp)

    def get_recording_min(self) -> Tuple[Union[float, str], Union[float, str]]:
        """CALCulate:RECording:MINimum? - Query the minimum recorded values."""
        resp = self._execute("CALCulate:RECording:MINimum?", is_query=True)
        return self._parse_rec_pair(resp)

    def get_recording_average(self) -> Tuple[Union[float, str], Union[float, str]]:
        """CALCulate:RECording:AVERage? - Query the calculated average values."""
        resp = self._execute("CALCulate:RECording:AVERage?", is_query=True)
        return self._parse_rec_pair(resp)

    def get_recording_present(self) -> Tuple[Union[float, str], Union[float, str]]:
        """CALCulate:RECording:PRESent? - Query the current instantaneous value within recording mode."""
        resp = self._execute("CALCulate:RECording:PRESent?", is_query=True)
        return self._parse_rec_pair(resp)

    # =========================================================================
    # MAIN DATA QUERY (FETCH)
    # =========================================================================

    def fetch_data(self) -> Tuple[Union[float, str], Union[float, str], Optional[int]]:
        """FETCH? - Read current measurements from the device buffer.
        Parses the response and converts exponential strings to normal Python types.
        
        Returns a tuple of 3 elements:
        (Primary_value, Secondary_value, Tolerance_bin_number)
        
        If the device is in DCR mode, the secondary value returns the bin number, and the third element is None.
        """
        resp = self._execute("FETCH?", is_query=True)
        if not resp:
            return "No Data", "No Data", None

        # Response is usually comma-separated: <Primary, Secondary, Bin_No>
        parts = resp.split(",")
        
        if len(parts) == 3:
            val_main = self._parse_nr3(parts[0])
            val_sub = self._parse_nr3(parts[1])
            try:
                bin_no = int(parts[2].strip())
            except ValueError:
                bin_no = parts[2].strip()
            return val_main, val_sub, bin_no
            
        elif len(parts) == 2:
            # DCR mode specific: <Primary, Bin_No>
            val_main = self._parse_nr3(parts[0])
            try:
                bin_no = int(parts[1].strip())
            except ValueError:
                bin_no = parts[1].strip()
            return val_main, "N/A (DCR)", bin_no

        return resp, "Raw Format Error", None


# =========================================================================
# DEMO CLIENT RUN
# =========================================================================
if __name__ == "__main__":
    # Configure for your system (Fedora Linux: "/dev/ttyUSB0", Windows: "COM3")
    lcr = LCRClient(port="COM23", baudrate=9600)
    
    try:
        lcr.connect()
        
        # 1. Device Identification
        print(f"\n[+] Device Info: {lcr.get_idn()}")
        
        # 2. Basic Mode Configuration
        print("[*] Configuring device for capacitance (C), quality factor (Q) measurements at 1kHz...")
        # lcr.set_primary_parameter("C")
        # lcr.set_secondary_parameter("Q")
        # lcr.set_frequency("100")
        # lcr.set_voltage_level(0.6)
        # lcr.set_equivalent_mode("PAL") # Capacitance is measured in parallel by default
        
        # Read the configuration back to verify synchronization
        print(f"    Settings check: Param={lcr.get_primary_parameter()} | Sec={lcr.get_secondary_parameter()} | Freq={lcr.get_frequency()} | Circuit={lcr.get_equivalent_mode()}")

        # 3. Demonstrate FETCH? parsing
        print("\n=== Real-time readings (5 iterations) ===")
        for i in range(5):
            main_val, sub_val, bin_num = lcr.fetch_data()
            
            print(f"Measurement #{i+1}:")
            # If it is a float, we can print it nicely or use it in math
            if isinstance(main_val, float):
                print(f"  Primary display: {main_val:.6e} (Value as float: {main_val})")
            else:
                print(f"  Primary display: {main_val}") # Will print 'OL/Unset' if no component is present
                
            print(f"  Secondary display: {sub_val}")
            print(f"  Tolerance bin (Bin No): {bin_num}")
            time.sleep(0.5)

    except Exception as e:
        print(f"[!] An error occurred: {e}")
    finally:
        lcr.go_to_local()
        lcr.disconnect()
