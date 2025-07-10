import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import random
import threading
import copy
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageTk
import os

# 设置Tesseract路径（如果环境变量未设置）
# pytesseract.pytesseract.tesseract_cmd = r'<你的Tesseract路径>'

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
        self.root = root
        self.root.title("数独求解器与识别器")
        self.root.geometry("700x750")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f5ff")
        
        # 设置图标
        try:
            self.root.iconbitmap("sudoku_icon.ico")
        except:
            pass
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 配置样式
        self.style.configure("TFrame", background="#f0f5ff")
        self.style.configure("TButton", font=("Arial", 10), padding=8)
        self.style.configure("TLabel", font=("Arial", 10), background="#f0f5ff")
        self.style.configure("Header.TLabel", font=("Arial", 16, "bold"), foreground="#2c3e50")
        self.style.configure("Time.TLabel", font=("Arial", 10), foreground="#3498db")
        self.style.map("TButton",
                      foreground=[('active', 'white'), ('!active', 'white')],
                      background=[('active', '#4a6baf'), ('!active', '#3a5599')])
        
        # 配置九宫格Frame样式
        self.style.configure("Odd.TFrame", background="#e8f4f8")
        self.style.configure("Even.TFrame", background="#ffffff")
        self.style.configure("Conflict.TFrame", background="#ffcccc")
        self.style.configure("Readonly.TEntry", background="#f0f0f0", foreground="#2c3e50")
        
        self.create_widgets()
        self.loading_window = None
        self.generating = False
        self.solution = None
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 标题
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header_frame, text="数独求解器与识别器", style="Header.TLabel").pack(side=tk.LEFT)
        
        # 创建数独网格框架
        grid_frame = ttk.Frame(main_frame, relief=tk.GROOVE, borderwidth=2, padding=5)
        grid_frame.pack(pady=10)
        
        # 创建数独网格
        self.entries = []
        for i in range(9):
            row_entries = []
            for j in range(9):
                # 创建单元格容器
                frame = ttk.Frame(grid_frame, borderwidth=0, relief=tk.FLAT)
                padx = (1, 5) if j in [2, 5] else 1
                pady = (1, 5) if i in [2, 5] else 1
                frame.grid(row=i, column=j, padx=padx, pady=pady)
                
                # 设置九宫格背景色
                bg_style = "Odd.TFrame" if (i // 3 + j // 3) % 2 == 0 else "Even.TFrame"
                frame.configure(style=bg_style)
                
                # 创建输入框
                entry = ttk.Entry(
                    frame, 
                    width=2, 
                    font=("Arial", 18, "bold"), 
                    justify="center"
                )
                entry.pack(ipadx=8, ipady=8)
                
                # 限制输入只能是数字
                entry.configure(validate="key", validatecommand=(self.root.register(self.validate_input), "%P"))
                
                # 绑定键盘事件用于实时检查
                entry.bind("<KeyRelease>", lambda event, i=i, j=j: self.check_cell(i, j))
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        # 创建控制面板 - 第一行
        control_frame1 = ttk.Frame(main_frame)
        control_frame1.pack(fill=tk.X, pady=(10, 5))
        
        # 难度选择
        ttk.Label(control_frame1, text="难度级别:").pack(side=tk.LEFT, padx=(0, 5))
        self.difficulty_var = tk.StringVar(value="中等")
        difficulty_combobox = ttk.Combobox(
            control_frame1, 
            textvariable=self.difficulty_var, 
            values=["简单", "中等", "困难", "专家"], 
            state="readonly", 
            width=8
        )
        difficulty_combobox.pack(side=tk.LEFT, padx=(0, 10))
        
        # 生成按钮和图像识别按钮
        generate_button = ttk.Button(control_frame1, text="生成随机数独", command=self.generate_random)
        generate_button.pack(side=tk.LEFT, padx=5)
        
        image_button = ttk.Button(control_frame1, text="从图片识别数独", command=self.select_image)
        image_button.pack(side=tk.LEFT, padx=5)
        
        # 信息显示
        info_frame = ttk.Frame(control_frame1)
        info_frame.pack(side=tk.RIGHT)
        self.time_label = ttk.Label(info_frame, text="求解耗时: -- ms", style="Time.TLabel")
        self.time_label.pack(side=tk.LEFT, padx=10)
        self.empty_label = ttk.Label(info_frame, text="空格数: --", style="Time.TLabel")
        self.empty_label.pack(side=tk.LEFT, padx=10)
        
        # 创建控制面板 - 第二行
        control_frame2 = ttk.Frame(main_frame)
        control_frame2.pack(fill=tk.X, pady=(5, 10))
        
        # 第二行功能按钮
        button_frame = ttk.Frame(control_frame2)
        button_frame.pack(side=tk.TOP, pady=5)
        
        ttk.Button(button_frame, text="检查冲突", command=self.check_board).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空棋盘", command=self.clear_board).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="显示提示", command=self.show_hint).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="求解数独", command=self.solve_sudoku).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出题目", command=self.export_sudoku).pack(side=tk.LEFT, padx=5)
    
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
                    entry.configure(state="normal")
    
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
        self.solution = None
    
    def show_loading(self, message="正在处理中..."):
        """显示加载弹窗"""
        if self.loading_window and self.loading_window.winfo_exists():
            return
            
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("加载中")
        self.loading_window.geometry("350x150")
        self.loading_window.resizable(False, False)
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()
        self.loading_window.configure(bg="#f0f0f0")
        
        # 设置窗口位置在父窗口中心
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        self.loading_window.geometry(f"+{x}+{y}")
        
        # 添加加载提示
        ttk.Label(
            self.loading_window, 
            text=message, 
            font=("Arial", 12, "bold"),
            foreground="#e74c3c",
            background="#f0f0f0"
        ).pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # 添加进度条
        self.progress = ttk.Progressbar(
            self.loading_window, 
            mode="indeterminate",
            length=280
        )
        self.progress.pack(pady=(0, 15), padx=20)
        self.progress.start(10)
        
        self.loading_window.update()
    
    def hide_loading(self):
        """隐藏加载弹窗"""
        if self.loading_window and self.loading_window.winfo_exists():
            self.progress.stop()
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
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成数独失败: {str(e)}"))
        finally:
            self.root.after(0, self.hide_loading)
            self.generating = False

    def generate_random(self):
        """生成随机数独题目并显示在界面上"""
        self.clear_board()
        if self.generating:
            return
            
        self.generating = True
        message = "正在生成专家级数独..." if self.difficulty_var.get() == "专家" else "正在生成数独..."
        self.show_loading(message)
        
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
                    entry.configure(foreground="#2c3e50", state="normal")
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
            self.show_loading("正在识别图片中的数独...")
            # 在后台线程中处理图像识别，避免UI冻结
            threading.Thread(target=lambda: self.recognize_sudoku(file_path), daemon=True).start()
    
    def recognize_sudoku(self, image_path):
        """识别图片中的数独并更新到界面"""
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                raise Exception("无法读取图片文件")
            
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 高斯模糊降噪
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 自适应阈值处理
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # 寻找轮廓
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 找到最大的矩形轮廓（数独网格）
            sudoku_contour = None
            max_area = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 5000:
                    perimeter = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                    if len(approx) == 4 and area > max_area:
                        max_area = area
                        sudoku_contour = approx
            
            if sudoku_contour is None:
                raise Exception("未检测到数独网格")
            
            # 透视变换提取数独网格
            pts = sudoku_contour.reshape(4, 2)
            rect = self._order_points(pts)
            (tl, tr, br, bl) = rect
            
            # 计算宽度和高度
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            
            # 变换矩阵
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype = "float32")
            
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(gray, M, (maxWidth, maxHeight))
            
            # 分割单元格并识别数字
            board = [[0 for _ in range(9)] for _ in range(9)]
            cell_size = maxWidth // 9
            
            for i in range(9):
                for j in range(9):
                    # 提取单元格区域
                    x = j * cell_size
                    y = i * cell_size
                    cell = warped[y:y+cell_size, x:x+cell_size]
                    
                    # 预处理单元格
                    cell = self._preprocess_cell(cell)
                    
                    # 识别数字
                    if cell is not None:
                        num = self._recognize_digit(cell)
                        board[i][j] = num
            
            # 更新UI
            self.root.after(0, lambda: self.set_board(board))
            self.root.after(0, lambda: self.empty_label.config(text=f"空格数: {sum(row.count(0) for row in board)}"))
            self.root.after(0, lambda: messagebox.showinfo("识别成功", "数独图片识别完成！"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("识别失败", f"无法识别数独: {str(e)}"))
        finally:
            self.root.after(0, self.hide_loading)
    
    def export_sudoku(self):
        """导出数独题目到文本文件"""
        board = self.get_board()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write("数独题目:\n")
                    for i, row in enumerate(board):
                        if i % 3 == 0 and i != 0:
                            f.write("------+-------+------\n")
                        line = " ".join(str(x) if x != 0 else "." for x in row)
                        line = line[:6] + "|" + line[6:12] + "|" + line[12:]
                        f.write(line.replace(" ", "  ") + "\n")
                messagebox.showinfo("导出成功", f"数独题目已保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"保存文件时出错: {str(e)}")
    
    def _order_points(self, pts):
        """对四边形的点进行排序"""
        rect = np.zeros((4, 2), dtype = "float32")
        
        # 左上角点的x+y值最小，右下角点的x+y值最大
        s = pts.sum(axis = 1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # 右上角点的x-y值最大，左下角点的x-y值最小
        diff = np.diff(pts, axis = 1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def _preprocess_cell(self, cell):
        """预处理单元格图像以便数字识别"""
        # 调整大小
        cell = cv2.resize(cell, (50, 50))
        
        # 阈值处理
        _, thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 查找轮廓
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 如果没有轮廓或轮廓太小，视为空格
        if not contours:
            return None
        
        # 找到最大轮廓
        max_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(max_contour) < 100:
            return None
        
        # 创建掩码
        mask = np.zeros_like(thresh)
        cv2.drawContours(mask, [max_contour], -1, 255, -1)
        
        # 提取数字区域
        digit = cv2.bitwise_and(thresh, thresh, mask=mask)
        
        return digit
    
    def _recognize_digit(self, digit_img):
        """使用Tesseract识别单个数字"""
        # 配置Tesseract
        config = '--oem 3 --psm 10 -c tessedit_char_whitelist=123456789'
        
        # 识别数字
        text = pytesseract.image_to_string(digit_img, config=config).strip()
        
        # 返回识别结果或0（无法识别）
        return int(text) if text and text.isdigit() else 0

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuUI(root)
    