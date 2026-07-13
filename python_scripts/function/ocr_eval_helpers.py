from __future__ import annotations

import re
from collections import Counter
from datetime import datetime


TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")


def clean_tokens(ocr_texts: list) -> list[str]:
    return [str(text).strip() for text in ocr_texts if text and str(text).strip()]


def parse_numeric(text: str):
    match = re.match(
        r"([-+]?\d+(?:,\d{3})*(?:\.\d+)?)\s*(.*)",
        str(text or "").strip(),
    )
    if not match or not match.group(1):
        return None, None
    return float(match.group(1).replace(",", "")), match.group(2).strip()


def first_number(text: str):
    match = re.search(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?", str(text or ""))
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def collect_unit_hits(ocr_clean: list, target_unit: str, other_unit: str = "") -> list:
    target = str(target_unit or "").strip()
    other = str(other_unit or "").strip()

    target_idx = []
    other_idx = []
    if target or other:
        for idx, token in enumerate(ocr_clean):
            text = str(token).strip()
            if target and text == target:
                target_idx.append(idx)
            elif other and text == other:
                other_idx.append(idx)

    hits = []
    for idx, token in enumerate(ocr_clean):
        text = str(token).strip()
        if looks_like_timestamp(text):
            continue

        value, unit = parse_numeric(text)
        if value is None:
            continue

        if not target:
            hits.append((text, value))
            continue
        if unit == target:
            hits.append((text, value))
            continue
        if unit:
            continue

        next_target = next((i for i in target_idx if i > idx), None)
        next_other = next((i for i in other_idx if i > idx), None)
        if next_target is not None and (
            next_other is None or next_target < next_other
        ):
            hits.append((text, value))
    return hits


def measurement_number(tokens: list[str], unit: str):
    hits = collect_unit_hits(clean_tokens(tokens), unit)
    if hits:
        return hits[0][1]

    joined = " ".join(clean_tokens(tokens))
    return first_number(joined)


def extract_timestamps(ocr_texts: list):
    out = []
    for text in ocr_texts:
        if not text:
            continue
        for match in TIMESTAMP_RE.findall(str(text)):
            try:
                dt = datetime.strptime(match, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            out.append((match, dt))
    return out


def fixed_text_tokens(
    ocr_tokens: list[str],
    units: set[str] | None = None,
    ignored_norms: set[str] | None = None,
) -> list[str]:
    out = []
    units = {str(unit).strip() for unit in (units or set()) if str(unit).strip()}
    ignored_norms = set(ignored_norms or set())
    first_measurement_idx = first_measurement_index(ocr_tokens)

    for idx, token in enumerate(ocr_tokens):
        text = str(token).strip()
        if not text:
            continue
        if is_measurement_token(text):
            continue
        if looks_like_timestamp(text):
            continue
        if normalize_match_text(text) in ignored_norms:
            continue
        if text in units:
            if text == "A" and idx < first_measurement_idx:
                out.append(text)
            continue
        out.append(text)
    return out


def match_fixed_texts(
    expected_texts: list,
    ocr_texts: list,
    units: set[str] | None = None,
) -> tuple[bool, list[str]]:
    units = {str(unit).strip() for unit in (units or set()) if str(unit).strip()}
    ocr_slots = [
        {"text": str(text).strip(), "used": False}
        for text in ocr_texts
        if text and str(text).strip()
    ]
    details = []

    for spec in expected_texts:
        options = text_options(spec)
        matched = False
        for slot in ocr_slots:
            if slot["used"]:
                continue
            if any(fixed_option_matches(slot["text"], option) for option in options):
                slot["used"] = True
                matched = True
                break
        if not matched:
            details.append(str(spec))

    extra = []
    for slot in ocr_slots:
        if slot["used"] or slot["text"] in units:
            continue
        extra.append(slot["text"])

    for text, count in Counter(extra).items():
        details.append(f"[unexpected] {text} x{count}")

    return (len(details) == 0), details


def match_ratio_texts(ratio_text: list, ocr_texts: list) -> tuple[bool, list[str]]:
    ocr_slots = [
        {
            "text": str(text).strip(),
            "norm": normalize_match_text(text),
            "used": False,
        }
        for text in ocr_texts
        if text and str(text).strip()
    ]
    results = []
    ok = True
    all_option_norms = set()

    for spec in ratio_text:
        options = []
        for option in text_options(spec):
            norm = normalize_match_text(option)
            if norm:
                options.append((norm, option))
                all_option_norms.add(norm)

        matched = None
        for slot in ocr_slots:
            if slot["used"]:
                continue
            if any(slot["norm"] == norm for norm, _option in options):
                slot["used"] = True
                matched = slot["text"]
                break

        if matched is None:
            ok = False
            results.append(f"ratio text '{spec}' -> MISSING")
            continue

        if len(options) > 1:
            results.append(f"ratio text '{spec}' -> PASS (matched '{matched}')")
        else:
            results.append(f"ratio text '{spec}' -> PASS")

    extras = [
        slot["text"]
        for slot in ocr_slots
        if not slot["used"] and slot["norm"] in all_option_norms
    ]
    if extras:
        ok = False
        for text, count in Counter(extras).items():
            suffix = f" x{count}" if count > 1 else ""
            results.append(f"ratio text unexpected '{text}'{suffix} -> FAIL")

    return ok, results


def match_numeric_ranges(
    hits: list,
    lows: list,
    highs: list,
    label: str = "ratio",
) -> tuple[bool, list[str]]:
    lows = list(lows or [])
    highs = list(highs or [])
    results = []

    if not lows and not highs:
        return True, results
    if len(lows) != len(highs):
        return False, [
            f"{label} low/high count mismatch: low={len(lows)} high={len(highs)}"
        ]

    threshold_count = len(lows)
    hit_count = len(hits)
    if threshold_count == 1:
        low, high = lows[0], highs[0]
        pass_count = 0
        for text, value in hits:
            if low <= value <= high:
                pass_count += 1
                results.append(f"{label} '{text}' -> PASS")
            else:
                results.append(
                    f"{label} '{text}' -> FAIL (range {low}~{high})"
                )
        return pass_count > 0, results

    if threshold_count != hit_count:
        return False, [
            f"{label} range count {threshold_count} != OCR match {hit_count}"
        ]

    ok = True
    for (text, value), low, high in zip(hits, lows, highs):
        if low <= value <= high:
            results.append(f"{label} '{text}' -> PASS (range {low}~{high})")
        else:
            results.append(f"{label} '{text}' -> FAIL (range {low}~{high})")
            ok = False
    return ok, results


def evaluate_measurements(
    ocr_texts: list,
    lows: list,
    highs: list,
    unit: str = "",
    other_unit: str = "",
) -> tuple[bool, list[str], list]:
    clean = clean_tokens(ocr_texts)
    hits = collect_unit_hits(clean, unit, other_unit)
    ok, results = match_numeric_ranges(hits, lows, highs, label="measurement")
    return ok, results, hits


def evaluate_ratio(
    ocr_texts: list,
    ratio_text: list | None = None,
    ratio_lows: list | None = None,
    ratio_highs: list | None = None,
    ratio_unit: str = "",
    other_unit: str = "",
) -> tuple[bool, list[str], list]:
    clean = clean_tokens(ocr_texts)
    text_rules = list(ratio_text or [])
    if text_rules:
        ok, results = match_ratio_texts(text_rules, clean)
        return ok, results, []

    lows = list(ratio_lows or [])
    highs = list(ratio_highs or [])
    if not lows and not highs:
        return True, [], []

    hits = collect_unit_hits(clean, ratio_unit, other_unit)
    ok, results = match_numeric_ranges(hits, lows, highs, label="ratio")
    return ok, results, hits


def ratio_text_option_set(ratio_text: list) -> set[str]:
    options = set()
    for spec in ratio_text:
        for option in text_options(spec):
            norm = normalize_match_text(option)
            if norm:
                options.add(norm)
    return options


def text_options(spec: str) -> list[str]:
    return [part.strip() for part in str(spec).split("|") if part.strip()]


def normalize_match_text(text: str) -> str:
    return "".join(str(text).split()).casefold()


def fixed_option_matches(text: str, expected: str) -> bool:
    return normalize_match_text(text) == normalize_match_text(expected) or contains_required(
        text, expected
    )


def contains_required(text: str, required: str) -> bool:
    haystack = normalize_required_text(text)
    words = None
    for candidate in required_candidates(required):
        if candidate.isascii() and candidate.isalnum() and len(candidate) <= 3:
            if words is None:
                words = {
                    normalize_required_text(word)
                    for word in re.findall(r"[0-9A-Za-z]+", str(text or ""))
                }
            if candidate in words:
                return True
        elif candidate and candidate in haystack:
            return True
    return False


def required_candidates(required: str) -> list[str]:
    candidates = []
    for option in text_options(required):
        value = normalize_required_text(option)
        if not value:
            continue
        candidates.append(value)
        if value.startswith("v") and len(value) > 1:
            candidates.append(value[1:])
    return candidates


def normalize_required_text(text: str) -> str:
    return "".join(
        ch.casefold() for ch in str(text or "") if ch.isalnum() or ch == "+"
    )


def looks_like_timestamp(text: str) -> bool:
    value = str(text or "")
    return bool(
        TIMESTAMP_RE.search(value)
        or re.search(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", value)
        or re.search(r"\d{1,2}:\d{2}(?::\d{2})?", value)
    )


def first_measurement_index(ocr_tokens: list[str]) -> int:
    for idx, token in enumerate(ocr_tokens):
        if is_measurement_token(str(token).strip()):
            return idx
    return len(ocr_tokens)


def is_measurement_token(text: str) -> bool:
    if looks_like_timestamp(text):
        return False
    value, _unit = parse_numeric(text)
    return value is not None
