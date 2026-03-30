# Feishu Document Export - Python version
# Fixes encoding issues by using subprocess directly

import subprocess
import json
import os
import sys
import re

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

EXPORT_ROOT = r"E:\downloads\feishu-doc-export"
TOTAL = 0; FETCHED = 0; FAILED = 0; SKIPPED = 0

NODE_SCRIPT = r"C:\Users\jonli\AppData\Roaming\npm\node_modules\@larksuite\cli\scripts\run.js"

def lark_cli(*args):
    """Call lark-cli via node directly, return stdout bytes"""
    cmd = ['node', NODE_SCRIPT] + list(args)
    proc = subprocess.run(cmd, capture_output=True)
    return proc.stdout

def lark_cli_powershell(*args):
    """Call lark-cli via PowerShell (for docs +fetch etc), return stdout bytes"""
    cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-Command',
           f"& lark-cli {' '.join(args)}"]
    proc = subprocess.run(cmd, capture_output=True)
    return proc.stdout

def lark_api(path, params=None):
    """Call lark API via node directly, return parsed JSON"""
    if params is None:
        params = {}
    params_json = json.dumps(params, separators=(',', ':'))
    # Note: path should NOT include /open-apis/ prefix - lark-cli adds it automatically
    raw = lark_cli('api', 'GET', path, '--params', params_json)
    if raw:
        try:
            return json.loads(raw.decode('utf-8'))
        except:
            return None
    return None

def sanitize(name):
    """Sanitize filename"""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, '_')
    name = name.strip()
    if len(name) > 120:
        name = name[:120]
    return name

def export_doc(token, filepath, doc_type='docx'):
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
        if doc_type == 'file':
            # lark-cli requires relative path, so we need to convert absolute path to relative
            rel_path = os.path.relpath(filepath, EXPORT_ROOT)
            raw = lark_cli_powershell('drive', '+download', '--file-token', token,
                          '--output', rel_path, '--overwrite')
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                FETCHED += 1
            else:
                FAILED += 1
        else:
            url = f"https://my.feishu.cn/docx/{token}"
            raw = lark_cli_powershell('docs', '+fetch', '--doc', url, '--format', 'json')
            if raw:
                data = json.loads(raw.decode('utf-8'))
                if data.get('ok') and data.get('data', {}).get('markdown'):
                    md = data['data']['markdown']
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(md)
                    FETCHED += 1
                else:
                    FAILED += 1
            else:
                FAILED += 1
    except Exception as e:
        FAILED += 1
        print(f"    ERROR: {e}", file=sys.stderr)

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
            params['folder_token'] = folder_token
        if page_token:
            params['page_token'] = page_token

        response = lark_api('drive/v1/files', params)
        if not response or response.get('code') != 0:
            print(f"    ERROR: Failed to list", flush=True)
            break

        files = response.get('data', {}).get('files', [])
        for f in files:
            count += 1
            ftype = f.get('type', '')
            fname = sanitize(f.get('name', ''))
            ftoken = f.get('token', '')
            shortcut = f.get('shortcut_info', {})
            base = os.path.join(EXPORT_ROOT, 'drive', relpath) if relpath else os.path.join(EXPORT_ROOT, 'drive')

            if ftype == 'folder':
                child = f"{relpath}/{fname}" if relpath else fname
                process_folder(ftoken, child)
            elif ftype in ('docx', 'doc'):
                export_doc(ftoken, os.path.join(base, f"{fname}.md"), 'docx')
            elif ftype == 'shortcut':
                tt = shortcut.get('target_type', '')
                tk = shortcut.get('target_token', '')
                if tt in ('docx', 'doc'):
                    export_doc(tk, os.path.join(base, f"{fname}.md"), 'docx')
                elif tt == 'file':
                    export_doc(tk, os.path.join(base, fname), 'file')
            elif ftype == 'file':
                export_doc(ftoken, os.path.join(base, fname), 'file')

        has_more = response.get('data', {}).get('has_more', False)
        page_token = response.get('data', {}).get('next_page_token', '')
        if not has_more or not page_token:
            break

    print(f"    -> {count} items", flush=True)

def export_wiki():
    """Export all wiki documents"""
    print("\n=== Wiki Documents ===", flush=True)

    raw = lark_cli_powershell('docs', '+search', '--format', 'json', '--page-size', '20')
    if not raw:
        print("  Search failed", flush=True)
        return

    data = json.loads(raw.decode('utf-8'))
    if not data.get('ok'):
        return

    results = data.get('data', {}).get('results', [])
    wiki_dir = os.path.join(EXPORT_ROOT, 'wiki')
    os.makedirs(wiki_dir, exist_ok=True)

    for item in results:
        if item.get('entity_type') == 'WIKI':
            token = item.get('result_meta', {}).get('token', '')
            title = sanitize(item.get('title_highlighted', ''))
            if not title:
                title = token

            # Resolve wiki node
            node_raw = lark_cli('wiki', 'spaces', 'get_node', '--params',
                               json.dumps({'token': token}, separators=(',', ':')))
            if node_raw:
                try:
                    nd = json.loads(node_raw.decode('utf-8'))
                    if nd.get('code') == 0 and nd.get('data', {}).get('node'):
                        node = nd['data']['node']
                        real_token = node.get('obj_token', '')
                        node_title = sanitize(node.get('title', '')) or title
                        export_doc(real_token, os.path.join(wiki_dir, f"{node_title}.md"), 'docx')
                        continue
                except:
                    pass

            export_doc(token, os.path.join(wiki_dir, f"{title}.md"), 'docx')

# ============================================
# Change to export root directory for relative path downloads
os.chdir(EXPORT_ROOT)

print("=" * 50, flush=True)
print("  Feishu Document Export", flush=True)
print(f"  Target: {EXPORT_ROOT}", flush=True)
print("=" * 50, flush=True)

print("\n=== Drive Documents ===", flush=True)
process_folder('', '')

export_wiki()

print(f"\n{'=' * 50}", flush=True)
print(f"  Done! Total={TOTAL} Fetched={FETCHED} Skipped={SKIPPED} Failed={FAILED}", flush=True)
print(f"  {EXPORT_ROOT}", flush=True)
print("=" * 50, flush=True)
