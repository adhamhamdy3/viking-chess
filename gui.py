import tkinter as tk
from tkinter import messagebox
import threading

from engine import (
    EMPTY, ATTACKER, DEFENDER, KING,
    BOARD_SIZE, THRONE, CORNERS,
    get_valid_moves, check_captures, get_owner,
    create_initial_board, check_win,
)
from alpha_beta import alpha_beta


CELL = 50
MARGIN = 20
BOARD_PX = BOARD_SIZE * CELL
WIN_W = BOARD_PX + 2 * MARGIN
WIN_H = BOARD_PX + 2 * MARGIN + 60

COLOR_LIGHT = "#EED9B6"
COLOR_DARK = "#B58863"
COLOR_THRONE = "#C9A96A"
COLOR_CORNER = "#A07040"
COLOR_HIGHLIGHT = "#5fbf5f"
COLOR_SELECT = "#3a7fbf"

DIFFICULTY_DEPTH = {"Easy": 1, "Medium": 3, "Hard": 5}


class HnefataflGUI:
    def __init__(self, root):
        self.root = root
        root.title("Hnefatafl — Viking Chess")
        root.resizable(False, False)

        self.board = create_initial_board()
        self.selected = None         # (r, c) of selected piece
        self.legal_targets = []      # list of (r, c)
        self.turn = 'BLACK'          # Attackers always move first
        self.human_side = 'WHITE'    # Human plays defenders by default
        self.depth = DIFFICULTY_DEPTH["Medium"]
        self.game_over = False
        self.ai_thinking = False

        self._build_ui()
        self._draw_board()
        self._update_status()

        # If AI moves first, schedule its move
        self.root.after(300, self._maybe_ai_move)

    # ---------- UI construction ----------
    def _build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=6, pady=4)

        tk.Label(top, text="Side:").pack(side=tk.LEFT)
        self.side_var = tk.StringVar(value="WHITE")
        side_menu = tk.OptionMenu(top, self.side_var, "WHITE", "BLACK")
        side_menu.pack(side=tk.LEFT, padx=4)

        tk.Label(top, text="Difficulty:").pack(side=tk.LEFT, padx=(10, 0))
        self.diff_var = tk.StringVar(value="Medium")
        diff_menu = tk.OptionMenu(top, self.diff_var, "Easy", "Medium", "Hard")
        diff_menu.pack(side=tk.LEFT, padx=4)

        tk.Button(top, text="New Game", command=self._new_game).pack(side=tk.LEFT, padx=10)

        self.canvas = tk.Canvas(self.root, width=WIN_W, height=BOARD_PX + 2 * MARGIN,
                                bg="#222", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        self.status = tk.Label(self.root, text="", anchor="w", font=("Segoe UI", 10))
        self.status.pack(fill=tk.X, padx=8, pady=4)

    # ---------- Drawing ----------
    def _draw_board(self):
        self.canvas.delete("all")
        # Squares
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x1 = MARGIN + c * CELL
                y1 = MARGIN + r * CELL
                x2 = x1 + CELL
                y2 = y1 + CELL
                if (r, c) in CORNERS:
                    fill = COLOR_CORNER
                elif (r, c) == THRONE:
                    fill = COLOR_THRONE
                else:
                    fill = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#333")

        # Highlight selected square + legal moves
        if self.selected is not None:
            sr, sc = self.selected
            self._outline_cell(sr, sc, COLOR_SELECT, 3)
            for (r, c) in self.legal_targets:
                self._outline_cell(r, c, COLOR_HIGHLIGHT, 3)

        # Pieces
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.board[r][c]
                if p == EMPTY:
                    continue
                self._draw_piece(r, c, p)

    def _outline_cell(self, r, c, color, width):
        x1 = MARGIN + c * CELL
        y1 = MARGIN + r * CELL
        self.canvas.create_rectangle(x1 + 2, y1 + 2, x1 + CELL - 2, y1 + CELL - 2,
                                     outline=color, width=width)

    def _draw_piece(self, r, c, piece):
        cx = MARGIN + c * CELL + CELL / 2
        cy = MARGIN + r * CELL + CELL / 2
        rad = CELL * 0.36
        if piece == ATTACKER:
            self.canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                                    fill="#1a1a1a", outline="#000", width=2)
        elif piece == DEFENDER:
            self.canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                                    fill="#f5f5f5", outline="#888", width=2)
        elif piece == KING:
            self.canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                                    fill="#ffd24a", outline="#a06000", width=2)
            self.canvas.create_text(cx, cy, text="K", font=("Segoe UI", 14, "bold"))

    # ---------- Status ----------
    def _update_status(self):
        if self.game_over:
            return
        side = "Black (Attackers)" if self.turn == 'BLACK' else "White (Defenders)"
        who = "You" if self.turn == self.human_side else "Computer"
        suffix = " — thinking..." if self.ai_thinking else ""
        self.status.config(text=f"Turn: {side} — {who}{suffix}")

    # ---------- New game ----------
    def _new_game(self):
        self.board = create_initial_board()
        self.selected = None
        self.legal_targets = []
        self.turn = 'BLACK'
        self.human_side = self.side_var.get()
        self.depth = DIFFICULTY_DEPTH[self.diff_var.get()]
        self.game_over = False
        self.ai_thinking = False
        self._draw_board()
        self._update_status()
        self.root.after(300, self._maybe_ai_move)

    # ---------- Input handling ----------
    def _on_click(self, event):
        if self.game_over or self.ai_thinking:
            return
        if self.turn != self.human_side:
            return

        c = (event.x - MARGIN) // CELL
        r = (event.y - MARGIN) // CELL
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            return

        piece = self.board[r][c]

        # If a target square is clicked while a piece is selected, try to move
        if self.selected is not None and (r, c) in self.legal_targets:
            self._apply_move(self.selected, (r, c))
            self.selected = None
            self.legal_targets = []
            self._draw_board()
            self._after_move()
            return

        # Otherwise, (re)select a piece belonging to the human
        if piece != EMPTY and get_owner(piece) == self.human_side:
            self.selected = (r, c)
            self.legal_targets = get_valid_moves(self.board, r, c)
            self._draw_board()
        else:
            self.selected = None
            self.legal_targets = []
            self._draw_board()

    # ---------- Move application ----------
    def _apply_move(self, start, end):
        sr, sc = start
        er, ec = end
        piece = self.board[sr][sc]
        self.board[sr][sc] = EMPTY
        self.board[er][ec] = piece
        check_captures(self.board, er, ec)

    def _after_move(self):
        winner = check_win(self.board)
        if winner is not None:
            self._declare_winner(winner)
            return
        # Switch turn
        self.turn = 'WHITE' if self.turn == 'BLACK' else 'BLACK'
        self._update_status()
        self.root.after(200, self._maybe_ai_move)

    def _declare_winner(self, winner):
        self.game_over = True
        msg = "White (Defenders) win — King escaped!" if winner == 'WHITE' \
              else "Black (Attackers) win — King captured!"
        self.status.config(text=f"Game over — {msg}")
        self._draw_board()
        messagebox.showinfo("Game over", msg)

    # ---------- AI ----------
    def _maybe_ai_move(self):
        if self.game_over or self.ai_thinking:
            return
        if self.turn == self.human_side:
            return

        self.ai_thinking = True
        self._update_status()

        # Run search in a worker thread so the UI stays responsive
        def worker():
            maximizing = (self.turn == 'WHITE')  # White = defenders = maximizing
            _, best_move = alpha_beta(
                self.board, self.depth, float('-inf'), float('inf'), maximizing
            )
            self.root.after(0, lambda: self._finish_ai_move(best_move))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_ai_move(self, best_move):
        self.ai_thinking = False
        if best_move is None:
            # No legal moves — opposing side wins
            opp = 'WHITE' if self.turn == 'BLACK' else 'BLACK'
            self._declare_winner(opp)
            return
        start, end = best_move
        self._apply_move(start, end)
        self._draw_board()
        self._after_move()


def main():
    root = tk.Tk()
    HnefataflGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
