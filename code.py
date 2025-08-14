import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import json
import re

# グローバル変数
TkinterDnD = None
DND_FILES = None

class FileStructureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ファイル構造ジェネレーター")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # アプリのスタイル設定
        self.setup_style()
        
        # メインフレームの作成
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # トップフレーム (ドラッグ&ドロップエリアとボタン)
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ドラッグ&ドロップエリア
        self.drop_frame = ttk.Frame(self.top_frame, padding="20", style="Drop.TFrame")
        self.drop_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.drop_label = ttk.Label(
            self.drop_frame, 
            text="ここにフォルダをドラッグ&ドロップするか、\nフォルダを選択ボタンをクリックしてください",
            justify=tk.CENTER,
            style="Drop.TLabel"
        )
        self.drop_label.pack(fill=tk.BOTH, expand=True)
        
        # ドラッグ&ドロップイベントのバインド
        if TkinterDnD:
            self.setup_drag_drop(self.drop_frame)
            self.setup_drag_drop(self.drop_label)
        
        # ボタンフレーム
        self.button_frame = ttk.Frame(self.top_frame)
        self.button_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        # フォルダ選択ボタン
        self.select_button = ttk.Button(
            self.button_frame, 
            text="フォルダを選択", 
            command=self.select_folder
        )
        self.select_button.pack(fill=tk.X, pady=(0, 5))
        
        # コピーボタン
        self.copy_button = ttk.Button(
            self.button_frame, 
            text="結果をコピー", 
            command=self.copy_to_clipboard
        )
        self.copy_button.pack(fill=tk.X, pady=(0, 5))
        
        # 保存ボタン
        self.save_button = ttk.Button(
            self.button_frame, 
            text="結果を保存", 
            command=self.save_to_file
        )
        self.save_button.pack(fill=tk.X)
        
        # 出力タブコントロール
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # テキスト形式タブ
        self.text_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.text_tab, text="テキスト形式")
        
        # インデントオプションフレーム
        self.indent_frame = ttk.Frame(self.text_tab, padding="5")
        self.indent_frame.pack(fill=tk.X)
        
        ttk.Label(self.indent_frame, text="インデント:").pack(side=tk.LEFT)
        
        self.indent_var = tk.StringVar(value="  ")
        indent_options = [("スペース2つ", "  "), ("スペース4つ", "    "), ("タブ", "\t")]
        
        for text, value in indent_options:
            ttk.Radiobutton(
                self.indent_frame, 
                text=text, 
                variable=self.indent_var, 
                value=value,
                command=self.update_output
            ).pack(side=tk.LEFT, padx=(5, 10))
        
        # テキスト形式の出力エリア
        self.text_output = ScrolledText(self.text_tab, wrap=tk.NONE, font=("Courier", 10))
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # JSONタブ
        self.json_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.json_tab, text="JSON形式")
        
        # JSON形式の出力エリア
        self.json_output = ScrolledText(self.json_tab, wrap=tk.NONE, font=("Courier", 10))
        self.json_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # 初期状態設定
        if not TkinterDnD:
            self.status_var.set("注意: ドラッグ&ドロップライブラリがインストールされていません。'pip install tkinterdnd2'でインストールしてください。")
        else:
            self.status_var.set("準備完了")
        
        # 最初に選択されているタブを保存
        self.current_tab_index = 0
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        # 現在のファイル構造
        self.current_structure = None

    def setup_style(self):
        """アプリのスタイルをセットアップ"""
        style = ttk.Style()
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TButton", padding=5)
        style.configure("TLabel", background="#f5f5f5", font=("Arial", 10))
        style.configure("TNotebook", background="#f5f5f5")
        style.configure("TNotebook.Tab", padding=[10, 2])
        
        # ドラッグ&ドロップエリアのスタイル
        style.configure(
            "Drop.TFrame", 
            background="#e1f5fe", 
            borderwidth=2, 
            relief="groove"
        )
        style.configure(
            "Drop.TLabel", 
            background="#e1f5fe", 
            font=("Arial", 12),
            foreground="#0277bd"
        )
        
    def setup_drag_drop(self, widget):
        """ドラッグ&ドロップイベントの設定"""
        if TkinterDnD:
            # tkinterdnd2がある場合
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self.drop_files)

    def drop_files(self, event):
        """ドラッグ&ドロップされたファイルの処理"""
        try:
            # ドラッグされたデータからパスを抽出
            path = event.data
            
            # Windows形式のパスを処理 ('{C:/path/to/file}' の形式)
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]
                
            # 引用符があれば削除
            path = path.strip('"')
                
            if os.path.isdir(path):
                self.process_folder(path)
            else:
                messagebox.showwarning("警告", "ドロップされたのはフォルダではありません。")
        except Exception as e:
            messagebox.showerror("エラー", f"ドラッグ&ドロップ処理中にエラーが発生しました:\n{str(e)}")

    def select_folder(self):
        """フォルダ選択ダイアログを表示"""
        folder_path = filedialog.askdirectory(title="フォルダを選択")
        if folder_path:
            self.process_folder(folder_path)

    def process_folder(self, folder_path):
        """フォルダの処理とファイル構造の生成"""
        try:
            self.status_var.set(f"処理中: {folder_path}")
            self.root.update()
            
            # フォルダ構造を取得
            self.current_structure = self.get_folder_structure(folder_path)
            
            # 出力を更新
            self.update_output()
            
            self.status_var.set(f"完了: {folder_path}")
        except Exception as e:
            messagebox.showerror("エラー", f"フォルダ処理中にエラーが発生しました:\n{str(e)}")
            self.status_var.set("エラーが発生しました")

    def get_folder_structure(self, folder_path):
        """フォルダ構造を再帰的に取得"""
        result = {}
        folder_name = os.path.basename(folder_path)
        if not folder_name:  # ルートディレクトリの場合
            folder_name = folder_path
        result[folder_name + "/"] = self._scan_directory(folder_path)
        return result

    def _scan_directory(self, path):
        """ディレクトリを再帰的にスキャン"""
        items = {}
        
        try:
            # ディレクトリ内のアイテムを取得してソート
            dir_items = sorted(os.listdir(path))
            
            for item in dir_items:
                item_path = os.path.join(path, item)
                
                # 隠しファイル/フォルダをスキップ（オプション）
                # if item.startswith('.'):
                #     continue
                    
                if os.path.isdir(item_path):
                    items[item + '/'] = self._scan_directory(item_path)
                else:
                    items[item] = None
        except PermissionError:
            # アクセス権限がない場合
            self.status_var.set(f"警告: アクセス権限がありません: {path}")
        except Exception as e:
            # その他のエラー
            self.status_var.set(f"警告: エラーが発生しました: {path} - {str(e)}")
            
        return items

    def update_output(self):
        """現在の構造に基づいて出力を更新"""
        if not self.current_structure:
            return
            
        # テキスト形式の出力を更新
        text_output = self.structure_to_text(self.current_structure)
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, text_output)
        
        # JSON形式の出力を更新
        json_output = json.dumps(self.current_structure, indent=2, ensure_ascii=False)
        self.json_output.delete(1.0, tk.END)
        self.json_output.insert(tk.END, json_output)

    def structure_to_text(self, structure, level=0):
        """構造をテキスト形式に変換"""
        indent = self.indent_var.get()
        result = []
        
        for folder, items in structure.items():
            result.append(indent * level + folder)
            
            if items:
                if isinstance(items, dict):
                    result.append(self.dict_to_text(items, level + 1, indent))
                    
        return "\n".join(result)

    def dict_to_text(self, items, level, indent):
        """辞書をテキスト形式に変換（再帰的）"""
        result = []
        
        for key, value in sorted(items.items()):
            result.append(indent * level + key)
            
            if value and isinstance(value, dict):
                result.append(self.dict_to_text(value, level + 1, indent))
                
        return "\n".join(result)

    def copy_to_clipboard(self):
        """現在のタブの内容をクリップボードにコピー"""
        try:
            if self.current_tab_index == 0:  # テキスト形式
                text = self.text_output.get(1.0, tk.END)
            else:  # JSON形式
                text = self.json_output.get(1.0, tk.END)
                
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("クリップボードにコピーしました")
        except Exception as e:
            messagebox.showerror("エラー", f"コピー中にエラーが発生しました:\n{str(e)}")

    def save_to_file(self):
        """現在のタブの内容をファイルに保存"""
        try:
            if self.current_tab_index == 0:  # テキスト形式
                file_types = [("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
                default_ext = ".txt"
                content = self.text_output.get(1.0, tk.END)
            else:  # JSON形式
                file_types = [("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
                default_ext = ".json"
                content = self.json_output.get(1.0, tk.END)
                
            file_path = filedialog.asksaveasfilename(
                filetypes=file_types,
                defaultextension=default_ext,
                title="ファイルに保存"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                self.status_var.set(f"保存しました: {file_path}")
        except Exception as e:
            messagebox.showerror("エラー", f"保存中にエラーが発生しました:\n{str(e)}")

    def on_tab_change(self, event):
        """タブが変更されたときのハンドラ"""
        self.current_tab_index = self.tab_control.index(self.tab_control.select())

# メインコード部分

# tkinterdnd2のインポートを試みる
try:
    from tkinterdnd2 import TkinterDnD as _TkinterDnD
    from tkinterdnd2 import DND_FILES as _DND_FILES
    TkinterDnD = _TkinterDnD
    DND_FILES = _DND_FILES
    # TkinterDnDを使用するためにルートウィンドウを置き換え
    root = TkinterDnD.Tk()
except ImportError:
    # モジュールがない場合は通常のTkを使用
    root = tk.Tk()
    # 警告を表示
    messagebox.showwarning(
        "警告", 
        "ドラッグ&ドロップライブラリがインストールされていません。\n"
        "完全な機能を使用するには、以下のコマンドでライブラリをインストールしてください：\n"
        "pip install tkinterdnd2\n\n"
        "現在はフォルダ選択ボタンのみ使用できます。"
    )

# アプリケーション起動
app = FileStructureApp(root)
root.mainloop()