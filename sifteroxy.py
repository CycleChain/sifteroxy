#!/usr/bin/env python3

from __future__ import annotations

import argparse
import concurrent.futures as cf
import ipaddress
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Dict, Set

import requests

APP_NAME = "sifteroxy"
APP_VERSION = "0.1"

UA = "{}/{}".format(APP_NAME, APP_VERSION)

# Translations
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "tr": {
        "source_failed": "Kaynak indirilemedi: %s (%s)",
        "no_source": "%s için kaynak yok",
        "downloading": "%s: %d kaynak indiriliyor…",
        "validating": "%d proxy doğrulanacak (test_url=%s, timeout=%ss, concurrency=%d)",
        "progress": "İlerleme: %d/%d (başarılı: %d) - %.1f%%",
        "total_downloaded": "Toplam indirilen aday proxy: %d",
        "after_dedup": "Tekilleştirme sonrası: %d",
        "alive_count": "Çalışan proxy sayısı: %d — yayınlandı: %s",
        "metrics_written": "Metrikler yazıldı: %s",
        "fastest_10": "En hızlı 10:",
        "cancelled": "\nİptal edildi.",
        "loading_sources_error": "sources.json yüklenemedi: %s",
        "description": "Ücretsiz proxy listelerini toplayan, doğrulayan ve atomik olarak .txt yayınlayan araç",
    },
    "en": {
        "source_failed": "Source failed to download: %s (%s)",
        "no_source": "No source for %s",
        "downloading": "%s: downloading %d sources…",
        "validating": "Validating %d proxies (test_url=%s, timeout=%ss, concurrency=%d)",
        "progress": "Progress: %d/%d (successful: %d) - %.1f%%",
        "total_downloaded": "Total downloaded candidate proxies: %d",
        "after_dedup": "After deduplication: %d",
        "alive_count": "Working proxy count: %d — published: %s",
        "metrics_written": "Metrics written: %s",
        "fastest_10": "Fastest 10:",
        "cancelled": "\nCancelled.",
        "loading_sources_error": "Failed to load sources.json: %s",
        "description": "Tool that collects, validates, and atomically publishes free proxy lists as .txt",
    },
}


