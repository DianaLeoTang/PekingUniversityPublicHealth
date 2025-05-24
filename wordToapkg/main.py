#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word文档转Anki APKG文件转换器
支持多种编号格式的识别和处理
"""

import os
import re
import sqlite3
import tempfile
import zipfile
from datetime import datetime
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
            '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20
        }
        
        # 编译正则表达式以提高性能
        self.patterns = {
            # 中文数字格式
            'chinese_num': re.compile(r'^([一二三四五六七八九十]+)[）)]?\s*(.+)$'),
            'chinese_paren': re.compile(r'^[（(]([一二三四五六七八九十]+)[）)]\s*(.+)$'),
            
            # 阿拉伯数字格式
            'arabic_num': re.compile(r'^(\d+)[）)]?\s*(.+)$'),
            'arabic_paren': re.compile(r'^[（(](\d+)[）)]\s*(.+)$'),
            
            # 字母格式
            'letter_paren': re.compile(r'^[（(]?([a-zA-Z])[）)]?\s*(.+)$'),
            'letter_dot': re.compile(r'^([a-zA-Z])、\s*(.+)$'),
            
            # 章节格式
            'chapter': re.compile(r'^第([一二三四五六七八九十]+)[章节课]\s*(.+)$'),
            
            # 层级结构检测
            'indent': re.compile(r'^(\s+)(.+)$')
        }
    
    def extract_text_from_word(self, file_path: str) -> List[str]:
        """从Word文档中提取文本段落"""
        try:
            doc = Document(file_path)
            paragraphs = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:  # 跳过空段落
                    paragraphs.append(text)
            
            return paragraphs
        except Exception as e:
            raise Exception(f"读取Word文档失败: {str(e)}")
    
    def parse_numbered_content(self, paragraphs: List[str]) -> List[Dict]:
        """解析带编号的内容"""
        parsed_items = []
        current_level = 0
        
        for i, para in enumerate(paragraphs):
            item = self.parse_single_paragraph(para, i)
            if item:
                parsed_items.append(item)
        
        return parsed_items
    
    def parse_single_paragraph(self, text: str, line_num: int) -> Optional[Dict]:
        """解析单个段落"""
        # 检测缩进层级
        indent_match = self.patterns['indent'].match(text)
        level = 0
        if indent_match:
            indent_text = indent_match.group(1)
            level = len(indent_text) // 2  # 假设每级缩进2个空格
            text = indent_match.group(2)
        
        # 尝试各种编号格式
        for pattern_name, pattern in self.patterns.items():
            if pattern_name == 'indent':
                continue
                
            match = pattern.match(text)
            if match:
                if pattern_name in ['chinese_num', 'chinese_paren']:
                    number = self.chinese_to_arabic(match.group(1))
                    content = match.group(2)
                elif pattern_name in ['arabic_num', 'arabic_paren']:
                    number = int(match.group(1))
                    content = match.group(2)
                elif pattern_name in ['letter_paren', 'letter_dot']:
                    number = ord(match.group(1).lower()) - ord('a') + 1
                    content = match.group(2)
                elif pattern_name == 'chapter':
                    number = self.chinese_to_arabic(match.group(1))
                    content = match.group(2)
                else:
                    continue
                
                return {
                    'type': pattern_name,
                    'number': number,
                    'content': content,
                    'level': level,
                    'line': line_num,
                    'original': text
                }
        
        # 如果没有匹配到编号格式，但有缩进，也保存
        if level > 0:
            return {
                'type': 'indented',
                'number': 0,
                'content': text,
                'level': level,
                'line': line_num,
                'original': text
            }
        
        return None
    
    def chinese_to_arabic(self, chinese_num: str) -> int:
        """将中文数字转换为阿拉伯数字"""
        if chinese_num in self.chinese_numbers:
            return self.chinese_numbers[chinese_num]
        
        # 处理复合数字（如十一、二十三等）
        if '十' in chinese_num:
            if chinese_num == '十':
                return 10
            elif chinese_num.startswith('十'):
                return 10 + self.chinese_numbers.get(chinese_num[1:], 0)
            elif chinese_num.endswith('十'):
                return self.chinese_numbers.get(chinese_num[:-1], 0) * 10
            else:
                parts = chinese_num.split('十')
                if len(parts) == 2:
                    tens = self.chinese_numbers.get(parts[0], 0) * 10
                    ones = self.chinese_numbers.get(parts[1], 0)
                    return tens + ones
        
        return 1  # 默认返回1
    
    def create_anki_cards(self, parsed_items: List[Dict]) -> List[Tuple[str, str]]:
        """创建Anki卡片"""
        cards = []
        
        for i, item in enumerate(parsed_items):
            # 创建问题（前面部分）
            question_parts = []
            
            # 添加上下文（前面的项目）
            for j in range(max(0, i-2), i):
                context_item = parsed_items[j]
                question_parts.append(f"{'  ' * context_item['level']}{context_item['original']}")
            
            # 添加当前项目的编号部分
            current_content = item['content']
            question_pattern = item['original'].replace(current_content, "______")
            question_parts.append(f"{'  ' * item['level']}{question_pattern}")
            
            question = "<br>".join(question_parts)
            answer = current_content
            
            # 添加标签
            tags = [f"level_{item['level']}", item['type']]
            
            cards.append((question, answer, tags))
        
        return cards
    
    def create_anki_deck(self, cards: List[Tuple[str, str]], deck_name: str = "Word导入") -> genanki.Deck:
        """创建Anki牌组"""
        # 定义卡片模板
        model = genanki.Model(
            1607392319,
            'Word导入模板',
            fields=[
                {'name': 'Question'},
                {'name': 'Answer'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{Question}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
                },
            ],
            css="""
            .card {
                font-family: "Microsoft YaHei", Arial, sans-serif;
                font-size: 16px;
                text-align: left;
                color: black;
                background-color: white;
                line-height: 1.5;
            }
            
            .question {
                margin-bottom: 20px;
            }
            
            .answer {
                color: #0066cc;
                font-weight: bold;
            }
            """
        )
        
        # 创建牌组
        deck = genanki.Deck(
            2059400110,
            deck_name
        )
        
        # 添加卡片
        for question, answer, tags in cards:
            note = genanki.Note(
                model=model,
                fields=[question, answer],
                tags=tags if isinstance(tags, list) else []
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
            
            # 步骤1: 提取文本
            paragraphs = self.extract_text_from_word(word_file)
            print(f"提取到 {len(paragraphs)} 个段落")
            
            # 步骤2: 解析编号内容
            parsed_items = self.parse_numbered_content(paragraphs)
            print(f"识别到 {len(parsed_items)} 个编号项目")
            
            if not parsed_items:
                print("警告：未识别到任何编号格式的内容")
                return None
            
            # 步骤3: 创建Anki卡片
            cards = self.create_anki_cards(parsed_items)
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
            paragraphs = self.extract_text_from_word(word_file)
            parsed_items = self.parse_numbered_content(paragraphs)
            
            print(f"\n=== 解析预览 (前{max_items}项) ===")
            for i, item in enumerate(parsed_items[:max_items]):
                indent = "  " * item['level']
                print(f"{i+1}. {indent}[{item['type']}] {item['number']}: {item['content']}")
            
            if len(parsed_items) > max_items:
                print(f"... 还有 {len(parsed_items) - max_items} 项")
                
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


if __name__ == "__main__":
    main()