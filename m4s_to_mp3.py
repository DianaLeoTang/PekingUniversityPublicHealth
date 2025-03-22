#!/usr/bin/env python3
"""
简单直接的m4s处理脚本 - 针对B站等平台的视频片段
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse

def extract_audio(input_file, output_file):
    """尝试直接提取音频流"""
    print(f"处理: {input_file}")
    
    # 方法1: 直接作为音频流提取
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_file,
        '-vn',                # 不处理视频
        '-acodec', 'copy',    # 直接复制音频流
        output_file + '.aac'  # 先保存为aac
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"✓ 音频流提取成功: {output_file}.aac")
        
        # 将aac转换为mp3
        cmd2 = [
            'ffmpeg',
            '-y',
            '-i', output_file + '.aac',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            output_file
        ]
        
        subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"✓ 成功转换为MP3: {output_file}")
        
        # 删除临时aac文件
        os.remove(output_file + '.aac')
        return True
    except subprocess.CalledProcessError:
        print(f"× 直接提取音频流失败，尝试方法2...")
    
    # 方法2: 将m4s重命名为mp4后处理
    temp_mp4 = input_file + '.mp4'
    try:
        # 复制文件并重命名为mp4
        with open(input_file, 'rb') as src, open(temp_mp4, 'wb') as dst:
            dst.write(src.read())
        
        # 使用mp4文件处理
        cmd = [
            'ffmpeg',
            '-y',
            '-i', temp_mp4,
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            output_file
        ]
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"✓ 方法2成功: {output_file}")
        
        # 删除临时mp4文件
        os.remove(temp_mp4)
        return True
    except subprocess.CalledProcessError:
        print(f"× 方法2也失败，尝试方法3...")
        # 清理临时文件
        if os.path.exists(temp_mp4):
            os.remove(temp_mp4)
    
    # 方法3: 追加适当的头部信息后尝试处理
    temp_file = input_file + '.tmp'
    try:
        # 第一种头部信息
        header = (
            b'\x00\x00\x00\x20\x66\x74\x79\x70\x69\x73\x6f\x6d\x00\x00\x02\x00'
            b'\x69\x73\x6f\x6d\x69\x73\x6f\x32\x61\x76\x63\x31\x6d\x70\x34\x31'
        )
        
        with open(temp_file, 'wb') as f:
            f.write(header)
            with open(input_file, 'rb') as src:
                f.write(src.read())
        
        cmd = [
            'ffmpeg',
            '-y',
            '-i', temp_file,
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            output_file
        ]
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"✓ 方法3成功: {output_file}")
        
        # 删除临时文件
        os.remove(temp_file)
        return True
    except subprocess.CalledProcessError:
        print(f"× 所有方法都失败，无法处理: {input_file}")
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def main():
    parser = argparse.ArgumentParser(description='简单的m4s音频提取工具')
    parser.add_argument('input_dir', help='包含m4s文件的目录')
    parser.add_argument('--output_dir', '-o', help='输出目录', default='./mp3_files')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 获取所有m4s文件
    m4s_files = list(input_dir.glob('*.m4s'))
    
    if not m4s_files:
        print(f"在 {input_dir} 中没有找到m4s文件")
        return
    
    print(f"找到 {len(m4s_files)} 个m4s文件，开始处理...")
    
    success = 0
    failed = 0
    
    for i, file_path in enumerate(m4s_files, 1):
        print(f"\n处理文件 {i}/{len(m4s_files)}: {file_path}")
        mp3_path = output_dir / f"{file_path.stem}.mp3"
        
        if extract_audio(str(file_path), str(mp3_path)):
            success += 1
        else:
            failed += 1
    
    print(f"\n处理完成! 成功: {success}, 失败: {failed}")

if __name__ == "__main__":
    main()