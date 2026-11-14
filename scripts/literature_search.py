#!/usr/bin/env python3
"""Bounded, opt-in academic metadata search; not full-text reading or approval.

Requires an explicit --allow-network switch. Crossref/OpenAlex results are
untrusted E0 metadata candidates. No project state, SIB or approval is written.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable
from urllib import error, parse, request

import yaml
from jsonschema import Draft202012Validator

from literature_evidence import CONTRACT_PATH, EvidenceError, validate_report

MAX_BRIEF_BYTES = 32768
MAX_RESPONSE_BYTES = 1048576
MAX_QUERY_COUNT = 4
MAX_TOTAL_SOURCES = 30
PROVIDER_BASES = {
    "crossref": "https://api.crossref.org/works",
    "openalex": "https://api.openalex.org/works",
}


class SearchError(ValueError):
    """A safe diagnostic without exposing external content or full queries."""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key, value in pairs:
        if key in found:
            raise SearchError("duplicate_brief_key")
        found[key] = value
    return found


def _not_json_number(_: str) -> None:
    raise SearchError("invalid_json_number")


def load_brief(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_BRIEF_BYTES:
            raise SearchError("brief_size_limit")
        raw = path.read_bytes()
        document = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
            parse_constant=_not_json_number,
        )
    except SearchError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise SearchError("invalid_brief_json") from exc
    if not isinstance(document, dict) or set(document) != {
        "protocol_version", "scope", "queries", "depth", "year_from",
    } or document.get("protocol_version") != "1.0.0":
        raise SearchError("brief_fields_invalid")
    scope = document.get("scope")
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    scope_schema = contract["properties"]["scope"]
    if not isinstance(scope, dict) or not Draft202012Validator(scope_schema).is_valid(scope):
        raise SearchError("brief_scope_invalid")
    if scope["mode"] == "model_design":
        if (scope["problem_contract_status"] != "frozen"
                or scope["question"] == "general"
                or not scope.get("problem_contract_anchor")):
            raise SearchError("model_design_requires_frozen_anchored_problem")
    elif scope["problem_contract_status"] != "not_applicable":
        raise SearchError("standalone_cannot_assert_problem_freeze")
    queries = document.get("queries")
    if (not isinstance(queries, list) or not 1 <= len(queries) <= MAX_QUERY_COUNT
            or any(not isinstance(q, str) or not 5 <= len(q) <= 180
                   or "\n" in q or "\r" in q for q in queries)):
        raise SearchError("brief_queries_invalid")
    if len({q.strip().casefold() for q in queries}) != len(queries):
        raise SearchError("brief_duplicate_query")
    depth = document.get("depth")
    if depth not in {"lightweight", "targeted", "deep"}:
        raise SearchError("brief_depth_invalid")
    year = document.get("year_from")
    current = datetime.now(timezone.utc).year
    if type(year) is not int or not 1900 <= year <= current:
        raise SearchError("brief_year_invalid")
    return document


def make_url(provider: str, query: str, *, year_from: int, per_query: int) -> str:
    if provider not in PROVIDER_BASES or not 1 <= per_query <= 10:
        raise SearchError("provider_or_result_limit_invalid")
    if provider == "crossref":
        parameters = {"query.bibliographic": query, "rows": per_query,
                      "filter": f"from-pub-date:{year_from}-01-01"}
    else:
        parameters = {"search": query, "per_page": per_query,
                      "filter": f"from_publication_date:{year_from}-01-01"}
    return PROVIDER_BASES[provider] + "?" + parse.urlencode(parameters)


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: Any,
                         msg: Any, headers: Any, newurl: Any) -> None:
        raise SearchError("provider_redirect_disallowed")


def fetch_json(url: str, *, timeout: float) -> dict[str, Any]:
    parsed = parse.urlparse(url)
    allowed = {parse.urlparse(x).hostname for x in PROVIDER_BASES.values()}
    if parsed.scheme != "https" or parsed.hostname not in allowed:
        raise SearchError("provider_host_disallowed")
    client = request.build_opener(NoRedirect)
    req = request.Request(url, headers={
        "User-Agent": "mathmodel-skill/10.30 academic-metadata-reader",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
    })
    try:
        with client.open(req, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type.lower():
                raise SearchError("provider_response_not_json")
            data = response.read(MAX_RESPONSE_BYTES + 1)
    except error.HTTPError as exc:
        if exc.code in {403, 408, 429, 500, 502, 503, 504}:
            raise SearchError("provider_unavailable") from exc
        raise SearchError("provider_http_error") from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise SearchError("provider_unavailable") from exc
    if len(data) > MAX_RESPONSE_BYTES:
        raise SearchError("provider_response_oversize")
    try:
        document = json.loads(data.decode("utf-8"), parse_constant=_not_json_number)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise SearchError("provider_response_invalid_json") from exc
    if not isinstance(document, dict):
        raise SearchError("provider_response_not_object")
    return document


def _doi(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    doi = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):]
    if not doi.lower().startswith("10.") or "/" not in doi or len(doi) > 256:
        return None
    return doi.lower()


def _bounded_text(value: Any, length: int) -> str | None:
    if not isinstance(value, str):
        return None
    value = " ".join(value.split()).strip()
    return value[:length] if value else None


def parse_items(provider: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if provider == "crossref":
        message = payload.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("items"), list):
            raise SearchError("crossref_payload_invalid")
        return message["items"]
    if provider == "openalex":
        if not isinstance(payload.get("results"), list):
            raise SearchError("openalex_payload_invalid")
        return payload["results"]
    raise SearchError("unknown_provider")


def source_record(provider: str, item: Any, *, retrieved_at: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    if provider == "crossref":
        raw_title = item.get("title")
        title = _bounded_text(raw_title[0] if isinstance(raw_title, list) and raw_title else None, 1024)
        doi = _doi(item.get("DOI"))
        url = "https://doi.org/" + doi if doi else None
        record_id = doi or _bounded_text(item.get("URL"), 256)
        raw_year = ((item.get("published") or item.get("issued") or {}).get("date-parts")
                    if isinstance(item.get("published") or item.get("issued") or {}, dict) else None)
        year = (raw_year[0][0] if isinstance(raw_year, list) and raw_year
                and isinstance(raw_year[0], list) and raw_year[0] else None)
        venue = item.get("container-title")
        venue = venue[0] if isinstance(venue, list) and venue else None
        retracted = None  # Crossref registration metadata alone is not a retraction audit.
    else:
        title = _bounded_text(item.get("display_name") or item.get("title"), 1024)
        doi = _doi(item.get("doi"))
        oid = item.get("id")
        oid = oid if isinstance(oid, str) and oid.startswith("https://openalex.org/W") else None
        url = "https://doi.org/" + doi if doi else oid
        record_id = oid
        year = item.get("publication_year")
        loc = item.get("primary_location")
        venue = (loc.get("source") or {}).get("display_name") if isinstance(loc, dict) and isinstance(loc.get("source"), dict) else None
        retracted = item.get("is_retracted")
    if not title or not url or not url.startswith("https://"):
        return None
    source = {
        "id": "L1", "title": title, "source_url": url,
        "origin": "academic_connector", "access_level": "metadata",
        "evidence_level": "E0", "retrieved_at": retrieved_at,
        "provider_record_id": (record_id or url)[:256],
    }
    if doi:
        source["doi"] = doi
    if isinstance(year, int) and 1600 <= year <= 2100:
        source["publication_year"] = year
    venue = _bounded_text(venue, 256)
    if venue:
        source["venue"] = venue
    if retracted is True:
        source["is_retracted"] = True
    return source


def search(
    brief: dict[str, Any], *, provider: str, allow_network: bool,
    per_query: int = 5, timeout: float = 10,
    fetch: Callable[..., dict[str, Any]] = fetch_json,
    clock: Callable[[], str] = now_utc,
) -> dict[str, Any]:
    if provider not in PROVIDER_BASES or type(per_query) is not int or not 1 <= per_query <= 10:
        raise SearchError("provider_or_result_limit_invalid")
    if not 1 <= timeout <= 20:
        raise SearchError("timeout_out_of_bounds")
    if not isinstance(brief, dict) or set(brief) != {
        "protocol_version", "scope", "queries", "depth", "year_from",
    }:
        raise SearchError("brief_fields_invalid")
    # Search only the explicit short keyword queries. Never send Problem Contract,
    # attachment content or the full independent mathematical structure to a provider.
    if not isinstance(brief["queries"], list) or not 1 <= len(brief["queries"]) <= MAX_QUERY_COUNT:
        raise SearchError("brief_queries_invalid")
    attempts: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    n_retracted = 0
    successful = 0
    errors: list[str] = []
    when = None
    if allow_network:
        for query in brief["queries"]:
            url = make_url(provider, query, year_from=brief["year_from"], per_query=per_query)
            when = clock()
            attempt = {"provider": provider, "channel": "academic_connector",
                       "query": query, "status": "success", "retrieved_at": when,
                       "provider_url": PROVIDER_BASES[provider]}
            try:
                payload = fetch(url, timeout=timeout)
                rows = parse_items(provider, payload)
                successful += 1
                attempt["result_count"] = len(rows)
                for item in rows:
                    record = source_record(provider, item, retrieved_at=when)
                    if record is None:
                        continue
                    if record.get("is_retracted") is True:
                        n_retracted += 1
                        continue
                    key = record.get("doi") or record["source_url"] or record["title"].casefold()
                    if key in seen:
                        continue
                    seen.add(key)
                    record["id"] = "L" + str(len(sources) + 1)
                    sources.append(record)
                    if len(sources) >= MAX_TOTAL_SOURCES:
                        break
            except SearchError as exc:
                attempt["status"] = "unavailable" if str(exc) == "provider_unavailable" else "failed"
                errors.append(str(exc))
            except (TypeError, ValueError, KeyError) as exc:
                attempt["status"] = "failed"
                errors.append("provider_payload_invalid")
            attempts.append(attempt)
            if len(sources) >= MAX_TOTAL_SOURCES:
                break
    if not allow_network:
        state = "skipped"
        reason = "Network access not explicitly authorized; no provider was contacted."
    elif successful == 0:
        state = "unavailable" if errors and all(e == "provider_unavailable" for e in errors) else "failed"
        reason = "No successful provider response. Search completion cannot be claimed."
    elif errors:
        state = "completed" if sources else "failed"
        reason = "Partial provider failures; uncovered queries remain unresolved."
    elif sources:
        state = "completed"
        reason = "Metadata search completed; original methods are not verified."
    else:
        state = "no_suitable_source"
        reason = "No usable metadata candidates in the bounded query scope; wider research is unresolved."
    gaps = ["Original-paper methods, assumptions, parameters and problem fit have not been verified."]
    if n_retracted:
        gaps.append("Provider-reported retracted items were excluded; this is not an independent retraction audit.")
    if errors:
        gaps.append("Some provider requests failed; retry or independent search may be needed.")
    if state in {"skipped", "failed", "unavailable", "no_suitable_source"}:
        gaps.append("Current bounded metadata search cannot establish suitable scientific sources.")
    record = {
        "protocol_version": "1.0.0",
        "scope": brief["scope"],
        "search": {"depth": brief["depth"], "status": state,
                   "attempts": attempts, "stop_reason": reason},
        "sources": sources,
        "methods": [],
        "decision": {"evidence_status": "insufficient",
                     "independent_model_reasoning": brief["scope"]["independent_problem_structure"],
                     "unresolved_gaps": gaps},
    }
    if successful:
        record["search"]["searched_at"] = when
    verdict = validate_report(record)
    if verdict["status"] != "passed":
        raise SearchError("constructed_report_contract_violation")
    return record


def write_new(path: Path, report: dict[str, Any]) -> None:
    """Write only to the caller's explicitly selected unused path; no overwrites."""
    data = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(data) > 262144:
        raise SearchError("report_size_limit")
    fd = None
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            fd = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise SearchError("refuse_overwrite_existing_report") from exc
    except OSError as exc:
        raise SearchError("cannot_write_report") from exc
    finally:
        if fd is not None:
            os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    cmd = sub.add_parser("run", help="Opt-in bounded metadata search")
    cmd.add_argument("--brief", type=Path, required=True)
    cmd.add_argument("--provider", choices=sorted(PROVIDER_BASES), default="crossref")
    cmd.add_argument("--allow-network", action="store_true", help="Explicitly authorize sending keyword queries")
    cmd.add_argument("--per-query", type=int, choices=range(1, 11), metavar="1..10", default=5)
    cmd.add_argument("--timeout", type=float, default=10.0)
    cmd.add_argument("--output", type=Path, help="Optional NEW report path; never overwrite")
    args = parser.parse_args(argv)
    try:
        report = search(load_brief(args.brief), provider=args.provider,
                        allow_network=args.allow_network,
                        per_query=args.per_query, timeout=args.timeout)
        if args.output:
            write_new(args.output, report)
            print(json.dumps({"status": report["search"]["status"],
                              "source_count": len(report["sources"]),
                              "file": str(args.output),
                              "authority": "metadata_only_no_approval"}, ensure_ascii=False))
        else:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    except (SearchError, EvidenceError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "failed", "reason": str(exc),
                          "human_model_approval": "not_granted"}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
