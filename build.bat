pyinstaller --onefile --noconsole --icon=hi.ico --clean --name=MediaDownloader --hidden-import=yt_dlp --hidden-import=tkinter --hidden-import=pyarmor_runtime --hidden-import=tkinter.ttk --hidden-import=tkinter.filedialog main.py