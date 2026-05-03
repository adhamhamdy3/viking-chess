EMPTY = 0
ATTACKER = 1  # Black
DEFENDER = 2  # White
KING = 3      # White

BOARD_SIZE = 11
THRONE = (5, 5)
CORNERS = {(0, 0), (0, 10), (10, 0), (10, 10)}

def get_owner(piece):
    if piece == ATTACKER: return 'BLACK'
    if piece in (DEFENDER, KING): return 'WHITE'
    return None

def is_opponent(piece1, piece2):
    if piece1 == EMPTY or piece2 == EMPTY: return False
    return get_owner(piece1) != get_owner(piece2)

def is_sandwiched(board, r, c, piece):
    """
    Checks if a piece at (r, c) would be sandwiched by opponents.
    Note: King is unarmed and cannot contribute to a sandwich.
    """
    owner = get_owner(piece)
    # Check horizontal
    if 0 <= c-1 and c+1 < BOARD_SIZE:
        left = board[r][c-1]
        right = board[r][c+1]
        # Opponent must be ATTACKER or DEFENDER (King is unarmed)
        if is_opponent(piece, left) and left != KING and \
           is_opponent(piece, right) and right != KING:
            return True
            
    # Check vertical
    if 0 <= r-1 and r+1 < BOARD_SIZE:
        up = board[r-1][c]
        down = board[r+1][c]
        if is_opponent(piece, up) and up != KING and \
           is_opponent(piece, down) and down != KING:
            return True
    return False

def get_valid_moves(board, r, c):
    piece = board[r][c]
    if piece == EMPTY: return []

    valid_moves = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in directions:
        curr_r, curr_c = r + dr, c + dc
        while 0 <= curr_r < BOARD_SIZE and 0 <= curr_c < BOARD_SIZE:
            # 1. Blocked by another piece
            if board[curr_r][curr_c] != EMPTY:
                break
            
            # 2. Throne & Corner Barriers
            # Logic: Only King can move INTO, NO piece moves PAST
            is_special = (curr_r, curr_c) == THRONE or (curr_r, curr_c) in CORNERS
            
            if is_special:
                if piece == KING:
                    valid_moves.append((curr_r, curr_c))
                # Path ends here for everyone
                break

            # 3. Sandwich Rule: Can move through, but not stop inside
            if piece != KING:
                if not is_sandwiched(board, curr_r, curr_c, piece):
                    valid_moves.append((curr_r, curr_c))
            else:
                valid_moves.append((curr_r, curr_c))
            
            curr_r += dr
            curr_c += dc
            
    return valid_moves

def check_captures(board, r, c):
    moved_piece = board[r][c]
    owner = get_owner(moved_piece)
    captured_positions = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # 1. Standard Piece Captures (Custodial with Anvils)
    # King cannot capture pieces because he is unarmed
    if moved_piece != KING:
        for dr, dc in directions:
            adj_r, adj_c = r + dr, c + dc
            past_r, past_c = adj_r + dr, adj_c + dc

            if 0 <= adj_r < BOARD_SIZE and 0 <= adj_c < BOARD_SIZE:
                adj_p = board[adj_r][adj_c]

                # Target must be an opponent and not the King
                if is_opponent(moved_piece, adj_p) and adj_p != KING:
                    anvil_valid = False
                    if 0 <= past_r < BOARD_SIZE and 0 <= past_c < BOARD_SIZE:
                        past_p = board[past_r][past_c]
                        # Friendly piece anvil (King is unarmed)
                        if get_owner(past_p) == owner and past_p != KING: 
                            anvil_valid = True
                        # Throne (occupied or not) is an anvil
                        elif (past_r, past_c) == THRONE: 
                            anvil_valid = True
                        # Corner is an anvil
                        elif (past_r, past_c) in CORNERS: 
                            anvil_valid = True

                    if anvil_valid: captured_positions.append((adj_r, adj_c))

    for cr, cc in captured_positions: board[cr][cc] = EMPTY

    # 2. King Capture (All 4 sides enclosed by Hostiles)
    king_captured = False
    if owner == 'BLACK':
        kp = next(((ri, ci) for ri in range(BOARD_SIZE) for ci in range(BOARD_SIZE) if board[ri][ci] == KING), None)
        if kp:
            kr, kc = kp
            hostile_count = 0
            for dr, dc in directions:
                ar, ac = kr + dr, kc + dc
                # Edge of board (OOB) is hostile
                if not (0 <= ar < BOARD_SIZE and 0 <= ac < BOARD_SIZE):
                    hostile_count += 1
                # Corner is hostile
                elif (ar, ac) in CORNERS:
                    hostile_count += 1
                # Attacker piece is hostile
                elif board[ar][ac] == ATTACKER:
                    hostile_count += 1
            
            # King falls if all 4 adjacent sides are hostile
            if hostile_count == 4:
                king_captured = True

    return captured_positions, king_captured