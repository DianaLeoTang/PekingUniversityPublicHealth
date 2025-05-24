#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word文档转Anki APKG文件转换器
正确处理标题和内容的关系，将标题作为问题，内容作为答案
"""

import os
import re
import tempfile
from typing import List, Dict, Tuple, Optional
import json

try:
    from docx import Document
    import genanki
except ImportError:
    print("请先安装必需的库：")
    print("pip install python-docx genanki")
    exit(1)


class WordToAnkiConverter:
    """Word文档转Anki卡片转换器"""
    
    def __init__(self):
        # 中文数字映射
        self.chinese_numbers = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
            '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
            '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25,
            '二十六': 26, '二十七': 27, '二十八': 28, '二十九': 29, '三十': 30
        }
        
        # 编译正则表达式以提高性能
        self.title_patterns = [
            # 中文数字格式 - 必须在行首
            re.compile(r'^([一二三四五六七八九十]+)[）)]?\s*(.+)$'),
            re.compile(r'^[（(]([一二三四五六七八九十]+)[）)]\s*(.+)$'),
            
            # 阿拉伯数字格式 - 必须在行首
            re.compile(r'^(\d+)[）)]?\s*(.+)$'),
            re.compile(r'^[（(](\d+)[）)]\s*(.+)$'),
            
            # 字母格式 - 必须在行首
            re.compile(r'^([a-zA-Z])[）)]?\s*(.+)$'),
            re.compile(r'^[（(]([a-zA-Z])[）)]\s*(.+)$'),
            re.compile(r'^([a-zA-Z])、\s*(.+)$'),
            
            # 章节格式 - 必须在行首
            re.compile(r'^第([一二三四五六七八九十]+)[章节课]\s*(.+)$'),
        ]
        
        # 主标题识别（单独一行的中文数字）
        self.main_title_pattern = re.compile(r'^([一二三四五六七八九十]{1,3})$')
    
    def extract_paragraphs_from_word(self, file_path: str) -> List[str]:
        """从Word文档中提取文本段落，保持原始格式"""
        try:
            doc = Document(file_path)
            paragraphs = []
            
            for para in doc.paragraphs:
                text = para.text.rstrip()  # 只去除右侧空白，保留左侧缩进
                paragraphs.append(text)  # 包括空行，用于判断段落分隔
            
            return paragraphs
        except Exception as e:
            raise Exception(f"读取Word文档失败: {str(e)}")
    
    def is_title_line(self, line: str) -> Tuple[bool, Optional[Dict]]:
        """判断是否为标题行，并返回标题信息"""
        line = line.strip()
        if not line:
            return False, None
        
        # 检查是否为主标题（单独的中文数字）
        main_match = self.main_title_pattern.match(line)
        if main_match:
            chinese_num = main_match.group(1)
            return True, {
                'type': 'main_title',
                'number': self.chinese_to_arabic(chinese_num),
                'title': chinese_num,
                'full_text': line
            }
        
        # 检查其他标题格式
        for i, pattern in enumerate(self.title_patterns):
            match = pattern.match(line)
            if match:
                number_part = match.group(1)
                title_part = match.group(2)
                
                # 确定标题类型和编号
                if i < 2:  # 中文数字
                    number = self.chinese_to_arabic(number_part)
                    title_type = 'chinese_number'
                elif i < 4:  # 阿拉伯数字
                    number = int(number_part)
                    title_type = 'arabic_number'
                elif i < 7:  # 字母
                    number = ord(number_part.lower()) - ord('a') + 1
                    title_type = 'letter'
                else:  # 章节
                    number = self.chinese_to_arabic(number_part)
                    title_type = 'chapter'
                
                return True, {
                    'type': title_type,
                    'number': number,
                    'title': title_part,
                    'full_text': line
                }
        
        return False, None
    
    def chinese_to_arabic(self, chinese_num: str) -> int:
        """将中文数字转换为阿拉伯数字"""
        if chinese_num in self.chinese_numbers:
            return self.chinese_numbers[chinese_num]
        
        # 处理复合数字
        if '十' in chinese_num:
            if chinese_num == '十':
                return 10
            elif chinese_num.startswith('十'):
                return 10 + self.chinese_numbers.get(chinese_num[1:], 0)
            elif chinese_num.endswith('十'):
                tens_digit = self.chinese_numbers.get(chinese_num[:-1], 0)
                return tens_digit * 10 if tens_digit else 10
            else:
                parts = chinese_num.split('十')
                if len(parts) == 2:
                    tens = self.chinese_numbers.get(parts[0], 0) * 10
                    ones = self.chinese_numbers.get(parts[1], 0) if parts[1] else 0
                    return tens + ones
        
        return 1
    
    def parse_document_structure(self, paragraphs: List[str]) -> List[Dict]:
        """解析文档结构，提取标题和对应内容"""
        items = []
        current_item = None
        
        i = 0
        while i < len(paragraphs):
            line = paragraphs[i]
            
            # 检查是否为标题行
            is_title, title_info = self.is_title_line(line)
            
            if is_title:
                # 如果之前有未完成的项目，先保存它
                if current_item and current_item.get('content'):
                    items.append(current_item)
                
                # 开始新的项目
                current_item = {
                    'title': title_info['title'],
                    'full_title': title_info['full_text'],
                    'type': title_info['type'],
                    'number': title_info['number'],
                    'content': [],
                    'line_start': i
                }
                
                # 对于主标题（单独的中文数字），需要找到下一行的实际标题
                if title_info['type'] == 'main_title' and i + 1 < len(paragraphs):
                    next_line = paragraphs[i + 1].strip()
                    if next_line and not self.is_title_line(next_line)[0]:
                        current_item['title'] = next_line
                        current_item['full_title'] = f"{title_info['full_text']} {next_line}"
                        i += 1  # 跳过下一行
            
            else:
                # 内容行
                if current_item is not None:
                    content = line.strip()
                    if content:  # 只添加非空内容
                        current_item['content'].append(content)
            
            i += 1
        
        # 添加最后一个项目
        if current_item and current_item.get('content'):
            items.append(current_item)
        
        return items
    
    def create_anki_cards(self, items: List[Dict]) -> List[Tuple[str, str, List[str]]]:
        """创建Anki卡片，标题作为问题，内容作为答案"""
        cards = []
        
        for item in items:
            # 问题：标题
            question = item['full_title']
            
            # 答案：内容
            if item['content']:
                # 将内容列表合并为HTML格式
                answer_lines = []
                for content_line in item['content']:
                    # 检查是否为子标题或列表项
                    if self.is_title_line(content_line)[0]:
                        answer_lines.append(f"<b>{content_line}</b>")
                    else:
                        answer_lines.append(content_line)
                
                answer = "<br><br>".join(answer_lines)
            else:
                answer = "（无内容）"
            
            # 标签
            tags = [item['type'], f"number_{item['number']}"]
            
            cards.append((question, answer, tags))
        
        return cards
    
    def create_anki_deck(self, cards: List[Tuple[str, str, List[str]]], deck_name: str = "Word导入") -> genanki.Deck:
        """创建Anki牌组"""
        # 定义卡片模板
        model = genanki.Model(
            1607392320,  # 使用不同的ID避免冲突
            'Word标题内容模板',
            fields=[
                {'name': 'Question'},
                {'name': 'Answer'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
                    <div class="question">
                        <h3>{{Question}}</h3>
                    </div>
                    ''',
                    'afmt': '''
                    <div class="question">
                        <h3>{{Question}}</h3>
                    </div>
                    <hr id="answer">
                    <div class="answer">
                        {{Answer}}
                    </div>
                    ''',
                },
            ],
            css="""
            .card {
                font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
                font-size: 16px;
                text-align: left;
                color: #333;
                background-color: #fafafa;
                padding: 20px;
                line-height: 1.6;
            }
            
            .question {
                margin-bottom: 15px;
            }
            
            .question h3 {
                color: #2c5aa0;
                margin: 0;
                padding: 10px;
                background-color: #e8f4f8;
                border-left: 4px solid #2c5aa0;
                border-radius: 4px;
            }
            
            .answer {
                background-color: white;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #ddd;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .answer b {
                color: #d63384;
                display: block;
                margin: 10px 0 5px 0;
            }
            
            hr {
                border: none;
                height: 2px;
                background: linear-gradient(to right, #2c5aa0, transparent);
                margin: 20px 0;
            }
            """
        )
        
        # 创建牌组
        deck = genanki.Deck(
            2059400111,  # 使用不同的ID
            deck_name
        )
        
        # 添加卡片
        for question, answer, tags in cards:
            note = genanki.Note(
                model=model,
                fields=[question, answer],
                tags=tags
            )
            deck.add_note(note)
        
        return deck
    
    def convert_word_to_anki(self, word_file: str, output_file: str = None) -> str:
        """主转换函数"""
        try:
            # 检查输入文件
            if not os.path.exists(word_file):
                raise FileNotFoundError(f"Word文件不存在: {word_file}")
            
            # 设置输出文件名
            if not output_file:
                base_name = os.path.splitext(os.path.basename(word_file))[0]
                output_file = f"{base_name}.apkg"
            
            print(f"正在处理Word文档: {word_file}")
            
            # 步骤1: 提取段落
            paragraphs = self.extract_paragraphs_from_word(word_file)
            print(f"提取到 {len(paragraphs)} 个段落")
            
            # 步骤2: 解析文档结构
            items = self.parse_document_structure(paragraphs)
            print(f"识别到 {len(items)} 个标题-内容项目")
            
            if not items:
                print("警告：未识别到任何标题格式的内容")
                return None
            
            # 步骤3: 创建Anki卡片
            cards = self.create_anki_cards(items)
            print(f"创建了 {len(cards)} 张卡片")
            
            # 步骤4: 生成APKG文件
            deck_name = os.path.splitext(os.path.basename(word_file))[0]
            deck = self.create_anki_deck(cards, deck_name)
            
            # 导出为APKG文件
            genanki.Package(deck).write_to_file(output_file)
            print(f"转换完成！输出文件: {output_file}")
            
            return output_file
            
        except Exception as e:
            print(f"转换失败: {str(e)}")
            return None
    
    def preview_parsing(self, word_file: str, max_items: int = 10):
        """预览解析结果"""
        try:
            paragraphs = self.extract_paragraphs_from_word(word_file)
            items = self.parse_document_structure(paragraphs)
            
            print(f"\n=== 解析预览 (前{max_items}项) ===")
            for i, item in enumerate(items[:max_items]):
                print(f"\n{i+1}. 标题: {item['full_title']}")
                print(f"   类型: {item['type']}")
                print(f"   内容: {len(item['content'])} 行")
                if item['content']:
                    # 显示前3行内容
                    content_preview = item['content'][:3]
                    for j, line in enumerate(content_preview):
                        print(f"      {j+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
                    if len(item['content']) > 3:
                        print(f"      ... 还有 {len(item['content']) - 3} 行")
                else:
                    print("      (无内容)")
            
            if len(items) > max_items:
                print(f"\n... 还有 {len(items) - max_items} 项")
                
        except Exception as e:
            print(f"预览失败: {str(e)}")


def main():
    """主函数"""
    converter = WordToAnkiConverter()
    
    # 使用示例
    word_file = input("请输入Word文件路径: ").strip().strip('"')
    
    if not word_file:
        print("未输入文件路径")
        return
    
    # 预览解析结果
    print("正在预览解析结果...")
    converter.preview_parsing(word_file)
    
    # 确认转换
    confirm = input("\n是否继续转换为APKG文件? (y/n): ").strip().lower()
    if confirm in ['y', 'yes', '是']:
        output_file = converter.convert_word_to_anki(word_file)
        if output_file:
            print(f"\n✅ 转换成功！")
            print(f"📁 输出文件: {output_file}")
            print(f"📋 请将 {output_file} 导入到Anki中使用")
            print(f"\n💡 卡片格式说明：")
            print(f"   - 正面：标题（问题）")
            print(f"   - 背面：对应的内容（答案）")


if __name__ == "__main__":
    main()