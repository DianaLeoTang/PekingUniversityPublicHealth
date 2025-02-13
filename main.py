import re

def remove_unnecessary_line_breaks(text):
    """
    删除不必要的折行符（如果行尾没有标点符号）
    """
    # 将文本按行分割
    lines = text.splitlines()
    
    # 初始化一个列表来存储处理后的行
    processed_lines = []
    
    # 遍历每一行
    i = 0
    while i < len(lines):
        # 如果当前行不为空
        if lines[i].strip():
            # 检查当前行末尾是否有标点符号
            if not re.search(r'[。！？，、；：,.!?;:]$', lines[i].rstrip()):
                # 如果行尾没有标点符号，则与下一行合并
                if i < len(lines) - 1:
                    lines[i + 1] = lines[i].rstrip() + ' ' + lines[i + 1].lstrip()
                else:
                    processed_lines.append(lines[i].rstrip())
            else:
                # 如果行尾有标点符号，则直接保留
                processed_lines.append(lines[i].rstrip())
        i += 1
    
    # 将处理后的行重新组合成文本
    processed_text = '\n'.join(processed_lines)
    return processed_text

def process_txt_file(input_file, output_file):
    """
    处理TXT文件：读取输入文件，删除不必要的折行符，保存到输出文件
    """
    # 读取输入文件内容
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # 处理文本
    processed_text = remove_unnecessary_line_breaks(text)
    
    # 将处理后的内容写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(processed_text)
    
    print(f"处理后的文件已保存到: {output_file}")

# 示例调用
input_file = 'input.txt'  # 输入文件路径
output_file = 'output.txt'  # 输出文件路径
process_txt_file(input_file, output_file)