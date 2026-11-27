#!/usr/bin/env python3
"""Checks the app's translations. Needs no game files and no Android SDK, so
CI runs it on every push.

- every string the Java code uses exists in res/values/strings.xml (Kazakh)
- every string in the default file is used, or is the app name
- no string is empty
- translations (values-*) have the same placeholders as the default
- the Java code shows no English text that is not a string resource

Exit status 0 when everything passes, 1 otherwise.
"""
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1] / "app" / "src" / "main"
RES = ROOT / "res"
# Our code only: the vendored SDL sources (org/libsdl) are third-party.
JAVA = sorted((ROOT / "java" / "io" / "github" / "belmantegu").rglob("*.java"))

# Text in the code that is a name, not a translatable phrase.
ALLOWED_LITERALS = {r"Rayman\nOrigins"}  # the game's title, shown if there is no logo
# Keys that are used by something other than the Java code (the system's own names).
EXTERNAL_KEYS = {"app_name"}

PLACEHOLDER = re.compile(r"%(?:\d+\$)?[-#+ 0,(]*\d*(?:\.\d+)?[a-zA-Z%]")
UI_LITERAL = re.compile(
    r'\b(setText|say|setMessage|text|setTitle|setPositiveButton|setNegativeButton|Toast\.makeText)'
    r'\(\s*(?:[^,()]*,\s*)?"([^"]*[A-Za-z][^"]*)"')


def strings(path):
    root = ET.parse(path).getroot()
    out = {}
    for el in root.findall("string"):
        out[el.get("name")] = el.text or ""
    return out


def placeholders(text):
    return sorted(p for p in PLACEHOLDER.findall(text) if p != "%%")


def main():
    failures = []
    default = strings(RES / "values" / "strings.xml")
    java_text = "\n".join(p.read_text(encoding="utf-8") for p in JAVA)

    used = set(re.findall(r"R\.string\.(\w+)", java_text))
    for key in sorted(used - set(default) - {"cancel", "ok"}):  # cancel/ok are Android's
        failures.append(f"R.string.{key} is used in Java but not defined")
    for key in sorted(set(default) - used - EXTERNAL_KEYS):
        failures.append(f"string '{key}' is defined but never used")
    for key, value in default.items():
        if not value.strip():
            failures.append(f"string '{key}' is empty")

    for values_dir in sorted(RES.glob("values-*")):
        f = values_dir / "strings.xml"
        if not f.exists():
            continue
        for key, value in strings(f).items():
            if key not in default:
                failures.append(f"{values_dir.name}: '{key}' has no default (Kazakh) entry")
            elif placeholders(value) != placeholders(default[key]):
                failures.append(f"{values_dir.name}: '{key}' placeholders differ from the default")

    for m in UI_LITERAL.finditer(java_text):
        literal = m.group(2)
        if literal not in ALLOWED_LITERALS:
            failures.append(f"English text in code, move it to strings.xml: {literal!r}")

    if failures:
        print("FAILED:")
        for f in failures:
            print("  " + f)
        return 1
    print(f"OK: {len(default)} strings, {len(used)} used from Java, translations consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