def load_sources() -> Dict[str, List[str]]:
    """Load SOURCES from sources.json file."""
    script_dir = Path(__file__).parent
    sources_path = script_dir / "sources.json"
    
    if not sources_path.exists():
        # Fallback to default sources if file doesn't exist
        logging.warning("sources.json not found, using default sources")
        return {
            "http": [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
                "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
                "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
                "https://raw.githubusercontent.com/proxylist-to/proxy-list/main/http.txt",
            ],
            "https": [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/https.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/https.txt",
            ],
            "socks4": [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
                "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            ],
            "socks5": [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
                "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            ],
        }
    
    try:
        with open(sources_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load sources.json: {e}")

IP_PORT_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})\b")

# Validation helpers

def _valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _parse_ip_ports(text: str) -> List[Tuple[str, int]]:
    found: List[Tuple[str, int]] = []
    for m in IP_PORT_RE.finditer(text):
        ip, port = m.group(1), int(m.group(2))
        if _valid_ip(ip) and 1 <= port <= 65535:
            found.append((ip, port))
    return found


class ProxyEntry:
    __slots__ = ("proto", "ip", "port")

    def __init__(self, proto: str, ip: str, port: int):
        self.proto = proto.lower()
        self.ip = ip
        self.port = port

    def key(self) -> Tuple[str, str, int]:
        return (self.proto, self.ip, self.port)

    def as_line(self) -> str:
        return f"{self.ip}:{self.port}"

    def as_requests_proxies(self) -> Dict[str, str]:
        url = f"{self.proto}://{self.ip}:{self.port}"
        return {"http": url, "https": url}

    def __repr__(self) -> str:
        return f"ProxyEntry(proto={self.proto}, ip={self.ip}, port={self.port})"


# Download

def fetch_source(url: str, timeout: int, lang: str = "tr") -> str:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
        r.raise_for_status()
        return r.text
    except Exception as e:
        msgs = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
        logging.warning(msgs["source_failed"], url, e)
        return ""


def collect_entries(protocols: List[str], timeout: int, max_sources: int, sources: Dict[str, List[str]], lang: str = "tr") -> List[ProxyEntry]:
    entries: List[ProxyEntry] = []
    msgs = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
    for proto in protocols:
        urls = sources.get(proto, [])
        if max_sources > 0:
            urls = urls[:max_sources]
        if not urls:
            logging.warning(msgs["no_source"], proto)
            continue
        logging.info(msgs["downloading"], proto, len(urls))
        with cf.ThreadPoolExecutor(max_workers=min(16, len(urls))) as ex:
            texts = list(ex.map(lambda u: fetch_source(u, timeout, lang), urls))
        for text in texts:
            for ip, port in _parse_ip_ports(text):
                entries.append(ProxyEntry(proto, ip, port))
    return entries


# Deduplication

def dedupe(entries: Iterable[ProxyEntry]) -> List[ProxyEntry]:
    seen: Set[Tuple[str, str, int]] = set()
    out: List[ProxyEntry] = []
    for e in entries:
        k = e.key()
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


# Validation

def check_proxy(entry: ProxyEntry, test_url: str, timeout: int, verify_tls: bool) -> Optional[Dict]:
    proxies = entry.as_requests_proxies()
    t0 = time.perf_counter()
    try:
        with requests.get(
            test_url,
            proxies=proxies,
            timeout=timeout,
            stream=True,
            headers={"User-Agent": UA},
            verify=verify_tls,
        ) as r:
            r.raise_for_status()
            first_byte_t = None
            for _ in r.iter_content(chunk_size=1):
                first_byte_t = time.perf_counter()
                break
            t1 = time.perf_counter()
            latency_ms = round((first_byte_t - t0) * 1000, 1) if first_byte_t else None
            total_ms = round((t1 - t0) * 1000, 1)
            return {
                "proto": entry.proto,
                "proxy": entry.as_line(),
                "status": r.status_code,
                "latency_ms": latency_ms,
                "total_ms": total_ms,
            }
    except Exception:
        return None


def validate_proxies(entries: List[ProxyEntry], test_url: str, timeout: int, concurrency: int, verify_tls: bool, lang: str = "tr") -> List[Dict]:
    alive: List[Dict] = []
    total = len(entries)
    msgs = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
    logging.info(msgs["validating"], total, test_url, timeout, concurrency)
    if total == 0:
        return alive

    def worker(e: ProxyEntry) -> Optional[Dict]:
        return check_proxy(e, test_url=test_url, timeout=timeout, verify_tls=verify_tls)

    with cf.ThreadPoolExecutor(max_workers=concurrency) as ex:
        for i, res in enumerate(ex.map(worker, entries), 1):
            if res:
                alive.append(res)
            if i % 100 == 0 or i == total:
                progress_pct = (i / total) * 100 if total > 0 else 0.0
                logging.info(msgs["progress"], i, total, len(alive), progress_pct)
    return alive


# Writing: Atomic publish + preview

def write_atomic_with_preview(final_path: Path, lines: List[str], do_preview: bool = True) -> None:
    final_path = final_path.expanduser().resolve()
    out_dir = final_path.parent
    tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Write to temporary file
    data = "\n".join(lines) + ("\n" if lines else "")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    # Open directory file descriptor
    dir_fd = os.open(out_dir, os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)  # Flush tmp file creation metadata

        # Create preview backup (optional)
        if do_preview and final_path.exists():
            prev_path = final_path.with_suffix(final_path.suffix + ".prev")
            try:
                os.replace(final_path, prev_path)  # atomic
            except FileNotFoundError:
                pass
            os.fsync(dir_fd)

        # Atomic publish
        os.replace(tmp_path, final_path)  # atomic rename
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def write_metrics(path: Path, alive: List[Dict]) -> None:
    data = {"generated_at": int(time.time()), "count": len(alive), "items": alive}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# Arguments

def build_argparser(lang: str = "tr") -> argparse.ArgumentParser:
    msgs = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
    p = argparse.ArgumentParser(
        description=msgs["description"],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--protocols", default="http,https,socks4,socks5", help="Hedef protokoller (virgülle)" if lang == "tr" else "Target protocols (comma-separated)")
    p.add_argument("--timeout", type=int, default=5, help="Doğrulama zaman aşımı (saniye)" if lang == "tr" else "Validation timeout (seconds)")
    p.add_argument("--concurrency", type=int, default=128, help="Eşzamanlı doğrulama iş parçacığı sayısı" if lang == "tr" else "Concurrent validation thread count")
    p.add_argument("--test-url", default="https://httpbin.org/ip", help="Proxy üzerinden çağrılacak test URL" if lang == "tr" else "Test URL to call via proxy")
    p.add_argument("--no-tls-verify", action="store_true", help="TLS sertifika doğrulamayı kapat (önerilmez)" if lang == "tr" else "Disable TLS certificate verification (not recommended)")
    p.add_argument("--out", default="proxies_alive.txt", help="Çalışan proxy çıktısı (txt)" if lang == "tr" else "Working proxy output (txt)")
    p.add_argument("--metrics", default=None, help="İsteğe bağlı metrik çıktısı (json)" if lang == "tr" else "Optional metrics output (json)")
    p.add_argument("--max-sources", type=int, default=0, help="Her protokolden en fazla N kaynak indir (0=hepsi)" if lang == "tr" else "Max N sources per protocol (0=all)")
    p.add_argument("--no-preview", action="store_true", help="Atomik yayında .prev yedeğini alma" if lang == "tr" else "Skip creating .prev backup in atomic publish")
    p.add_argument("--log-level", default="INFO", help="Log seviyesi (DEBUG, INFO, WARNING, ERROR)" if lang == "tr" else "Log level (DEBUG, INFO, WARNING, ERROR)")
    p.add_argument("--language", default="tr", choices=["tr", "en"], help="Dil seçimi (tr/en)" if lang == "tr" else "Language selection (tr/en)")
    p.add_argument("--order", default="desc", choices=["desc", "asc"], help="Sıralama: desc (en hızlıdan en yavaşa) veya asc (en yavaştan en hızlıya)" if lang == "tr" else "Sort order: desc (fastest to slowest) or asc (slowest to fastest)")
    return p


# Main flow

def main(argv: Optional[List[str]] = None) -> int:
    # First parse to get language, then rebuild parser with correct language
    lang = "tr"
    if argv:
        for i, arg in enumerate(argv):
            if arg == "--language" and i + 1 < len(argv):
                lang = argv[i + 1]
                break
    
    args = build_argparser(lang).parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s: %(message)s")

    lang = args.language
    msgs = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])

    # Load sources from JSON
    try:
        sources = load_sources()
    except Exception as e:
        logging.error(msgs["loading_sources_error"], e)
        return 1

    protocols = [s.strip().lower() for s in args.protocols.split(",") if s.strip()]

    # Download and parse
    raw_entries: List[ProxyEntry] = collect_entries(protocols, timeout=args.timeout, max_sources=args.max_sources, sources=sources, lang=lang)
    logging.info(msgs["total_downloaded"], len(raw_entries))

    # Deduplicate
    entries = dedupe(raw_entries)
    logging.info(msgs["after_dedup"], len(entries))

    # Validate
    alive = validate_proxies(entries, test_url=args.test_url, timeout=args.timeout, concurrency=args.concurrency, verify_tls=(not args.no_tls_verify), lang=lang)

    # Sort according to order parameter
    def _score(x: Dict) -> float:
        return (x.get("latency_ms") or 9e9) * 10 + (x.get("total_ms") or 9e9)
    
    if args.order == "desc":
        # Fastest to slowest (low score = fast)
        alive = sorted(alive, key=_score)
    else:
        # Slowest to fastest (high score = slow)
        alive = sorted(alive, key=_score, reverse=True)

    # Output: atomic publish (+ preview)
    out_path = Path(args.out)
    write_atomic_with_preview(out_path, [row["proxy"] for row in alive], do_preview=(not args.no_preview))
    logging.info(msgs["alive_count"], len(alive), out_path)

    if args.metrics:
        mpath = Path(args.metrics).expanduser().resolve()
        write_metrics(mpath, alive)
        logging.info(msgs["metrics_written"], mpath)

    # Summary (fastest 10)
    if alive:
        top = sorted(alive, key=_score)[:10]
        logging.info(f"{msgs['fastest_10']}\n%s", "\n".join(f"[{i+1:02d}] {row['proto']}://{row['proxy']} ~ {row.get('latency_ms')}ms/{row.get('total_ms')}ms" for i, row in enumerate(top)))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        # Try to get language from args, default to Turkish
        try:
            temp_args = argparse.ArgumentParser().add_argument("--language", default="tr", choices=["tr", "en"]).parse_known_args()[0]
            lang = temp_args.language if hasattr(temp_args, "language") else "tr"
        except:
            lang = "tr"
        msgs = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
        print(msgs["cancelled"])