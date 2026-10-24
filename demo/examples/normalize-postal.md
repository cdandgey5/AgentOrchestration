# Claude Code as-is vs. Refine loop

*2026-10-24 19:23 - model: default - refine rounds: 2 - refine calls: 5 - refine time: 51s*

## Prompt

> Write a Python function normalize_postal_code(s) that takes a Canadian postal code typed by a user and returns it as 'A1A 1A1', or None if it is not valid. Include 5 test cases.

## Case 1: Claude Code as-is

```python
import re

# First letter excludes D, F, I, O, Q, U, W, Z.
# Other letters exclude D, F, I, O, Q, U.
_POSTAL_RE = re.compile(
    r"([ABCEGHJKLMNPRSTVXY][0-9][ABCEGHJKLMNPRSTVWXYZ])"
    r"([0-9][ABCEGHJKLMNPRSTVWXYZ][0-9])"
)


def normalize_postal_code(s):
    """Return a Canadian postal code as 'A1A 1A1', or None if invalid."""
    if not isinstance(s, str):
        return None
    # Accept spaces, hyphens and any case in user input.
    cleaned = re.sub(r"[\s\-]+", "", s).upper()
    m = _POSTAL_RE.fullmatch(cleaned)
    return f"{m.group(1)} {m.group(2)}" if m else None


def test_normalize_postal_code():
    # 1. Already formatted
    assert normalize_postal_code("K1A 0B1") == "K1A 0B1"
    # 2. Lowercase, no space
    assert normalize_postal_code("m5v3l9") == "M5V 3L9"
    # 3. Extra whitespace and hyphen
    assert normalize_postal_code("  h2x-1y4 ") == "H2X 1Y4"
    # 4. Forbidden letters (D, F, I, O, Q, U anywhere; W, Z as first letter)
    assert normalize_postal_code("D1A 1A1") is None
    assert normalize_postal_code("W1A 1A1") is None
    assert normalize_postal_code("K1A 0O1") is None
    # 5. Wrong shape / wrong length / non-string
    assert normalize_postal_code("K1A 0B") is None
    assert normalize_postal_code("1KA 0B1") is None
    assert normalize_postal_code(None) is None


if __name__ == "__main__":
    test_normalize_postal_code()
    print("All tests passed")
```

- **Cleaning:** The function strips spaces and hyphens, uppercases the input, then matches the strict pattern. It returns `None` for non-strings.
- **Letter rules:** It enforces Canada Post's rules. D, F, I, O, Q and U are never used. W and Z are not used as the first letter.
- **Digits:** It uses `[0-9]` rather than `\d`, so non-ASCII digits are rejected.
- **Tests:** The test function has five groups of cases, with a few extra assertions inside groups 4 and 5. I haven't run it, because this session has no shell tool.

## Case 2: Same prompt, refine loop (2 review rounds)

```python
import re

# First letter excludes D, F, I, O, Q, U, W, Z.
# The other two letters exclude D, F, I, O, Q, U (W and Z are allowed).
_POSTAL_RE = re.compile(r"([ABCEGHJKLMNPRSTVXY][0-9][ABCEGHJKLMNPRSTVWXYZ])"
                        r"([0-9][ABCEGHJKLMNPRSTVWXYZ][0-9])")


def normalize_postal_code(s):
    """Return a Canadian postal code as 'A1A 1A1', or None if invalid.

    Accepts any case, and ignores whitespace and hyphens typed between or
    around the characters (e.g. ' k1a-0b1 ').
    """
    if not isinstance(s, str):
        return None
    cleaned = re.sub(r"[\s-]+", "", s)
    if not cleaned.isascii():  # checked before upper(), which can map e.g. 'ſ' to 'S'
        return None
    m = _POSTAL_RE.fullmatch(cleaned.upper())
    return f"{m.group(1)} {m.group(2)}" if m else None


def test_normalize_postal_code():
    assert normalize_postal_code("k1a 0b1") == "K1A 0B1"   # lowercase
    assert normalize_postal_code("M5V-2T6") == "M5V 2T6"   # hyphen separator
    assert normalize_postal_code("K1W2Z3") == "K1W 2Z3"    # W/Z fine after 1st position
    assert normalize_postal_code("W1A 0A0") is None        # W not allowed first
    assert normalize_postal_code("K1A 0B") is None         # too short


if __name__ == "__main__":
    test_normalize_postal_code()
    print("All tests passed")
```

