import gc
import hashlib
import json
import os
import random
import resource
import sys
import time

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


def peak_rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def deep_size(d):
    size = sys.getsizeof(d)
    for k, v in d.items():
        size += sys.getsizeof(k) + sys.getsizeof(v)
    return size


def gen_users(n):
    users = []
    for i in range(1, n + 1):
        if rng.random() < 0.5:
            name = f"{SURNAMES[rng.randrange(NS)]} {MALE_NAMES[rng.randrange(NM)]} {PATRONYMICS_M[rng.randrange(NPM)]}"
        else:
            name = f"{SURNAMES[rng.randrange(NS)]} {FEMALE_NAMES[rng.randrange(NF)]} {PATRONYMICS_F[rng.randrange(NPF)]}"
        email = f"user{i:07d}@{EMAIL_DOMAINS[rng.randrange(ND)]}"
        phone = f"+7 9{rng.randrange(10 ** 9):09d}"
        bdate = f"{rng.randrange(1950, 2005)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}"
        users.append((i, name, email, phone, bdate))
    return users


def gen_contacts(users, k):
    rows = []
    uid = 0
    for (pid, _, pemail, _, _) in users:
        for _ in range(k):
            uid += 1
            rows.append((uid, pid, pemail))
    return rows


def gen_orders(users):
    return [(i, u[0]) for i, u in enumerate(users, 1)]


def run_drim(users, contacts, orders, stats):
    m = DRIM(KEY)
    t0 = time.perf_counter()
    u_out = [(m.mask(str(i), "int_id"), m.mask(nm, "fio"), m.mask(em, "email"),
              m.mask(ph, "phone"), m.mask(bd, "date")) for (i, nm, em, ph, bd) in users]
    c_out = [(m.mask(str(i), "int_id"), m.mask(str(uid), "int_id"), m.mask(em, "email"))
             for (i, uid, em) in contacts]
    o_out = [(m.mask(str(i), "int_id"), m.mask(str(uid), "int_id"))
             for (i, uid) in orders]
    stats["time"] = time.perf_counter() - t0
    stats["dict_bytes"] = 32
    return u_out, c_out, o_out


def run_dict(users, contacts, orders, stats):
    t0 = time.perf_counter()
    d_int, d_fio, d_email, d_phone, d_date = {}, {}, {}, {}, {}
    int_ctr = [10 ** 8]

    def dict_mask(v, d, fake):
        if v not in d:
            d[v] = fake()
        return d[v]

    def fk_int():
        int_ctr[0] += 1
        return str(int_ctr[0])

    def fk_fio():
        if rng.random() < 0.5:
            return f"{SURNAMES[rng.randrange(NS)]} {FEMALE_NAMES[rng.randrange(NF)]} {PATRONYMICS_F[rng.randrange(NPF)]}"
        return f"{SURNAMES[rng.randrange(NS)]} {MALE_NAMES[rng.randrange(NM)]} {PATRONYMICS_M[rng.randrange(NPM)]}"

    def fk_email():
        return f"{rng.randrange(10 ** 10):010d}@{EMAIL_DOMAINS[rng.randrange(ND)]}"

    def fk_phone():
        return f"+7 9{rng.randrange(10 ** 9):09d}"

    def fk_date():
        return f"{rng.randrange(1950, 2005)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}"

    u_out = [(dict_mask(str(i), d_int, fk_int), dict_mask(nm, d_fio, fk_fio),
              dict_mask(em, d_email, fk_email), dict_mask(ph, d_phone, fk_phone),
              dict_mask(bd, d_date, fk_date)) for (i, nm, em, ph, bd) in users]
    c_out = [(dict_mask(str(i), d_int, fk_int), dict_mask(str(uid), d_int, fk_int),
             dict_mask(em, d_email, fk_email)) for (i, uid, em) in contacts]
    o_out = [(dict_mask(str(i), d_int, fk_int), dict_mask(str(uid), d_int, fk_int))
             for (i, uid) in orders]
    stats["time"] = time.perf_counter() - t0
    stats["dict_bytes"] = sum(deep_size(d) for d in (d_int, d_fio, d_email, d_phone, d_date))
    return u_out, c_out, o_out


