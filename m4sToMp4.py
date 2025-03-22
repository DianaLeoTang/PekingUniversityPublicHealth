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

def batch_process_directory(directory, pattern='*.m4s', is_paired=False):
    """
    批量处理目录中的所有m4s文件
    
    参数:
        directory (str): 包含m4s文件的目录
        pattern (str): 文件匹配模式
        is_paired (bool): 是否将文件视为音视频配对处理
    """
    # 获取所有匹配的文件
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
    
    args = parser.parse_args()
    
    # 检查必要的参数组合
    if args.directory:
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

if __name__ == "__main__":
    main()