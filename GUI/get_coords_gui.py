# -*- coding: utf-8 -*-
"""
@作者     : 为您修改和优化的AI助手
@文件名   : get_coords_gui_final.py
@描述     : 最终优化版坐标拾取工具。视频在左，控制在右，坐标显示为表格。
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import pyperclip

class CoordinatePickerApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # --- 窗口基础设置 ---
        self.title("视频坐标拾取工具")
        self.geometry("1200x700")
        # 让左侧的视频列 (column 0) 随窗口缩放
        self.grid_columnconfigure(0, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # --- 核心变量 ---
        self.video_path = None
        self.video_cap = None
        self.original_frame = None
        self.photo_image = None
        
        self.frame_width = 0
        self.frame_height = 0

        # 创建所有界面组件
        self._create_widgets()

    def _create_widgets(self):
        # --- 左侧：视频预览区 (新布局) ---
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack(expand=True, fill="both")

        # --- 右侧：控制面板 (新布局) ---
        self.control_frame = ctk.CTkFrame(self, width=250)
        self.control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        self.btn_open = ctk.CTkButton(self.control_frame, text="打开视频文件", command=self.open_video_file)
        self.btn_open.pack(pady=10, padx=10, fill="x")

        # 视频进度滑块
        self.slider_label = ctk.CTkLabel(self.control_frame, text="视频进度 (帧):")
        self.slider_label.pack(pady=(10, 0))
        self.frame_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=self.on_slider_move)
        self.frame_slider.set(0)
        self.frame_slider.pack(pady=10, padx=10, fill="x")

        # Y 和 H 滑块
        self.y_label = ctk.CTkLabel(self.control_frame, text="Y (上边界): 0")
        self.y_label.pack(pady=(10, 0))
        self.y_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=self.update_all)
        self.y_slider.pack(pady=5, padx=10, fill="x")

        self.h_label = ctk.CTkLabel(self.control_frame, text="H (高度): 0")
        self.h_label.pack(pady=(10, 0))
        self.h_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=self.update_all)
        self.h_slider.pack(pady=5, padx=10, fill="x")

        # X 和 W 滑块
        self.x_label = ctk.CTkLabel(self.control_frame, text="X (左边界): 0")
        self.x_label.pack(pady=(10, 0))
        self.x_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=self.update_all)
        self.x_slider.pack(pady=5, padx=10, fill="x")

        self.w_label = ctk.CTkLabel(self.control_frame, text="W (宽度): 0")
        self.w_label.pack(pady=(10, 0))
        self.w_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, command=self.update_all)
        self.w_slider.pack(pady=5, padx=10, fill="x")

        # --- 全新的表格化坐标显示区域 ---
        self.coords_title_label = ctk.CTkLabel(self.control_frame, text="最终坐标:", font=("微软雅黑", 14, "bold"))
        self.coords_title_label.pack(pady=(20, 5))
        
        # 创建一个框架来容纳表格
        self.coords_table_frame = ctk.CTkFrame(self.control_frame)
        self.coords_table_frame.pack(pady=5, padx=10, fill="x")
        self.coords_table_frame.grid_columnconfigure(1, weight=1)

        # ymin 行
        ctk.CTkLabel(self.coords_table_frame, text="ymin:").grid(row=0, column=0, padx=5, sticky="w")
        self.ymin_val_label = ctk.CTkLabel(self.coords_table_frame, text="0", font=("Consolas", 12))
        self.ymin_val_label.grid(row=0, column=1, padx=5, sticky="e")
        # ymax 行
        ctk.CTkLabel(self.coords_table_frame, text="ymax:").grid(row=1, column=0, padx=5, sticky="w")
        self.ymax_val_label = ctk.CTkLabel(self.coords_table_frame, text="0", font=("Consolas", 12))
        self.ymax_val_label.grid(row=1, column=1, padx=5, sticky="e")
        # xmin 行
        ctk.CTkLabel(self.coords_table_frame, text="xmin:").grid(row=2, column=0, padx=5, sticky="w")
        self.xmin_val_label = ctk.CTkLabel(self.coords_table_frame, text="0", font=("Consolas", 12))
        self.xmin_val_label.grid(row=2, column=1, padx=5, sticky="e")
        # xmax 行
        ctk.CTkLabel(self.coords_table_frame, text="xmax:").grid(row=3, column=0, padx=5, sticky="w")
        self.xmax_val_label = ctk.CTkLabel(self.coords_table_frame, text="0", font=("Consolas", 12))
        self.xmax_val_label.grid(row=3, column=1, padx=5, sticky="e")
        
        self.btn_copy = ctk.CTkButton(self.control_frame, text="复制元组 (ymin, ymax, xmin, xmax)", command=self.copy_coordinates)
        self.btn_copy.pack(pady=20, padx=10, fill="x")
        
    def open_video_file(self):
        self.video_path = filedialog.askopenfilename(filetypes=(("视频文件", "*.mp4 *.flv *.wmv *.avi"), ("所有文件", "*.*")))
        if not self.video_path: return
            
        self.video_cap = cv2.VideoCapture(self.video_path)
        if not self.video_cap.isOpened():
            messagebox.showerror("错误", "无法打开视频文件。")
            return
            
        self.frame_width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 更新所有滑块的范围
        self.frame_slider.configure(to=frame_count)
        self.y_slider.configure(to=self.frame_height)
        self.h_slider.configure(to=self.frame_height)
        self.x_slider.configure(to=self.frame_width)
        self.w_slider.configure(to=self.frame_width)
        
        # 默认加载第一帧
        self.on_slider_move(1)

    def on_slider_move(self, frame_no_str):
        if not self.video_cap: return
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, int(float(frame_no_str)))
        ret, frame = self.video_cap.read()
        if ret:
            self.original_frame = frame
            # 触发一次更新来显示新帧
            self.update_all(None)

    def update_all(self, _):
        if self.original_frame is None: return

        # 从滑块获取 y, h, x, w 的值
        y = int(self.y_slider.get())
        h = int(self.h_slider.get())
        x = int(self.x_slider.get())
        w = int(self.w_slider.get())
        
        # 更新滑块旁边的标签
        self.y_label.configure(text=f"Y (上边界): {y}")
        self.h_label.configure(text=f"H (高度): {h}")
        self.x_label.configure(text=f"X (左边界): {x}")
        self.w_label.configure(text=f"W (宽度): {w}")

        # 计算最终坐标
        ymin, ymax, xmin, xmax = y, y + h, x, x + w
        
        # 更新表格化的坐标显示
        self.ymin_val_label.configure(text=str(ymin))
        self.ymax_val_label.configure(text=str(ymax))
        self.xmin_val_label.configure(text=str(xmin))
        self.xmax_val_label.configure(text=str(xmax))

        # 绘制预览矩形框
        draw_frame = self.original_frame.copy()
        cv2.rectangle(draw_frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 3)

        # 延迟执行图像显示，以确保窗口尺寸已就绪
        self.after(1, lambda: self.display_image(draw_frame))

    def display_image(self, image_to_show):
        label_w, label_h = self.video_label.winfo_width(), self.video_label.winfo_height()
        if label_w < 50 or label_h < 50:
             self.after(20, lambda: self.display_image(image_to_show))
             return
             
        h, w, _ = image_to_show.shape
        scale = min(label_w / w, label_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        resized_frame = cv2.resize(image_to_show, (new_w, new_h))
        img = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        self.photo_image = ImageTk.PhotoImage(image=Image.fromarray(img))
        self.video_label.configure(image=self.photo_image)

    def copy_coordinates(self):
        # 重新计算一次以确保数据最新
        y = int(self.y_slider.get())
        h = int(self.h_slider.get())
        x = int(self.x_slider.get())
        w = int(self.w_slider.get())
        ymin, ymax, xmin, xmax = y, y + h, x, x + w
        
        # 格式化为元组字符串
        coords_tuple_string = f"({ymin}, {ymax}, {xmin}, {xmax})"
        
        # 使用 pyperclip 库复制
        pyperclip.copy(coords_tuple_string)
        messagebox.showinfo("成功", f"坐标已复制到剪贴板:\n{coords_tuple_string}")


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = CoordinatePickerApp()
    app.mainloop()
