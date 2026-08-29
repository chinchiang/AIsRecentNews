#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIsRecentNews 自動化格式與安全驗證腳本
用於檢核 latest-snapshot.yaml 與 HTML 週報檔案的格式、Schema 與安全性。
支援零依賴（純 Python 標準函式庫）或搭配 PyYAML 執行。
"""

import sys
import os
import re
from pathlib import Path

# 設定 stdout 編碼為 utf-8 避免 Windows CP950 編碼錯誤
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent

# 驗證規則定義
VALID_TRACKS = {'A', 'B', 'C', 'D'}
VALID_EVIDENCES = {'已證實', '廠商主張', '第三方評論', '尚未證實'}
VALID_STATUSES = {'active', 'new', 'retired'}
DANGEROUS_HTML_PATTERNS = [
    re.compile(r'<\s*script\b', re.IGNORECASE),
    re.compile(r'<\s*iframe\b', re.IGNORECASE),
    re.compile(r'<\s*object\b', re.IGNORECASE),
    re.compile(r'<\s*embed\b', re.IGNORECASE),
    re.compile(r'href\s*=\s*["\']\s*javascript:', re.IGNORECASE),
    re.compile(r'href\s*=\s*["\']\s*data:', re.IGNORECASE),
    re.compile(r'\son[a-z]+\s*=', re.IGNORECASE),  # onload=, onerror=, onclick= 等
]

def parse_yaml_fallback(content: str) -> dict:
    """純 Python 標準函式庫之簡易 YAML 解析器（適用於 snapshot YAML 結構）"""
    data = {"targets": []}
    current_target = None
    
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
            
        # 頂層 key-value
        if not line.startswith(' ') and ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip().strip('"\'')
            if key in ('period_end', 'week_id'):
                data[key] = val
            elif key == 'targets':
                continue
        # targets 陣列項目起點
        elif stripped.startswith('- id:'):
            val = stripped.split(':', 1)[1].strip().strip('"\'')
            current_target = {'id': val}
            data['targets'].append(current_target)
        # target 內部屬性
        elif current_target is not None and ':' in stripped:
            key, val = stripped.split(':', 1)
            key = key.strip()
            val = val.strip()
            if val.lower() == 'true':
                val_parsed = True
            elif val.lower() == 'false':
                val_parsed = False
            else:
                val_parsed = val.strip('"\'')
            current_target[key] = val_parsed
            
    return data

def load_yaml(file_path: Path) -> dict:
    content = file_path.read_text(encoding='utf-8')
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        return parse_yaml_fallback(content)

def validate_snapshot(yaml_path: Path) -> list:
    errors = []
    if not yaml_path.exists():
        return [f"找不到快照檔案: {yaml_path}"]
        
    try:
        data = load_yaml(yaml_path)
    except Exception as e:
        return [f"YAML 解析失敗: {e}"]
        
    if not isinstance(data, dict):
        return ["快照 YAML 根結構必須為 Mapping 物件"]
        
    # 檢查頂層欄位
    period_end = data.get('period_end')
    week_id = data.get('week_id')
    targets = data.get('targets')
    
    if not period_end or not re.match(r'^\d{4}-\d{2}-\d{2}$', str(period_end)):
        errors.append(f"period_end 格式無效 (應為 YYYY-MM-DD): '{period_end}'")
        
    if not week_id or not re.match(r'^\d{4}-W\d{2}$', str(week_id)):
        errors.append(f"week_id 格式無效 (應為 YYYY-Www): '{week_id}'")
        
    if not isinstance(targets, list) or len(targets) == 0:
        errors.append("targets 必須為非空陣列")
        return errors
        
    seen_ids = set()
    for idx, target in enumerate(targets):
        t_id = target.get('id')
        prefix = f"target[{idx}] (id: {t_id})"
        
        if not t_id or not isinstance(t_id, str):
            errors.append(f"{prefix}: 缺少合法 id")
            continue
            
        if not re.match(r'^[a-z0-9-]+$', t_id):
            errors.append(f"{prefix}: id 格式應為全小寫與連字號 ('{t_id}')")
            
        if t_id in seen_ids:
            errors.append(f"{prefix}: 重複的 target id '{t_id}'")
        seen_ids.add(t_id)
        
        track = target.get('track')
        if track not in VALID_TRACKS:
            errors.append(f"{prefix}: track 無效 ('{track}'，必須為 A, B, C, D 之一)")
            
        state = target.get('state')
        if not state or not str(state).strip():
            errors.append(f"{prefix}: state 欄位不可為空")
            
        evidence = target.get('evidence')
        if evidence not in VALID_EVIDENCES:
            errors.append(f"{prefix}: evidence 無效 ('{evidence}'，必須為 {VALID_EVIDENCES} 之一)")
            
        source_date = target.get('source_date')
        if not source_date or not re.match(r'^\d{4}(-\d{2})?(-\d{2})?$', str(source_date)):
            errors.append(f"{prefix}: source_date 格式不符: '{source_date}'")
            
        status = target.get('status')
        if status not in VALID_STATUSES:
            errors.append(f"{prefix}: status 無效 ('{status}'，必須為 {VALID_STATUSES} 之一)")
            
        carried_over = target.get('carried_over')
        if not isinstance(carried_over, bool):
            errors.append(f"{prefix}: carried_over 必須為布林值 (true/false)")
            
    return errors

def validate_html(html_path: Path) -> list:
    errors = []
    try:
        content = html_path.read_text(encoding='utf-8')
    except Exception as e:
        return [f"無法讀取 HTML 檔案 {html_path}: {e}"]
        
    rel_path = html_path.relative_to(ROOT_DIR)
    
    # 檢查 CSP
    if 'http-equiv="Content-Security-Policy"' not in content and "http-equiv='Content-Security-Policy'" not in content:
        errors.append(f"{rel_path}: 缺少 Content-Security-Policy (CSP) meta 標籤")
        
    # 檢查基本 HTML5 標籤宣告
    if '<html lang="zh-Hant">' not in content:
        errors.append(f"{rel_path}: 缺少或未正確設定 <html lang=\"zh-Hant\">")
        
    if 'charset="utf-8"' not in content and "charset='utf-8'" not in content:
        errors.append(f"{rel_path}: 缺少 <meta charset=\"utf-8\">")
        
    # 檢查危險語法與 XSS 風險模式
    for pattern in DANGEROUS_HTML_PATTERNS:
        match = pattern.search(content)
        if match:
            errors.append(f"{rel_path}: 偵測到潛在危險 HTML 語法或偽協定: '{match.group(0)}'")
            
    return errors

def main():
    print("=" * 60)
    print("[INFO] 開始執行 AIsRecentNews 格式與安全驗證")
    print("=" * 60)
    
    total_errors = 0
    
    # 1. 驗證 latest-snapshot.yaml
    snapshot_path = ROOT_DIR / "latest-snapshot.yaml"
    print(f"\n[1/3] 檢驗快照檔案: {snapshot_path.name}")
    snapshot_errors = validate_snapshot(snapshot_path)
    if snapshot_errors:
        for err in snapshot_errors:
            print(f"  [FAIL] {err}")
        total_errors += len(snapshot_errors)
    else:
        print("  [PASS] 快照 Schema 與資料完整性檢查通過")
        
    # 2. 驗證 index.html
    index_path = ROOT_DIR / "index.html"
    print(f"\n[2/3] 檢驗首頁: {index_path.name}")
    index_errors = validate_html(index_path)
    if index_errors:
        for err in index_errors:
            print(f"  [FAIL] {err}")
        total_errors += len(index_errors)
    else:
        print("  [PASS] 首頁安全性與標籤檢查通過")
        
    # 3. 驗證 reports/*.html
    reports = list(ROOT_DIR.glob("reports/*.html"))
    print(f"\n[3/3] 檢驗各期週報頁面 ({len(reports)} 個檔案)")
    for report in reports:
        report_errors = validate_html(report)
        if report_errors:
            for err in report_errors:
                print(f"  [FAIL] {err}")
            total_errors += len(report_errors)
        else:
            print(f"  [PASS] {report.name} 通過安全與 CSP 檢查")
            
    print("\n" + "=" * 60)
    if total_errors == 0:
        print("[SUCCESS] 全部檢查通過！無任何格式或安全違規。")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"[WARNING] 檢查發現 {total_errors} 個錯誤，請修復後再行發布。")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    main()
