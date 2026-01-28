"""Rules engine for Goro Goro Shogi (5x6 mini shogi).

This mirrors the browser rules so AI training can run locally.
The state is small and deterministic, which is ideal for self-play.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

PLAYER_S = "S"  # South (moves up)
PLAYER_N = "N"  # North (moves down)

PIECE_LION = "L"
PIECE_DOG = "D"  # Gold equivalent
PIECE_CAT = "C"  # Silver equivalent
PIECE_PAWN = "P"
PIECE_HEN = "H"  # Promoted pawn
PIECE_SUPER_CAT = "U"  # Promoted cat

PROMOTES = {PIECE_PAWN: PIECE_HEN, PIECE_CAT: PIECE_SUPER_CAT}
DEMOTES = {PIECE_HEN: PIECE_PAWN, PIECE_SUPER_CAT: PIECE_CAT}

BACK_RANK = [PIECE_CAT, PIECE_DOG, PIECE_LION, PIECE_DOG, PIECE_CAT]
PAWN_COLS = [1, 2, 3]
PAWN_ROWS = {PLAYER_N: 2, PLAYER_S: 3}  # chicks meet in the middle

ROWS = 6
COLS = 5


@dataclass(frozen=True)
class Move:
    drop: bool
    piece: str
    to: Tuple[int, int]
    frm: Optional[Tuple[int, int]] = None
    promote: bool = False


@dataclass
class GameState:
    board: List[List[Optional[Tuple[str, str]]]]
    hands: Dict[str, Dict[str, int]]
    turn: str
    move_number: int = 1

    @staticmethod
    def initial() -> "GameState":
        board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        for c, piece in enumerate(BACK_RANK):
            board[0][c] = (piece, PLAYER_N)
            board[ROWS - 1][c] = (piece, PLAYER_S)
        for c in PAWN_COLS:
            board[PAWN_ROWS[PLAYER_N]][c] = (PIECE_PAWN, PLAYER_N)
            board[PAWN_ROWS[PLAYER_S]][c] = (PIECE_PAWN, PLAYER_S)

        hands = {
            PLAYER_N: {PIECE_PAWN: 0, PIECE_CAT: 0, PIECE_DOG: 0},
            PLAYER_S: {PIECE_PAWN: 0, PIECE_CAT: 0, PIECE_DOG: 0},
        }
        return GameState(board=board, hands=hands, turn=PLAYER_S, move_number=1)

    def clone(self) -> "GameState":
        return GameState(
            board=[[cell if cell is None else (cell[0], cell[1]) for cell in row] for row in self.board],
            hands={
                PLAYER_N: dict(self.hands[PLAYER_N]),
                PLAYER_S: dict(self.hands[PLAYER_S]),
            },
            turn=self.turn,
            move_number=self.move_number,
        )

    @staticmethod
    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < ROWS and 0 <= c < COLS

    @staticmethod
    def forward_dir(player: str) -> int:
        return -1 if player == PLAYER_S else 1

    @staticmethod
    def enemy_camp(player: str, row: int) -> bool:
        return row in (0, 1) if player == PLAYER_S else row in (ROWS - 2, ROWS - 1)

    @staticmethod
    def last_rank(player: str, row: int) -> bool:
        return row == 0 if player == PLAYER_S else row == ROWS - 1

    @staticmethod
    def movement_deltas(piece_type: str, player: str) -> List[Tuple[int, int]]:
        f = GameState.forward_dir(player)
        if piece_type == PIECE_LION:
            return [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1), (0, 1),
                (1, -1), (1, 0), (1, 1),
            ]
        if piece_type in (PIECE_DOG, PIECE_HEN, PIECE_SUPER_CAT):
            return [(f, 0), (f, -1), (f, 1), (0, -1), (0, 1), (-f, 0)]
        if piece_type == PIECE_CAT:
            return [(f, 0), (f, -1), (f, 1), (-f, -1), (-f, 1)]
        if piece_type == PIECE_PAWN:
            return [(f, 0)]
        return []

    def find_lion(self, player: str) -> Optional[Tuple[int, int]]:
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.board[r][c]
                if cell and cell[0] == PIECE_LION and cell[1] == player:
                    return (r, c)
        return None

    def is_in_check(self, player: str) -> bool:
        lion_pos = self.find_lion(player)
        if lion_pos is None:
            return True
        opponent = PLAYER_N if player == PLAYER_S else PLAYER_S
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.board[r][c]
                if not cell or cell[1] != opponent:
                    continue
                for dr, dc in self.movement_deltas(cell[0], cell[1]):
                    nr, nc = r + dr, c + dc
                    if nr == lion_pos[0] and nc == lion_pos[1]:
                        return True
        return False

    def _apply_promotion_options(self, move: Move, piece_type: str, player: str) -> List[Move]:
        if piece_type not in PROMOTES:
            return [move]
        in_camp = self.enemy_camp(player, move.frm[0]) or self.enemy_camp(player, move.to[0])
        if not in_camp:
            return [move]
        must_promote = piece_type == PIECE_PAWN and self.last_rank(player, move.to[0])
        if must_promote:
            return [Move(drop=False, piece=move.piece, frm=move.frm, to=move.to, promote=True)]
        return [
            Move(drop=False, piece=move.piece, frm=move.frm, to=move.to, promote=False),
            Move(drop=False, piece=move.piece, frm=move.frm, to=move.to, promote=True),
        ]

    def _generate_piece_moves(self, r: int, c: int, piece_type: str, player: str) -> List[Move]:
        moves = []
        for dr, dc in self.movement_deltas(piece_type, player):
            nr, nc = r + dr, c + dc
            if not self.in_bounds(nr, nc):
                continue
            target = self.board[nr][nc]
            if target and target[1] == player:
                continue
            base_move = Move(drop=False, piece=piece_type, frm=(r, c), to=(nr, nc), promote=False)
            moves.extend(self._apply_promotion_options(base_move, piece_type, player))
        return moves

    def _has_pawn_in_file(self, player: str, file_idx: int) -> bool:
        for r in range(ROWS):
            cell = self.board[r][file_idx]
            if cell and cell[1] == player and cell[0] == PIECE_PAWN:
                return True
        return False

    def _is_pawn_drop_mate(self, player: str, r: int, c: int) -> bool:
        move = Move(drop=True, piece=PIECE_PAWN, to=(r, c))
        next_state = self.apply_move(move)
        opponent = PLAYER_N if player == PLAYER_S else PLAYER_S
        if not next_state.is_in_check(opponent):
            return False
        opp_moves = next_state.generate_legal_moves(opponent, skip_pawn_drop_mate_check=True)
        return len(opp_moves) == 0

    def generate_drop_moves(self, player: str, skip_pawn_drop_mate_check: bool = False) -> List[Move]:
        moves = []
        hand = self.hands[player]
        for piece_type, count in hand.items():
            if count <= 0:
                continue
            for r in range(ROWS):
                for c in range(COLS):
                    if self.board[r][c] is not None:
                        continue
                    if piece_type == PIECE_PAWN:
                        if self.last_rank(player, r):
                            continue
                        if self._has_pawn_in_file(player, c):
                            continue
                        if not skip_pawn_drop_mate_check and self._is_pawn_drop_mate(player, r, c):
                            continue
                    moves.append(Move(drop=True, piece=piece_type, to=(r, c)))
        return moves

    def generate_legal_moves(self, player: Optional[str] = None, skip_pawn_drop_mate_check: bool = False) -> List[Move]:
        if player is None:
            player = self.turn
        moves: List[Move] = []
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.board[r][c]
                if not cell or cell[1] != player:
                    continue
                moves.extend(self._generate_piece_moves(r, c, cell[0], cell[1]))
        moves.extend(self.generate_drop_moves(player, skip_pawn_drop_mate_check))

        legal: List[Move] = []
        for move in moves:
            next_state = self.apply_move(move)
            if not next_state.is_in_check(player):
                legal.append(move)
        return legal

    def apply_move(self, move: Move) -> "GameState":
        next_state = self.clone()
        player = next_state.turn

        if move.drop:
            next_state.board[move.to[0]][move.to[1]] = (move.piece, player)
            next_state.hands[player][move.piece] -= 1
        else:
            frm_r, frm_c = move.frm
            piece_type, piece_owner = next_state.board[frm_r][frm_c]
            target = next_state.board[move.to[0]][move.to[1]]
            next_state.board[frm_r][frm_c] = None

            if target:
                captured_type, _ = target
                captured_type = DEMOTES.get(captured_type, captured_type)
                if captured_type != PIECE_LION:
                    next_state.hands[player][captured_type] += 1

            if move.promote and piece_type in PROMOTES:
                piece_type = PROMOTES[piece_type]

            next_state.board[move.to[0]][move.to[1]] = (piece_type, piece_owner)

        next_state.turn = PLAYER_N if player == PLAYER_S else PLAYER_S
        next_state.move_number += 1
        return next_state

    def outcome(self) -> Optional[int]:
        """Returns +1 if South wins, -1 if North wins, 0 draw, None if ongoing."""
        if self.find_lion(PLAYER_S) is None:
            return -1
        if self.find_lion(PLAYER_N) is None:
            return 1
        moves = self.generate_legal_moves(self.turn)
        if not moves:
            if self.is_in_check(self.turn):
                return 1 if self.turn == PLAYER_N else -1
            return 0
        return None

    def to_planes(self) -> List[List[List[int]]]:
        """12 binary planes for pieces + 1 turn plane.

        Order: [S-L, S-D, S-C, S-P, S-H, S-U, N-L, N-D, N-C, N-P, N-H, N-U, turn]
        """
        types = [PIECE_LION, PIECE_DOG, PIECE_CAT, PIECE_PAWN, PIECE_HEN, PIECE_SUPER_CAT]
        planes = [[[0 for _ in range(COLS)] for _ in range(ROWS)] for _ in range(len(types) * 2 + 1)]
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.board[r][c]
                if not cell:
                    continue
                t, owner = cell
                idx = types.index(t)
                offset = 0 if owner == PLAYER_S else len(types)
                planes[idx + offset][r][c] = 1
        turn_plane = len(types) * 2
        val = 1 if self.turn == PLAYER_S else 0
        for r in range(ROWS):
            for c in range(COLS):
                planes[turn_plane][r][c] = val
        return planes

    @staticmethod
    def square_to_index(r: int, c: int) -> int:
        return r * COLS + c

    @staticmethod
    def index_to_square(idx: int) -> Tuple[int, int]:
        return divmod(idx, COLS)

    @staticmethod
    def action_size() -> int:
        return 30 * 30 * 2 + 3 * 30

    @staticmethod
    def move_to_action(move: Move) -> int:
        if move.drop:
            drop_offset = 30 * 30 * 2
            piece_map = {PIECE_PAWN: 0, PIECE_CAT: 1, PIECE_DOG: 2}
            to_idx = GameState.square_to_index(move.to[0], move.to[1])
            return drop_offset + piece_map[move.piece] * 30 + to_idx
        from_idx = GameState.square_to_index(move.frm[0], move.frm[1])
        to_idx = GameState.square_to_index(move.to[0], move.to[1])
        promo_flag = 1 if move.promote else 0
        return (from_idx * 30 + to_idx) * 2 + promo_flag

    @staticmethod
    def action_to_move(action_id: int) -> Move:
        drop_offset = 30 * 30 * 2
        if action_id >= drop_offset:
            piece_idx, to_idx = divmod(action_id - drop_offset, 30)
            piece_map = {0: PIECE_PAWN, 1: PIECE_CAT, 2: PIECE_DOG}
            r, c = GameState.index_to_square(to_idx)
            return Move(drop=True, piece=piece_map[piece_idx], to=(r, c))
        pair, promo_flag = divmod(action_id, 2)
        from_idx, to_idx = divmod(pair, 30)
        frm = GameState.index_to_square(from_idx)
        to = GameState.index_to_square(to_idx)
        return Move(drop=False, piece="", frm=frm, to=to, promote=bool(promo_flag))
