import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drim import DRIM
from drim.pools import (
    SURNAMES, MALE_NAMES, FEMALE_NAMES, PATRONYMICS_M, PATRONYMICS_F,
    EMAIL_DOMAINS,
)

KEY = hashlib.sha256(b"drim-benchmark-key-2026").digest()
rng = random.Random(2026)

NS = len(SURNAMES)
NM = len(MALE_NAMES)
NF = len(FEMALE_NAMES)
NPM = len(PATRONYMICS_M)
NPF = len(PATRONYMICS_F)
ND = len(EMAIL_DOMAINS)


def tv(p, q):
    return 0.5 * sum(abs(p.get(k, 0) - q.get(k, 0)) for k in set(p) | set(q))


def hist(values):
    values = list(values)
    h = {}
    for v in values:
        h[v] = h.get(v, 0) + 1
    n = len(values)
    return {k: c / n for k, c in h.items()}


n = 100000
m = DRIM(KEY)
emails, phones, fios, dates, ids = [], [], [], [], []
for i in range(1, n + 1):
    if rng.random() < 0.5:
        name = f"{SURNAMES[rng.randrange(NS)]} {FEMALE_NAMES[rng.randrange(NF)]} {PATRONYMICS_F[rng.randrange(NPF)]}"
    else:
        name = f"{SURNAMES[rng.randrange(NS)]} {MALE_NAMES[rng.randrange(NM)]} {PATRONYMICS_M[rng.randrange(NPM)]}"
    emails.append(f"user{i:07d}@{EMAIL_DOMAINS[rng.randrange(ND)]}")
    phones.append(f"+7 9{rng.randrange(10 ** 9):09d}")
    fios.append(name)
    dates.append(f"{rng.randrange(1950, 2005)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}")
    ids.append(str(i))

m_emails = [m.mask(e, "email") for e in emails]
m_phones = [m.mask(p, "phone") for p in phones]
m_fios = [m.mask(f, "fio") for f in fios]
m_dates = [m.mask(d, "date") for d in dates]
m_ids = [m.mask(x, "int_id") for x in ids]

res = {
    "n": n,
    "uniq_emails_orig": len(set(emails)), "uniq_emails_masked": len(set(m_emails)),
    "uniq_phones_orig": len(set(phones)), "uniq_phones_masked": len(set(m_phones)),
    "uniq_ids_orig": len(set(ids)), "uniq_ids_masked": len(set(m_ids)),
    "tv_email_domains": round(tv(hist(e.split("@")[1] for e in emails),
                                 hist(e.split("@")[1] for e in m_emails)), 4),
    "tv_birth_years": round(tv(hist(d[:4] for d in dates),
                               hist(d[:4] for d in m_dates)), 4),
    "avg_fio_len_orig": round(sum(len(f) for f in fios) / n, 1),
    "avg_fio_len_masked": round(sum(len(f) for f in m_fios) / n, 1),
    "fio_collisions": n - len(set(m_fios)),
    "phone_collisions": n - len(set(m_phones)),
    "email_collisions": n - len(set(m_emails)),
}
print(json.dumps(res, ensure_ascii=False, indent=1))
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp3_results.json"), "w") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
