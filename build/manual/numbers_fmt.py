"""Number formatting, as the dashboard formats numbers.

The dashboard uses ``Intl.NumberFormat`` with ``es-MX`` and ``en-AU``
(``js/strings.js``): both use a decimal point and comma thousands separators,
so the only difference between the languages here is none -- which keeps a
figure quoted in either edition identical.  Negative numbers take a true
minus sign, as the dashboard's ``minus()`` gives them.
"""

import math


def fmt(value, digits=1, lang='en'):
    if value is None:
        return '–'
    value = float(value)
    if math.isnan(value):
        return '–'
    text = f'{value:,.{digits}f}'
    if text.startswith('-'):
        stripped = text[1:].replace('0', '').replace('.', '').replace(',', '')
        text = ('−' + text[1:]) if stripped else text[1:]
    return text


def digits_for(values):
    """Decimals for a set of values, from their spread."""
    finite = [abs(float(v)) for v in values
              if v is not None and not math.isnan(float(v))]
    if not finite:
        return 1
    span = max(finite)
    if span >= 100:
        return 0
    if span >= 10:
        return 1
    if span >= 1:
        return 2
    return 3


def pct(value, lang='en', digits=1):
    return '–' if value is None else f'{fmt(value, digits, lang)}%'
