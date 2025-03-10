import json
import markdown2
import sys
import os
import argparse
import html

STATS_FINAL_FILENAME = 'stats_final.json'
REPODOC_FOLDER = '.repodoc'

# 引数パーサーを設定
parser = argparse.ArgumentParser(description='Generate a repository analysis report.')
parser.add_argument('analysis_path_file', nargs='?', help='File containing the analysis path')
parser.add_argument('-o', '--output', help='Output file path for the report', default=None)
args = parser.parse_args()

# 指定されたファイルから解析パスを読み取るか、ユーザーに入力を促す
if args.analysis_path_file:
    with open(os.path.abspath(args.analysis_path_file), 'r', encoding='utf-8') as f:
        analysis_path = f.read().strip()
else:
    analysis_path = input("Enter the analysis path: ").strip()
    analysis_path = os.path.abspath(analysis_path)

stats_final_filename = os.path.join(analysis_path, REPODOC_FOLDER, STATS_FINAL_FILENAME)

# stats_final.jsonファイルを読み込む
with open(stats_final_filename, 'r', encoding='utf-8') as f:
    data = json.load(f)

# HTMLコンテンツを生成
html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>リポジトリ解析レポート</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .not-analyzed {{ color: #999; }}
        .directory {{ background-color: #a4a4ff; }}
        .file-name {{ width: 15%; font-size: 1.2em; }}
        .file-type {{ width: 15%; }}
        .description {{ width: 50%; font-size:0.9em;}}
        .references {{ width: 10%; }}
        .entry-points {{ width: 10%; }}
    </style>
</head>
<body>
    <h1>リポジトリ解析レポート</h1>
    <h2>フォルダ: {html.escape(data['folder_name'])}</h2>
    <p>ファイル数: {data['num_files']}</p>
    <p>ディレクトリ数: {data['num_dirs']}</p>
    <p>合計サイズ: {data['total_size']} bytes</p>
"""

for folder in data['structure']:
    if folder[2]:  # ファイルが存在するフォルダのみ表示
        escaped_folder_name = html.escape(folder[0])
        html_content += f"""
        <h2 class="directory">ディレクトリ: {escaped_folder_name}</h2>
        <table>
            <thead>
                <tr>
                    <th class="file-name">ファイル名</th>
                    <th class="file-type">ファイルタイプ</th>
                    <th class="description">説明</th>
                    <th class="references">参照</th>
                    <th class="entry-points">エントリポイント</th>
                </tr>
            </thead>
            <tbody>
        """
        for file, analysis in zip(folder[2], folder[3]):
            escaped_file = html.escape(file)
            if isinstance(analysis, dict):
                escaped_desc = html.escape(analysis['description'])
                description_html = markdown2.markdown(escaped_desc)
                escaped_file_type = html.escape(analysis['file_type'])
                references_str = ', '.join(html.escape(r) for r in analysis['references'])
                entry_points_str = ', '.join(html.escape(e) for e in analysis['entry_points'])
                html_content += f"""
                <tr>
                    <td class="file-name">{escaped_file}</td>
                    <td class="file-type">{escaped_file_type}</td>
                    <td class="description">{description_html}</td>
                    <td class="references">{references_str}</td>
                    <td class="entry-points">{entry_points_str}</td>
                </tr>
                """
            else:
                html_content += f"""
                <tr>
                    <td class="file-name">{escaped_file}</td>
                    <td colspan="4" class="not-analyzed">解析されていません</td>
                </tr>
                """
        html_content += """
            </tbody>
        </table>
        """

html_content += """
</body>
</html>
"""

# 出力ファイルパスを決定
if args.output:
    output_html_filename = args.output
else:
    output_html_filename = os.path.join(analysis_path, 'repodoc-report.html')

# HTMLファイルに書き出し
with open(output_html_filename, "w", encoding="utf-8") as f:
    f.write(html_content)