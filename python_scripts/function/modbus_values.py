# -*- coding: utf-8 -*-
"""Modbus register value 인코딩/디코딩 공용 헬퍼.

setup_runner / clipping_runner 에 동일한 로직이 각각 복사돼 있던 것을 추출.

주의: source_runner._encode_value / demo_runner._decode_register_value 는
에러 처리 의미가 다르다 (미지원 타입에서 raise, 64비트 미지원 등).
의도 확인 전까지 그쪽은 각자 유지 — 여기로 통합하려면 semantics 결정 필요.
"""

from __future__ import annotations


def encode_value(value, value_type, client) -> list:
    """value 를 register word 리스트로 인코딩.

    지원 타입: uint16/int16/uint32/int32/uint64/int64/float.
    미지원 타입은 uint16 으로 취급 (기존 setup/clipping runner 동작 유지).
    float 은 client 의 convert_to_registers (FLOAT32, big word order) 사용.
    """
    t = (value_type or "uint16").lower()
    if t == "uint16":
        return [int(value) & 0xFFFF]
    if t == "int16":
        v = int(value)
        if v < 0:
            v = (v + 0x10000) & 0xFFFF
        return [v]
    if t == "uint32":
        v = int(value) & 0xFFFFFFFF
        return [(v >> 16) & 0xFFFF, v & 0xFFFF]
    if t == "int32":
        v = int(value)
        if v < 0:
            v = (v + 0x100000000) & 0xFFFFFFFF
        return [(v >> 16) & 0xFFFF, v & 0xFFFF]
    if t == "uint64":
        v = int(value) & 0xFFFFFFFFFFFFFFFF
        return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF,
                (v >> 16) & 0xFFFF, v & 0xFFFF]
    if t == "int64":
        v = int(value)
        if v < 0:
            v = (v + 0x10000000000000000) & 0xFFFFFFFFFFFFFFFF
        return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF,
                (v >> 16) & 0xFFFF, v & 0xFFFF]
    if t == "float":
        return list(client.convert_to_registers(
            float(value), client.DATATYPE.FLOAT32, word_order="big"
        ))
    return [int(value) & 0xFFFF]


def decode_registers(regs, value_type, client):
    """register word 리스트를 값으로 디코딩.

    regs 가 비어있으면 None (clipping runner 의 기존 가드 동작).
    지원 타입 외에는 첫 word 반환 (기존 동작 유지).
    """
    t = (value_type or "uint16").lower()
    if not regs:
        return None
    if t == "uint16":
        return regs[0]
    if t == "int16":
        v = regs[0]
        return v - 0x10000 if v & 0x8000 else v
    if t == "uint32":
        return (regs[0] << 16) | regs[1] if len(regs) >= 2 else regs[0]
    if t == "int32":
        v = (regs[0] << 16) | regs[1] if len(regs) >= 2 else regs[0]
        return v - 0x100000000 if v & 0x80000000 else v
    if t == "uint64":
        if len(regs) < 4:
            return regs[0]
        return ((regs[0] & 0xFFFF) << 48) | ((regs[1] & 0xFFFF) << 32) \
            | ((regs[2] & 0xFFFF) << 16) | (regs[3] & 0xFFFF)
    if t == "int64":
        if len(regs) < 4:
            return regs[0]
        v = ((regs[0] & 0xFFFF) << 48) | ((regs[1] & 0xFFFF) << 32) \
            | ((regs[2] & 0xFFFF) << 16) | (regs[3] & 0xFFFF)
        return v - 0x10000000000000000 if v & 0x8000000000000000 else v
    if t == "float":
        return client.convert_from_registers(
            regs, client.DATATYPE.FLOAT32, word_order="big"
        )
    return regs[0]
