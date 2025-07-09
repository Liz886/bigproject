import tkinter as tk
from tkinter import ttk, messagebox
import time

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

class SudokuUI:
    def __init__(self, root):
        self.root = root
        self.root.title("数独求解器")
        self.root.resizable(False, False)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 12))
        self.style.configure("TLabel", font=("微软雅黑", 12))
        
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        
        # 创建数独网格
        self.entries = []
        for i in range(9):
            row_entries = []
            for j in range(9):
                # 设置输入框大小和字体
                entry = ttk.Entry(main_frame, width=2, font=("微软雅黑", 18), justify="center")
                # 设置网格位置，每3行3列添加较宽的边框
                padx = 2 if (j % 3) != 2 else 5
                pady = 2 if (i % 3) != 2 else 5
                entry.grid(row=i, column=j, padx=padx, pady=pady)
                # 限制输入只能是数字
                entry.configure(validate="key", validatecommand=(self.root.register(self.validate_input), "%P"))
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        # 创建按钮框架
        button_frame = ttk.Frame(main_frame, padding="10 0 0 0")
        button_frame.grid(row=9, column=0, columnspan=9, sticky=tk.E, pady=10)
        
        # 求解按钮
        solve_button = ttk.Button(button_frame, text="求解", command=self.solve_sudoku)
        solve_button.pack(side=tk.RIGHT, padx=5)
        
        # 清空按钮
        clear_button = ttk.Button(button_frame, text="清空", command=self.clear_board)
        clear_button.pack(side=tk.RIGHT, padx=5)

        # 求解时间显示标签
        self.time_label = ttk.Label(button_frame, text="求解耗时: --")
        self.time_label.pack(side=tk.LEFT, padx=5)
        
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
                    self.entries[i][j].configure(foreground="blue")
    
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

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuUI(root)
    root.mainloop()