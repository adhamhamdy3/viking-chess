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

def _is_hostile_anvil(board, r, c, piece):
    """
    Returns True if the square at (r, c) acts as a hostile anvil for `piece`:
    an opponent piece (not the unarmed King), or an empty throne, or a corner.
    """
    if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
        return False
    if (r, c) in CORNERS:
        return True
    if (r, c) == THRONE and board[r][c] == EMPTY:
        return True
    sq = board[r][c]
    if is_opponent(piece, sq) and sq != KING:
        return True
    return False


def is_sandwiched(board, r, c, piece):
    """
    Checks if a piece at (r, c) would be sandwiched by hostile anvils.
    King is unarmed and cannot contribute to a sandwich. Throne (empty) and
    corners count as hostile anvils.
    """
    # Horizontal
    if _is_hostile_anvil(board, r, c - 1, piece) and _is_hostile_anvil(board, r, c + 1, piece):
        return True
    # Vertical
    if _is_hostile_anvil(board, r - 1, c, piece) and _is_hostile_anvil(board, r + 1, c, piece):
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
                        # Empty throne is an anvil (King on throne does not assist — he is unarmed)
                        elif (past_r, past_c) == THRONE and board[past_r][past_c] == EMPTY:
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
            sides = 0
            for dr, dc in directions:
                ar, ac = kr + dr, kc + dc
                # Edge of board (OOB): wall — not counted as a side that needs surrounding
                if not (0 <= ar < BOARD_SIZE and 0 <= ac < BOARD_SIZE):
                    continue
                sides += 1
                # Corner is hostile
                if (ar, ac) in CORNERS:
                    hostile_count += 1
                # Empty throne is hostile to the King
                elif (ar, ac) == THRONE and board[ar][ac] == EMPTY:
                    hostile_count += 1
                # Attacker piece is hostile
                elif board[ar][ac] == ATTACKER:
                    hostile_count += 1

            # King falls if every on-board side is hostile
            # (4 sides in open, 3 against a wall, 2 against a corner)
            if sides > 0 and hostile_count == sides:
                king_captured = True

    return captured_positions, king_captured


def create_initial_board():
    """
    Builds the 11x11 starting position.
    King on the throne, 12 defenders in cross around him,
    24 attackers in 4 groups of 6 along the edges.
    """
    b = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    # King on the throne
    b[5][5] = KING

    # 12 defenders in cross formation around the throne
    defender_positions = [
        (3, 5), (4, 5), (6, 5), (7, 5),
        (5, 3), (5, 4), (5, 6), (5, 7),
        (4, 4), (4, 6), (6, 4), (6, 6),
    ]
    for r, c in defender_positions:
        b[r][c] = DEFENDER

    # 24 attackers in 4 groups of 6 along the edges
    attacker_positions = [
        # Top edge
        (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (1, 5),
        # Bottom edge
        (10, 3), (10, 4), (10, 5), (10, 6), (10, 7), (9, 5),
        # Left edge
        (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (5, 1),
        # Right edge
        (3, 10), (4, 10), (5, 10), (6, 10), (7, 10), (5, 9),
    ]
    for r, c in attacker_positions:
        b[r][c] = ATTACKER

    return b


def check_win(board):
    """
    Returns 'WHITE' if defenders won (King on a corner),
    'BLACK' if attackers won (King no longer on the board), else None.
    """
    king_pos = None
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == KING:
                king_pos = (r, c)
                break
        if king_pos:
            break

    if king_pos is None:
        return 'BLACK'
    if king_pos in CORNERS:
        return 'WHITE'
    return None