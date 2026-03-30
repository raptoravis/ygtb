# Feishu Document Export - Comprehensive version
# Exports: Cloud Drive, Wiki, My Documents, Sheets, Bitable

import json
import os
import subprocess
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

EXPORT_ROOT = r"E:\downloads\feishu-doc-export"
TOTAL = 0
FETCHED = 0
FAILED = 0
SKIPPED = 0

NODE_SCRIPT = r"C:\Users\jonli\AppData\Roaming\npm\node_modules\@larksuite\cli\scripts\run.js"


def lark_cli(*args):
    """Call lark-cli via node directly, return stdout bytes"""
    cmd = ["node", NODE_SCRIPT] + list(args)
    proc = subprocess.run(cmd, capture_output=True)
    return proc.stdout


def lark_cli_powershell(*args):
    """Call lark-cli via PowerShell, return stdout bytes"""
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", f"& lark-cli {' '.join(args)}"]
    proc = subprocess.run(cmd, capture_output=True)
    return proc.stdout


def lark_api(path, params=None):
    """Call lark API via node directly, return parsed JSON"""
    if params is None:
        params = {}
    params_json = json.dumps(params, separators=(",", ":"))
    raw = lark_cli("api", "GET", path, "--params", params_json)
    if raw:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None
    return None


def sanitize(name):
    """Sanitize filename"""
    if not name:
        return "untitled"
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    name = name.strip()
    if len(name) > 120:
        name = name[:120]
    return name or "untitled"


def export_doc(token, filepath, doc_type="docx"):
    """Export a single document"""
    global TOTAL, FETCHED, FAILED, SKIPPED
    TOTAL += 1

    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        SKIPPED += 1
        return

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    idx = TOTAL
    fname = os.path.basename(filepath)
    print(f"  [{idx}] {fname}", flush=True)

    try:
        if doc_type == "file":
            rel_path = os.path.relpath(filepath, EXPORT_ROOT)
            raw = lark_cli_powershell("drive", "+download", "--file-token", token, "--output", rel_path, "--overwrite")
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                FETCHED += 1
            else:
                FAILED += 1
        elif doc_type == "sheet":
            rel_path = os.path.relpath(filepath, EXPORT_ROOT)
            raw = lark_cli_powershell(
                "sheets", "+export", "--spreadsheet-token", token, "--output", rel_path, "--overwrite"
            )
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                FETCHED += 1
            else:
                FAILED += 1
        elif doc_type == "bitable":
            export_bitable(token, filepath)
        else:
            url = f"https://my.feishu.cn/docx/{token}"
            raw = lark_cli_powershell("docs", "+fetch", "--doc", url, "--format", "json")
            if raw:
                data = json.loads(raw.decode("utf-8"))
                if data.get("ok") and data.get("data", {}).get("markdown"):
                    md = data["data"]["markdown"]
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(md)
                    FETCHED += 1
                else:
                    FAILED += 1
            else:
                FAILED += 1
    except Exception as e:
        FAILED += 1
        print(f"    ERROR: {e}", file=sys.stderr)


def export_bitable(base_token, filepath):
    """Export bitable (multi-dimensional table) to CSV"""
    global TOTAL, FETCHED, FAILED, SKIPPED
    try:
        raw = lark_cli_powershell("base", "+table-list", "--base-token", base_token, "--format", "json")
        if not raw:
            FAILED += 1
            return
        data = json.loads(raw.decode("utf-8"))
        if not data.get("data") or not data["data"].get("data"):
            FAILED += 1
            return

        tables = data["data"]["data"]
        if not tables:
            FAILED += 1
            return

        table_id = tables[0].get("table_id")
        if not table_id:
            FAILED += 1
            return

        records = []
        page_token = ""
        while True:
            params = {"table_id": table_id}
            if page_token:
                params["page_token"] = page_token

            raw = lark_cli_powershell(
                "base", "+record-list", "--base-token", base_token, "--table-id", table_id, "--format", "json"
            )
            if not raw:
                break
            rd = json.loads(raw.decode("utf-8"))
            if not rd.get("data") or not rd["data"].get("items"):
                break
            records.extend(rd["data"]["items"])
            page_token = rd["data"].get("page_token", "")
            if not page_token:
                break

        if records:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json.dumps(records, ensure_ascii=False, indent=2))
            FETCHED += 1
        else:
            FAILED += 1
    except Exception as e:
        FAILED += 1
        print(f"    BITABLE ERROR: {e}", file=sys.stderr)


