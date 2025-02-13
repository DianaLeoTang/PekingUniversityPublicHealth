'''
Author: Diana Tang
Date: 2025-02-13 21:48:23
LastEditors: Diana Tang
Description: some description
FilePath: /PekingUniversityCode/main.py
'''

from docx import Document
import re

# 读取文档并打印所有文本，看看实际格式是什么样的
doc = Document('./我的科研助理：GPT.docx')
for para in doc.paragraphs:
    if '578' in para.text:  # 只打印包含"578"的段落
        print(f"找到的文本: '{para.text}'")

# # 使用示例
# try:
#     input_file = "./我的科研助理：GPT.docx"  # 输入文件名
#     output_file = "./处理后.docx"  # 输出文件名
#     success = remove_page_numbers(input_file, output_file)
#     if success:
#         print("页码删除成功！新文档已保存为:", output_file)
# except Exception as e:
#     print("处理文档时发生错误:", str(e))