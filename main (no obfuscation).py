import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import re

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("影音下載器")
        self.root.geometry("600x350")
        self.root.resizable(False, False)
        
        # 設定風格
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Microsoft JhengHei", 10))
        self.style.configure("TRadiobutton", font=("Microsoft JhengHei", 10))
        self.style.configure("TLabel", font=("Microsoft JhengHei", 10))
        
        # 建立主框架
        main_frame = ttk.Frame(root, padding=(20, 10, 20, 20))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL 輸入
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        url_label = ttk.Label(url_frame, text="請輸入影片連結:")
        url_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(fill=tk.X)
        
        # 格式選擇
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill=tk.X, pady=10)
        
        format_label = ttk.Label(format_frame, text="請選擇下載格式:")
        format_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.format_var = tk.StringVar(value="mp4")
        
        mp4_radio = ttk.Radiobutton(format_frame, text="視訊格式 (mp4)", variable=self.format_var, value="mp4")
        mp4_radio.pack(anchor=tk.W)
        
        mp3_radio = ttk.Radiobutton(format_frame, text="音訊格式 (mp3)", variable=self.format_var, value="mp3")
        mp3_radio.pack(anchor=tk.W)
        
        # 下載位置
        location_frame = ttk.Frame(main_frame)
        location_frame.pack(fill=tk.X, pady=10)
        
        location_label = ttk.Label(location_frame, text="下載位置:")
        location_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.location_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        location_entry = ttk.Entry(location_frame, textvariable=self.location_var, width=30)
        location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(location_frame, text="瀏覽", command=self.browse_location)
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 進度條
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="準備下載")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # 下載按鈕
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)
        
        self.download_button = ttk.Button(button_frame, text="開始下載", command=self.start_download)
        self.download_button.pack(fill=tk.X, pady=(0, 10))
    
    def browse_location(self):
        """選擇下載位置"""
        directory = filedialog.askdirectory()
        if directory:
            self.location_var.set(directory)
    
    def start_download(self):
        """開始下載處理"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("錯誤", "請輸入有效的影片連結")
            return
        
        # 禁用下載按鈕防止重複點擊
        self.download_button.configure(state="disabled")
        self.status_var.set("正在準備下載...")
        self.progress_var.set(0)
        
        # 在新線程中執行下載以避免凍結UI
        download_thread = threading.Thread(target=self.download_media, args=(url,))
        download_thread.daemon = True
        download_thread.start()
    
    def download_media(self, url):
        """使用yt-dlp下載媒體"""
        try:
            download_format = self.format_var.get()
            
            # 根據所選格式設定yt-dlp選項
            if download_format == "mp4":
                output_template = os.path.join(self.location_var.get(), '%(title)s.%(ext)s')
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': output_template,
                    'progress_hooks': [self.progress_hook],
                }
            else:  # mp3
                output_template = os.path.join(self.location_var.get(), '%(title)s.%(ext)s')
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_template,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [self.progress_hook],
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.root.after(0, lambda: self.status_var.set("獲取影片信息..."))
                info = ydl.extract_info(url, download=False)
                self.root.after(0, lambda: self.status_var.set(f"開始下載: {info.get('title', '未知標題')}"))
                ydl.download([url])
                
                # 下載完成後更新UI
                self.root.after(0, lambda: self.complete_download("下載完成!"))
        
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: self.complete_download(f"錯誤: {error_message}"))
    
    def format_eta(self, eta_str):
        """格式化剩餘時間，確保顯示正確"""
        if not eta_str:
            return "未知"
            
        # 移除可能的方括號，確保格式一致
        eta_str = eta_str.replace("[", "").replace("]", "")
        
        # 檢查是否為 HH:MM:SS 格式
        if re.match(r'^\d+:\d+:\d+$', eta_str):
            return eta_str
        # 檢查是否為 MM:SS 格式
        elif re.match(r'^\d+:\d+$', eta_str):
            return eta_str
        # 如果是純數字，假設為秒數
        elif eta_str.isdigit():
            seconds = int(eta_str)
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        else:
            return eta_str  # 無法格式化，返回原字符串
    
    def progress_hook(self, d):
        """處理下載進度回調"""
        if d['status'] == 'downloading':
            # 計算下載百分比
            if 'total_bytes' in d and d['total_bytes'] > 0:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percent = 0
            
            # 更新進度條
            self.root.after(0, lambda: self.progress_var.set(percent))
            
            # 獲取並格式化下載信息
            percent_str = d.get('_percent_str', '0%').strip()
            speed_str = d.get('_speed_str', '未知').strip()
            eta_str = self.format_eta(d.get('_eta_str', '未知').strip())
            
            # 顯示下載速度和剩餘時間，確保格式完整
            status_text = f"下載中: {percent_str} 速度: {speed_str} 剩餘時間: {eta_str}"
            self.root.after(0, lambda: self.status_var.set(status_text))
        
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.status_var.set("下載完成，正在處理文件..."))
    
    def complete_download(self, message):
        """完成下載，重設UI狀態"""
        self.status_var.set(message)
        self.download_button.configure(state="normal")
        if "錯誤" not in message:
            self.progress_var.set(100)

if __name__ == "__main__":
    root = tk.Tk()
    # 修正高DPI顯示問題 (Windows)
    if sys.platform.startswith('win'):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    app = DownloaderApp(root)
    root.mainloop()