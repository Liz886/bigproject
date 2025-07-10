import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import random
import threading
import copy
import cv2
import pytesseract
import os
import numpy as np
from PIL import Image, ImageTk

# 配置Tesseract路径
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

class SudokuSolver:
    def __init__(self, board):
        self.board = board
        self.size = 9
        self.subgrid_size = 3

    def is_valid(self, row, col, num):
        # 检查行
        for i in range(self.size):
            if self.board[row][i] == num and i != col:
                return False
        # 检查列
        for i in range(self.size):
            if self.board[i][col] == num and i != row:
                return False
        # 检查九宫格
        start_row = row - row % self.subgrid_size
        start_col = col - col % self.subgrid_size
        for i in range(self.subgrid_size):
            for j in range(self.subgrid_size):
                cell_row = start_row + i
                cell_col = start_col + j
                if self.board[cell_row][cell_col] == num and (cell_row != row or cell_col != col):
                    return False
        return True

    def find_empty(self):
        # 找到候选数最少的空格，优化回溯效率
        min_candidates = self.size + 1
        empty_cell = None
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    candidates = self.get_candidates(i, j)
                    if len(candidates) < min_candidates:
                        min_candidates = len(candidates)
                        empty_cell = (i, j)
                        if min_candidates == 1:  # 找到只有一个候选数的格子，直接返回
                            return empty_cell
        return empty_cell

    def get_candidates(self, row, col):
        candidates = set(range(1, self.size + 1))
        # 移除行中已有的数字
        for num in self.board[row]:
            if num != 0:
                candidates.discard(num)
        # 移除列中已有的数字
        for i in range(self.size):
            num = self.board[i][col]
            if num != 0:
                candidates.discard(num)
        # 移除九宫格中已有的数字
        start_row = row - row % self.subgrid_size
        start_col = col - col % self.subgrid_size
        for i in range(self.subgrid_size):
            for j in range(self.subgrid_size):
                num = self.board[start_row + i][start_col + j]
                if num != 0:
                    candidates.discard(num)
        return list(candidates)

    def solve(self):
        empty_cell = self.find_empty()
        if not empty_cell:
            return True  # 数独已解
        row, col = empty_cell
        for num in self.get_candidates(row, col):
            if self.is_valid(row, col, num):
                self.board[row][col] = num
                if self.solve():
                    return True
                self.board[row][col] = 0  # 回溯
        return False
    
    def count_solutions(self):
        """计算数独解的数量，最多只计算到2个以提高效率"""
        self.solution_count = 0
        self._count_solutions_helper()
        return self.solution_count
    
    def _count_solutions_helper(self):
        empty_cell = self.find_empty()
        if not empty_cell:
            self.solution_count += 1
            return self.solution_count < 2  # 找到2个解后停止搜索
        row, col = empty_cell
        for num in self.get_candidates(row, col):
            if self.is_valid(row, col, num):
                self.board[row][col] = num
                if not self._count_solutions_helper():
                    self.board[row][col] = 0  # 回溯
                    return False
                self.board[row][col] = 0  # 回溯
        return True

    @staticmethod
    def generate_random_board(difficulty="中等"):
        """生成随机数独题目
        difficulty: 难度级别(简单/中等/困难/专家)
        返回值: (题目, 答案)
        """
        max_attempts = 150
        # 难度参数配置
        difficulty_params = {
            "简单": {"min_empty": 30, "max_empty": 35, "symmetry": True},
            "中等": {"min_empty": 40, "max_empty": 45, "symmetry": True},
            "困难": {"min_empty": 50, "max_empty": 55, "symmetry": True},
            "专家": {"min_empty": 58, "max_empty": 64, "symmetry": False}
        }
        params = difficulty_params.get(difficulty, difficulty_params["中等"])
        
        for attempt in range(max_attempts):
            # 创建空棋盘
            board = [[0 for _ in range(9)] for _ in range(9)]
            solver = SudokuSolver(board)
            
            # 随机填充对角线九宫格
            for i in range(0, 9, 3):
                nums = list(range(1, 10))
                random.shuffle(nums)
                for row in range(3):
                    for col in range(3):
                        board[i+row][i+col] = nums[row*3 + col]
            
            # 填充剩余部分
            if not solver.solve():
                continue  # 如果无法生成完整解，重新开始
            
            # 保存完整解
            solution = [row.copy() for row in board]
            
            # 随机确定挖空数量
            empty_cells = random.randint(params["min_empty"], params["max_empty"])
            
            # 生成所有可能的格子位置
            all_cells = [(i, j) for i in range(9) for j in range(9)]
            random.shuffle(all_cells)
            
            # 尝试挖空的格子列表
            cells_to_remove = []
            
            # 专家难度使用特殊策略：关键位置加权
            if difficulty == "专家":
                # 创建关键位置列表并加权
                key_positions = []
                for i in range(9):
                    for j in range(9):
                        # 中心区域（权重5）
                        if 3 <= i <= 5 and 3 <= j <= 5:
                            key_positions.extend([(i, j)] * 5)
                        # 角落位置（权重3）
                        elif (i in [0, 8] and j in [0, 8]):
                            key_positions.extend([(i, j)] * 3)
                        # 边缘中心位置（权重2）
                        elif (i in [0, 8] and j == 4) or (i == 4 and j in [0, 8]):
                            key_positions.extend([(i, j)] * 2)
                        # 其他位置（权重1）
                        else:
                            key_positions.append((i, j))
                
                # 打乱关键位置
                random.shuffle(key_positions)
                # 创建挖空单元格组（每个格子单独处理）
                cells_to_remove = [[cell] for cell in key_positions]
                
                # 准备第二阶段的备用单元格
                backup_cells = [(i, j) for i in range(9) for j in range(9)]
                random.shuffle(backup_cells)
                backup_cells = [[cell] for cell in backup_cells]
            # 对称挖空模式（用于非专家难度）
            elif params["symmetry"]:
                # 生成对称的格子对（中心对称）
                symmetric_pairs = []
                seen = set()
                for i in range(9):
                    for j in range(9):
                        if (i, j) not in seen:
                            symmetric_i, symmetric_j = 8 - i, 8 - j
                            symmetric_cell = (symmetric_i, symmetric_j)
                            if (i, j) == symmetric_cell:
                                # 中心对称点（单独处理）
                                symmetric_pairs.append([(i, j)])
                                seen.add((i, j))
                            else:
                                symmetric_pairs.append([(i, j), symmetric_cell])
                                seen.add((i, j))
                                seen.add(symmetric_cell)
                
                # 打乱对称格子对
                random.shuffle(symmetric_pairs)
                cells_to_remove = symmetric_pairs
            else:
                # 非对称模式，直接使用所有格子
                cells_to_remove = [[cell] for cell in all_cells]
            
            current_empty = 0
            removed_cells = []
            removed_values = []
            
            # 第一阶段：尝试挖空格子
            for cell_group in cells_to_remove:
                if current_empty >= empty_cells:
                    break
                
                # 跳过已经挖空的格子
                skip = False
                for (i, j) in cell_group:
                    if board[i][j] == 0 or (i, j) in removed_cells:
                        skip = True
                        break
                if skip:
                    continue
                
                # 保存原始值用于回溯
                original_values = []
                for (i, j) in cell_group:
                    original_values.append(board[i][j])
                
                # 临时挖空这些格子
                for (i, j) in cell_group:
                    board[i][j] = 0
                    current_empty += 1
                
                # 检查挖空后是否仍有唯一解
                temp_board = [row.copy() for row in board]
                temp_solver = SudokuSolver(temp_board)
                solution_count = temp_solver.count_solutions()
                
                if solution_count == 1:
                    # 挖空成功，记录这些格子
                    removed_cells.extend(cell_group)
                    removed_values.extend(original_values)
                else:
                    # 解不唯一，恢复原始值
                    for idx, (i, j) in enumerate(cell_group):
                        board[i][j] = original_values[idx]
                        current_empty -= 1
            
            # 专家模式第二阶段：补充挖空
            if difficulty == "专家" and current_empty < params["min_empty"]:
                for cell_group in backup_cells:
                    if current_empty >= params["min_empty"]:
                        break
                    
                    # 跳过已经挖空的格子
                    skip = False
                    for (i, j) in cell_group:
                        if board[i][j] == 0 or (i, j) in removed_cells:
                            skip = True
                            break
                    if skip:
                        continue
                    
                    # 保存原始值用于回溯
                    original_values = []
                    for (i, j) in cell_group:
                        original_values.append(board[i][j])
                    
                    # 临时挖空这些格子
                    for (i, j) in cell_group:
                        board[i][j] = 0
                        current_empty += 1
                    
                    # 检查挖空后是否仍有唯一解
                    temp_board = [row.copy() for row in board]
                    temp_solver = SudokuSolver(temp_board)
                    solution_count = temp_solver.count_solutions()
                    
                    if solution_count == 1:
                        # 挖空成功，记录这些格子
                        removed_cells.extend(cell_group)
                        removed_values.extend(original_values)
                    else:
                        # 解不唯一，恢复原始值
                        for idx, (i, j) in enumerate(cell_group):
                            board[i][j] = original_values[idx]
                            current_empty -= 1
            
            # 专家模式第三阶段：激进挖空策略
            if difficulty == "专家" and current_empty < params["min_empty"]:
                # 获取所有当前有数字的格子
                filled_cells = [(i, j) for i in range(9) for j in range(9) if board[i][j] != 0]
                random.shuffle(filled_cells)
                
                # 尝试挖空更多格子
                for cell in filled_cells:
                    if current_empty >= params["min_empty"]:
                        break
                    i, j = cell
                    
                    # 跳过已挖空的格子
                    if (i, j) in removed_cells:
                        continue
                    
                    # 保存原始值
                    original_value = board[i][j]
                    board[i][j] = 0
                    current_empty += 1
                    
                    # 检查挖空后是否仍有唯一解
                    temp_board = [row.copy() for row in board]
                    temp_solver = SudokuSolver(temp_board)
                    solution_count = temp_solver.count_solutions()
                    
                    if solution_count == 1:
                        # 挖空成功
                        removed_cells.append((i, j))
                        removed_values.append(original_value)
                    else:
                        # 解不唯一，恢复原始值
                        board[i][j] = original_value
                        current_empty -= 1
            
            # 最终检查解的唯一性
            final_board = [row.copy() for row in board]
            final_solver = SudokuSolver(final_board)
            solution_count = final_solver.count_solutions()
            
            if solution_count == 1:
                # 专家模式允许略低于最小值
                if difficulty == "专家":
                    if current_empty >= params["min_empty"] - 2:  # 允许56-64
                        return board, solution
                else:
                    return board, solution
        
        # 如果达到最大尝试次数仍未生成有效题目，则生成中等难度题目
        if difficulty == "专家":
            return SudokuSolver.generate_random_board("困难")
        return SudokuSolver.generate_random_board("中等")

