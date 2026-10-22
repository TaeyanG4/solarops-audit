"""Canonical calendar bounds shared by reports and read-only APIs."""

import re
from datetime import date, timedelta


def iso_day(value: str) -> date:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("Expected YYYY-MM-DD")
    return date.fromisoformat(value)


def date_bounds(start: str, end: str) -> tuple[str, str]:
    if iso_day(start) >= iso_day(end):
        raise ValueError("Expected from < to (exclusive)")
    return start, end


def next_day(value: str) -> str:
    try:
        return (iso_day(value) + timedelta(days=1)).isoformat()
    except OverflowError:
        raise ValueError("Date has no representable next day") from None


def month_bounds(period: str) -> tuple[str, str]:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", period):
        raise ValueError("Expected YYYY-MM")
    first = iso_day(period + "-01")
    end = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    return first.isoformat(), end.isoformat()
