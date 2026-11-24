import datetime as dt
import math
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drim import DRIM
from drim.pools import (
    SURNAMES, MALE_NAMES, FEMALE_NAMES, PATRONYMICS_M, PATRONYMICS_F,
    EMAIL_DOMAINS,
)

KEY = bytes(range(32))
rng = random.Random(42)
failures = []


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


m = DRIM(KEY)
m2 = DRIM(bytes(range(1, 33)))

check("pools have no duplicates",
      len(SURNAMES) == len(set(SURNAMES)) and
      len(MALE_NAMES) == len(set(MALE_NAMES)) and
      len(FEMALE_NAMES) == len(set(FEMALE_NAMES)) and
      len(PATRONYMICS_M) == len(set(PATRONYMICS_M)) and
      len(PATRONYMICS_F) == len(set(PATRONYMICS_F)))

emails = [f"user{i}@yandex.ru" for i in range(500)]
masked = [m.mask(e, "email") for e in emails]
check("determinism (500 e-mails)", all(m.mask(e, "email") == m.mask(e, "email") for e in emails))
check("e-mail domain pool + @", all(
    "@" in x and x.split("@")[1] in EMAIL_DOMAINS and x.split("@")[0][0].isalpha()
    for x in masked
))

phones = [f"+7 9{rng.randint(10, 99)} {rng.randint(100, 999)}-{rng.randint(10, 99)}-{rng.randint(10, 99)}" for _ in range(300)]
check("phone format +7 (XXX) XXX-XX-XX", all(
    (lambda p: p.startswith("+7 (") and p[7] == ")" and len(p) == 18 and
     sum(c.isdigit() for c in p) == 11)(m.mask(ph, "phone"))
    for ph in phones
))

ids = [str(rng.randint(1, 10 ** 9)) for _ in range(300)]
check("int_id keeps digit length", all(
    m.mask(i, "int_id").isdigit() and len(m.mask(i, "int_id")) == len(i) for i in ids
))

dates = [f"2024-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}" for _ in range(200)]
check("date stays ISO, same year", all(
    dt.date.fromisoformat(m.mask(s, "date")).year == dt.date.fromisoformat(s).year
    for s in dates
))

fios = [f"{SURNAMES[rng.randrange(len(SURNAMES))]} {FEMALE_NAMES[rng.randrange(len(FEMALE_NAMES))]} {PATRONYMICS_F[rng.randrange(len(PATRONYMICS_F))]}" for _ in range(200)]
check("fio -> 3 components", all(len(m.mask(f, "fio").split()) == 3 for f in fios))

check("female fio keeps female patronymic", all(
    m.mask(f, "fio").split()[2].endswith("на") and not m.mask(f, "fio").split()[2].endswith("ична")
    for f in fios
))

mfios = [f"{SURNAMES[rng.randrange(len(SURNAMES))]} {MALE_NAMES[rng.randrange(len(MALE_NAMES))]} {PATRONYMICS_M[rng.randrange(len(PATRONYMICS_M))]}" for _ in range(200)]
check("male fio keeps male patronymic", all(
    m.mask(f, "fio").split()[2].endswith("ич")
    for f in mfios
))

check("NULL -> None", m.mask(None, "email") is None)
check("empty -> empty string", m.mask("", "email") == "")
check("spaces -> empty string", m.mask("   ", "email") == "")

check("cross-table e-mail consistency (case/space)",
      m.mask("Ivan.Petrov@YANDEX.RU ", "email") == m.mask("ivan.petrov@yandex.ru", "email"))
check("cross-table int_id consistency", m.mask("12345", "int_id") == m.mask(" 12345 ", "int_id"))

big = [str(i) for i in range(1, 50001)]
mapped = [m.mask(x, "int_id") for x in big]
check("int_id injectivity on 50k values", len(set(mapped)) == len(set(big)))

n = 10000
fio_in = [
    f"{SURNAMES[i % len(SURNAMES)]} "
    f"{MALE_NAMES[(i // len(SURNAMES)) % len(MALE_NAMES)]} "
    f"{PATRONYMICS_M[i // (len(SURNAMES) * len(MALE_NAMES))]}"
    for i in range(n)
]
fio_out = [m.mask(f, "fio") for f in fio_in]
pool = len(SURNAMES) * len(MALE_NAMES) * len(PATRONYMICS_M)
expected_distinct = pool * (1 - math.exp(-n / pool))
print(f"INFO fio distinct outputs {len(set(fio_out))}/{n} "
      f"(expected {expected_distinct:.0f} for pool {pool})")
check("fio collisions within 5% of birthday estimate",
      abs(len(set(fio_out)) - expected_distinct) <= 0.05 * expected_distinct)

from drim.stream import PrfStream

counts = [0] * 10
for _ in range(10000):
    prf = PrfStream(KEY, b"test", os.urandom(32))
    counts[prf.next_index(10)] += 1
chi2 = sum((c - 1000) ** 2 / 1000 for c in counts)
print(f"INFO rj_index chi2 = {chi2:.1f} (df=9, crit 16.92)")
check("next_index uniformity chi2 < 16.92", chi2 < 16.92)

check("different key -> different mask", m.mask("a@b.ru", "email") != m2.mask("a@b.ru", "email"))
check("malformed email fallback", "@" in m.mask("no-at-sign", "email"))

login = m.mask("Иванов Пётр Сергеевич", "login")
check("login is latin with dot", login[0].isascii() and "." in login)

print()
if failures:
    print(f"SOME TESTS FAILED ({len(failures)})")
    sys.exit(1)
print("ALL OK")
