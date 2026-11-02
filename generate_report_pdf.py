#!/usr/bin/env python3
"""
Script to generate a high-quality academic PDF report from LAPORAN_TUGAS_INTEGRASI.md
Uses markdown_it, clean Mermaid SVG injection, and Google Chrome headless.
"""

import os
import re
import base64
import subprocess
from markdown_it import MarkdownIt

def build_html_report(md_content):
    # Load UMI logo as base64 data URI
    logo_path = "/home/ichwal/Documents/tugas-project/logo_umi.png"
    logo_base64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
            logo_base64 = f"data:image/png;base64,{b64_str}"

    # For report body, start from DAFTAR ISI so the cover is not duplicated on page 2
    if "## DAFTAR ISI" in md_content:
        body_content = md_content[md_content.index("## DAFTAR ISI"):]
    else:
        body_content = md_content

    # Extract mermaid blocks cleanly using alphanumeric placeholders (no underscores)
    mermaid_blocks = []
    def mermaid_replacer(match):
        idx = len(mermaid_blocks)
        code = match.group(1).strip()
        mermaid_blocks.append(code)
        return f"\n\nMERMAIDTOKENXYZ{idx}\n\n"

    processed_md = re.sub(r"```mermaid\n(.*?)\n```", mermaid_replacer, body_content, flags=re.DOTALL)
    
    # Render Markdown to HTML
    md = MarkdownIt("commonmark").enable("table")
    html_body = md.render(processed_md)
    
    # Re-inject Mermaid divs cleanly
    for i, code in enumerate(mermaid_blocks):
        clean_mermaid_div = (
            f'<div class="mermaid-container">\n'
            f'  <div class="mermaid">\n{code}\n  </div>\n'
            f'</div>'
        )
        html_body = html_body.replace(f"<p>MERMAIDTOKENXYZ{i}</p>", clean_mermaid_div)
        html_body = html_body.replace(f"MERMAIDTOKENXYZ{i}", clean_mermaid_div)

    # Full HTML Document Template
    html_doc = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>Laporan Tugas Integrasi Sistem - Ichwal (13020230049)</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'neutral',
      fontFamily: '"Times New Roman", Times, "Liberation Serif", serif',
      fontSize: 12,
      flowchart: {{ htmlLabels: true, curve: 'basis' }},
      sequence: {{ mirrorActors: false }}
    }});
  </script>
  <style>
    @page {{
      size: A4;
      margin: 20mm 20mm 25mm 20mm;
      @bottom-center {{
        content: counter(page);
        font-family: 'Times New Roman', Times, 'Liberation Serif', serif;
        font-size: 10pt;
        color: #64748b;
      }}
    }}
    
    body {{
      font-family: 'Times New Roman', Times, 'Liberation Serif', serif;
      font-size: 12pt;
      line-height: 1.5;
      color: #1e293b;
      background-color: #ffffff;
      margin: 0;
      padding: 0;
    }}

    /* Cover Page Styling */
    .cover-page {{
      height: 94vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
      text-align: center;
      page-break-after: always;
      padding: 10px 10px 15px 10px;
      box-sizing: border-box;
      font-family: 'Times New Roman', Times, 'Liberation Serif', serif;
    }}
    .cover-header {{
      margin-top: 5px;
    }}
    .cover-inst {{
      font-size: 16pt;
      font-weight: 700;
      letter-spacing: 1px;
      color: #0f172a;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .cover-dept {{
      font-size: 12pt;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #1e3a8a;
      text-transform: uppercase;
    }}
    .cover-logo-box {{
      margin: 12px 0 8px 0;
    }}
    .cover-logo {{
      width: 120px;
      height: auto;
      object-fit: contain;
    }}
    .cover-title-box {{
      margin: 10px 0;
      padding: 15px 20px;
      border-top: 3px solid #1e3a8a;
      border-bottom: 3px solid #1e3a8a;
      max-width: 92%;
    }}
    .cover-type {{
      font-size: 12pt;
      font-weight: 700;
      color: #475569;
      letter-spacing: 1.5px;
      margin-bottom: 8px;
      text-transform: uppercase;
    }}
    .cover-title {{
      font-size: 13.5pt;
      font-weight: 700;
      line-height: 1.35;
      color: #0f172a;
      text-transform: uppercase;
    }}
    .cover-author-box {{
      margin: 8px 0 12px 0;
      background: #f8fafc;
      padding: 12px 30px;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      width: 82%;
      max-width: 520px;
    }}
    .cover-author-table {{
      margin: 0 auto;
      width: 100%;
      text-align: left;
      font-size: 11pt;
      font-family: 'Times New Roman', Times, 'Liberation Serif', serif;
    }}
    .cover-author-table td {{
      padding: 3px 8px;
    }}
    .cover-footer {{
      margin-bottom: 10px;
      font-size: 11pt;
      font-weight: 700;
      color: #334155;
      letter-spacing: 1px;
    }}

    /* Main Content Headings */
    h1, h2, h3, h4 {{
      font-family: 'Times New Roman', Times, 'Liberation Serif', serif;
      color: #0f172a;
      font-weight: 700;
      margin-top: 22pt;
      margin-bottom: 10pt;
      page-break-after: avoid;
    }}

    h1 {{
      font-size: 16pt;
      border-bottom: 2px solid #1e293b;
      padding-bottom: 6px;
    }}

    h2 {{
      font-size: 13.5pt;
      color: #1e3a8a;
      border-bottom: 1px solid #cbd5e1;
      padding-bottom: 4px;
      margin-top: 24pt;
    }}

    h3 {{
      font-size: 12pt;
      color: #1e293b;
      margin-top: 16pt;
    }}

    h4 {{
      font-size: 11.5pt;
      color: #334155;
    }}

    p {{
      margin-top: 0;
      margin-bottom: 10pt;
      text-align: justify;
      text-justify: inter-word;
    }}

    ul, ol {{
      margin-top: 0;
      margin-bottom: 10pt;
      padding-left: 24px;
      text-align: justify;
    }}

    li {{
      margin-bottom: 4pt;
    }}

    blockquote {{
      margin: 12pt 0;
      padding: 10pt 16pt;
      background: #f1f5f9;
      border-left: 4px solid #2563eb;
      border-radius: 4px;
      font-style: italic;
      color: #334155;
      font-family: 'Times New Roman', Times, 'Liberation Serif', serif;
    }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16pt 0;
      font-size: 10pt;
      font-family: 'Times New Roman', Times, 'Liberation Serif', serif;
      page-break-inside: avoid;
    }}

    th, td {{
      padding: 8px 10px;
      border: 1px solid #cbd5e1;
      text-align: left;
    }}

    th {{
      background-color: #f1f5f9;
      color: #0f172a;
      font-weight: 600;
    }}

    tr:nth-child(even) {{
      background-color: #f8fafc;
    }}

    /* Code Blocks */
    pre {{
      background-color: #0f172a;
      color: #f8fafc;
      padding: 12px 16px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
      font-size: 8.5pt;
      line-height: 1.45;
      overflow-x: auto;
      page-break-inside: avoid;
      margin: 12pt 0;
    }}

    code {{
      font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
      font-size: 8.5pt;
      background-color: #f1f5f9;
      color: #0369a1;
      padding: 2px 4px;
      border-radius: 4px;
    }}

    pre code {{
      background-color: transparent;
      color: inherit;
      padding: 0;
    }}

    /* Mermaid Diagrams */
    .mermaid-container {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 16px;
      margin: 16pt 0;
      text-align: center;
      page-break-inside: avoid;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}

    .mermaid svg {{
      max-width: 100% !important;
      height: auto !important;
      margin: 0 auto;
    }}

    hr {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 20pt 0;
    }}
  </style>
