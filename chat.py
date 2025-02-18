import json
import os
from pydantic import BaseModel
from openai_utils import get_parsed_completion, get_token_count, estimate_cost_for_gpt4o_0806

STATS_FINAL_FILENAME = 'stats_final.json'

class CheckRequest(BaseModel):
    complex_level: int
    need_file_confirmation: list[str]

class AnalyzeComment(BaseModel):
    answer: str
    recommend_web_search_keywords: list[str]

def read_stats_from_file(filename):
    """Read JSON stats from a file."""
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

def format_structure_common(structure, with_description=False):
    """Format the structure of the repository."""
    top_indent_level = 0
    lines = []
    for root, dirs, files, analyses, modified_times in structure:
        if top_indent_level == 0:
            top_indent_level = root.count(os.sep)
        indent_level = root.count(os.sep) - top_indent_level
        indent = ' ' * 4 * indent_level
        if with_description and files:
            lines.append(f"■■ {root}/\n")
        elif not with_description:
            lines.append(f"{indent}{os.path.basename(root)}/")
        for index, f in enumerate(files):
            if with_description:
                if 0 <= index < len(analyses):
                    analysis = analyses[index]
                    if isinstance(analysis, dict):
                        file_type = analysis.get('file_type', '---')
                        description = analysis.get('description', '---')
                        references = analysis.get('references', [])
                        entry_points = analysis.get('entry_points', [])
                        lines.append(f"■ {f} ({file_type})")
                        lines.append(f"{description}\n")
                        lines.append(f"# 参照・呼び出し先")
                        for ref in references:
                            lines.append(f"  - {ref}")
                        lines.append(f"\n# エントリーポイント")
                        for ep in entry_points:
                            lines.append(f"  - {ep}")
                        lines.append(f"\n# ファイルパス")
                        lines.append(f"  - {root}/{f}")
                        lines.append("\n")
                    elif analysis == "NOT_ANALYZED":
                        lines.append(f"■ {f}")
                        lines.append(f" - ※解析対象外\n")
                    elif analysis == "FILE_READ_ERROR":
                        lines.append(f"■ {f}")
                        lines.append(f" - ※ファイル読み取りエラー\n")
                    else:
                        raise ValueError(f"Unexpected analysis result: {analysis}")
            else:
                lines.append(f"{indent}    {f}")
    return '\n'.join(lines)

def format_structure(structure):
    """Format the structure of the repository without descriptions."""
    return format_structure_common(structure, with_description=False)

def format_structure_with_description(structure):
    """Format the structure of the repository with descriptions."""
    return format_structure_common(structure, with_description=True)

def generate_additional_system_prompt(file_paths):
    """Generate additional system prompt based on file paths."""
    additional_system_prompt = ""
    print("Try to confirm the following file paths:")
    for file_path in file_paths:
        print(f"  - {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = "(現在このファイルは存在しません)"
        additional_system_prompt += f"### 参考情報 - {file_path}\n{content}\n"
    return additional_system_prompt

if __name__ == "__main__":
    if os.path.exists(STATS_FINAL_FILENAME):
        stats = read_stats_from_file(STATS_FINAL_FILENAME)
        structure_text = format_structure(stats['structure'])
        print("==== REPOSITORY STRUCTURE ====")
        print(structure_text)
        print("==============================")

        structure_with_description_text = format_structure_with_description(stats['structure'])
        print("==== REPOSITORY WITH DESCRIPTION STRUCTURE ====")
        print(structure_with_description_text)
        print("===============================================")
        print("ABOVE TEXT TOKEN SIZE(k): ", get_token_count(structure_with_description_text) / 1000)
    else:
        print(f"No saved stats file found at {STATS_FINAL_FILENAME}")

    print("Let's start a new chat!")
    check_system_prompt = f"""\
You are an expert engineer in system development and operations projects.
Please check the content of the user's inquiry and confirm the complexity and necessary files.

Your response should include the following elements:

- complex_level: The complexity level of the question. Specify a number according to the following definitions.
 - 0: When it is possible to create a response without referring to the original file, based solely on the current summary information.
 - 1: When it is desirable to refer to and confirm the original file in order to create a response.
 - 2: When it is not necessary to refer to the original file, but advanced skills are required to create new content or edit existing files.
 - 3: When it is desirable to refer to and confirm the original file, and advanced skills are required to create new content or edit existing files.
 - 4: When impact analysis and verification of interdependent files are required, both on the caller and callee sides, in order to create a response.

- need_file_confirmation: The file path that should be confirmed based on the user's question (if any)
 The following files are relevant.
 - Files that need to be checked
 - Files that may be useful for user requests
 If the complex_level is 4, all files related to upstream and downstream dependencies are also included.
 **Unless it is self-evident, actively refer to the files.**
 Only **File paths** are required. Do not point Folder paths.

### Repository Structure
{structure_with_description_text}

"""

    system_prompt = f"""\
You are an expert engineer in system development and operations projects.
Please respond to user inquiries about the attached repository structure in Japanese.

Your response should include the following elements:
- answer: Your response
- recommend_web_search_keywords: Web search keywords to use if additional information is needed (if any)

### Repository Structure
{structure_with_description_text}

"""

    messages_ex_system_prompt = []

    total_input_tokens = 0
    total_output_tokens = 0

    while True:
        print('-------------------------------------------------')
        print("Current estimated cost (gpt-4o-08-06 global): $", estimate_cost_for_gpt4o_0806(total_input_tokens, total_output_tokens))
        user_input = input("Enter your message or stop the chat(n or N): ")
        if user_input in ['n', 'ｎ', 'Ｎ', 'N']:
            print("Goodbye!")
            break
                
        check_messages = [
            {"role": "system", "content": check_system_prompt},
        ]

        for message in messages_ex_system_prompt:
            check_messages.append(message)
        check_messages.append({"role": "user", "content": user_input})

        completion, input_tokens, output_tokens = get_parsed_completion(check_messages, CheckRequest)
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

        complex_level = completion.complex_level

        print("COMPLEX LEVEL = ", complex_level)

        if complex_level == 0 or complex_level == 2:
            new_messages = [{"role": "system", "content": system_prompt}]
            for message in messages_ex_system_prompt:
                new_messages.append(message)
            new_messages.append({"role": "user", "content": user_input})
            completion, input_tokens, output_tokens = get_parsed_completion(new_messages, AnalyzeComment)
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens

            messages_ex_system_prompt.append({"role": "user", "content": user_input})
            messages_ex_system_prompt.append({"role": "assistant", "content": completion.answer})

            print("==============================")
            print(completion.answer)

            if completion.recommend_web_search_keywords:
                print("* Recommend Web Search Keywords: ", completion.recommend_web_search_keywords)

        if complex_level == 1 or complex_level == 3 or complex_level == 4:
            additional_system_prompt = generate_additional_system_prompt(completion.need_file_confirmation)
            
            new_messages = [{"role": "system", "content": system_prompt + additional_system_prompt}]
            for message in messages_ex_system_prompt:
                new_messages.append(message)
            new_messages.append({"role": "user", "content": user_input})
            completion, input_tokens, output_tokens = get_parsed_completion(new_messages, AnalyzeComment)
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens

            messages_ex_system_prompt.append({"role": "user", "content": user_input})
            messages_ex_system_prompt.append({"role": "assistant", "content": completion.answer})

            print("==============================")
            print(completion.answer)

            if completion.recommend_web_search_keywords:
                print("* Recommend Web Search Keywords: ", completion.recommend_web_search_keywords)