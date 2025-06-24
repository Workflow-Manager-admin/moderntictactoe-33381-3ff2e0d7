import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_TTT_BACKEND_URL || 'http://localhost:3001'; // Change if needed

// Utility: get status message from backend state
function getStatusText(game) {
  if (!game) return '';
  if (game.status === 'waiting') return 'Waiting for players...';
  if (game.status === 'in_progress')
    return `Turn: Player ${game.current_player === 'X' ? '1 (X)' : '2 (O)'}`;
  if (game.status === 'draw') return 'It\'s a draw!';
  if (game.status === 'won')
    return `Winner: Player ${game.winner === 'X' ? '1 (X)' : '2 (O)'}`;
  return '';
}

// PUBLIC_INTERFACE
function App() {
  // gameId: unique id for the game instance
  const [gameId, setGameId] = useState(null);
  // game: game state object from backend: {board: [["","",""],...], current_player, status, winner, ...}
  const [game, setGame] = useState(null);
  // For disabled states during API calls
  const [loading, setLoading] = useState(false);
  // For displaying error messages
  const [error, setError] = useState('');

  // PUBLIC_INTERFACE
  // Start a new game
  const startNewGame = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error('Failed to start new game');
      const data = await response.json();
      setGameId(data.game_id);
      setGame(data);
    } catch (e) {
      setError('Could not start new game.');
    } finally {
      setLoading(false);
    }
  };

  // PUBLIC_INTERFACE
  // Make a move: row, col are 0-indexed
  const makeMove = async (row, col) => {
    if (
      !game ||
      loading ||
      game.status !== 'in_progress' ||
      game.board[row][col] !== ''
    ) {
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/game/${gameId}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row, col }),
      });
      if (!response.ok) {
        const err = await response.json();
        setError(err.detail || 'Move failed');
        setLoading(false);
        return;
      }
      const data = await response.json();
      setGame(data);
    } catch (e) {
      setError('Could not make the move.');
    } finally {
      setLoading(false);
    }
  };

  // PUBLIC_INTERFACE
  // Sync current game state from backend (e.g., after page reload)
  const syncGameState = async () => {
    if (!gameId) return;
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/game/${gameId}`);
      if (response.ok) {
        const data = await response.json();
        setGame(data);
      }
    } catch (e) {
      setError('Could not sync game state.');
    } finally {
      setLoading(false);
    }
  };

  // On mount: Optionally sync game from localStorage (for UX), otherwise always start fresh
  useEffect(() => {
    // Optionally: Persist game ID to localStorage. Clear on reload for clean start.
    // To persist between reloads, remove the following line.
    setGameId(null);
    setGame(null);
  }, []);

  // If gameId changes, auto-sync state from backend
  useEffect(() => {
    if (gameId) syncGameState();
  }, [gameId]);

  // Helper: Render game board 3x3
  const renderBoard = () => {
    if (!game) return null;
    return (
      <div className="ttt-board">
        {[0,1,2].map(rowIdx => (
          <div className="ttt-row" key={rowIdx}>
            {[0,1,2].map(colIdx => (
              <button
                key={colIdx}
                className="ttt-cell"
                onClick={() => makeMove(rowIdx, colIdx)}
                disabled={
                  loading ||
                  game.status !== 'in_progress' ||
                  game.board[rowIdx][colIdx] !== ''
                }
                aria-label={`Cell ${rowIdx+1},${colIdx+1}`}
                style={cellStyleForValue(game.board[rowIdx][colIdx])}
              >
                {game.board[rowIdx][colIdx]}
              </button>
            ))}
          </div>
        ))}
      </div>
    );
  };

  // UI: game controls (New Game)
  const renderControls = () => (
    <div className="ttt-controls">
      <button
        className="btn btn-large ttt-primary"
        onClick={startNewGame}
        disabled={loading}
      >
        {game ? 'Restart Game' : 'Start New Game'}
      </button>
    </div>
  );

  // UI: game status
  const renderStatus = () => (
    <div className="ttt-status">
      {error && <div className="ttt-error">{error}</div>}
      <div className="ttt-status-main">{getStatusText(game)}</div>
    </div>
  );

  // UI: winner/ending
  const renderResult = () => {
    if (!game) return null;
    if (game.status === 'won' || game.status === 'draw') {
      return (
        <div className="ttt-result">
          <span>
            {game.status === 'won'
              ? `🎉 Player ${game.winner === 'X' ? '1 (X)' : '2 (O)'} wins!`
              : 'It\'s a draw!'}
          </span>
        </div>
      );
    }
    return null;
  };

  // Main Render
  return (
    <div className="app">
      <nav className="navbar">
        <div className="container" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%'}}>
          <div className="logo"><span className="logo-symbol" style={{color: 'var(--primary-color)'}}>◎</span> Tic Tac Toe</div>
          <a href="https://github.com/" className="btn ttt-secondary" target="_blank" rel="noopener noreferrer" style={{fontWeight: 400, background: 'none', color: 'var(--primary-color)', border: '1px solid var(--primary-color)'}}>Source</a>
        </div>
      </nav>
      <main>
        <div className="ttt-container">
          <div className="ttt-center">
            <h1 className="ttt-title">Tic Tac Toe</h1>
            <p className="ttt-desc">A modern, minimal web-based tic-tac-toe game.</p>
            {renderControls()}
            {renderStatus()}
            {game && renderBoard()}
            {renderResult()}
          </div>
        </div>
      </main>
    </div>
  );
}

// Utility: Style X and O differently
function cellStyleForValue(val) {
  if (val === 'X')
    return { color: 'var(--primary-color)', fontWeight: 700 };
  if (val === 'O')
    return { color: 'var(--accent-color)', fontWeight: 700 };
  return {};
}

export default App;
