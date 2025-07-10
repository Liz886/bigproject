import tkinter as tk
from tkinter import ttk, messagebox
import time
import random
import threading
import copy

class SudokuSolver:
    def __init__(self, board):
        self.board = board
        self.size = 9
        self.subgrid_size = 3

    def is_valid(self, row, col, num):
        # 检查行
        for i in range(self.size):
            if self.board[row][i] == num:
                return False
        # 检查列
        for i in range(self.size):
            if self.board[i][col] == num:
                return False
        # 检查九宫格
        start_row = row - row % self.subgrid_size
        start_col = col - col % self.subgrid_size
        for i in range(self.subgrid_size):
            for j in range(self.subgrid_size):
                if self.board[start_row + i][start_col + j] == num:
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
        max_attempts = 150  # 增加最大尝试次数
        
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
            
            # 根据难度设置挖空参数
            if difficulty == "简单":
                min_empty = 30
                max_empty = 35
                symmetry = True  # 使用对称挖空
            elif difficulty == "中等":
                min_empty = 40
                max_empty = 45
                symmetry = True
            elif difficulty == "困难":
                min_empty = 50
                max_empty = 55
                symmetry = True
            elif difficulty == "专家":
                min_empty = 58
                max_empty = 64  # 接近理论极限
                symmetry = False  # 专家难度不使用对称挖空
                
            # 随机确定挖空数量
            empty_cells = random.randint(min_empty, max_empty)
            
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
            elif symmetry:
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
            if difficulty == "专家" and current_empty < min_empty:
                for cell_group in backup_cells:
                    if current_empty >= min_empty:
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
            if difficulty == "专家" and current_empty < min_empty:
                # 获取所有当前有数字的格子
                filled_cells = [(i, j) for i in range(9) for j in range(9) if board[i][j] != 0]
                random.shuffle(filled_cells)
                
                # 尝试挖空更多格子
                for cell in filled_cells:
                    if current_empty >= min_empty:
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
                    if current_empty >= min_empty - 2:  # 允许56-64
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
        
        self.create_widgets()
        self.loading_window = None
        self.generating = False
        
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
                # 设置输入框大小和字体
                entry = ttk.Entry(
                    grid_frame, 
                    width=2, 
                    font=("微软雅黑", 16, "bold"), 
                    justify="center"
                )
                # 设置网格位置，每3行3列添加较宽的边框
                padx = (1, 3) if j in [2, 5] else 1
                pady = (1, 3) if i in [2, 5] else 1
                
                # 使用Frame实现边框效果
                entry_frame = ttk.Frame(grid_frame, borderwidth=0, relief=tk.FLAT)
                entry_frame.grid(row=i, column=j, padx=padx, pady=pady)
                entry.grid(in_=entry_frame, ipadx=6, ipady=6)
                entry.lift()  # 将输入框置于顶层
                
                # 设置背景色区分九宫格
                if (i // 3 + j // 3) % 2 == 0:
                    entry.configure(background="#e8f4f8", foreground="#000000")
                    entry_frame.configure(style="Odd.TFrame")
                else:
                    entry.configure(background="#ffffff", foreground="#000000")
                    entry_frame.configure(style="Even.TFrame")
                
                # 限制输入只能是数字
                entry.configure(validate="key", validatecommand=(self.root.register(self.validate_input), "%P"))
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        # 创建控制面板框架
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 左侧控制区域
        left_control = ttk.Frame(control_frame)
        left_control.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 难度选择
        difficulty_frame = ttk.Frame(left_control)
        difficulty_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(difficulty_frame, text="难度:").pack(side=tk.LEFT)
        self.difficulty_var = tk.StringVar(value="专家")  # 默认设置为专家难度
        difficulty_combobox = ttk.Combobox(
            difficulty_frame, 
            textvariable=self.difficulty_var, 
            values=["简单", "中等", "困难", "专家"], 
            state="readonly", 
            width=8
        )
        difficulty_combobox.pack(side=tk.LEFT)
        
        # 生成按钮
        generate_button = ttk.Button(left_control, text="生成随机数独", command=self.generate_random)
        generate_button.pack(side=tk.LEFT, padx=5)
        
        # 右侧控制区域
        right_control = ttk.Frame(control_frame)
        right_control.pack(side=tk.RIGHT)
        
        # 求解时间显示标签
        self.time_label = ttk.Label(right_control, text="求解耗时: --", style="Time.TLabel")
        self.time_label.pack(side=tk.LEFT, padx=10)
        
        # 空格数量显示标签
        self.empty_label = ttk.Label(right_control, text="空格数: --", style="Time.TLabel")
        self.empty_label.pack(side=tk.LEFT, padx=10)
        
        # 清空按钮
        clear_button = ttk.Button(right_control, text="清空", command=self.clear_board)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # 求解按钮
        solve_button = ttk.Button(right_control, text="求解", command=self.solve_sudoku)
        solve_button.pack(side=tk.LEFT, padx=(5, 0))
    
    def validate_input(self, value):
        # 只允许输入1-9或空
        if not value:
            return True
        if len(value) > 1:
            return False
        if value.isdigit() and 1 <= int(value) <= 9:
            return True
        return False
    
    def get_board(self):
        # 从输入框获取数独数据
        board = []
        for i in range(9):
            row = []
            for j in range(9):
                text = self.entries[i][j].get()
                row.append(int(text) if text else 0)
            board.append(row)
        return board
    
    def set_board(self, board):
        # 将求解结果设置到输入框
        for i in range(9):
            for j in range(9):
                value = board[i][j]
                self.entries[i][j].delete(0, tk.END)
                if value != 0:
                    self.entries[i][j].insert(0, str(value))
                    # 设置已解出的数字为蓝色
                    self.entries[i][j].configure(foreground="#3498db")
    
    def count_empty_cells(self):
        """计算当前棋盘的空格数量"""
        count = 0
        for i in range(9):
            for j in range(9):
                if not self.entries[i][j].get():
                    count += 1
        return count
    
    def solve_sudoku(self):
        board = self.get_board()
        # 创建临时求解器检查解的数量
        temp_board = [row.copy() for row in board]
        temp_solver = SudokuSolver(temp_board)
        solution_count = temp_solver.count_solutions()
        
        if solution_count == 0:
            messagebox.showerror("错误", "该数独无解！")
            return
        elif solution_count > 1:
            messagebox.showwarning("提示", "该数独存在多个解！")
            return
        
        # 如果只有一个解，继续求解
        solver = SudokuSolver(board)
        start_time = time.time()
        solve_result = solver.solve()
        end_time = time.time()
        solve_duration = end_time - start_time
        self.time_label.config(text=f"求解耗时: {solve_duration:.6f}秒")
        
        if solve_result:
            self.set_board(solver.board)
        else:
            messagebox.showerror("错误", "该数独无解！")
    
    def clear_board(self):
        # 清空所有输入框
        for i in range(9):
            for j in range(9):
                self.entries[i][j].delete(0, tk.END)
                self.entries[i][j].configure(foreground="black")
                # 恢复背景色
                if (i // 3 + j // 3) % 2 == 0:
                    self.entries[i][j].configure(background="#e8f4f8")
                else:
                    self.entries[i][j].configure(background="#ffffff")
                self.entries[i][j].configure(state="normal")  # 恢复可编辑状态
        self.time_label.config(text="求解耗时: --")
        self.empty_label.config(text="空格数: --")

    def show_loading(self):
        """显示加载弹窗"""
        if self.loading_window and self.loading_window.winfo_exists():
            return
            
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("加载中")
        self.loading_window.geometry("300x100")
        self.loading_window.resizable(False, False)
        self.loading_window.transient(self.root)  # 设置为父窗口的临时窗口
        self.loading_window.grab_set()  # 设置为模态窗口
        
        # 设置窗口位置在父窗口中心
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 50
        self.loading_window.geometry(f"+{x}+{y}")
        
        # 添加加载提示
        ttk.Label(
            self.loading_window, 
            text="正在拼命加载...", 
            font=("微软雅黑", 12)
        ).pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # 添加进度条
        self.progress = ttk.Progressbar(
            self.loading_window, 
            mode="indeterminate",
            length=280
        )
        self.progress.pack(pady=(0, 10), padx=10)
        self.progress.start(10)  # 开始动画
        
        # 确保窗口显示
        self.loading_window.update()
    
    def hide_loading(self):
        """隐藏加载弹窗"""
        if self.loading_window and self.loading_window.winfo_exists():
            self.loading_window.grab_release()
            self.loading_window.destroy()
        self.loading_window = None
    
    def generate_random_thread(self):
        """后台线程生成数独"""
        difficulty = self.difficulty_var.get()
        try:
            # 生成数独题目和答案
            puzzle, solution = SudokuSolver.generate_random_board(difficulty)
            
            # 计算空格数量
            empty_count = sum(row.count(0) for row in puzzle)
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.set_generated_board(puzzle, solution, empty_count))
        except Exception as e:
            self.root.after(0, lambda e=e: messagebox.showerror("错误", f"生成数独失败: {str(e)}"))
        finally:
            self.generating = False

    def generate_random(self):
        """生成随机数独题目并显示在界面上"""
        # 生成前清除所有数字
        self.clear_board()
        
        if self.generating:
            return
        self.generating = True
        # 在后台线程中生成数独
        thread = threading.Thread(target=self.generate_random_thread)
        thread.daemon = True
        thread.start()

    def set_generated_board(self, board, solution, empty_count):
        """设置生成的数独题目到界面，生成的数字设为只读"""
        # 保存答案供后续使用
        self.solution = solution
        
        for i in range(9):
            for j in range(9):
                value = board[i][j]
                entry = self.entries[i][j]
                entry.delete(0, tk.END)
                entry.configure(foreground="black")
                entry.configure(state="normal")  # 先恢复可编辑状态
                if value != 0:
                    entry.insert(0, str(value))
                    entry.configure(state="readonly")  # 生成的数字设为只读
                    entry.configure(foreground="#2c3e50")  # 生成的数字为深灰色
                else:
                    entry.configure(state="normal")  # 空白格子可编辑
                    # 恢复背景色
                    if (i // 3 + j // 3) % 2 == 0:
                        entry.configure(background="#e8f4f8")
                    else:
                        entry.configure(background="#ffffff")
                
                # 强制刷新每个输入框
                entry.update_idletasks()
        
        # 更新空格数量显示
        self.empty_label.config(text=f"空格数: {empty_count}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuUI(root)
    root.mainloop()