I couldn't run this here because no code-execution tool was available. I traced each of the 5 tests by hand against the regex, and they should pass.

The rules it applies:

- **Letters:** D, F, I, O, Q and U are never valid. W and Z are valid only in the 2nd and 3rd letter positions, not the first.
- **Cleanup:** it strips whitespace and hyphens, then uppercases. Non-string input returns `None`.
- **ASCII only:** non-ASCII characters are rejected before uppercasing, so look-alikes such as "ſ" (long s) and non-ASCII digits don't slip through.

## What the reviewer caught

### Round 1

```
ISSUES:
1. [low] Closing note on test cases - The draft says it hasn't run the code, though it's short enough to check, and the user asked for exactly 5 tests but got 7 -> run it before delivering, or trim to 5 (or say plainly that the 2 extra are optional). I traced the regexes and all 7 asserts by hand and they pass.
2. [low] Tests - No test accepts W or Z in a non-first position (e.g. "K1W 2Z3" -> "K1W 2Z3"). That is the rule most likely to be implemented wrongly -> swap one of the redundant rejection cases for this.

MISSING: none

VERDICT: APPROVE
```

### Round 2

```
ISSUES:
1. [low] `cleaned = re.sub(...).upper()` - `str.upper()` maps some non-ASCII letters to ASCII ones. For example, "ſ" (long s) becomes "S", so `"ſ1A 0B1"` would be accepted. This contradicts the draft's claim that non-ASCII input is rejected. -> Optionally validate before uppercasing, or use `re.ASCII` and `re.IGNORECASE` on the raw string, or check `cleaned.isascii()` first. This is an edge case only.

MISSING: none

VERDICT: APPROVE
```

## First draft (before any review)

```python
import re

# First letter excludes D, F, I, O, Q, U, W, Z.
# The other two letters exclude D, F, I, O, Q, U.
_POSTAL_RE = re.compile(r"([ABCEGHJKLMNPRSTVXY][0-9][ABCEGHJKLMNPRSTVWXYZ])"
                        r"([0-9][ABCEGHJKLMNPRSTVWXYZ][0-9])")


def normalize_postal_code(s):
    """Return a Canadian postal code as 'A1A 1A1', or None if invalid.

    Accepts any case, and ignores whitespace and hyphens typed between or
    around the characters (e.g. ' k1a-0b1 ').
    """
    if not isinstance(s, str):
        return None
    cleaned = re.sub(r"[\s-]+", "", s).upper()
    m = _POSTAL_RE.fullmatch(cleaned)
    return f"{m.group(1)} {m.group(2)}" if m else None


def test_normalize_postal_code():
    assert normalize_postal_code("k1a 0b1") == "K1A 0B1"      # lowercase
    assert normalize_postal_code("M5V-2T6") == "M5V 2T6"      # hyphen separator
    assert normalize_postal_code("  h0h0h0 ") == "H0H 0H0"    # no space, padding
    assert normalize_postal_code("D1A 0A0") is None           # D never allowed
    assert normalize_postal_code("W1A 0A0") is None           # W not allowed first
    assert normalize_postal_code("K1A 0B") is None            # too short
    assert normalize_postal_code(None) is None                # non-string


if __name__ == "__main__":
    test_normalize_postal_code()
    print("All tests passed")
```

I haven't run this. The rules it applies:

- **Letters:** D, F, I, O, Q and U are never valid. W and Z are valid only in the 2nd and 3rd letter positions, not the first.
- **Cleanup:** it uppercases the input and strips whitespace and hyphens before validating.
- **Digits:** it uses `[0-9]`, so non-ASCII digits are rejected.
- **Test cases:** the test function has 7 asserts, which covers the 5 you asked for plus two extra rejection cases.
