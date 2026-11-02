"""Prepare copy-only JSON provenance localization proposals for maintainer review.

This never rewrites production source or changes an acceptance decision. Generated
copies are not admitted build inputs: their new hashes require separate source
closure review. Raw workstation path mappings stay in the ignored proposal tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat


# Equivalent adjacent literals avoid reporting the regex itself as user data.
USER_PATH = re.compile(r"(?i)(?:[a-z]:/users/[^/\s\"']+|/" r"home/[^/\s\"']+)")


def _normalize(value: str) -> str:
    return value.replace("\\", "/")


def _pointer(parts) -> str:
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def localize(document, workspace: str):
    """Return an isolated JSON value plus exact changes and unresolved prose.

    Only a complete absolute path value is localized. A private path embedded in
    prose is held for manual review rather than silently editing its claim.
    External source records receive an opaque relative reference; they are not
    copied, licensed, made available or promoted into production inputs.
    """
    prefix = _normalize(workspace).rstrip("/")
    changes, unresolved = [], []

    def visit(value, parts):
        if isinstance(value, dict):
            for key in value:
                if USER_PATH.search(_normalize(key)):
                    unresolved.append({"pointer": _pointer((*parts, key)), "reason": "private path in a JSON key"})
            return {key: visit(item, (*parts, key)) for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item, (*parts, index)) for index, item in enumerate(value)]
        if not isinstance(value, str):
            return value
        normalized = _normalize(value)
        found = USER_PATH.search(normalized)
        if not found:
            return value
        # Whitespace can be legitimate in a filename but can also introduce
        # command arguments or prose. Hold it rather than guess the semantics.
        if found.start() != 0 or any(char.isspace() for char in normalized) or "\0" in normalized:
            unresolved.append({"pointer": _pointer(parts), "reason": "private path embedded in prose or multiline data"})
            return value
        segments = normalized.split("/")
        if any(part in {".", ".."} for part in segments):
            unresolved.append({"pointer": _pointer(parts), "reason": "ambiguous private path"})
            return value
        if normalized.casefold().startswith(prefix.casefold() + "/"):
            replacement = normalized[len(prefix) + 1:]
            kind = "workspace-relative"
        else:
            token = hashlib.sha256(value.encode("utf-8")).hexdigest()
            # Keep names out of the public placeholder as well: a filename can
            # itself contain an account name, email or private project title.
            replacement = "private-provenance/" + token
            kind = "unresolved-external-record"
        changes.append({"pointer": _pointer(parts), "original": value,
                        "replacement": replacement, "kind": kind})
        return replacement

    return visit(document, ()), changes, unresolved


def _direct(path: Path, *, file=False):
    path = Path(path).absolute()
    if ".." in path.parts or any(part.endswith((".", " ")) for part in path.parts if part != path.anchor):
        raise ValueError("Ambiguous source or output path")
    for item in reversed((path, *path.parents)):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Linked path refused: " + str(item))
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise ValueError("Non-directory ancestor refused: " + str(item))
        if item == path and file and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
            raise ValueError("Input must be a regular single-link file: " + str(item))
    return path


def _relative(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("Expected a literal workspace-relative file path")
    if any(part in {"", ".", ".."} or part.endswith((".", " ")) or
           any(char in part for char in '*?<>|"') or
           re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)
           for part in name.split("/")):
        raise ValueError("Ambiguous relative input path")
    path = Path(name)
    if path.is_absolute() or path.parts[0] in {".git", "matt_dev"}:
        raise ValueError("Input is outside the production source tree")
    return path


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def proposal(root: Path, names, output: Path, *, manifest: Path | None = None):
    """Write only a new ignored proposal directory, preserving every input byte."""
    root = _direct(root)
    output = _direct(output)
    if not output.is_relative_to(root / "matt_dev") or output == root / "matt_dev":
        raise ValueError("Proposal output must be a new directory inside the local archive")
    if output.exists():
        raise ValueError("Existing proposal output is never overwritten")
    manifest_strings = set()
    if manifest is not None:
        manifest = _direct(root / _relative(str(manifest).replace("\\", "/")), file=True)
        parsed_manifest = json.loads(manifest.read_text(encoding="utf-8-sig"))

        def strings(value):
            if isinstance(value, str):
                manifest_strings.add(value)
            elif isinstance(value, dict):
                for item in value.values():
                    strings(item)
            elif isinstance(value, list):
                for item in value:
                    strings(item)

        strings(parsed_manifest)
    rows, payloads, seen = [], [], set()
    for name in sorted(set(names)):
        relative = _relative(name)
        if name.casefold() in seen:
            raise ValueError("Case-aliased source paths refused")
        seen.add(name.casefold())
        path = _direct(root / relative, file=True)
        raw = path.read_bytes()
        row = {"path": relative.as_posix(), "original_sha256": _hash(raw),
               "original_size": len(raw), "production_replacement_admitted": False}
        # Demacia's manifest uses project-relative source paths. Record exact
        # string links only; this is not a proof of all dynamic dependencies.
        project_relative = Path(*relative.parts[1:]).as_posix()
        row["exact_manifest_reference"] = relative.as_posix() in manifest_strings or project_relative in manifest_strings
        if path.suffix.lower() != ".json":
            row.update(status="manual-review", reason="non-JSON source is never transformed")
        else:
            try:
                document = json.loads(raw.decode("utf-8-sig"))
                localized, changes, unresolved = localize(document, str(root))
                row.update(changes=changes, unresolved=unresolved)
                if unresolved:
                    row.update(status="manual-review", reason="not every private occurrence is a standalone path value")
                elif not changes:
                    row.update(status="unchanged", reason="no private path values found")
                else:
                    encoded = (json.dumps(localized, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
                    row.update(status="copy-proposal", proposed_sha256=_hash(encoded),
                               candidate="candidate/" + relative.as_posix())
                    payloads.append((relative, encoded))
            except (ValueError, UnicodeError) as error:
                row.update(status="manual-review", reason=str(error))
        rows.append(row)
    # Validate all source paths/JSON and construct payloads before creating any
    # output. A later I/O error may leave an explicitly labelled proposal only.
    output.mkdir(parents=True)
    for relative, encoded in payloads:
        target = output / "candidate" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encoded)
    result = {"format_version": 1, "status": "authored configuration proposal",
              "production_replacement_admitted": False, "files": rows,
              "limitations": ["Original source and acceptance hashes are unchanged.",
                              "New copies are not approved production replacements.",
                              "External record placeholders do not supply the external files.",
                              "Exact manifest references do not prove full dependency closure.",
                              "This mapping contains private original paths and stays local."]}
    (output / "private-path-map.json").write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (output / "README.txt").write_text(
        "COPY-ONLY LOCALIZATION PROPOSAL — NOT AN ADMITTED SOURCE EXPORT\n\n"
        "Original source files were not edited. Candidate JSON retains attribution and existing\n"
        "status values, but changed bytes invalidate old hashes. External placeholders are unresolved\n"
        "records, not files. Review active consumers/source closure and fresh tests before adoption.\n"
        "private-path-map.json contains the exact private originals and must remain local.\n",
        encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--audit", type=Path, required=True, help="local publication audit JSON")
    parser.add_argument("--output", type=Path, required=True, help="new ignored proposal directory")
    parser.add_argument("--manifest", type=Path, default=Path("runeterra-demacia/assets/manifest.json"))
    args = parser.parse_args(argv)
    audit = json.loads(args.audit.read_text(encoding="utf-8-sig"))
    names = audit["findings"].get("text containing a user-directory path", [])
    names = [name for name in names if name.startswith("runeterra-demacia/")]
    result = proposal(args.root, names, args.output, manifest=args.manifest)
    counts = {}
    for row in result["files"]:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"files": len(result["files"]), "statuses": counts,
                      "exact_manifest_references": sum(row["exact_manifest_reference"] for row in result["files"]),
                      "production_replacement_admitted": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
