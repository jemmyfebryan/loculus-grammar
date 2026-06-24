const GRID_SIZE = 5;
let sequence = [];
let isDragging = false;

const gridContainer = document.getElementById('auth-grid');
const clearBtn = document.getElementById('clear-btn');
const loginBtn = document.getElementById('login-btn');
const messageContainer = document.getElementById('message-container');

// Initialize the grid
function initGrid() {
    gridContainer.innerHTML = '';
    for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.addEventListener('mousedown', handleCellStart);
            cell.addEventListener('mouseenter', handleCellEnter);
            cell.addEventListener('touchstart', handleTouchStart, { passive: false });
            gridContainer.appendChild(cell);
        }
    }
}

// Handle cell click/start
function handleCellStart(event) {
    event.preventDefault();
    isDragging = true;
    addCellToSequence(event.currentTarget);
}

// Handle cell enter during drag
function handleCellEnter(event) {
    if (isDragging) {
        addCellToSequence(event.currentTarget);
    }
}

// Handle touch start
function handleTouchStart(event) {
    event.preventDefault();
    isDragging = true;
    const touch = event.touches[0];
    const cell = document.elementFromPoint(touch.clientX, touch.clientY);
    if (cell && cell.classList.contains('grid-cell')) {
        addCellToSequence(cell);
    }
}

// Handle touch move
function handleTouchMove(event) {
    if (!isDragging) return;
    event.preventDefault();
    const touch = event.touches[0];
    const cell = document.elementFromPoint(touch.clientX, touch.clientY);
    if (cell && cell.classList.contains('grid-cell')) {
        addCellToSequence(cell);
    }
}

// Handle touch end
function handleTouchEnd(event) {
    isDragging = false;
}

// Handle drag end
function handleDragEnd() {
    isDragging = false;
}

// Add cell to sequence
function addCellToSequence(cell) {
    const x = parseInt(cell.dataset.x);
    const y = parseInt(cell.dataset.y);

    // Check if this cell is already in sequence
    const existingIndex = sequence.findIndex(item => item.x === x && item.y === y);

    if (existingIndex !== -1) {
        // Cell already clicked, ignore
        return;
    }

    // Add to sequence
    sequence.push({ x, y });
    updateGrid();
}

// Update grid display
function updateGrid() {
    const cells = gridContainer.querySelectorAll('.grid-cell');
    cells.forEach(cell => {
        const x = parseInt(cell.dataset.x);
        const y = parseInt(cell.dataset.y);
        const index = sequence.findIndex(item => item.x === x && item.y === y);

        if (index !== -1) {
            cell.classList.add('active');
            cell.textContent = index + 1;
        } else {
            cell.classList.remove('active');
            cell.textContent = '';
        }
    });

    // Update login button state
    loginBtn.disabled = sequence.length < 5;
}

// Clear pattern
clearBtn.addEventListener('click', () => {
    sequence = [];
    updateGrid();
    clearMessages();
});

// Login handler
loginBtn.addEventListener('click', async () => {
    if (sequence.length < 5) {
        showMessage('Please select at least 5 cells', 'error');
        return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'Authenticating...';

    try {
        const response = await fetch('grid-login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sequence: sequence
            })
        });

        const data = await response.json();

        if (data.success) {
            showMessage('Authentication successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 500);
        } else {
            showMessage(data.error || 'Authentication failed', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    } finally {
        loginBtn.disabled = sequence.length < 5;
        loginBtn.textContent = 'Login';
    }
});

// Show message
function showMessage(text, type) {
    messageContainer.innerHTML = `<div class="${type}">${text}</div>`;
}

// Clear messages
function clearMessages() {
    messageContainer.innerHTML = '';
}

// Touch events
document.addEventListener('mouseup', handleDragEnd);
document.addEventListener('touchend', handleTouchEnd, { passive: false });
document.addEventListener('touchmove', handleTouchMove, { passive: false });

// Initialize
initGrid();
