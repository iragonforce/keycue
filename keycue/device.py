"""Linux hidraw discovery and HID feature-report transport; no dependencies."""
from __future__ import annotations
import fcntl
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
from .protocol import FEATURE_DATA_SIZE, FEATURE_REPORT_SIZE, Transfer

HID_ID_LINE = 'HID_ID=0003:000005AC:0000024F'


def _hid_ioctl(direction: int, number: int, length: int) -> int:
    # Linux _IOC(direction, 'H', number, length)
    return (direction << 30) | (length << 16) | (ord('H') << 8) | number

HIDIOCSFEATURE = _hid_ioctl(3, 0x06, FEATURE_REPORT_SIZE)
HIDIOCGFEATURE = _hid_ioctl(3, 0x07, FEATURE_REPORT_SIZE)

@dataclass(frozen=True)
class Candidate:
    device: Path
    physical_path: str
    readable: bool
    writable: bool


def discover(root: Path = Path('/sys/class/hidraw'), dev_root: Path = Path('/dev')) -> list[Candidate]:
    """Find Keychron 05ac:024f USB interface 0 by HID_PHYS (not device numbering)."""
    found = []
    if not root.is_dir():
        return found
    for entry in sorted(root.glob('hidraw*')):
        uevent = entry / 'device' / 'uevent'
        try:
            lines = uevent.read_text().splitlines()
        except OSError:
            continue
        if HID_ID_LINE not in lines:
            continue
        physical_path = next((line.removeprefix('HID_PHYS=') for line in lines if line.startswith('HID_PHYS=')), '')
        if not physical_path.startswith('usb-') or not physical_path.endswith('/input0'):
            continue
        device = dev_root / entry.name
        found.append(Candidate(device, physical_path, os.access(device, os.R_OK), os.access(device, os.W_OK)))
    return found


def choose_device(devices: Sequence[Candidate]) -> Path:
    if len(devices) != 1:
        raise RuntimeError(
            f'Expected exactly one Keychron K2 (05ac:024f, USB input0), found {len(devices)}. '
            'Inspect `keycue identify` and unplug other matching keyboards.'
        )
    return devices[0].device


def execute(device: Path, actions: Sequence[Transfer], pacing_s: float = 0.001) -> tuple[int, float]:
    """Perform a single transaction: no polling, retries, or background writes."""
    start = time.perf_counter()
    writes = 0
    fd = os.open(device, os.O_RDWR | os.O_CLOEXEC)
    try:
        for item in actions:
            if item.operation == 'write':
                if len(item.data) != FEATURE_DATA_SIZE:
                    raise ValueError('Expected exactly 64 feature data bytes')
                report = bytearray(b'\x00' + item.data)
                fcntl.ioctl(fd, HIDIOCSFEATURE, report, True)
                writes += 1
            elif item.operation == 'read':
                report = bytearray(FEATURE_REPORT_SIZE)
                fcntl.ioctl(fd, HIDIOCGFEATURE, report, True)
            else:
                raise ValueError(f'Unknown transfer operation {item.operation!r}')
            time.sleep(pacing_s)
    finally:
        os.close(fd)
    return writes, (time.perf_counter() - start) * 1000
