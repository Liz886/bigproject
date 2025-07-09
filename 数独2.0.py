import tkinter as tk
from tkinter import ttk, messagebox
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
        min_candidates = self.size + 1
        empty_cell = None
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    candidates = self.get_candidates(i, j)
                    if len(candidates) < min_candidates:
                        min_candidates = len(candidates)
                        empty_cell = (i, j)
                        if min_candidates == 1:  # 优化：找到只有一个候选数的格子
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

    def solve(self):
        empty_cell = self.find_empty()
        if not empty_cell:
            return True  # 数独已解
        
        row, col = empty_cell
        candidates = self.get_candidates(row, col)
        
        # 优化：按冲突数排序候选数
        sorted_candidates = sorted(candidates, key=lambda n: self.conflict_count(row, col, n))
        
        for num in sorted_candidates:
            if self.is_valid(row, col, num):
                self.board[row][col] = num
                if self.solve():
                    return True
                self.board[row][col] = 0  # 回溯
        return False
    
    # 新增：冲突计数函数
    def conflict_count(self, row, col, num):
        count = 0
        for i in range(9):
            # 检查行冲突
            if self.board[row][i] == 0 and num in self.get_candidates(row, i):
                count += 1
            # 检查列冲突
            if self.board[i][col] == 0 and num in self.get_candidates(i, col):
                count += 1
        return count
    
    # 新增：难度评估
    def get_difficulty(self):
        empty_count = sum(1 for row in self.board for cell in row if cell == 0)
        if empty_count > 50: 
            return "专家"
        elif empty_count > 40: 
            return "困难"
        elif empty_count > 30:
            return "中等"
        else: 
            return "简单"

