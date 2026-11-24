import math
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
MAX_RADIX = len(ALPHABET)
MIN_DOMAIN = 100


class FF1:
    def __init__(self, key, radix):
        if radix < 2 or radix > MAX_RADIX:
            raise ValueError("radix must be in [2..36]")
        if len(key) not in (16, 24, 32):
            raise ValueError("AES key must be 128/192/256 bits")
        self.radix = radix
        self.alphabet = ALPHABET[:radix]
        self._char2num = {c: i for i, c in enumerate(self.alphabet)}
        self.minlen = 1
        while radix ** self.minlen < MIN_DOMAIN:
            self.minlen += 1
        self.maxlen = 2 ** 32 - 1
        self._cipher = Cipher(algorithms.AES(key), modes.ECB())

    def _num(self, x):
        acc = 0
        r = self.radix
        for ch in x:
            acc = acc * r + self._char2num[ch]
        return acc

    def _str(self, x, m):
        r = self.radix
        out = [""] * m
        for k in range(m):
            out[m - 1 - k] = self.alphabet[x % r]
            x //= r
        return "".join(out)

    def _rounds(self, X, T, encrypt):
        enc = self._cipher.encryptor()

        def ciph(block):
            return enc.update(block)

        def prf(data):
            y = b"\x00" * 16
            for j in range(0, len(data), 16):
                y = ciph(bytes(a ^ b for a, b in zip(y, data[j:j + 16])))
            return y

        n = len(X)
        t = len(T)
        u = n // 2
        v = n - u
        b = math.ceil(v * math.log2(self.radix) / 8)
        d = 4 * math.ceil(b / 4) + 4
        P = (bytes([1, 2, 1]) + self.radix.to_bytes(3, "big") + bytes([10, u % 256])
             + n.to_bytes(4, "big") + t.to_bytes(4, "big"))
        pad = (-t - b - 1) % 16
        A = X[:u]
        B = X[u:]
        idx = range(10) if encrypt else range(9, -1, -1)
        for i in idx:
            src = B if encrypt else A
            Q = T + b"\x00" * pad + bytes([i]) + self._num(src).to_bytes(b, "big")
            R = prf(P + Q)
            blocks = [R] + [ciph(bytes(a ^ c for a, c in zip(R, j.to_bytes(16, "big"))))
                             for j in range(1, math.ceil(d / 16))]
            S = b"".join(blocks)[:d]
            y = int.from_bytes(S, "big")
            m = u if i % 2 == 0 else v
            if encrypt:
                c = (self._num(A) + y) % (self.radix ** m)
            else:
                c = (self._num(B) - y) % (self.radix ** m)
            C = self._str(c, m)
            if encrypt:
                A, B = B, C
            else:
                B, A = A, C
        return A + B

    def encrypt(self, X, T=b""):
        self._validate(X)
        return self._rounds(X, T, True)

    def decrypt(self, X, T=b""):
        self._validate(X)
        return self._rounds(X, T, False)

    def _validate(self, X):
        n = len(X)
        if not (self.minlen <= n <= self.maxlen):
            raise ValueError(f"length {n} outside [{self.minlen}, {self.maxlen}]")
        if any(ch not in self._char2num for ch in X):
            raise ValueError("character outside alphabet")
