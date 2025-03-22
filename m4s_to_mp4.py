import os
import sys
import subprocess
import argparse
import shutil
from glob import glob

def convert_m4s_to_mp4(input_file, output_file=None):
    """
    将m4s文件转换为MP4格式
    
    参数:
        input_file (str): 输入m4s文件的路径
        output_file (str, optional): 输出MP4文件的路径，如果不提供则自动生成
    
    返回:
        str: 输出文件的路径
    """
    # 如果没有提供输出文件名，则自动生成
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + '.mp4'
    
    print(f"转换: {input_file} -> {output_file}")
    
    try:
        # 使用FFmpeg进行转换
        cmd = ['ffmpeg', '-i', input_file, '-c', 'copy', '-y', output_file]
        
        result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 检查文件是否正确生成
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"转换成功: {input_file} -> {output_file}")
            return output_file
        else:
            print("转换失败，尝试使用备用方法...")
            # 备用方法: 使用文件扩展名更改
            try:
                with open(input_file, 'rb') as src, open(output_file, 'wb') as dst:
                    dst.write(src.read())
                print(f"使用直接拷贝方法: {input_file} -> {output_file}")
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    return output_file
            except Exception as e:
                print(f"直接拷贝失败: {e}")
            
            return None
    
    except Exception as e:
        print(f"转换时发生错误: {e}")
        return None

def merge_video_audio_m4s(video_m4s, audio_m4s, output_file=None):
    """
    合并视频m4s和音频m4s文件为一个MP4文件
    
    参数:
        video_m4s (str): 视频m4s文件路径
        audio_m4s (str): 音频m4s文件路径
        output_file (str, optional): 输出MP4文件的路径，如果不提供则自动生成
    
    返回:
        str: 输出文件的路径
    """
    # 如果没有提供输出文件名，则自动生成
    if output_file is None:
        base_name = os.path.splitext(video_m4s)[0]
        base_name = base_name.replace('_video', '')
        output_file = f"{base_name}.mp4"
    
    print(f"合并: {video_m4s} + {audio_m4s} -> {output_file}")
    
    # 尝试合并
    try:
        cmd = [
            'ffmpeg',
            '-i', video_m4s,
            '-i', audio_m4s,
            '-c', 'copy',
            '-y', output_file
        ]
        
        result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 检查是否成功
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"合并成功: {video_m4s} + {audio_m4s} -> {output_file}")
            return output_file
        else:
            # 如果合并失败，尝试使用备用方法
            print("合并失败，尝试使用备用方法...")
            alt_cmd = [
                'ffmpeg',
                '-i', video_m4s,
                '-i', audio_m4s,
                '-bsf:a', 'aac_adtstoasc',
                '-c', 'copy',
                '-y', output_file
            ]
            
            alt_result = subprocess.run(alt_cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"备用方法合并成功: {video_m4s} + {audio_m4s} -> {output_file}")
                return output_file
            else:
                # 如果仍然失败，只使用视频文件
                print("备用方法合并失败，只使用视频文件...")
                return convert_m4s_to_mp4(video_m4s, output_file)
    
    except Exception as e:
        print(f"合并时发生错误: {e}")
        # 如果出错，只使用视频文件
        print("发生错误，只使用视频文件...")
        return convert_m4s_to_mp4(video_m4s, output_file)

def process_bilibili_structure(root_dir):
    """
    处理哔哩哔哩下载的目录结构
    
    参数:
        root_dir (str): 包含多个视频目录的根目录
    """
    # 遍历根目录下的所有子目录（视频ID目录）
    video_dirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d)) and d.isdigit()]
    
    if not video_dirs:
        print(f"在 {root_dir} 中没有找到视频目录")
        return
    
    for video_dir in video_dirs:
        video_path = os.path.join(root_dir, video_dir)
        print(f"\n处理视频目录: {video_dir}")
        
        # 查找所有m4s文件
        m4s_files = []
        for root, _, files in os.walk(video_path):
            for file in files:
                if file.endswith('.m4s'):
                    m4s_files.append(os.path.join(root, file))
        
        if not m4s_files:
            print(f"  在 {video_dir} 中没有找到m4s文件")
            continue
        
        # 获取视频标题
        video_title = video_dir
        json_path = os.path.join(video_path, 'videoInfo.json')
        if os.path.exists(json_path):
            try:
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    video_info = json.load(f)
                    if 'title' in video_info:
                        video_title = video_info['title']
                        # 移除标题中的非法字符
                        video_title = "".join([c for c in video_title if c.isalnum() or c in " _-.,()[]{}"])
            except Exception as e:
                print(f"  读取视频信息失败: {e}")
        
        # 打印找到的文件
        print(f"  找到 {len(m4s_files)} 个m4s文件:")
        for f in m4s_files:
            print(f"    - {os.path.basename(f)} ({os.path.getsize(f) / 1024 / 1024:.2f} MB)")
        
        # 识别视频和音频文件
        # 哔哩哔哩通常使用特定的后缀
        video_files = [f for f in m4s_files if '30032' in f]
        audio_files = [f for f in m4s_files if '30232' in f]
        
        # 如果没找到符合特定模式的文件，按大小排序
        if not video_files or not audio_files:
            print("  未找到符合标准模式的文件，按大小排序...")
            m4s_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
            
            if len(m4s_files) >= 2:
                video_files = [m4s_files[0]]  # 最大的文件可能是视频
                audio_files = [m4s_files[1]]  # 第二大的可能是音频
            elif len(m4s_files) == 1:
                video_files = [m4s_files[0]]
                audio_files = []
        
        # 输出文件路径 - 放在上级目录
        output_dir = os.path.dirname(root_dir)
        safe_title = video_title.replace('/', '_').replace('\\', '_')
        output_file = os.path.join(output_dir, f"{safe_title}_{video_dir}.mp4")
        
        print(f"  输出文件: {output_file}")
        
        # 处理文件
        if video_files and audio_files:
            print(f"  尝试合并视频和音频...")
            result = merge_video_audio_m4s(video_files[0], audio_files[0], output_file)
            if not result:
                print("  合并失败，尝试只处理视频文件...")
                convert_m4s_to_mp4(video_files[0], output_file)
        elif video_files:
            print("  只找到视频文件，直接转换...")
            convert_m4s_to_mp4(video_files[0], output_file)
        elif m4s_files:
            print("  使用找到的第一个m4s文件...")
            convert_m4s_to_mp4(m4s_files[0], output_file)
        else:
            print("  没有可处理的文件")
        
        # 检查最终输出
        if os.path.exists(output_file):
            print(f"  成功生成: {output_file} ({os.path.getsize(output_file) / 1024 / 1024:.2f} MB)")
        else:
            print(f"  无法生成输出文件")