class SudokuUI:
    def __init__(self, root):
        self.root = root
        self.root.title("数独求解器")
        self.root.resizable(False, False)
        
        # 配置样式
        self.configure_styles()
        
        # 创建UI组件
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
    
    def configure_styles(self):
        """配置UI样式"""
        self.style = ttk.Style()
        
        # 主按钮样式
        self.style.configure("TButton", 
                            font=("微软雅黑", 12), 
                            padding=6)
        
        # 输入框基础样式
        self.style.configure("Sudoku.TEntry", 
                            font=("Courier New", 14, "bold"), 
                            justify="center",
                            width=3)
        
        # 输入框聚焦状态
        self.style.map("Sudoku.TEntry", 
                      fieldbackground=[("focus", "#E1F5FE")],
                      foreground=[("focus", "#0066CC")])
        
        # 九宫格交替背景
        self.style.configure("SudokuAlt.TEntry", 
                           background="#F0F0F0")
        
        # 状态栏样式
        self.style.configure("Status.TLabel",
                           font=("微软雅黑", 10),
                           background="#E0E0E0",
                           padding=5)
    
    def create_widgets(self):
        """创建UI组件"""
        # 创建数独网格
        self.cells = []
        for i in range(9):
            row = []
            for j in range(9):
                # 创建输入框并应用样式
                entry = ttk.Entry(
                    self.root, 
                    style="Sudoku.TEntry",
                    validate="key",
                    validatecommand=(self.root.register(self.validate_input), "%P")
                )
                # 九宫格交替背景
                if (i // 3 + j // 3) % 2 == 0:
                    entry.configure(style="SudokuAlt.TEntry")
                
                entry.grid(row=i, column=j , ipadx=1, ipady=5, padx=(1 if j%3 !=0 else 3), pady=(1 if i%3 !=0 else 3))
                row.append(entry)
            self.cells.append(row)
        
        # 功能按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.grid(row=9, column=0, columnspan=9, pady=10)
        
        # 随机数独生成区域
        generate_frame = ttk.Frame(btn_frame)
        generate_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(generate_frame, text="难度:", style="TLabel").pack(side=tk.LEFT)
        
        self.difficulty_var = tk.StringVar(value="中等")
        difficulty_combo = ttk.Combobox(generate_frame, textvariable=self.difficulty_var,
                                        values=["简单", "中等", "困难", "专家"],
                                        state="readonly", width=6)
        difficulty_combo.pack(side=tk.LEFT, padx=5)
        
        generate_btn = ttk.Button(generate_frame, text="生成随机数独", command=self.generate_random)
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        # 求解按钮
        self.solve_btn = ttk.Button(btn_frame, text="求解", command=self.solve)
        self.solve_btn.pack(side=tk.RIGHT, padx=10)
        
        # 清空按钮
        self.clear_btn = ttk.Button(btn_frame, text="清除", command=self.clear)
        self.clear_btn.pack(side=tk.RIGHT, padx=10)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪 | 难度: -")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, style="Status.TLabel", anchor="center")
        status_bar.grid(row=10, column=0, columnspan=9, sticky="ew")
    
    def bind_events(self):
        """绑定键盘事件"""
        for i in range(9):
            for j in range(9):
                self.cells[i][j].bind("<Key>", lambda e, i=i, j=j: self.on_key_press(e, i, j))
                self.cells[i][j].bind("<FocusIn>", lambda e, i=i, j=j: self.on_focus(e, i, j))
    
    def validate_input(self, value):
        """验证输入是否有效"""
        return value == "" or (len(value) == 1 and value.isdigit() and 1 <= int(value) <= 9)
    
    def on_key_press(self, event, i, j):
        """处理键盘导航"""
        # 方向键导航
        if event.keysym == "Up" and i > 0:
            self.cells[i-1][j].focus()
        elif event.keysym == "Down" and i < 8:
            self.cells[i+1][j].focus()
        elif event.keysym == "Left" and j > 0:
            self.cells[i][j-1].focus()
        elif event.keysym == "Right" and j < 8:
            self.cells[i][j+1].focus()
        
        # Tab键导航
        elif event.keysym == "Tab":
            if j < 8:
                self.cells[i][j+1].focus()
            elif i < 8:
                self.cells[i+1][0].focus()
            else:
                self.cells[0][0].focus()
            return "break"  # 阻止默认Tab行为
    
    def on_focus(self, event, i, j):
        """高亮当前单元格"""
        # 清除所有高亮
        for row in self.cells:
            for cell in row:
                cell.configure(foreground="black")
        
        # 高亮当前单元格
        event.widget.configure(foreground="#FF5722")
    
    def solve(self):
        """求解数独"""
        try:
            # 从UI获取当前棋盘状态
            board = []
            for i in range(9):
                row = []
                for j in range(9):
                    val = self.cells[i][j].get()
                    row.append(int(val) if val else 0)
                board.append(row)
            
            # 创建求解器实例
            solver = SudokuSolver(board)
            
            # 更新状态栏显示难度
            difficulty = solver.get_difficulty()
            self.status_var.set(f"求解中... | 难度: {difficulty}")
            self.root.update()  # 强制更新UI
            
            # 尝试求解
            if solver.solve():
                # 显示求解结果
                self.update_board(solver.board)
                self.status_var.set(f"求解成功! | 难度: {difficulty}")
            else:
                raise ValueError("此数独无解")
                
        except ValueError as e:
            messagebox.showerror("求解失败", str(e))
            self.status_var.set("求解失败! | 难度: -")
        except Exception as e:
            messagebox.showerror("错误", f"发生未知错误: {str(e)}")
            self.status_var.set("错误! | 难度: -")
    
    def update_board(self, board):
        """更新棋盘显示"""
        for i in range(9):
            for j in range(9):
                value = board[i][j]
                if value != 0:
                    self.cells[i][j].delete(0, tk.END)
                    self.cells[i][j].insert(0, str(value))
                else:
                    self.cells[i][j].delete(0, tk.END)
    
    def generate_random(self):
        """生成随机数独题目"""
        difficulty = self.difficulty_var.get()
        self.status_var.set(f"生成{difficulty}难度数独中...")
        self.root.update()
        
        try:
            # 生成随机数独
            board, _ = SudokuSolver.generate_random_board(difficulty)
            
            # 清空当前棋盘
            self.clear()
            
            # 填充生成的数独
            for i in range(9):
                for j in range(9):
                    value = board[i][j]
                    if value != 0:
                        self.cells[i][j].delete(0, tk.END)
                        self.cells[i][j].insert(0, str(value))
                        # 设置生成的数字为不可修改
                        self.cells[i][j].configure(state="readonly")
                    else:
                        # 设置空白单元格为可修改
                        self.cells[i][j].configure(state="normal")
            
            self.status_var.set(f"已生成{difficulty}难度数独 | 请开始解题")
        except Exception as e:
            messagebox.showerror("错误", f"生成数独失败: {str(e)}")
            self.status_var.set("生成失败 | 请重试")

    def clear(self):
        """清除所有输入"""
        for i in range(9):
            for j in range(9):
                self.cells[i][j].configure(state="normal")
                self.cells[i][j].delete(0, tk.END)
        self.status_var.set("已清除 | 难度: -")

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuUI(root)
    root.mainloop()