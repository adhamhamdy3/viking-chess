import copy
from engine import ATTACKER, DEFENDER, KING, EMPTY, BOARD_SIZE, CORNERS, THRONE, get_valid_moves, check_captures, get_owner

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
    """
    Creates a deep copy of the board and applies the move, updating captures.
    """
    new_board = copy.deepcopy(board)
    sr, sc = start_pos
    er, ec = end_pos
    
    piece = new_board[sr][sc]
    new_board[sr][sc] = EMPTY
    new_board[er][ec] = piece
    
    # Process captures
    check_captures(new_board, er, ec)
    return new_board

def alpha_beta(board, depth, alpha, beta, maximizing_player):
    """
    Alpha-Beta Pruning algorithm implementation.
    """
    if depth == 0:
        return evaluate_board(board), None

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        # Maximizing side: DEFENDER (White)
        possible_moves = get_all_possible_moves(board, DEFENDER)
        
        for move in possible_moves:
            start, end = move
            new_board = make_move(board, start, end)
            eval_score, _ = alpha_beta(new_board, depth - 1, alpha, beta, False)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
                
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Beta cutoff
                
        return max_eval, best_move

    else:
        min_eval = float('inf')
        best_move = None
        # Minimizing side: ATTACKER (Black)
        possible_moves = get_all_possible_moves(board, ATTACKER)
        
        for move in possible_moves:
            start, end = move
            new_board = make_move(board, start, end)
            eval_score, _ = alpha_beta(new_board, depth - 1, alpha, beta, True)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
                
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Alpha cutoff
                
        return min_eval, best_move