"""API client and provenance capture shared by data-collection agents."""
from __future__ import annotations
import hashlib
import json
import logging
import os
import ssl
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import requests

log = logging.getLogger(__name__)

# modis.ornl.gov (NASA ORNL DAAC) serves a chain ending at "emSign Root CA - G1",
# which recent Mozilla/certifi trust stores no longer include. Without it every
# MODIS request fails with CERTIFICATE_VERIFY_FAILED. We trust this one public
# root ONLY for the hosts below, on top of the normal CA bundle, and refuse to
# use it if the file's fingerprint does not match.
EXTRA_ROOT_FILE = Path(__file__).resolve().parent.parent / "config" / "certs" / "emsign_root_ca_g1.pem"
EXTRA_ROOT_SHA256 = "40f6af0346a99aa1cd1d555a4e9cce62c7f9634603ee406615833dc8c8d00367"
EXTRA_ROOT_HOSTS = {"modis.ornl.gov"}


def _default_ca_bundle() -> str:
    for var in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
        path = os.environ.get(var)
        if path and Path(path).is_file():
            return path
    import certifi
    return certifi.where()


def build_extra_root_bundle(target: Path) -> Path:
    """Write default CA bundle + verified emSign root to `target` and return it."""
    pem = EXTRA_ROOT_FILE.read_text(encoding="ascii")
    der = ssl.PEM_cert_to_DER_cert(pem[pem.index("-----BEGIN"):])
    if hashlib.sha256(der).hexdigest() != EXTRA_ROOT_SHA256:
        raise APIError(f"Fingerprint mismatch for {EXTRA_ROOT_FILE}; refusing to trust it")
    base = Path(_default_ca_bundle()).read_text(encoding="utf-8", errors="ignore")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(base.rstrip() + "\n" + pem, encoding="utf-8")
    return target


class APIError(RuntimeError):
    pass


class CachedHTTP:
    """Read-through JSON cache. It never invents or substitutes observational data."""

    def __init__(self, cache_dir: Path, retries: int = 5, offline: bool = False, max_backoff: float = 60.0):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "KATOUWA-earth-science-hackathon/0.1", "Accept": "application/json"})
        self.retries = retries
        self.offline = offline
        self.max_backoff = max_backoff
        self.trace: list[dict[str, Any]] = []
        self._extra_bundle: Path | None = None

    def _verify_for(self, url: str) -> bool | str:
        if urlparse(url).hostname not in EXTRA_ROOT_HOSTS:
            return True
        if self._extra_bundle is None:
            self._extra_bundle = build_extra_root_bundle(self.cache_dir.parent / "ca_bundle_with_emsign.pem")
        return str(self._extra_bundle)

    def get_json(self, url: str, params: dict | None = None, refresh: bool = False) -> dict | list:
        request = requests.Request("GET", url, params=params).prepare()
        url_full = request.url
        digest = hashlib.sha256(url_full.encode("utf-8")).hexdigest()
        path = self.cache_dir / f"{digest}.json"
        if path.exists() and not refresh:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.trace.append({"url": url_full, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "cache_hit": True, "file": str(path)})
            return payload
        if self.offline:
            raise APIError(f"No cached response and offline flag set: {url_full}")
        last_exc = None
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, params=params, timeout=(15, 90), verify=self._verify_for(url))
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, (dict, list)):
                    raise APIError("API returned neither JSON object nor array")
                # Do not persist obvious HTTP-200 JSON error envelopes as data.
                # Product-specific schema checks remain in the collection agents.
                if isinstance(payload, dict) and not any(k in payload for k in ('dates','subset','properties','parameters','bands')):
                    detail = payload.get('error') or payload.get('message') or payload.get('detail')
                    if detail:
                        raise APIError(f"API returned error document: {str(detail)[:350]}")
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                self.trace.append({"url": url_full, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "cache_hit": False, "file": str(path)})
                return payload
            except (requests.RequestException, ValueError, APIError) as exc:
                last_exc = exc
                log.warning("API request attempt %d/%d failed (%s): %s", attempt + 1, self.retries, url, exc)
                if attempt < self.retries - 1:
                    # Busy NASA servers (ORNL answers 502/503 under load) need
                    # real pauses; client errors (4xx) get only a short one.
                    status = getattr(getattr(exc, 'response', None), 'status_code', None)
                    busy = status is None or status >= 500 or status == 429
                    time.sleep(min(5 * 2 ** attempt, self.max_backoff) if busy else 1)
        raise APIError(f"API unavailable after {self.retries} attempts: {url_full}\nReason: {last_exc}")
