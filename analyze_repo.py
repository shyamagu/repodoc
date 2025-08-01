import os
import fnmatch
import json
import time
import sys
from pydantic import BaseModel
from openai_utils import get_parsed_completion, get_token_count, estimate_cost_for_gpt4o_0806

STATS_FINAL_FILENAME = 'stats_final.json'
STATS_INTERMEDIATE_FILENAME = 'stats_intermediate.json'
IGNORE_FILENAME = '.repodocignore'
REPODOC_FOLDER = '.repodoc'

class FileContent(BaseModel):
    type: str
    file_type: str
    description: str
    references: list[str]
    entry_points: list[str]

def read_repodocignore_setting(folder_path):
    """
    Reads the .repodocignore file in the specified folder and returns a list of patterns to ignore.
    """

    repodocignore_path = os.path.join(folder_path, REPODOC_FOLDER, IGNORE_FILENAME)
    patterns = []
    if os.path.exists(repodocignore_path):
        with open(repodocignore_path, 'r') as file:
            patterns = [line.strip() for line in file if line.strip() and not line.startswith('#')]

    return patterns

def read_gitignore_setting(folder_path):
    """
    Reads the .gitignore file in the specified folder and returns a list of patterns to ignore.
    """

    gitignore_path = os.path.join(folder_path, '.gitignore')
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as file:
            patterns = [line.strip() for line in file if line.strip() and not line.startswith('#')]

    # Add patterns for files starting with a dot and containing "ignore"
    patterns.append('.*ignore*')
    return patterns

def should_ignore(path, patterns):
    """
    Checks if the given path matches any of the ignore patterns.
    """

    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def analyze_folder(folder_path):
    """
    Analyzes the folder structure, counting the number of files and directories,
    and calculating the total size of files.
    """

    # Initialize counters, total size, and structure
    num_files = 0
    num_dirs = 0
    total_size = 0
    structure = []

    global_ignore_patterns = read_repodocignore_setting(folder_path)

    # Walk through the directory
    for root, dirs, files in os.walk(folder_path):
        # Read .gitignore patterns for the current directory
        ignore_patterns = read_gitignore_setting(root)

        # Combine global and local ignore patterns
        ignore_patterns += global_ignore_patterns

        # Filter out directories and files based on .gitignore patterns
        filtered_dirs = [d for d in dirs if not should_ignore(os.path.relpath(os.path.join(root, d), root), ignore_patterns)]
        filtered_files = [f for f in files if not should_ignore(os.path.relpath(os.path.join(root, f), root), ignore_patterns)]

        # Only store the structure if there are files or directories
        if filtered_dirs or filtered_files:
            structure.append((root, filtered_dirs, filtered_files, [], []))

        num_dirs += len(filtered_dirs)
        num_files += len(filtered_files)
        for file in filtered_files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)

        # Update dirs in-place to continue walking
        dirs[:] = filtered_dirs

    # Return the statistics and structure
    return {
        'folder_name': os.path.basename(folder_path),
        'num_files': num_files,
        'num_dirs': num_dirs,
        'total_size': total_size,
        'structure': structure
    }

def format_structure(structure):
    """
    Formats the folder structure into a readable string format.
    """

    lines = []
    for root, dirs, files, analyses, modified_time in structure:
        indent_level = root.count(os.sep)
        indent = ' ' * 4 * indent_level
        lines.append(f"{indent}{os.path.basename(root)}/")
        #for d in dirs:
        #    lines.append(f"{indent}    {d}/")
        for index, f in enumerate(files):
            lines.append(f"{indent}    {f}")
            if index < len(analyses) and analyses[index]:
                analysis = analyses[index]
                if isinstance(analysis, dict):
                    file_type = analysis.get('file_type', '---')
                    description = analysis.get('description', '---')
                    lines.append(f"{indent}    {file_type}")
                    lines.append(f"{indent}    {description}\n")
                elif analysis == "NOT_ANALYZED":
                    lines.append(f"{indent}    ※解析対象外\n")
                elif analysis == "FILE_READ_ERROR":
                    lines.append(f"{indent}    ※ファイル読み取りエラー\n")
                else:
                    raise ValueError(f"Unexpected analysis result: {analysis}")

    return '\n'.join(lines)

