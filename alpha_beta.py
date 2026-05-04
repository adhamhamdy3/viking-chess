import copy
from engine import ATTACKER, DEFENDER, KING, EMPTY, BOARD_SIZE, CORNERS, THRONE, get_valid_moves, check_captures, get_owner, is_king_in_corner

def evaluate_board(board):
    """
    Adequate utility function that evaluates the current game state.
    Positive values favor defenders, negative values favor attackers.
    """
    attacker_count = 0
    defender_count = 0
    king_pos = None

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece == ATTACKER:
                attacker_count += 1
            elif piece == DEFENDER:
                defender_count += 1
            elif piece == KING:
                king_pos = (r, c)

    score = defender_count - attacker_count

    #king reaching near corners or moving away from center
    if king_pos:
        kr, kc = king_pos
        # Example heuristic: distance from the throne (5, 5)
        distance_from_throne = abs(kr - 5) + abs(kc - 5)
        score += distance_from_throne * 0.5

        if (kr, kc) in CORNERS:
            score += 100

    return score

def get_all_possible_moves(board, player):
    """
    Generates all valid moves for a given player type (ATTACKER or DEFENDER).
    """
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece == EMPTY:
                continue
                
            # Check player pieces
            if player == ATTACKER and piece == ATTACKER:
                valid = get_valid_moves(board, r, c)
                for move in valid:
                    moves.append(((r, c), move))
            elif player == DEFENDER and piece in (DEFENDER, KING):
                valid = get_valid_moves(board, r, c)
                for move in valid:
                    moves.append(((r, c), move))
    return moves

def make_move(board, start_pos, end_pos):
    sr, sc = start_pos
    er, ec = end_pos

    changes = []

    piece = board[sr][sc]
    changes.append((sr, sc, piece))
    changes.append((er, ec, board[er][ec]))
    board[sr][sc] = EMPTY
    board[er][ec] = piece

    # snapshot all potentially captured squares before check_captures modifies them
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    snapshots = {}
    for dr, dc in directions:
        adj_r, adj_c = er + dr, ec + dc
        if 0 <= adj_r < BOARD_SIZE and 0 <= adj_c < BOARD_SIZE:
            snapshots[(adj_r, adj_c)] = board[adj_r][adj_c]

    captured, king_captured = check_captures(board, er, ec)

    for (r, c) in captured:
        changes.append((r, c, snapshots[(r, c)]))

    return changes, king_captured

def undo_move(board, changes):
    for (r, c, old_val) in reversed(changes):
        board[r][c] = old_val

def alpha_beta(board, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate_board(board), None

    if maximizing_player:
        max_eval = float('-inf')
        possible_moves = get_all_possible_moves(board, DEFENDER)
        best_move = possible_moves[0]

        for move in possible_moves:
            start, end = move
            
            # do
            ch1, king_captured = make_move(board, start, end)

            # Early exit: king reached a corner — best possible outcome for white
            if is_king_in_corner(board):
                undo_move(board, ch1)
                return float('inf'), move

            # recurse
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, False)

            # undo
            undo_move(board, ch1)

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break

        return max_eval, best_move

    else:
        min_eval = float('inf')
        possible_moves = get_all_possible_moves(board, ATTACKER)
        best_move = possible_moves[0]

        for move in possible_moves:
            start, end = move

            # do
            ch2, king_captured = make_move(board, start, end)

            # Early exit: king captured — best possible outcome for black
            if king_captured:
                undo_move(board, ch2)
                return float('-inf'), move

            # recurse
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, True)

            # undo
            undo_move(board, ch2)

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move

            beta = min(beta, eval_score)
            if beta <= alpha:
                break

        return min_eval, best_move