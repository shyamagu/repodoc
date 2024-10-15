import json
import markdown2

# stats_final.jsonファイルをロード
with open('stats_final.json', 'r', encoding='utf-8') as f:
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
        .direcotry {{ background-color: #a4a4ff; }}
        .file-name {{ width: 15%; font-size: 1.2em; }}
        .file-type {{ width: 15%; }}
        .description {{ width: 50%; font-size:0.9em;}}
        .references {{ width: 10%; }}
        .entry-points {{ width: 10%; }}
    </style>
</head>
<body>
    <h1>リポジトリ解析レポート</h1>
    <h2>フォルダ: {data['folder_name']}</h2>
    <p>ファイル数: {data['num_files']}</p>
    <p>ディレクトリ数: {data['num_dirs']}</p>
    <p>合計サイズ: {data['total_size']} bytes</p>
"""

for folder in data['structure']:
    if folder[2]:  # ファイルが存在するフォルダのみ表示
        html_content += f"""
        <h2 class="direcotry" >ディレクトリ: {folder[0]}</h2>
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
            if analysis != "NOT_ANALYZED":
                description_html = markdown2.markdown(analysis['description'])
                html_content += f"""
                <tr>
                    <td class="file-name">{file}</td>
                    <td class="file-type">{analysis['file_type']}</td>
                    <td class="description">{description_html}</td>
                    <td class="references">{', '.join(analysis['references'])}</td>
                    <td class="entry-points">{', '.join(analysis['entry_points'])}</td>
                </tr>
                """
            else:
                html_content += f"""
                <tr>
                    <td class="file-name">{file}</td>
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

# HTMLファイルに書き出し
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html_content)