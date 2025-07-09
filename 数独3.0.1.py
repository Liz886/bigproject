import tkinter as tk
from tkinter import ttk, messagebox
import time
import random

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

    @staticmethod
    def generate_random_board(difficulty="中等"):
        """生成随机数独题目
        difficulty: 难度级别(简单/中等/困难/专家)
        返回值: (题目, 答案)
        """
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
        solver.solve()
        
        # 保存完整解
        solution = [row.copy() for row in board]
        
        # 根据难度挖空
        empty_cells = 40  # 默认中等难度
        if difficulty == "简单":
            empty_cells = 30
        elif difficulty == "困难":
            empty_cells = 50
        elif difficulty == "专家":
            empty_cells = 60
        
        # 随机挖空
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        
        for i, j in cells[:empty_cells]:
            board[i][j] = 0
        
        return board, solution

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
        self.difficulty_var = tk.StringVar(value="中等")
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
    
    def solve_sudoku(self):
        board = self.get_board()
        solver = SudokuSolver(board)
        # 测量求解算法执行时间
        start_time = time.time()
        solve_result = solver.solve()
        end_time = time.time()
        solve_duration = end_time - start_time
        # 更新时间显示
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

    def generate_random(self):
        """生成随机数独题目并显示在界面上"""
        difficulty = self.difficulty_var.get()
        try:
            # 在生成新数独前清除所有现有数字
            self.clear_board()
            
            puzzle, _ = SudokuSolver.generate_random_board(difficulty)
            self.set_generated_board(puzzle)
            self.time_label.config(text="求解耗时: --")  # 重置时间显示
            
            # 确保UI更新
            self.root.update()
        except Exception as e:
            messagebox.showerror("错误", f"生成数独失败: {str(e)}")
    
    def set_generated_board(self, board):
        """设置生成的数独题目到界面，生成的数字设为只读"""
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
                    entry.configure(foreground="black")  # 生成的数字为黑色
                else:
                    entry.configure(state="normal")  # 空白格子可编辑
                    # 恢复背景色
                    if (i // 3 + j // 3) % 2 == 0:
                        entry.configure(background="#e8f4f8")
                    else:
                        entry.configure(background="#ffffff")
                
                # 强制刷新每个输入框
                entry.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuUI(root)
    root.mainloop()