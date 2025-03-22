import os
import sys
import subprocess
import argparse
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
    
    try:
        # 使用FFmpeg进行转换
        # -i: 指定输入文件
        # -c copy: 复制原始编解码器，不重新编码（保持质量，提高速度）
        # -y: 覆盖输出文件（如果存在）
        cmd = ['ffmpeg', '-i', input_file, '-c', 'copy', '-y', output_file]
        
        # 执行命令
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"转换成功: {input_file} -> {output_file}")
        return output_file
    
    except subprocess.CalledProcessError as e:
        print(f"转换失败: {e}")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
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
        # 移除可能的后缀如"_video"
        base_name = base_name.replace('_video', '')
        output_file = f"{base_name}.mp4"
    
    try:
        # 使用FFmpeg合并视频和音频
        cmd = [
            'ffmpeg',
            '-i', video_m4s,  # 视频输入
            '-i', audio_m4s,  # 音频输入
            '-c', 'copy',     # 复制编解码器（不重新编码）
            '-y',             # 覆盖输出文件
            output_file
        ]
        
        # 执行命令
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"合并成功: {video_m4s} + {audio_m4s} -> {output_file}")
        return output_file
    
    except subprocess.CalledProcessError as e:
        print(f"合并失败: {e}")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def process_bilibili_structure(root_dir):
    """
    处理哔哩哔哩下载的目录结构
    
    参数:
        root_dir (str): 包含多个视频目录的根目录
    """
    # 遍历根目录下的所有子目录（视频ID目录）
    for video_dir in [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d)) and d.isdigit()]:
        video_path = os.path.join(root_dir, video_dir)
        print(f"处理视频目录: {video_dir}")
        
        # 查找所有m4s文件
        m4s_files = []
        for root, _, files in os.walk(video_path):
            for file in files:
                if file.endswith('.m4s'):
                    m4s_files.append(os.path.join(root, file))
        
        if not m4s_files:
            print(f"  在 {video_dir} 中没有找到m4s文件")
            continue
            
        # 获取视频标题（如果有videoInfo.json）
        video_title = video_dir
        json_path = os.path.join(video_path, 'videoInfo.json')
        if os.path.exists(json_path):
            try:
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    video_info = json.load(f)
                    if 'title' in video_info:
                        video_title = video_info['title']
            except Exception as e:
                print(f"  读取视频信息失败: {e}")
        
        # 分类处理不同分P的视频
        video_parts = {}
        for m4s_file in m4s_files:
            # 提取分P标识符（例如 341072436_u1-1-30232.m4s）
            filename = os.path.basename(m4s_file)
            part_match = filename.split('_')[0]
            if part_match not in video_parts:
                video_parts[part_match] = []
            video_parts[part_match].append(m4s_file)
        
        # 对每个分P，处理视频
        for part_id, files in video_parts.items():
            if len(files) == 1:
                # 只有一个文件，直接转换
                output_file = os.path.join(root_dir, f"{video_title}_{part_id}.mp4")
                convert_m4s_to_mp4(files[0], output_file)
            else:
                # 多个文件，可能需要合并
                # 通常，较大的是视频文件，较小的是音频文件
                files.sort(key=lambda x: os.path.getsize(x), reverse=True)
                if len(files) >= 2:
                    output_file = os.path.join(root_dir, f"{video_title}_{part_id}.mp4")
                    merge_video_audio_m4s(files[0], files[1], output_file)
                else:
                    print(f"  警告: 分P {part_id} 没有足够的文件进行合并")

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
            merge_video_audio_m4s(video_files[i], audio_files[i])
    else:
        # 单独处理每个文件
        for file in files:
            convert_m4s_to_mp4(file)

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
    
    # 检查必要的参数组合
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