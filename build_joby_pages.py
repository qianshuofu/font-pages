#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 JOBY 下所有 CSV，生成统一 HTML（ticker + date 选择器，前 0 条为构造数据）。"""

import csv
import json
import os
import re
import html

JOBY_DIR = os.path.join(os.path.dirname(__file__), "JOBY")
CONSTRUCTED_COUNT = 0  # 前 N 条为构造数据，其余为真实数据


def escape(s):
    if s is None or s == "":
        return ""
    return html.escape(str(s).strip())


def parse_id(raw):
    if raw is None or raw == "":
        return None
    s = str(raw).strip()
    if s in ("-1", ""):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_hit_id_true(raw):
    if raw is None or raw == "":
        return None
    s = str(raw).strip()
    if s in ("-1", ""):
        return None
    try:
        return int(s)
    except ValueError:
        return s


def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r, None)
        for row in r:
            if len(row) < 7:
                continue
            idx = row[0].strip() if row[0] else ""
            text_clean = (row[1] or "").strip()
            hit_id_true = parse_hit_id_true(row[2])
            id_val = parse_id(row[3])
            indictor_name = (row[4] or "").strip()
            condition = (row[5] or "").strip()
            reason = (row[6] or "").strip()
            rows.append({
                "idx": idx,
                "text_clean": text_clean,
                "hit_id_true": hit_id_true,
                "id": id_val,
                "indictor_name": indictor_name,
                "condition": condition,
                "reason": reason,
            })
    return rows


def collect_joby_data():
    data = {}
    for name in sorted(os.listdir(JOBY_DIR)):
        if not name.endswith(".csv") or "_JOBY" not in name:
            continue
        m = re.match(r"(\d{8})_JOBY\.csv", name)
        if not m:
            continue
        date_key = m.group(1)
        path = os.path.join(JOBY_DIR, name)
        data[date_key] = load_csv(path)
    return data


