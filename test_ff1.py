import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drim.ff1 import FF1

K128 = bytes.fromhex("2B7E151628AED2A6ABF7158809CF4F3C")
K192 = K128 + bytes.fromhex("EF4359D8D580AA4F")
K256 = K128 + bytes.fromhex("EF4359D8D580AA4F7F036D6F04FC6A94")

VECTORS = [
    ("S1 AES-128 r10 emptyT", K128, 10, "", "0123456789", "2433477484"),
    ("S2 AES-128 r10 T10", K128, 10, "39383736353433323130", "0123456789", "6124200773"),
    ("S3 AES-128 r36 T11", K128, 36, "3737373770717273373737", "0123456789abcdefghi", "a9tv40mll9kdu509eum"),
    ("S4 AES-192 r10 emptyT", K192, 10, "", "0123456789", "2830668132"),
    ("S5 AES-192 r10 T10", K192, 10, "39383736353433323130", "0123456789", "2496655549"),
    ("S6 AES-192 r36 T11", K192, 36, "3737373770717273373737", "0123456789abcdefghi", "xbj3kv35jrawxv32ysr"),
    ("S7 AES-256 r10 emptyT", K256, 10, "", "0123456789", "6657667009"),
    ("S8 AES-256 r10 T10", K256, 10, "39383736353433323130", "0123456789", "1001623463"),
]

failures = []


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


for name, key, radix, twhex, pt, ct in VECTORS:
    f = FF1(key, radix)
    got = f.encrypt(pt, bytes.fromhex(twhex))
    back = f.decrypt(ct, bytes.fromhex(twhex))
    check(f"{name}: enc={got} dec={back}", got == ct and back == pt)

f = FF1(K128, 10)
T = bytes.fromhex("39383736353433323130")
seen = set()
for x in range(10000, 100000):
    y = f.encrypt(str(x), T)
    seen.add(y)
check("bijection over 90000 inputs", len(seen) == 90000)

roundtrip = all(
    f.decrypt(f.encrypt(str(x), T), T) == str(x)
    for x in range(1000, 1200)
)
check("roundtrip on 200 values", roundtrip)

check("minlen radix10 is 2", FF1(K128, 10).minlen == 2)
check("minlen radix36 is 2", FF1(K128, 36).minlen == 2)

try:
    FF1(K128, 10).encrypt("1", T)
    check("rejects below-minlen input", False)
except ValueError:
    check("rejects below-minlen input", True)

try:
    FF1(bytes(15), 10)
    check("rejects bad key length", False)
except ValueError:
    check("rejects bad key length", True)

try:
    FF1(K128, 37)
    check("rejects radix > 36", False)
except ValueError:
    check("rejects radix > 36", True)

print()
if failures:
    print(f"SOME TESTS FAILED ({len(failures)})")
    sys.exit(1)
print("ALL OK")