def batch_process_directory(directory, pattern='*.m4s', is_paired=False):
    """
    批量处理目录中的所有m4s文件
    
    参数:
        directory (str): 包含m4s文件的目录
        pattern (str): 文件匹配模式
        is_paired (bool): 是否将文件视为音视频配对处理
    """
    # 检测是否为哔哩哔哩下载的目录结构
    is_bilibili = False
    for item in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, item)) and item.isdigit():
            is_bilibili = True
            break
    
    if is_bilibili:
        print("检测到哔哩哔哩下载目录结构，使用专用处理方法...")
        process_bilibili_structure(directory)
        return
    
    # 常规处理方法
    files = glob(os.path.join(directory, pattern))
    
    if not files:
        print(f"在 {directory} 中没有找到匹配的文件")
        return
    
    print(f"找到 {len(files)} 个m4s文件")
    
    if is_paired:
        # 尝试识别视频和音频文件对
        video_files = [f for f in files if '_video' in f or 'video' in f.lower()]
        audio_files = [f for f in files if '_audio' in f or 'audio' in f.lower()]
        
        # 如果没有明确的命名规则，尝试按顺序配对
        if not video_files or not audio_files:
            # 按文件大小排序，通常视频文件较大
            files.sort(key=lambda x: os.path.getsize(x), reverse=True)
            mid = len(files) // 2
            video_files = files[:mid]
            audio_files = files[mid:]
        
        # 配对处理
        for i in range(min(len(video_files), len(audio_files))):
            output_file = os.path.splitext(video_files[i])[0] + '.mp4'
            merge_video_audio_m4s(video_files[i], audio_files[i], output_file)
    else:
        # 单独处理每个文件
        for file in files:
            output_file = os.path.splitext(file)[0] + '.mp4'
            convert_m4s_to_mp4(file, output_file)

def main():
    parser = argparse.ArgumentParser(description='将m4s文件转换或合并为MP4格式')
    
    # 添加命令行参数
    parser.add_argument('-i', '--input', required=False, help='输入m4s文件路径')
    parser.add_argument('-o', '--output', required=False, help='输出MP4文件路径')
    parser.add_argument('-d', '--directory', required=False, help='包含m4s文件的目录')
    parser.add_argument('-v', '--video', required=False, help='视频m4s文件路径')
    parser.add_argument('-a', '--audio', required=False, help='音频m4s文件路径')
    parser.add_argument('-p', '--paired', action='store_true', help='将目录中的文件作为音视频对处理')
    parser.add_argument('-b', '--bilibili', action='store_true', help='处理哔哩哔哩下载目录结构')
    
    args = parser.parse_args()
    
    # 检查FFmpeg是否可用
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("FFmpeg 检测成功")
    except Exception:
        print("错误: 未检测到FFmpeg。请确保FFmpeg已安装并添加到系统PATH中。")
        return
    
    # 检查参数
    if args.directory:
        if args.bilibili:
            # 直接使用哔哩哔哩专用处理方法
            process_bilibili_structure(args.directory)
        else:
            # 批量处理目录
            batch_process_directory(args.directory, is_paired=args.paired)
    elif args.video and args.audio:
        # 合并视频和音频
        merge_video_audio_m4s(args.video, args.audio, args.output)
    elif args.input:
        # 单文件处理
        convert_m4s_to_mp4(args.input, args.output)
    else:
        parser.print_help()
        print("\n错误: 必须提供以下参数组合之一:")
        print("  1. --input: 单个m4s文件")
        print("  2. --video 和 --audio: 视频和音频m4s文件")
        print("  3. --directory: 包含m4s文件的目录")
        print("  4. --directory --bilibili: 处理哔哩哔哩下载目录结构")

if __name__ == "__main__":
    main()