def build_html():
    joby = collect_joby_data()
    if not joby:
        raise SystemExit("未找到 JOBY/*_JOBY.csv 文件")

    dates = sorted(joby.keys())
    data_json = json.dumps({"JOBY": joby}, ensure_ascii=False)
    # 避免嵌入的 </script> 提前关闭 script 标签
    data_json = re.sub(r"</[sS][cC][rR][iI][pP][tT]>", r"<\\/script>", data_json)

    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>JOBY 指标命中分析 - 多日期</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
      line-height: 1.6;
      min-height: 100vh;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      padding: 30px;
    }
    h1 {
      color: #333;
      text-align: center;
      margin-bottom: 24px;
      font-size: 1.9em;
      border-bottom: 3px solid #667eea;
      padding-bottom: 12px;
    }
    .subtitle {
      text-align: center;
      color: #666;
      margin-bottom: 24px;
      font-size: 0.95em;
    }
    .selectors {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      align-items: center;
      margin-bottom: 24px;
      padding: 16px 20px;
      background: #f0f4ff;
      border-radius: 8px;
      border: 1px solid #c5d4f7;
    }
    .selectors label { font-weight: 600; color: #444; }
    .selectors select {
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid #ccc;
      font-size: 1em;
      min-width: 140px;
    }
    .stats {
      background: #e9ecef;
      padding: 16px 20px;
      border-radius: 8px;
      margin-bottom: 28px;
      display: flex;
      justify-content: space-around;
      flex-wrap: wrap;
      gap: 16px;
    }
    .stat-item { text-align: center; }
    .stat-value { font-size: 1.6em; font-weight: bold; color: #667eea; }
    .stat-label { color: #666; font-size: 0.9em; }

    .item {
      margin-bottom: 26px;
      padding: 18px 18px 20px;
      border-left: 4px solid #667eea;
      background: #f8f9fa;
      border-radius: 8px;
      transition: transform .15s, box-shadow .15s;
    }
    .item:hover {
      transform: translateX(4px);
      box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    }
    .item-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      gap: 10px;
      flex-wrap: wrap;
    }
    .item-number { font-size: 1.1em; font-weight: 600; color: #667eea; }
    .data-type {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 14px;
      font-size: 0.85em;
      font-weight: 600;
    }
    .data-type.constructed { background: #ffc107; color: #654d03; }
    .data-type.real { background: #28a745; color: #fff; }

    .text-content {
      background: #fff;
      padding: 12px 14px;
      border-radius: 6px;
      border: 1px solid #e0e0e0;
      margin-bottom: 12px;
      font-size: 0.98em;
      color: #333;
      white-space: pre-wrap;
      word-wrap: break-word;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 12px;
      margin-top: 8px;
    }
    .info-item {
      background: #fff;
      padding: 10px 12px;
      border-radius: 6px;
      border: 1px solid #e0e0e0;
    }
    .info-label {
      font-weight: 600;
      color: #555;
      font-size: 0.86em;
      margin-bottom: 4px;
    }
    .info-value { color: #333; font-size: 0.9em; word-break: break-word; }

    .status-badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.8em;
      font-weight: 700;
      vertical-align: middle;
    }
    .status-badge.bull { background: #d4edda; color: #155724; }
    .status-badge.bear { background: #f8d7da; color: #721c24; }
    .status-badge.empty { background: #e2e3e5; color: #383d41; }
    .ai-id { font-weight: 600; margin-right: 6px; }

    .indicator-name { font-weight: 500; }
    .indicator-condition { font-style: italic; color: #555; }

    .reason {
      background: #f0f0f0;
      padding: 10px 12px;
      border-radius: 6px;
      margin-top: 10px;
      color: #444;
      border-left: 3px solid #667eea;
      font-size: 0.9em;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .empty-state {
      text-align: center;
      color: #666;
      padding: 48px 24px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>JOBY 指标命中分析</h1>
    <div class="subtitle">来源：JOBY 文件夹 CSV · 选择 Ticker 与日期进入该具体页面（前 ''' + str(CONSTRUCTED_COUNT) + ''' 条为构造数据，其余为真实数据）</div>

    <div class="selectors">
      <label for="ticker">Ticker</label>
      <select id="ticker">
        <option value="JOBY">JOBY</option>
      </select>
      <label for="date">Date</label>
      <select id="date">
''' + "\n".join(
        '        <option value="' + d + '">' + d + '</option>' for d in dates
    ) + '''
      </select>
    </div>

    <div id="stats" class="stats"></div>
    <div id="items"></div>
  </div>

  <script>
    const CONSTRUCTED = ''' + str(CONSTRUCTED_COUNT) + ''';
    const DATA = ''' + data_json + ''';

    function esc(s) {
      if (s == null || s === "") return "";
      const d = document.createElement("div");
      d.textContent = s;
      return d.innerHTML;
    }

    function hitLabel(id) {
      if (id == null) return "未命中";
      const n = parseInt(id, 10);
      if (n >= 1 && n <= 5) return "BULL";
      if (n >= 6 && n <= 10) return "BEAR";
      return "未命中";
    }

    function hitClass(id) {
      if (id == null) return "empty";
      const n = parseInt(id, 10);
      if (n >= 1 && n <= 5) return "bull";
      if (n >= 6 && n <= 10) return "bear";
      return "empty";
    }

    function hitIdTrueDisplay(r, i) {
      const isConstructed = i < CONSTRUCTED;
      if (isConstructed) return r.hit_id_true != null ? String(r.hit_id_true) : "无";
      if (r.id != null) return r.hit_id_true != null ? String(r.hit_id_true) : "无";
      return "无";
    }

    function renderItem(r, i) {
      const isConstructed = i < CONSTRUCTED;
      const typeClass = isConstructed ? "constructed" : "real";
      const typeLabel = isConstructed ? "构造数据" : "真实数据";
      const noHit = r.id == null;
      const hitTrue = hitIdTrueDisplay(r, i);

      let aiBlock = "";
      if (noHit) {
        aiBlock = '<span class="status-badge empty">未命中</span>';
      } else {
        const label = hitLabel(r.id);
        const cls = hitClass(r.id);
        aiBlock = '<span class="ai-id">' + esc(String(r.id)) + '</span> <span class="status-badge ' + cls + '">' + label + '</span>';
      }
      const indName = noHit ? "无" : (r.indictor_name || "无");
      const cond = noHit ? "无" : (r.condition || "无");

      return (
        '<div class="item">' +
          '<div class="item-header">' +
            '<span class="item-number">记录 #' + i + '</span>' +
            '<span class="data-type ' + typeClass + '">' + typeLabel + '</span>' +
          '</div>' +
          '<div class="text-content">' + esc(r.text_clean || "") + '</div>' +
          '<div class="info-grid">' +
            '<div class="info-item"><div class="info-label">构造命中ID (hit_id_true)</div><div class="info-value">' + esc(hitTrue) + '</div></div>' +
            '<div class="info-item"><div class="info-label">AI 命中ID (id)</div><div class="info-value">' + aiBlock + '</div></div>' +
            '<div class="info-item"><div class="info-label">AI 指标名称</div><div class="info-value indicator-name">' + esc(indName) + '</div></div>' +
            '<div class="info-item"><div class="info-label">AI 指标触发条件</div><div class="info-value indicator-condition">' + esc(cond) + '</div></div>' +
          '</div>' +
          '<div class="reason"><strong>原因：</strong><br>' + esc(r.reason || "") + '</div>' +
        '</div>'
      );
    }

    function update() {
      const ticker = document.getElementById("ticker").value;
      const date = document.getElementById("date").value;
      const list = (DATA[ticker] && DATA[ticker][date]) || [];

      const constructed = Math.min(CONSTRUCTED, list.length);
      const real = list.length - constructed;
      let hitCount = 0;
      for (let i = 0; i < list.length; i++) {
        const r = list[i];
        if (r.id != null && r.id >= 1 && r.id <= 10) hitCount++;
      }

      const statsEl = document.getElementById("stats");
      statsEl.innerHTML =
        '<div class="stat-item"><div class="stat-value">' + list.length + '</div><div class="stat-label">总记录数</div></div>' +
        '<div class="stat-item"><div class="stat-value">' + constructed + '</div><div class="stat-label">构造数据</div></div>' +
        '<div class="stat-item"><div class="stat-value">' + real + '</div><div class="stat-label">真实数据</div></div>' +
        '<div class="stat-item"><div class="stat-value">' + hitCount + '</div><div class="stat-label">AI 命中 (id ∈ [1,10])</div></div>';

      const itemsEl = document.getElementById("items");
      if (list.length === 0) {
        itemsEl.innerHTML = '<div class="empty-state">该日期无数据</div>';
        return;
      }
      itemsEl.innerHTML = list.map((r, i) => renderItem(r, i)).join("");
    }

    function applyHash() {
      const h = (location.hash || "").slice(1);
      const m = /^([A-Z]+)\\/(\\d{8})$/.exec(h);
      if (!m) return;
      const t = document.getElementById("ticker"), d = document.getElementById("date");
      if (DATA[m[1]] && DATA[m[1]][m[2]]) {
        t.value = m[1];
        d.value = m[2];
      }
    }

    document.getElementById("ticker").addEventListener("change", function() {
      update();
      location.hash = document.getElementById("ticker").value + "/" + document.getElementById("date").value;
    });
    document.getElementById("date").addEventListener("change", function() {
      update();
      location.hash = document.getElementById("ticker").value + "/" + document.getElementById("date").value;
    });
    window.addEventListener("hashchange", applyHash);
    applyHash();
    update();
  </script>
</body>
</html>
'''
    return html_content


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "JOBY_index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_html())
    print("已生成:", out)
