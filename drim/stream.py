import hmac
import hashlib


class PrfStream:
    def __init__(self, key, tag, nonce):
        self._key = key
        self._tag = tag
        self._nonce = nonce
        self._blocks = bytearray()
        self._ctr = 0
        self._pos = 0
        self._extend()

    def _extend(self):
        digest = hmac.new(
            self._key,
            self._tag + b"\x00" + self._nonce + self._ctr.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        self._blocks.extend(digest)
        self._ctr += 1

    def _bit(self, pos):
        while (pos >> 3) >= len(self._blocks):
            self._extend()
        byte = self._blocks[pos >> 3]
        return (byte >> (7 - (pos & 7))) & 1

    def next_index(self, n):
        k = (n - 1).bit_length()
        limit = (1 << k) - ((1 << k) % n)
        bits = 0
        while True:
            r = 0
            for _ in range(k):
                r = (r << 1) | self._bit(self._pos + bits)
                bits += 1
            if r < limit:
                self._pos += bits
                return r % n