</head>
<body>

  <!-- Halaman Sampul Formal -->
  <div class="cover-page">
    <div class="cover-header">
      <div class="cover-inst">UNIVERSITAS MUSLIM INDONESIA</div>
      <div class="cover-dept">FAKULTAS ILMU KOMPUTER &bull; TEKNIK INFORMATIKA</div>
    </div>

    <div class="cover-logo-box">
      <img src="{logo_base64}" alt="Logo UMI" class="cover-logo" />
    </div>

    <div class="cover-title-box">
      <div class="cover-type">LAPORAN TUGAS BESAR CLOUD COMPUTING (KELAS C3)</div>
      <div class="cover-title">
        IMPLEMENTASI OTOMASI MANAJEMEN KONTEN BERBASIS AUTONOMOUS AI AGENT DENGAN MENGINTEGRASIKAN WORDPRESS, HERMES AGENT, DAN 9ROUTER MENGGUNAKAN DOCKER DAN TELEGRAM BOT
      </div>
    </div>

    <div class="cover-author-box">
      <table class="cover-author-table">
        <tr>
          <td><strong>Nama Mahasiswa</strong></td>
          <td>:</td>
          <td><strong>Ichwal</strong></td>
        </tr>
        <tr>
          <td><strong>Stambuk / NIM</strong></td>
          <td>:</td>
          <td><strong>13020230049</strong></td>
        </tr>
        <tr>
          <td><strong>Program Studi</strong></td>
          <td>:</td>
          <td>Teknik Informatika / Ilmu Komputer</td>
        </tr>
        <tr>
          <td><strong>Mata Kuliah</strong></td>
          <td>:</td>
          <td><strong>Cloud Computing (Kelas C3)</strong></td>
        </tr>
        <tr>
          <td><strong>Repository GitHub</strong></td>
          <td>:</td>
          <td><a href="https://github.com/ichwalM/OTOMASI-MANAJEMEN-KONTEN" style="color: #2563eb; text-decoration: none; font-weight: 600;">github.com/ichwalM/OTOMASI-MANAJEMEN-KONTEN</a></td>
        </tr>
      </table>
    </div>

    <div class="cover-footer">
      MAKASSAR<br>
      TAHUN 2026 / 2027
    </div>
  </div>

  <!-- Konten Utama Laporan -->
  <div class="report-body">
    {html_body}
  </div>

</body>
</html>
"""
    return html_doc

def main():
    base_dir = "/home/ichwal/Documents/tugas-project"
    md_file = os.path.join(base_dir, "LAPORAN_TUGAS_INTEGRASI.md")
    html_file = os.path.join(base_dir, "Laporan_Integrasi_Ichwal_13020230049.html")
    pdf_file = os.path.join(base_dir, "Laporan_Integrasi_Ichwal_13020230049.pdf")

    print(f"[1/3] Membaca berkas markdown: {md_file}...")
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("[2/3] Mengonversi Markdown ke format HTML Akademik...")
    html_content = build_html_report(md_text)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"      HTML tersimpan di: {html_file}")

    print(f"[3/3] Merender PDF menggunakan Google Chrome Headless...")
    cmd = [
        "google-chrome",
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--virtual-time-budget=8000",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_file}",
        html_file
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(pdf_file):
        size_kb = os.path.getsize(pdf_file) / 1024
        print(f"\n[SUKSES] Berkas PDF Berhasil Dibuat!")
        print(f"Lokasi PDF: {pdf_file} ({size_kb:.1f} KB)")
    else:
        print(f"[ERROR] Gagal merender PDF:\n{res.stderr}")

if __name__ == "__main__":
    main()
