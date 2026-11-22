"""Tiny DBC subset reader for unsigned little-endian signals; offline research only.

Reference DBC fields are sourced from OpenDBC vw_mqbevo.dbc, but the complete
vehicle compatibility, CRC/counter logic, and network topology are UNKNOWN.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re

MESS_RE = re.compile(r'^BO_\s+(\d+)\s+(\w+):\s+(\d+)\s+(\w+)')
SIGN_RE = re.compile(r'^\s*SG_\s+(\w+)\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*\(([-\d.]+),([-\d.]+)\)')

@dataclass(frozen=True)
class Signal:
    name: str
    start: int
    length: int
    byte_order: str
    unsigned: bool
    factor: float
    offset: float

@dataclass(frozen=True)
class Message:
    name: str
    can_id: int
    size: int
    ecu: str
    signals: dict[str, Signal]


def load_dbc(path: Path) -> dict[str, Message]:
    result = {}
    current = None
    for line in path.read_text(encoding='utf-8').splitlines():
        if m := MESS_RE.match(line):
            can_id, name, size, ecu = m.groups()
            current = Message(name, int(can_id), int(size), ecu, {})
            result[name] = current
        elif current and (s := SIGN_RE.match(line)):
            name, start, length, order, sign, factor, offset = s.groups()
            if order != '1' or sign != '+':
                raise ValueError('Subset supports only unsigned Intel signals')
            current.signals[name] = Signal(name, int(start), int(length), 'little', True, float(factor), float(offset))
    if not result:
        raise ValueError('DBC does not contain BO_ messages')
    return result


def encode(msg: Message, physical: dict[str, float]) -> bytes:
    """No OEM CRC. Never transmit these frames to vehicle hardware."""
    bits = 0
    for name, value in physical.items():
        s = msg.signals[name]
        raw = round((float(value) - s.offset) / s.factor)
        if raw < 0 or raw >= (1 << s.length):
            raise ValueError(f'{name} out of bit range')
        mask = ((1 << s.length) - 1) << s.start
        bits = (bits & ~mask) | (raw << s.start)
    return bits.to_bytes(msg.size, 'little')


def decode(msg: Message, payload: bytes) -> dict[str, float]:
    if len(payload) != msg.size:
        raise ValueError('DLC mismatch')
    value = int.from_bytes(payload, 'little')
    result = {}
    for name,s in msg.signals.items():
        raw = (value >> s.start) & ((1 << s.length) - 1)
        result[name] = round(raw * s.factor + s.offset, 5)
    return result