def process_folder(folder_token, relpath):
    """Recursively process a drive folder"""
    global TOTAL, FETCHED, FAILED, SKIPPED

    label = relpath if relpath else "(root)"
    print(f"\n  Folder: {label}", flush=True)

    page_token = ""
    count = 0

    while True:
        params = {}
        if folder_token:
            params["folder_token"] = folder_token
        if page_token:
            params["page_token"] = page_token

        response = lark_api("drive/v1/files", params)
        if not response or response.get("code") != 0:
            print("    ERROR: Failed to list", flush=True)
            break

        files = response.get("data", {}).get("files", [])
        for f in files:
            count += 1
            ftype = f.get("type", "")
            fname = sanitize(f.get("name", ""))
            ftoken = f.get("token", "")
            shortcut = f.get("shortcut_info", {})
            base = os.path.join(EXPORT_ROOT, "drive", relpath) if relpath else os.path.join(EXPORT_ROOT, "drive")

            if ftype == "folder":
                child = f"{relpath}/{fname}" if relpath else fname
                process_folder(ftoken, child)
            elif ftype in ("docx", "doc"):
                export_doc(ftoken, os.path.join(base, f"{fname}.md"), "docx")
            elif ftype == "sheet":
                ext = ".xlsx"
                export_doc(ftoken, os.path.join(base, f"{fname}{ext}"), "sheet")
            elif ftype == "shortcut":
                tt = shortcut.get("target_type", "")
                tk = shortcut.get("target_token", "")
                if tt in ("docx", "doc"):
                    export_doc(tk, os.path.join(base, f"{fname}.md"), "docx")
                elif tt == "sheet":
                    export_doc(tk, os.path.join(base, f"{fname}.xlsx"), "sheet")
                elif tt == "bitable":
                    export_doc(tk, os.path.join(base, f"{fname}.json"), "bitable")
                elif tt == "file":
                    export_doc(tk, os.path.join(base, fname), "file")
            elif ftype == "file":
                export_doc(ftoken, os.path.join(base, fname), "file")

        has_more = response.get("data", {}).get("has_more", False)
        page_token = response.get("data", {}).get("next_page_token", "")
        if not has_more or not page_token:
            break

    print(f"    -> {count} items", flush=True)


def export_wiki():
    """Export all wiki documents across all spaces"""
    print("\n=== Wiki Documents ===", flush=True)

    wiki_dir = os.path.join(EXPORT_ROOT, "wiki")
    os.makedirs(wiki_dir, exist_ok=True)

    page = 1
    while True:
        raw = lark_cli_powershell("docs", "+search", "--format", "json", "--page-size", "50", "--page", str(page))
        if not raw:
            break
        data = json.loads(raw.decode("utf-8"))
        if not data.get("ok") or not data.get("data", {}).get("results"):
            break

        results = data["data"]["results"]
        found_wiki = False

        for item in results:
            if item.get("entity_type") == "WIKI":
                found_wiki = True
                token = item.get("result_meta", {}).get("token", "")
                title = sanitize(item.get("title_highlighted", ""))
                if not title:
                    title = token

                node_raw = lark_cli(
                    "wiki", "spaces", "get_node", "--params", json.dumps({"token": token}, separators=(",", ":"))
                )
                if node_raw:
                    try:
                        nd = json.loads(node_raw.decode("utf-8"))
                        if nd.get("code") == 0 and nd.get("data", {}).get("node"):
                            node = nd["data"]["node"]
                            obj_type = node.get("obj_type", "")
                            real_token = node.get("obj_token", "")
                            node_title = sanitize(node.get("title", "")) or title

                            if obj_type == "sheet":
                                export_doc(real_token, os.path.join(wiki_dir, f"{node_title}.xlsx"), "sheet")
                            elif obj_type == "bitable":
                                export_doc(real_token, os.path.join(wiki_dir, f"{node_title}.json"), "bitable")
                            elif obj_type in ("docx", "doc"):
                                export_doc(real_token, os.path.join(wiki_dir, f"{node_title}.md"), "docx")
                            else:
                                export_doc(real_token, os.path.join(wiki_dir, f"{node_title}.md"), "docx")
                            continue
                    except Exception:
                        pass

                export_doc(token, os.path.join(wiki_dir, f"{title}.md"), "docx")

        if not found_wiki and page > 1:
            break
        if not results:
            break
        page += 1


