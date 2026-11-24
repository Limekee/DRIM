import hmac
import hashlib
import unicodedata

from .ff1 import FF1
from .stream import PrfStream
from .rules import build_rules

SUPPORTED_TYPES = ("email", "fio", "login", "phone", "int_id", "date")


class DRIM:
    def __init__(self, key):
        if len(key) != 32:
            raise ValueError("DRIM key must be 256 bits (32 bytes)")
        self.key = key
        self._ff1 = FF1(key, 10)
        self._tweaks = {
            "phone": hmac.new(key, b"tweak|phone", hashlib.sha256).digest()[:16],
            "int_id": hmac.new(key, b"tweak|int_id", hashlib.sha256).digest()[:16],
        }
        self._rules = build_rules(self._ff1, self._tweaks)

    def mask(self, value, vtype):
        if vtype not in self._rules:
            raise ValueError(f"unsupported type: {vtype}")
        if value is None:
            return None
        text = unicodedata.normalize("NFC", str(value))
        rule = self._rules[vtype]
        text = rule.canonical(text)
        if text == "":
            return ""
        h0 = hmac.new(
            self.key,
            rule.tag + b"|" + text.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        prf = PrfStream(self.key, rule.tag, h0)
        return rule.mask(text, prf)

    def mask_row(self, row, types):
        return {k: self.mask(v, types[k]) for k, v in row.items()}
