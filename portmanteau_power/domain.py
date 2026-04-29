"""
domain.py – Lightweight domain-availability checker using stdlib DNS lookups.

No external dependencies required.  Checks whether <name>.<tld> resolves via
DNS – a fast proxy for "this domain is taken".  False negatives are possible
(parked / expired domains that still resolve), but false positives (saying a
domain is free when it is not) are rare.

Usage::

    from portmanteau_power.domain import check_domain, check_domains_bulk

    result = check_domain("novaforge")
    # {"name": "novaforge", "com": False, "net": True, "io": True}

    results = check_domains_bulk(["novaforge", "titanpulse"], tlds=["com", "io"])
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

# Default TLDs to check
DEFAULT_TLDS: List[str] = ["com", "net", "io"]

# DNS lookup timeout in seconds
_TIMEOUT: float = 2.0


def _is_registered(name: str, tld: str) -> bool:
    """
    Return True when *name*.*tld* resolves (i.e. the domain is taken).
    Returns False on NXDOMAIN, timeout, or any socket error.
    """
    fqdn = f"{name}.{tld}"
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(_TIMEOUT)
        socket.getaddrinfo(fqdn, None)
        return True
    except (socket.gaierror, socket.timeout, OSError):
        return False
    finally:
        socket.setdefaulttimeout(old_timeout)


def check_domain(
    name: str,
    tlds: Optional[List[str]] = None,
) -> Dict[str, object]:
    """
    Check availability of *name* across *tlds*.

    Returns a dict::

        {
            "name": "novaforge",
            "com": False,   # True  = taken, False = available (or failed)
            "net": True,
            "io": True,
        }

    The boolean values represent: ``True`` means the domain **appears available**
    (DNS did not resolve), ``False`` means it appears **taken**.
    """
    tlds = tlds or DEFAULT_TLDS
    result: Dict[str, object] = {"name": name}
    for tld in tlds:
        taken = _is_registered(name, tld)
        result[tld] = not taken  # True = available
    return result


def check_domains_bulk(
    names: List[str],
    tlds: Optional[List[str]] = None,
    max_workers: int = 20,
) -> List[Dict[str, object]]:
    """
    Concurrently check all *names* across *tlds*.

    Returns a list of dicts in the same order as *names*.
    """
    tlds = tlds or DEFAULT_TLDS
    results: Dict[str, Dict[str, object]] = {}

    def _check(n: str) -> Dict[str, object]:
        return check_domain(n, tlds)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_name = {pool.submit(_check, n): n for n in names}
        for future in as_completed(future_to_name):
            n = future_to_name[future]
            try:
                results[n] = future.result()
            except Exception:
                results[n] = {"name": n, **{t: None for t in tlds}}

    return [results[n] for n in names]


def domain_available_any(check_result: Dict[str, object]) -> Optional[bool]:
    """
    Return True if at least one TLD is available in *check_result*,
    False if all are taken, None if all lookups failed (None values).
    """
    tld_values = [v for k, v in check_result.items() if k != "name"]
    available = [v for v in tld_values if v is True]
    failed = [v for v in tld_values if v is None]
    if available:
        return True
    if len(failed) == len(tld_values):
        return None
    return False
