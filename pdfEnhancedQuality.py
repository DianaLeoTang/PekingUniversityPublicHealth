'''
Author: Diana Tang
Date: 2025-03-30 23:57:55
LastEditors: Diana Tang
Description: some description
FilePath: /AI-Health-News-Agent-Back/main.py
'''
import os
import tempfile
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from pdf2image import convert_from_path

def enhance_pdf_clarity(input_pdf_path, output_pdf_path, dpi=300):
    """提升PDF文件的清晰度"""
    print(f"正在处理PDF文件: {input_pdf_path}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 将PDF转换为图像
        print("将PDF转换为图像...")
        images = convert_from_path(input_pdf_path, dpi=dpi)
        
        # 创建新的PDF文档
        pdf_output = fitz.open()
        
        for i, img in enumerate(images):
            print(f"正在增强第 {i+1}/{len(images)} 页...")
            
            # 转换为OpenCV格式进行处理
            img_np = np.array(img)
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            # 应用图像增强技术
            # 1. 去噪
            img_cv = cv2.fastNlMeansDenoisingColored(img_cv, None, 10, 10, 7, 21)
            
            # 2. 锐化
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            img_cv = cv2.filter2D(img_cv, -1, kernel)
            
            # 3. 对比度增强
            img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
            enhancer = ImageEnhance.Contrast(img_pil)
            img_pil = enhancer.enhance(1.2)
            
            # 4. 亮度调整
            enhancer = ImageEnhance.Brightness(img_pil)
            img_pil = enhancer.enhance(1.1)
            
            # 5. 锐度增强
            enhancer = ImageEnhance.Sharpness(img_pil)
            img_pil = enhancer.enhance(1.5)
            
            # 保存增强后的图像到临时文件
            temp_img_path = os.path.join(temp_dir, f"enhanced_{i}.png")
            img_pil.save(temp_img_path)
            
            # 将图像添加到PDF
            pdf_page = pdf_output.new_page(
                width=img_pil.width,
                height=img_pil.height
            )
            
            # 将图像插入页面
            rect = fitz.Rect(0, 0, img_pil.width, img_pil.height)
            pdf_page.insert_image(rect, filename=temp_img_path)
        
        # 保存PDF
        pdf_output.save(output_pdf_path)
        pdf_output.close()
        
        print(f"增强后的PDF已保存至: {output_pdf_path}")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
    
    finally:
        # 清理临时文件
        for file in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, file))
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass

if __name__ == "__main__":
    # 使用示例
   input_pdf = "./卫生统计学_赵耐青.pdf"  # 替换为您的输入PDF路径
   output_pdf = "./enhanced_卫生统计学_赵耐青.pdf"  # 输出PDF路径
   enhance_pdf_clarity(input_pdf, output_pdf, dpi=300)