def write_stats_to_file(stats, filename):
    """
    Writes the statistics to a JSON file.
    """

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(stats, file, indent=4, ensure_ascii=False)

def read_stats_from_file(filename):
    """
    Reads the statistics from a JSON file.
    """

    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)
    
def gpt_analyze(structure, structure_text, interactive=True):
    """
    Analyzes the folder structure using GPT and updates the structure with the analysis results.
    """

    print("Analyzing structure...")
    print(structure_text)
    print("====")

    total_input_tokens = 0
    total_output_tokens = 0

    flag_yesall = False

    for root, dirs, files, analyses, modified_time in structure:
        for index, file in enumerate(files):
            file_path = os.path.join(root, file)
            print("************************************")
            print("Analyzing file:", file_path)
            print("************************************")
            try:
                # Get the last modified time
                last_modified_time = time.ctime(os.path.getmtime(file_path))

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print("-----------------")
                    print(f"Content of {file_path}:")
                    print(content)

                    user_prompt = f"""\
# Content of {file_path}:
{content}
"""

                    token_num = get_token_count(content)
                    token_numk = token_num / 1000                    

                    print("====>> TOKEN SIZE(k): ", token_numk)
                    print("====>> FILE_NAME: ", file_path)

                    if index < len(modified_time) and last_modified_time == modified_time[index]:
                        print("Skip because this file has not been modified since the last analysis.")
                        choice = 'no'
                    elif flag_yesall:
                        choice = 'yes'
                    elif not interactive:
                        choice = 'yes'
                    else:
                        choice = input("Do you want to start a new GPT analysis or skip this file? (yes/no or yesall)(y/n/a): ").strip().lower()
                        if choice == 'yesall' or choice == 'a':
                            flag_yesall = True
                            choice = 'yes'

                    if choice == 'yes' or choice == 'y':
                        print("Starting GPT analysis...")

                        code_description_short_sample = """\
# ClassName
The overview of the class including its responsibilities and main functionalities.

## Method1
Overview of the processing of Method1, its inputs and outputs, and the flow

## Method2
Overview of the processing of Method2, its inputs and outputs, and the flow
"""

                        code_description_long_sample = """\
# Class: ClassName

## Overview
This class is responsible for [brief description of the class's purpose]. It provides functionalities to [describe main functionalities].

## Attributes
- `attribute1`: Description of attribute1
- `attribute2`: Description of attribute2

## Methods

### Method 1: methodName1

#### Description
[Brief description of what Method 1 does]

#### Parameters
- `param1` (Type): Description of param1
- `param2` (Type): Description of param2

#### Returns
- (ReturnType): Description of the return value
"""

                        code_description_sample = code_description_short_sample
                        # Add GPT analysis code here
                        system_prompt = f"""\
Analyze the given file name and file content, and extract the following information:

- type
Classification of the file as either code, config, or document

- file_type
Analysis result of the file content, such as whether the file is Java code, GitHub Actions YAML, etc.

- description
Write a brief summary of the file contents in Japanese.
For program code, describe the processing content and each function. (Refer to the sample description below)
For documents or configuration files, please explain the purpose of the file and provide additional details in bullet points if necessary. It does not need to be in Markdown title/section format.
Regardless of the type of text, please keep the content as concise as possible.
And please add appropriate bullet points and line breaks to make it easier to read.
**The descrption should be Japanese.**

- references
The destination files called from this file

- entry_points
The entry points when this file is called (such as public methods in the case of a program)

===== Sample description for program code
{code_description_sample}

===== The overall file structure is as follows.
{structure_text}
"""
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ]

                        result, input_tokens, output_tokens = get_parsed_completion(messages, FileContent)
                        print(result)
                        total_input_tokens += input_tokens
                        total_output_tokens += output_tokens

                        # Add GPT analysis result to the corresponding file in stats['structure']
                        for item in stats['structure']:
                            if item[0] == root:
                                item[3].append(result.dict())
                                item[4].append(last_modified_time)

                    else:
                        print(f"Skipping {file_path}")
                        for item in stats['structure']:
                            if item[0] == root:
                                item[3].append("NOT_ANALYZED")
                                item[4].append(last_modified_time)

            except Exception as e:
                print(f"Could not read {file_path}: {e}")
                for item in stats['structure']:
                    if item[0] == root:
                        item[3].append("FILE_READ_ERROR")

    print("*****************")
    print("Total input tokens:", total_input_tokens)
    print("Total output tokens:", total_output_tokens)
    print("-----------------")
    print("Estimated cost (gpt-4o-08-06 global): $", estimate_cost_for_gpt4o_0806(total_input_tokens, total_output_tokens))
    print("*****************")

    return stats