def export_my_docs():
    """Export personal 'My Documents' (excluding wiki and drive)"""
    print("\n=== My Documents ===", flush=True)

    my_docs_dir = os.path.join(EXPORT_ROOT, "my_docs")
    os.makedirs(my_docs_dir, exist_ok=True)

    page = 1
    while True:
        raw = lark_cli_powershell("docs", "+search", "--format", "json", "--page-size", "50", "--page", str(page))
        if not raw:
            break
        data = json.loads(raw.decode("utf-8"))
        if not data.get("ok") or not data.get("data", {}).get("results"):
            break

        results = data["data"]["results"]
        found_doc = False

        for item in results:
            entity = item.get("entity_type", "")
            if entity in ("DOCX", "DOC"):
                found_doc = True
                token = item.get("result_meta", {}).get("token", "")
                title = sanitize(item.get("title_highlighted", ""))
                if not title:
                    title = token
                export_doc(token, os.path.join(my_docs_dir, f"{title}.md"), "docx")
            elif entity == "SHEET":
                found_doc = True
                token = item.get("result_meta", {}).get("token", "")
                title = sanitize(item.get("title_highlighted", ""))
                if not title:
                    title = token
                export_doc(token, os.path.join(my_docs_dir, f"{title}.xlsx"), "sheet")

        if not found_doc and page > 1:
            break
        page += 1


def export_sheets():
    """Export all spreadsheets from search"""
    print("\n=== Sheets ===", flush=True)

    sheets_dir = os.path.join(EXPORT_ROOT, "sheets")
    os.makedirs(sheets_dir, exist_ok=True)

    seen_tokens = set()

    page = 1
    while True:
        raw = lark_cli_powershell(
            "docs", "+search", "--format", "json", "--page-size", "50", "--page", str(page), "--doc-type", "sheet"
        )
        if not raw:
            break
        data = json.loads(raw.decode("utf-8"))
        if not data.get("ok") or not data.get("data", {}).get("results"):
            break

        results = data["data"]["results"]
        if not results:
            break

        for item in results:
            token = item.get("result_meta", {}).get("token", "")
            if token and token not in seen_tokens:
                seen_tokens.add(token)
                title = sanitize(item.get("title_highlighted", "") or item.get("title", ""))
                if not title:
                    title = token
                export_doc(token, os.path.join(sheets_dir, f"{title}.xlsx"), "sheet")

        page += 1


def export_bitables():
    """Export all bitables from wiki spaces"""
    print("\n=== Bitable (Multi-dimensional Tables) ===", flush=True)

    bitable_dir = os.path.join(EXPORT_ROOT, "bitable")
    os.makedirs(bitable_dir, exist_ok=True)

    raw = lark_cli_powershell("wiki", "+list", "--format", "json")
    if not raw:
        print("  Failed to list wiki spaces", flush=True)
        return

    try:
        data = json.loads(raw.decode("utf-8"))
        spaces = data.get("data", {}).get("spaces", []) if data.get("ok") else []

        for space in spaces:
            space_id = space.get("space_id")
            if not space_id:
                continue

            nodes_raw = lark_cli_powershell("wiki", "spaces", "list_nodes", "--space-id", space_id, "--format", "json")
            if not nodes_raw:
                continue
            try:
                nd = json.loads(nodes_raw.decode("utf-8"))
                nodes = nd.get("data", {}).get("nodes", []) if nd.get("ok") else []
                for node in nodes:
                    if node.get("obj_type") == "bitable":
                        token = node.get("obj_token", "")
                        title = sanitize(node.get("title", "")) or token
                        export_doc(token, os.path.join(bitable_dir, f"{title}.json"), "bitable")
            except Exception:
                pass
    except Exception:
        pass


# ============================================
# Main execution
os.chdir(EXPORT_ROOT)

print("=" * 50, flush=True)
print("  Feishu Document Export (All Types)", flush=True)
print(f"  Target: {EXPORT_ROOT}", flush=True)
print("=" * 50, flush=True)

print("\n=== Cloud Drive ===", flush=True)
process_folder("", "")

export_wiki()
export_my_docs()
export_sheets()
export_bitables()

print(f"\n{'=' * 50}", flush=True)
print(f"  Done! Total={TOTAL} Fetched={FETCHED} Skipped={SKIPPED} Failed={FAILED}", flush=True)
print(f"  {EXPORT_ROOT}", flush=True)
print("=" * 50, flush=True)
