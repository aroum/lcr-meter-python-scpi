# LCR Meter Control Client (AKIP-6108 / BK Precision 880)

A Python client implementation using `pyserial` to interface with LCR meters. It allows query/command execution for setting testing frequency, voltage levels, measurement modes (L/C/R/Z/DCR), equivalent circuits (series/parallel), tolerance sorting bins, and recording max/min/average statistics.

## Hardware & Compatibility

- **USB-to-UART Chip**: CH340G
- **Presumed Compatible Models**:
  - АКИП-6108 / АКИП-6109
  - BK Precision 878B / 879B / 880
  - MECO LCR999A
  - TECPEL LCR-615
  - Keysight U1733C
  - Tonghui TH2822E

Refer to the included BK PRECISION 880.pdf manual starting from **page 47** for command protocols.

---

## Dependencies

- Python 3.6+
- [pySerial](https://pythonhosted.org/pyserial/)

Install the serial connection dependency:
```bash
pip install pyserial
```

---

## Usage

You can use `LCRClient` directly in your code or run the built-in demo.

### Example Code

```python
import time
from RLC import LCRClient

# Initialize client (specify the correct port for your system)
# Windows: e.g., "COM23"
# Linux: e.g., "/dev/ttyUSB0"
lcr = LCRClient(port="/dev/ttyUSB0", baudrate=9600)

try:
    lcr.connect()
    
    # 1. Device Info
    print(f"Device Identity: {lcr.get_idn()}")

    # 2. Configure Settings
    lcr.set_primary_parameter("C")       # Capacitance
    lcr.set_secondary_parameter("Q")     # Quality factor
    lcr.set_frequency("1kHz")            # 1 kHz test frequency
    lcr.set_equivalent_mode("PAL")       # Parallel circuit mode

    # 3. Read live measurements
    for i in range(5):
        val_main, val_sub, bin_no = lcr.fetch_data()
        print(f"Read #{i+1}: {val_main} | {val_sub} (Bin: {bin_no})")
        time.sleep(1.0)

except Exception as e:
    print(f"Error: {e}")
finally:
    lcr.go_to_local()                    # Reset local panel lockout
    lcr.disconnect()
```

### Running the Demo

To run the built-in demo script:
```bash
python RLC.py
```
*(Ensure the port specified in `if __name__ == "__main__":` block matches your connection).*