if __name__ == "__main__":
    # メイン処理開始
    print("""\
*****************************************
**            REPO DOC  v0.9           **
*****************************************
""")

    # オプション引数パース
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=str, help='解析対象のフォルダパス')
    parser.add_argument('--mode', type=str, default='new', help='new/inter/update/final など')
    args = parser.parse_args()

    if args.folder:
        # 自動実行モード
        folder_path = os.path.abspath(args.folder)
        choice = args.mode.strip().lower() if args.mode else 'new'
        interactive = False
    else:
        # 対話型モード
        folder_path = input("Enter the folder path to analyze: ")
        folder_path = os.path.abspath(folder_path)
        choice = input("""\
Select an option:
    - Start a new analysis: (new)/(n)
    - Continue from an intermediate file: (inter)/(i)
    - Update the analysis with GPT *File update only: (update)/(u)
    - Confirm a final file: (final)/(f)
>""").strip().lower()
        interactive = True

    # 統計ファイル名の設定
    stats_intermediate_filename = os.path.join(folder_path, REPODOC_FOLDER, STATS_INTERMEDIATE_FILENAME)
    stats_final_filename = os.path.join(folder_path, REPODOC_FOLDER, STATS_FINAL_FILENAME)

    if choice in ['new', 'n']:
        stats = analyze_folder(folder_path)
        # 分析パスの最後のディレクトリ名に .rd 拡張子を付けたファイルに分析パスを保存する
        analysis_path_filename = os.path.basename(folder_path) + '.rd'
        with open(analysis_path_filename, 'w', encoding='utf-8') as f:
            f.write(folder_path)
        structure_text = format_structure(stats['structure'])
        print("====")
        print(structure_text)
        if not interactive:
            write_stats_to_file(stats, stats_intermediate_filename)
            print(f"Stats have been written to {stats_intermediate_filename}")
        else:
            user_input = input("Is the structure OK? (yes/no): ").strip().lower()
            if user_input in ['yes', 'y']:
                write_stats_to_file(stats, stats_intermediate_filename)
                print(f"Stats have been written to {stats_intermediate_filename}")
            else:
                print("Stats were not written to file.")

    if choice in ['new', 'n', 'inter', 'i']:
        # 中間ファイルから読み込み、構造を表示し、GPT解析を実行
        if os.path.exists(stats_intermediate_filename):
            stats = read_stats_from_file(stats_intermediate_filename)
            structure_text = format_structure(stats['structure'])
            print("====")
            print(structure_text)
            stats2 = gpt_analyze(stats['structure'], structure_text, interactive=interactive)
            write_stats_to_file(stats2, stats_final_filename)
        else:
            print(f"No saved stats file found at {stats_intermediate_filename}")

    if choice in ['update', 'u']:
        # 最終ファイルから読み込み、GPT解析を再実行
        if os.path.exists(stats_final_filename):
            stats = read_stats_from_file(stats_final_filename)
            structure_text = format_structure(stats['structure'])
            print("====")
            print(structure_text)
            stats2 = gpt_analyze(stats['structure'], structure_text, interactive=interactive)
            write_stats_to_file(stats2, stats_final_filename)
        else:
            print(f"No saved stats file found at {stats_final_filename}")

    if choice in ['new', 'n', 'inter', 'i', 'final', 'f', 'update', 'u']:
        # 最終ファイルの内容を表示
        if os.path.exists(stats_final_filename):
            stats = read_stats_from_file(stats_final_filename)
            if not interactive:
                structure_text = format_structure(stats['structure'])
                print("========================")
                print(structure_text)
            else:
                user_check = input("Check the result? (yes/no)(y/n): ").strip().lower()
                if user_check in ['yes', 'y']:
                    structure_text = format_structure(stats['structure'])
                    print("========================")
                    print(structure_text)
        else:
            print(f"No saved stats file found at {stats_final_filename}")
    else:
        print("Invalid choice. Please enter 'new' or 'inter' or 'final'.")

