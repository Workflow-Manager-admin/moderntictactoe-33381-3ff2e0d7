from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict
import uuid

# Tag definitions for OpenAPI groups
openapi_tags = [
    {"name": "game", "description": "Tic Tac Toe Game Operations"},
]

app = FastAPI(
    title="Tic Tac Toe Backend API",
    description="Backend API serving game logic and game state management for Tic Tac Toe.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory "database" for games
games_store: Dict[str, dict] = {}

# Models


class GameCreateResponse(BaseModel):
    game_id: str = Field(..., description="Unique ID of the new game")
    board: list[list[Optional[str]]] = Field(
        ..., description="3x3 board. Each cell is 'X', 'O', or null"
    )
    next_player: Literal["X", "O"] = Field(..., description="Whose turn it is")
    winner: Optional[Literal["X", "O", "Draw"]] = Field(
        None, description="Winner if game is finished"
    )


class MoveRequest(BaseModel):
    row: int = Field(..., ge=0, le=2, description="Row (0..2) for the move")
    col: int = Field(..., ge=0, le=2, description="Column (0..2) for the move")


class MoveResponse(BaseModel):
    board: list[list[Optional[str]]] = Field(
        ..., description="3x3 board after the move"
    )
    next_player: Optional[Literal["X", "O"]] = Field(
        None, description="Whose turn is next (None if finished)"
    )
    winner: Optional[Literal["X", "O", "Draw"]] = Field(
        None, description="Winner if game has ended"
    )
    move_valid: bool = Field(..., description="Whether the move was valid")
    message: str = Field(..., description="Move result message to present to the user")


class GameStateResponse(BaseModel):
    game_id: str = Field(..., description="Game ID")
    board: list[list[Optional[str]]] = Field(..., description="Current 3x3 board")
    next_player: Optional[Literal["X", "O"]] = Field(
        None, description="Next turn (None if game is finished)"
    )
    winner: Optional[Literal["X", "O", "Draw"]] = Field(
        None, description="Winner, if the game is finished"
    )


# Helper functions

def new_board():
    """Create a new 3x3 tic tac toe board."""
    return [[None for _ in range(3)] for _ in range(3)]


def calc_winner(board):
    """Check for winner or draw."""
    # Rows, cols, diags
    for i in range(3):
        if board[i][0] and all(board[i][j] == board[i][0] for j in range(3)):
            return board[i][0]  # Row win
        if board[0][i] and all(board[j][i] == board[0][i] for j in range(3)):
            return board[0][i]  # Col win
    if board[0][0] and all(board[d][d] == board[0][0] for d in range(3)):
        return board[0][0]
    if board[0][2] and all(board[d][2 - d] == board[0][2] for d in range(3)):
        return board[0][2]
    # Draw
    if all(board[i][j] for i in range(3) for j in range(3)):
        return "Draw"
    return None


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["game"],
    summary="Health check",
    description="Check if server is running",
)
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/game",
    response_model=GameCreateResponse,
    tags=["game"],
    summary="Start New Game",
    description="Create a new Tic Tac Toe game",
)
def start_new_game():
    """Create a new tic tac toe game. Returns game ID and initial game state."""
    game_id = str(uuid.uuid4())
    board = new_board()
    state = {
        "id": game_id,
        "board": board,
        "next_player": "X",
        "winner": None,
    }
    games_store[game_id] = state
    return GameCreateResponse(
        game_id=game_id,
        board=board,
        next_player="X",
        winner=None,
    )


# PUBLIC_INTERFACE
@app.post(
    "/game/{game_id}/move",
    response_model=MoveResponse,
    tags=["game"],
    summary="Make a Move",
    description="Make a move for the current player",
)
def make_move(game_id: str, move: MoveRequest):
    """
    Make a move for the current player in the specified game.

    - **game_id**: The game to play in.
    - **row**/**col**: Position to play (0-based indices).

    Returns updated board, next player, winner status, and move validity.
    """
    state = games_store.get(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")

    board = state["board"]
    next_player = state["next_player"]
    winner = state["winner"]

    # If game over
    if winner:
        return MoveResponse(
            board=board,
            next_player=None,
            winner=winner,
            move_valid=False,
            message=f"Game already finished. Result: {winner}",
        )
    row, col = move.row, move.col
    if board[row][col] is not None:
        return MoveResponse(
            board=board,
            next_player=next_player,
            winner=None,
            move_valid=False,
            message="Cell already occupied.",
        )

    # Make move
    board[row][col] = next_player
    winner_check = calc_winner(board)

    if winner_check:
        state["winner"] = winner_check
        state["next_player"] = None
        msg = (
            f"Move made! Game Over: {winner_check}"
            if winner_check != "Draw"
            else "Move made! Game Over: Draw"
        )
        return MoveResponse(
            board=board,
            next_player=None,
            winner=winner_check,
            move_valid=True,
            message=msg,
        )

    # Switch player turn
    next_p = "O" if next_player == "X" else "X"
    state["next_player"] = next_p
    state["winner"] = None
    return MoveResponse(
        board=board,
        next_player=next_p,
        winner=None,
        move_valid=True,
        message=f"Move made. Next turn: {next_p}",
    )


# PUBLIC_INTERFACE
@app.get(
    "/game/{game_id}",
    response_model=GameStateResponse,
    tags=["game"],
    summary="Get Game State",
    description="Retrieve the current board, player turn, and result for a game.",
)
def get_game_state(game_id: str):
    """
    Retrieve the game state: board, next player, and results for a given game.

    - **game_id**: ID for the game to get state for.
    """
    state = games_store.get(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameStateResponse(
        game_id=state["id"],
        board=state["board"],
        next_player=state["next_player"],
        winner=state["winner"],
    )


# PUBLIC_INTERFACE
@app.get(
    "/game/{game_id}/board",
    response_model=list,
    tags=["game"],
    summary="Get Board",
    description="Get just the board layout for a given game (as a 2D list).",
)
def get_board(game_id: str):
    """
    Return 2D board array for a game. Each cell is "X", "O", or None.
    """
    state = games_store.get(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return state["board"]


# PUBLIC_INTERFACE
@app.get(
    "/game/{game_id}/player",
    response_model=dict,
    tags=["game"],
    summary="Get Player Turn",
    description="Get which player's turn it is.",
)
def get_player_turn(game_id: str):
    """
    Return the player whose turn it currently is.
    """
    state = games_store.get(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"next_player": state["next_player"]}