class SudokuUI:
    def __init__(self, root):
        self.log_errors = []
        self.root = root
        self.root.title("数独求解器")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 配置样式
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", font=("微软雅黑", 10), padding=5)
        self.style.configure("TLabel", font=("微软雅黑", 10), background="#f0f0f0")
        self.style.configure("Header.TLabel", font=("微软雅黑", 14, "bold"), foreground="#2c3e50")
        self.style.configure("Time.TLabel", font=("微软雅黑", 10), foreground="#3498db")
        self.style.map("TButton",
                      foreground=[('active', 'black'), ('!active', 'black')],
                      background=[('active', '#e0e0e0'), ('!active', '#d0d0d0')])
                      
        # 配置九宫格Frame样式
        self.style.configure("Odd.TFrame", background="#e8f4f8")
        self.style.configure("Even.TFrame", background="#ffffff")
        self.style.configure("Conflict.TFrame", background="#ffcccc")
        self.style.configure("Readonly.TEntry", background="#f0f0f0", foreground="#2c3e50")
        
        self.create_widgets()
        self.loading_window = None
        self.generating = False
        self.solution = None
        self.recognition_progress = 0
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="数独求解器", style="Header.TLabel").pack(side=tk.LEFT)
        
        # 创建数独网格框架
        grid_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        grid_frame.pack(pady=10)
        
        # 创建数独网格
        self.entries = []
        for i in range(9):
            row_entries = []
            for j in range(9):
                # 创建单元格容器
                frame = ttk.Frame(grid_frame, borderwidth=0, relief=tk.FLAT)
                padx = (1, 3) if j in [2, 5] else 1
                pady = (1, 3) if i in [2, 5] else 1
                frame.grid(row=i, column=j, padx=padx, pady=pady)
                
                # 设置九宫格背景色
                bg_style = "Odd.TFrame" if (i // 3 + j // 3) % 2 == 0 else "Even.TFrame"
                frame.configure(style=bg_style)
                
                # 创建输入框
                entry = ttk.Entry(
                    frame, 
                    width=2, 
                    font=("微软雅黑", 16, "bold"), 
                    justify="center"
                )
                entry.pack(ipadx=6, ipady=6)
                
                # 限制输入只能是数字
                entry.configure(validate="key", validatecommand=(self.root.register(self.validate_input), "%P"))
                
                # 绑定键盘事件用于实时检查
                entry.bind("<KeyRelease>", lambda event, i=i, j=j: self.check_cell(i, j))
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        # 创建控制面板 - 第一行
        control_frame1 = ttk.Frame(main_frame)
        control_frame1.pack(fill=tk.X, pady=(10, 5))
        
        # 第一行左侧控制区域
        left_control1 = ttk.Frame(control_frame1)
        left_control1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 难度选择
        ttk.Label(left_control1, text="难度:").pack(side=tk.LEFT, padx=(0, 5))
        self.difficulty_var = tk.StringVar(value="专家")
        difficulty_combobox = ttk.Combobox(
            left_control1, 
            textvariable=self.difficulty_var, 
            values=["简单", "中等", "困难", "专家"], 
            state="readonly", 
            width=8
        )
        difficulty_combobox.pack(side=tk.LEFT, padx=(0, 10))
        
        # 生成按钮和图像识别按钮
        generate_button = ttk.Button(left_control1, text=" 生成随机数独", command=self.generate_random)
        generate_button.pack(side=tk.LEFT, padx=5)
        
        image_button = ttk.Button(left_control1, text="从图片识别", command=self.select_image)
        image_button.pack(side=tk.LEFT, padx=5)
        
        # 第一行右侧信息显示
        info_frame = ttk.Frame(control_frame1)
        info_frame.pack(side=tk.RIGHT)
        self.time_label = ttk.Label(info_frame, text="求解耗时: -- ms", style="Time.TLabel")
        self.time_label.pack(side=tk.LEFT, padx=10)
        self.empty_label = ttk.Label(info_frame, text="空格数: --", style="Time.TLabel")
        self.empty_label.pack(side=tk.LEFT, padx=10)
        
        # 创建控制面板 - 第二行
        control_frame2 = ttk.Frame(main_frame)
        control_frame2.pack(fill=tk.X, pady=(5, 0))
        
        # 第二行功能按钮
        button_frame = ttk.Frame(control_frame2)
        button_frame.pack(side=tk.TOP)
        ttk.Button(button_frame, text="检查", command=self.check_board).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空", command=self.clear_board).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="提示", command=self.show_hint).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="求解", command=self.solve_sudoku).pack(side=tk.LEFT, padx=5)
    
    def validate_input(self, value):
        """验证输入是否为1-9或空"""
        return not value or (value.isdigit() and 1 <= int(value) <= 9 and len(value) == 1)
    
    def get_board(self):
        """从输入框获取数独数据"""
        return [[int(entry.get()) if entry.get() else 0 for entry in row] for row in self.entries]
    
    def set_board(self, board):
        """将求解结果设置到输入框"""
        for i in range(9):
            for j in range(9):
                value = board[i][j]
                entry = self.entries[i][j]
                entry.delete(0, tk.END)
                if value != 0:
                    entry.insert(0, str(value))
                    entry.configure(foreground="#3498db")  # 已解出的数字为蓝色
    
    def count_empty_cells(self):
        """计算当前棋盘的空格数量"""
        return sum(1 for row in self.entries for entry in row if not entry.get())
    
    def solve_sudoku(self):
        """求解数独并显示结果"""
        board = self.get_board()
        solver = SudokuSolver(copy.deepcopy(board))
        
        # 检查是否有解
        solution_count = solver.count_solutions()
        if solution_count == 0:
            messagebox.showerror("错误", "该数独无解！")
            return
        elif solution_count > 1:
            messagebox.showwarning("提示", "该数独存在多个解！")
            return
        
        # 求解数独
        start_time = time.perf_counter()
        solve_result = solver.solve()
        end_time = time.perf_counter()
        
        # 显示求解时间
        solve_duration_ms = (end_time - start_time) * 1000
        self.time_label.config(text=f"求解耗时: {solve_duration_ms:.3f} ms")
        
        if solve_result:
            self.set_board(solver.board)
        else:
            messagebox.showerror("错误", "求解失败！")
    
    def clear_board(self):
        """清空所有输入框"""
        for i, row in enumerate(self.entries):
            for j, entry in enumerate(row):
                entry.delete(0, tk.END)
                entry.configure(foreground="black", state="normal")
                self.reset_cell_style(i, j)
        self.time_label.config(text="求解耗时: -- ms")
        self.empty_label.config(text="空格数: --")
    
    def show_loading(self, title="加载中", message="正在处理中...", show_progress=True):
        """显示加载弹窗"""
        if self.loading_window and self.loading_window.winfo_exists():
            return
            
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title(title)
        self.loading_window.geometry("300x120")
        self.loading_window.resizable(False, False)
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()
        self.loading_window.configure(bg="#f0f0f0")
        
        # 设置窗口位置在父窗口中心
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 60
        self.loading_window.geometry(f"+{x}+{y}")
        
        # 添加加载提示
        self.loading_label = ttk.Label(
            self.loading_window, 
            text=message, 
            font=("微软雅黑", 12, "bold"),
            foreground="#e74c3c",
            background="#f0f0f0"
        )
        self.loading_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # 添加进度条
        if show_progress:
            self.progress = ttk.Progressbar(
                self.loading_window, 
                mode="determinate",
                length=260
            )
            self.progress.pack(pady=(0, 15), padx=20)
            self.progress["value"] = 0
        
        self.loading_window.update()
    
    def update_progress(self, value, message=None):
        """更新进度条值"""
        if self.loading_window and self.loading_window.winfo_exists():
            if message:
                # 更新消息文本
                self.loading_label.config(text=message)
            
            if hasattr(self, 'progress'):
                self.progress["value"] = value
                self.progress.update()
    
    def hide_loading(self):
        """隐藏加载弹窗"""
        if self.loading_window and self.loading_window.winfo_exists():
            self.loading_window.grab_release()
            self.loading_window.destroy()
        self.loading_window = None

    def generate_random_thread(self):
        """后台线程生成数独"""
        try:
            difficulty = self.difficulty_var.get()
            puzzle, solution = SudokuSolver.generate_random_board(difficulty)
            empty_count = sum(row.count(0) for row in puzzle)
            self.root.after(0, lambda: self.set_generated_board(puzzle, solution, empty_count))
        except Exception as e:
            # 修复：捕获异常信息并传递给 lambda
            error_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成数独失败: {error_msg}"))
        finally:
            self.root.after(0, self.hide_loading)
            self.generating = False

    def generate_random(self):
        """生成随机数独题目并显示在界面上"""
        self.clear_board()
        if self.generating:
            return
            
        self.generating = True
        self.show_loading()
        
        # 在后台线程中生成数独
        threading.Thread(target=self.generate_random_thread, daemon=True).start()

    def set_generated_board(self, board, solution, empty_count):
        """设置生成的数独题目到界面"""
        self.solution = solution
        
        for i, row in enumerate(board):
            for j, value in enumerate(row):
                entry = self.entries[i][j]
                entry.delete(0, tk.END)
                if value != 0:
                    entry.insert(0, str(value))
                    entry.configure(foreground="#2c3e50", state="readonly")
                else:
                    entry.configure(state="normal")
                self.reset_cell_style(i, j)
        
        # 更新空格数量
        self.empty_label.config(text=f"空格数: {empty_count}")
        self.hide_loading()
    
    def check_board(self):
        """检查整个数独板是否有冲突"""
        board = self.get_board()
        solver = SudokuSolver(board)
        
        # 重置所有单元格样式
        for i in range(9):
            for j in range(9):
                self.reset_cell_style(i, j)
        
        conflicts = set()
        
        # 检查行冲突
        for i in range(9):
            row_values = [num for num in board[i] if num != 0]
            if len(row_values) != len(set(row_values)):
                conflicts.update((i, j) for j in range(9) if board[i][j] != 0)
        
        # 检查列冲突
        for j in range(9):
            col_values = [board[i][j] for i in range(9) if board[i][j] != 0]
            if len(col_values) != len(set(col_values)):
                conflicts.update((i, j) for i in range(9) if board[i][j] != 0)
        
        # 检查九宫格冲突
        for box_i in range(0, 9, 3):
            for box_j in range(0, 9, 3):
                box_values = [board[i][j] for i in range(box_i, box_i+3) 
                             for j in range(box_j, box_j+3) if board[i][j] != 0]
                if len(box_values) != len(set(box_values)):
                    conflicts.update((i, j) for i in range(box_i, box_i+3) 
                             for j in range(box_j, box_j+3) if board[i][j] != 0)
        
        # 标记冲突单元格
        for i, j in conflicts:
            self.mark_cell_as_conflict(i, j)
        
        # 显示检查结果
        if conflicts:
            messagebox.showwarning("检查结果", f"发现{len(conflicts)}个冲突！")
        else:
            messagebox.showinfo("检查结果", "恭喜！当前没有冲突。")
    
    def check_cell(self, row, col):
        """实时检查单个单元格是否有冲突"""
        entry = self.entries[row][col]
        if not entry.get():
            self.reset_cell_style(row, col)
            return
        
        num = int(entry.get())
        board = self.get_board()
        
        # 重置当前单元格样式
        self.reset_cell_style(row, col)
        
        # 检查当前单元格是否有冲突
        if not SudokuSolver(board).is_valid(row, col, num):
            self.mark_cell_as_conflict(row, col)
    
    def mark_cell_as_conflict(self, row, col):
        """将单元格标记为冲突状态"""
        self.entries[row][col].configure(background="#ffcccc")
        frame = self.entries[row][col].master
        frame.configure(style="Conflict.TFrame")
    
    def reset_cell_style(self, row, col):
        """重置单元格样式为正常状态"""
        entry = self.entries[row][col]
        frame = entry.master
        
        # 确定九宫格背景
        bg_style = "Odd.TFrame" if (row // 3 + col // 3) % 2 == 0 else "Even.TFrame"
        frame.configure(style=bg_style)
        
        # 设置输入框背景
        if bg_style == "Odd.TFrame":
            entry.configure(background="#e8f4f8")
        else:
            entry.configure(background="#ffffff")

    def show_hint(self):
        """显示一个随机空格的正确数字作为提示"""
        if not self.solution:
            messagebox.showinfo("提示", "请先生成数独题目")
            return

        # 获取当前棋盘的空格位置
        empty_cells = []
        for i in range(9):
            for j in range(9):
                if not self.entries[i][j].get():
                    empty_cells.append((i, j))

        if not empty_cells:
            messagebox.showinfo("提示", "数独已完成，没有空格需要提示")
            return

        # 随机选择一个空格
        i, j = random.choice(empty_cells)
        correct_value = self.solution[i][j]

        # 填入正确数字并设置样式
        entry = self.entries[i][j]
        entry.delete(0, tk.END)
        entry.insert(0, str(correct_value))
        entry.configure(foreground="#e74c3c")  # 提示数字为红色
        self.check_cell(i, j)  # 检查是否有冲突

    def select_image(self):
        """选择图片文件并识别数独"""
        file_path = filedialog.askopenfilename(
            title="选择数独图片",
            filetypes=[("图像文件", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            # 在后台线程中处理图像识别，避免UI冻结
            threading.Thread(target=lambda: self.recognize_sudoku(file_path), daemon=True).start()
    
    def recognize_sudoku(self, image_path):
        """识别图片中的数独并更新到界面"""
        try:
            # 重置进度
            self.recognition_progress = 0
            
            # 显示带有进度条的加载窗口
            self.show_loading(title="图片识别中", message="正在加载图片...", show_progress=True)
            self.update_progress(5, "正在加载图片...")
            
            # 读取图片（支持中文路径）
            import os
            import numpy as np
            
            if not os.path.exists(image_path):
                raise Exception(f"图片文件不存在: {image_path}")
            
            try:
                # 使用numpy和cv2.imdecode支持中文路径
                img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            except Exception as e:
                raise Exception(f"读取图片失败: {str(e)}, 路径: {image_path}")
            
            if img is None:
                raise Exception(f"无法解析图片文件，可能格式不支持: {image_path}")
            
            # 显示原始图像（调试用）
            # cv2.imshow("Original", img)
            # cv2.waitKey(0)
            
            self.update_progress(15, "正在预处理图像...")
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 高斯模糊降噪
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 自适应阈值处理
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # 形态学操作 - 开运算去除小噪点
            kernel = np.ones((3, 3), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # 显示处理后的图像（调试用）
            # cv2.imshow("Processed", processed)
            # cv2.waitKey(0)
            
            self.update_progress(25, "正在检测数独网格...")
            # 寻找轮廓
            contours, _ = cv2.findContours(processed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 按面积排序取前5个轮廓进行检测
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
            sudoku_contour = None
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1000:  # 降低面积阈值，适应更多图片
                    continue
                
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                
                # 检查是否为四边形且近似正方形
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h)
                    if 0.8 <= aspect_ratio <= 1.2:  # 允许更大的宽高比误差
                        sudoku_contour = approx
                        break
            
            if sudoku_contour is None:
                raise Exception("未检测到数独网格，请确保图片中包含清晰的数独且背景简单")
            
            self.update_progress(35, "正在校正图像...")
            
            # 获取轮廓的四个顶点
            points = sudoku_contour.reshape(4, 2)
            rect = np.zeros((4, 2), dtype="float32")
            
            # 按顺序排列顶点（左上、右上、右下、左下）
            s = points.sum(axis=1)
            rect[0] = points[np.argmin(s)]
            rect[2] = points[np.argmax(s)]
            
            diff = np.diff(points, axis=1)
            rect[1] = points[np.argmin(diff)]
            rect[3] = points[np.argmax(diff)]
            
            # 计算变换后图像的宽度和高度
            (tl, tr, br, bl) = rect
            widthA = np.sqrt(((br[0] - bl[0]) **2) + ((br[1] - bl[1])** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) **2) + ((tr[1] - tl[1])** 2))
            heightA = np.sqrt(((tr[0] - br[0]) **2) + ((tr[1] - br[1])** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) **2) + ((tl[1] - bl[1])** 2))
            
            # 取最大值作为目标宽度和高度
            maxWidth = max(int(widthA), int(widthB))
            maxHeight = max(int(heightA), int(heightB))
            
            # 检查变换尺寸是否有效
            if maxWidth < 200 or maxHeight < 200:
                raise Exception(f"数独网格尺寸过小，可能无法识别: {maxWidth}x{maxHeight}")
            
            # 定义目标透视变换后的点
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype="float32")
            
            # 计算透视变换矩阵并应用
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(gray, M, (maxWidth, maxHeight))
            
            # 检查变换后的图像是否有效
            if warped is None or warped.size == 0:
                raise Exception("透视变换失败，无法获取数独网格清晰视图")
            
            # 显示校正后的图像（调试用）
            # cv2.imshow("Warped", warped)
            # cv2.waitKey(0)
            
            self.update_progress(50, "正在提取数独单元格...")
            # 准备分割单元格
            cell_size = maxWidth // 9
            if cell_size < 10:
                raise Exception(f"数独网格过小，无法分割单元格: 单元格大小 {cell_size}px")
            
            # 初始化数独棋盘
            board = [[0 for _ in range(9)] for _ in range(9)]
            empty_cells = 0
            
            # 计算每个单元格的进度增量
            progress_per_cell = 45 / 81  # 剩余45%进度分配给81个单元格
            
            # 分割并识别每个单元格
            for i in range(9):
                for j in range(9):
                    # 更新进度
                    self.recognition_progress = 50 + (i * 9 + j) * progress_per_cell
                    self.update_progress(self.recognition_progress, 
                                        f"识别单元格 ({i+1}, {j+1})...")
                    
                    # 计算单元格坐标
                    x = j * cell_size
                    y = i * cell_size
                    w = cell_size
                    h = cell_size
                    
                    # 提取单元格图像
                    cell_img = warped[y:y+h, x:x+w]
                    
                    # 检查单元格图像是否有效
                    if cell_img.size == 0:
                        empty_cells += 1
                        continue
                    
                    # 预处理单元格图像
                    processed_cell = self._preprocess_cell(cell_img)
                    
                    # 识别数字
                    if processed_cell is not None:
                        num = self._recognize_digit(processed_cell)
                        if num != 0:
                            board[i][j] = num
                        else:
                            empty_cells += 1
                    else:
                        empty_cells += 1
            
            # 检查空单元格比例
            if empty_cells > 60:  # 超过60个空单元格视为识别失败
                raise Exception(f"无法识别足够的数字，仅识别到 {81-empty_cells} 个数字，请提供更清晰的数独图片")
            
            self.update_progress(95, "正在更新界面...")
            # 更新UI
            self.root.after(0, lambda: self.set_board(board))
            self.root.after(0, lambda: self.empty_label.config(text=f"空格数: {empty_cells}"))
            self.root.after(0, lambda: messagebox.showinfo("识别成功", "数独图片识别完成！"))
        except Exception as e:
            # 修复：捕获异常信息并传递给 lambda
            error_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("识别失败", f"无法识别数独: {error_msg}"))
        finally:
            self.update_progress(100, "完成！")
            time.sleep(0.5)  # 短暂显示100%进度
            self.root.after(0, self.hide_loading)
    
    def _preprocess_cell(self, cell_img):
        """预处理单元格图像以便数字识别"""
        # 调整大小
        cell_img = cv2.resize(cell_img, (50, 50))
        
        # 高斯模糊降噪
        blurred = cv2.GaussianBlur(cell_img, (3, 3), 0)
        
        # 直方图均衡化增强对比度
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equalized = clahe.apply(blurred)
        
        # 自适应阈值处理
        thresh = cv2.adaptiveThreshold(
            equalized, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 15, 3
        )
        
        # 形态学操作 - 开运算去除小噪点
        kernel = np.ones((2, 2), np.uint8)  # 减小内核大小
        processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 膨胀操作增强数字轮廓
        kernel = np.ones((1, 1), np.uint8)  # 减小内核，减少迭代次数
        processed = cv2.dilate(processed, kernel, iterations=1)
        
        # 腐蚀操作清理边缘
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.erode(processed, kernel, iterations=1)
        
        # 查找轮廓
        contours, _ = cv2.findContours(processed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 如果没有轮廓或轮廓太小，视为空格
        if not contours:
            return None
        
        # 找到最大轮廓
        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        if area < 30:  # 进一步降低面积阈值
            return None
        
        # 创建掩码
        mask = np.zeros_like(processed)
        cv2.drawContours(mask, [max_contour], -1, 255, -1)
        
        # 提取数字区域
        digit = cv2.bitwise_and(processed, processed, mask=mask)
        
        # 计算数字区域的边界框
        x, y, w, h = cv2.boundingRect(max_contour)
        
        # 裁剪数字区域
        digit_roi = digit[y:y+h, x:x+w]
        
        # 添加边框使数字居中
        bordered = cv2.copyMakeBorder(
            digit_roi, 10, 10, 10, 10, 
            cv2.BORDER_CONSTANT, value=0
        )
        
        # 调整大小为32x32以保留更多细节
        resized = cv2.resize(bordered, (32, 32))
        
        # 二值化处理
        _, binary = cv2.threshold(resized, 127, 255, cv2.THRESH_BINARY)
        
        # 确保数字为白色，背景为黑色
        if np.mean(binary) > 127:
            binary = cv2.bitwise_not(binary)
            
        return binary
    
    def _recognize_digit(self, digit_img):
        """使用Tesseract识别单个数字"""
        # 配置Tesseract
        config = '--oem 3 --psm 10 -c tessedit_char_whitelist=123456789 -c classifier_min_confidence=35 -c tessedit_enable_doc_dict=0 -c load_system_dawg=0 -c load_freq_dawg=0'
        
        # 尝试识别数字
        text = pytesseract.image_to_string(digit_img, config=config).strip()
        
        # 如果识别失败或结果不是数字，尝试使用轮廓特征进行识别
        if not text or not text.isdigit():
            # 计算轮廓特征作为备用识别方法
            contours, _ = cv2.findContours(digit_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # 取最大轮廓
                c = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(c)
                
                # 计算轮廓特征
                aspect_ratio = w / float(h)
                extent = cv2.contourArea(c) / float(w * h)
                
                # 根据特征识别数字
                if aspect_ratio > 0.8 and extent > 0.5:
                    return 8  # 8通常是封闭的
                elif aspect_ratio > 1.2:
                    return 1  # 1通常是细长的
                elif extent < 0.3:
                    return 7  # 7通常面积较小
                elif aspect_ratio < 0.7:
                    return 0  # 0通常是宽高比较小的
            return 0
        
        # 有时Tesseract会返回多个字符，只取第一个数字
        if len(text) > 1:
            for char in text:
                if char.isdigit():
                    return int(char)
            return 0
        
        return int(text)

    def log_error(self, message):
        self.log_errors.append(message)
        print(f"识别错误: {message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuUI(root)
    root.mainloop()