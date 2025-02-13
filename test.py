'''
Author: Diana Tang
Date: 2025-02-13 22:18:59
LastEditors: Diana Tang
Description: some description
FilePath: /PekingUniversityCode/PekingUniversityPublicHealth/test.py
'''
def process_text(text):
    # 分割成行
    lines = text.split('\n')
    
    # 中文标点符号集合
    punctuation = {'。', '，', '！', '？', '；', '：', '、', '"', '"', ''', ''', '【', '】', '（', '）', '《', '》', '—', '…', '．'}
    
    result = []
    temp_line = ''
    
    for line in lines:
        if not line:  # 跳过空行
            if temp_line:
                result.append(temp_line)
                temp_line = ''
            result.append('')
            continue
            
        # 如果当前行末尾有标点符号
        if line[-1] in punctuation:
            if temp_line:
                temp_line += line
                result.append(temp_line)
                temp_line = ''
            else:
                result.append(line)
        else:
            # 如果没有标点符号，累积到临时行
            temp_line += line
    
    # 处理最后一行
    if temp_line:
        result.append(temp_line)
    
    return '\n'.join(result)

# 测试文本
text = """作为一名大学研究者，我的专业
领域是健康的社会决定因素。具体来
说，我对探索不良童年经历（ACEs）与
成年重度抑郁性障碍（也称为重度抑
郁症）的发展和严重程度之间的相关
性感兴趣。然而，我并不通晓这一领
域的最新研究和进展。因此，我希望
你能向我提供10个可行的研究问题，
并对每个问题进行简要说明，帮助我
确定有创意的研究课题。你能提出10
个关于不良童年经历对成年后抑郁症
影响的研究问题吗？"""

processed_text = process_text(text)
print(processed_text)