def run_random(users, contacts, orders, stats):
    t0 = time.perf_counter()

    def r_int():
        return str(rng.randrange(10 ** 9)).rjust(9, "0")

    def r_fio():
        if rng.random() < 0.5:
            return f"{SURNAMES[rng.randrange(NS)]} {FEMALE_NAMES[rng.randrange(NF)]} {PATRONYMICS_F[rng.randrange(NPF)]}"
        return f"{SURNAMES[rng.randrange(NS)]} {MALE_NAMES[rng.randrange(NM)]} {PATRONYMICS_M[rng.randrange(NPM)]}"

    def r_email():
        return f"{rng.randrange(10 ** 10):010d}@{EMAIL_DOMAINS[rng.randrange(ND)]}"

    def r_phone():
        return f"+7 9{rng.randrange(10 ** 9):09d}"

    def r_date():
        return f"{rng.randrange(1950, 2005)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}"

    u_out = [(r_int(), r_fio(), r_email(), r_phone(), r_date()) for _ in users]
    c_out = [(r_int(), r_int(), r_email()) for _ in contacts]
    o_out = [(r_int(), r_int()) for _ in orders]
    stats["time"] = time.perf_counter() - t0
    stats["dict_bytes"] = 0
    return u_out, c_out, o_out


def integrity_report(users, u_out, c_out, o_out):
    ids = set(str(u[0]) for u in users)
    emails = set(u[2] for u in users)
    ids_m = set(u[0] for u in u_out)
    emails_m = set(u[2] for u in u_out)
    return {
        "pk_unique_users": len(ids_m) == len(ids),
        "pk_unique_emails": len(emails_m) == len(emails),
        "fk_contacts_ok": all(c[1] in ids_m for c in c_out),
        "fk_contacts_email_ok": all(c[2] in emails_m for c in c_out),
        "fk_orders_ok": all(o[1] in ids_m for o in o_out),
    }


def experiment_scale(scales):
    results = []
    for n in scales:
        gc.collect()
        users = gen_users(n)
        contacts = gen_contacts(users, 2)
        orders = gen_orders(users)
        total_rows = len(users) + len(contacts) + len(orders)
        for method_name, fn in (("DRIM", run_drim), ("DICT", run_dict), ("RANDOM", run_random)):
            gc.collect()
            stats = {}
            u_out, c_out, o_out = fn(users, contacts, orders, stats)
            integ = integrity_report(users, u_out, c_out, o_out)
            rec = {
                "n_users": n, "rows": total_rows, "method": method_name,
                "time_s": round(stats["time"], 3),
                "rows_per_s": int(total_rows / stats["time"]),
                "dict_mb": round(stats.get("dict_bytes", 0) / 1048576, 2),
                "integrity": integ,
                "integrity_ok": all(integ.values()),
            }
            results.append(rec)
            print(f"n={n:>8,} {method_name:6s} rows={total_rows:>9,} t={rec['time_s']:8.3f}s "
                  f"{rec['rows_per_s']:>8,} rows/s  dictMB={rec['dict_mb']:8.2f}  "
                  f"integrity={'OK' if rec['integrity_ok'] else 'BROKEN'}", flush=True)
            del u_out, c_out, o_out
        del users, contacts, orders
    return results


def experiment_memory(ks):
    results = []
    for k in ks:
        emails = [f"user{i:08d}@mail.ru" for i in range(k)]
        d = {}
        t0 = time.perf_counter()
        for e in emails:
            d[e] = f"{rng.randrange(10 ** 10):010d}@mail.ru"
        build_s = time.perf_counter() - t0
        mb = deep_size(d) / 1048576
        results.append({"k": k, "dict_mb": round(mb, 2),
                        "bytes_per_entry": round(deep_size(d) / k, 1),
                        "build_s": round(build_s, 3)})
        print(f"memory k={k:>9,}: dict={mb:9.2f} MB ({results[-1]['bytes_per_entry']:.0f} B/entry), "
              f"DRIM state = 32 B", flush=True)
        del d, emails
        gc.collect()
    return results


def main():
    scales = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [1000, 5000, 10000, 50000, 100000]
    print("=== Experiment 1: scale (full pipeline) ===", flush=True)
    scale_res = experiment_scale(scales)
    print("\n=== Experiment 2: dictionary footprint ===", flush=True)
    mem_res = experiment_memory([1000, 10000, 100000, 1000000])
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench_results.json")
    with open(out_path, "w") as f:
        json.dump({"scale": scale_res, "memory": mem_res}, f, ensure_ascii=False, indent=1)
    print("saved:", out_path)


if __name__ == "__main__":
    main()
