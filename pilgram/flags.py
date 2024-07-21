from abc import ABC
from typing import Tuple, Type

import numpy as np


_NEXT_FLAG: np.uint32 = np.uint32(1)  # we can have a maximum of 32 flags


class Flag(ABC):
    FLAG: np.uint32

    def __init_subclass__(cls, **kwargs):
        global _NEXT_FLAG
        super().__init_subclass__()
        cls.FLAG = _NEXT_FLAG
        _NEXT_FLAG = np.left_shift(_NEXT_FLAG, 1)

    @classmethod
    def set(cls, target: np.uint32) -> np.uint32:
        """ returns the target flag container (a 64 bit int) with the current flag set """
        return np.bitwise_or(cls.FLAG, target)

    @classmethod
    def unset(cls, target: np.uint32) -> np.uint32:
        return np.bitwise_xor(cls.FLAG, target)

    @classmethod
    def is_set(cls, target: np.uint32) -> bool:
        return np.bitwise_and(cls.FLAG, target) == cls.FLAG

    @classmethod
    def get(cls) -> np.uint32:
        return cls.FLAG

    @classmethod
    def get_empty(cls) -> np.uint32:
        return np.uint32(0)


class HexedFlag(Flag):
    pass


class CursedFlag(Flag):
    pass


class AlloyGlitchFlag1(Flag):
    pass


class AlloyGlitchFlag2(Flag):
    pass


class AlloyGlitchFlag3(Flag):
    pass


class LuckFlag1(Flag):
    pass


class LuckFlag2(Flag):
    pass


class StrengthBuff(Flag):
    """ buff all normal damage (slash, pierce & blunt) """
    pass


class OccultBuff(Flag):
    pass


class FireBuff(Flag):
    pass


class IceBuff(Flag):
    pass


class AcidBuff(Flag):
    pass


class ElectricBuff(Flag):
    pass


BUFF_FLAGS: Tuple[Type[Flag], ...] = (StrengthBuff, OccultBuff, FireBuff, IceBuff, AcidBuff, ElectricBuff)
