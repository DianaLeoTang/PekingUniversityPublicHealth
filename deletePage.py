'''
Author: Diana Tang
Date: 2025-02-13 21:48:23
LastEditors: Diana Tang
Description: some description
FilePath: /PekingUniversityCode/PekingUniversityPublicHealth/main.py
'''
from docx import Document
import re

def remove_page_numbers(input_file, output_file):
    doc = Document(input_file)
    # 修改后的正则表达式，匹配数字/578，后面没有点号
    pattern = r'\d+/578'
    
    # 处理所有段落
    for paragraph in doc.paragraphs:
        if re.search(pattern, paragraph.text):
            # 替换匹配到的内容
            new_text = re.sub(pattern, '', paragraph.text)
            paragraph.text = new_text
    
    # 保存修改后的文档
    doc.save(output_file)

# 使用示例
input_file = "./我的科研助理：GPT.docx"  # 你的输入文件名
output_file = "处理后文档.docx"  # 你想保存的文件名
remove_page_numbers(input_file, output_file)