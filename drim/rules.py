import datetime as dt

from .pools import (
    SURNAMES, MALE_NAMES, FEMALE_NAMES, PATRONYMICS_M, PATRONYMICS_F,
    EMAIL_DOMAINS, EMAIL_LOCAL_ALPHABET, EMAIL_LOCAL_HEAD, TRANSLIT,
)


class Rule:
    tag = b""

    def canonical(self, value):
        return value

    def mask(self, value, prf):
        raise NotImplementedError


class EmailRule(Rule):
    tag = b"email"
    fallback = "user@example.com"

    def canonical(self, value):
        return value.strip().lower()

    def mask(self, value, prf):
        local, _, _ = value.partition("@")
        if not local or "@" not in value:
            return self.fallback
        chars = [EMAIL_LOCAL_HEAD[prf.next_index(len(EMAIL_LOCAL_HEAD))]]
        for _ in range(max(len(local) - 1, 5)):
            chars.append(EMAIL_LOCAL_ALPHABET[prf.next_index(len(EMAIL_LOCAL_ALPHABET))])
        domain = EMAIL_DOMAINS[prf.next_index(len(EMAIL_DOMAINS))]
        return "".join(chars) + "@" + domain


class FioRule(Rule):
    tag = b"fio"

    def mask(self, value, prf):
        parts = value.split()
        fam = parts[0] if parts else ""
        name = parts[1] if len(parts) > 1 else ""
        patr = parts[2] if len(parts) > 2 else ""
        female = patr.lower().endswith("на") and not patr.lower().endswith("ична")
        name_pool = FEMALE_NAMES if female else MALE_NAMES
        patr_pool = PATRONYMICS_F if female else PATRONYMICS_M
        fi = prf.next_index(len(SURNAMES))
        ni = prf.next_index(len(name_pool))
        pi = prf.next_index(len(patr_pool))
        return f"{SURNAMES[fi]} {name_pool[ni]} {patr_pool[pi]}"


class LoginRule(Rule):
    tag = b"fio"

    def mask(self, value, prf):
        parts = value.split()
        fam = parts[0] if parts else ""
        name = parts[1] if len(parts) > 1 else "Иван"
        patr = parts[2] if len(parts) > 2 else "Иванович"
        fio = FioRule().mask(f"{fam} {name} {patr}", prf)
        latin = ["".join(TRANSLIT.get(ch, ch) for ch in w) for w in fio.lower().split()]
        return latin[0][:6] + "." + latin[1][:1] + latin[2][:1]


class PhoneRule(Rule):
    tag = b"phone"

    def __init__(self, ff1, tweak):
        self._ff1 = ff1
        self._tweak = tweak

    def canonical(self, value):
        return value.strip()

    def mask(self, value, prf):
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 11 or not digits.startswith("7"):
            digits = "7" + digits.lstrip("7")[-10:].rjust(10, "0")
        tail = self._ff1.encrypt(digits[1:], self._tweak)
        return "+7 (" + tail[0:3] + ") " + tail[3:6] + "-" + tail[6:8] + "-" + tail[8:10]


class IntIdRule(Rule):
    tag = b"int_id"

    def __init__(self, ff1, tweak):
        self._ff1 = ff1
        self._tweak = tweak

    def canonical(self, value):
        return value.strip().lstrip("0") or "0"

    def mask(self, value, prf):
        digits = value.rjust(2, "0")
        return self._ff1.encrypt(digits, self._tweak)


class DateRule(Rule):
    tag = b"date"

    def mask(self, value, prf):
        d = dt.date.fromisoformat(value)
        day_idx = prf.next_index(365)
        try:
            return (dt.date(d.year, 1, 1) + dt.timedelta(days=day_idx)).isoformat()
        except (OverflowError, ValueError):
            return d.isoformat()


RULES = {
    "email": EmailRule,
    "fio": FioRule,
    "login": LoginRule,
    "phone": PhoneRule,
    "int_id": IntIdRule,
    "date": DateRule,
}


def build_rules(ff1, tweaks):
    return {
        name: (
            cls(ff1, tweaks[name]) if name in ("phone", "int_id") else cls()
        )
        for name, cls in RULES.items()
    }
