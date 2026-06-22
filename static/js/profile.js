// Change Password Functionality
const GRID_SIZE = 5;
const ROOT_PATH = typeof window !== 'undefined' ? (window.ROOT_PATH || '') : '';
let currentSequence = [];
let newSequence = [];
let confirmSequence = [];
let isDragging = false;

const changePasswordBtn = document.getElementById('changePasswordBtn');
const changePasswordModal = document.getElementById('changePasswordModal');
const changePasswordClose = document.getElementById('changePasswordClose');
const passwordError = document.getElementById('passwordError');

// Step elements
const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');
const step3 = document.getElementById('step3');

// Grid containers
const currentGrid = document.getElementById('currentGrid');
const newGrid = document.getElementById('newGrid');
const confirmGrid = document.getElementById('confirmGrid');

// Buttons
const verifyCurrentBtn = document.getElementById('verifyCurrentBtn');
const setNewBtn = document.getElementById('setNewBtn');
const confirmChangeBtn = document.getElementById('confirmChangeBtn');
const clearCurrentBtn = document.getElementById('clearCurrentBtn');
const clearNewBtn = document.getElementById('clearNewBtn');
const clearConfirmBtn = document.getElementById('clearConfirmBtn');

// Initialize grids
function initPasswordGrid(container, sequenceVar) {
    container.innerHTML = '';
    for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.dataset.seq = sequenceVar;
            cell.addEventListener('mousedown', handlePasswordCellStart);
            cell.addEventListener('mouseenter', handlePasswordCellEnter);
            cell.addEventListener('touchstart', handlePasswordTouchStart, { passive: false });
            container.appendChild(cell);
        }
    }
}

function handlePasswordCellStart(event) {
    event.preventDefault();
    isDragging = true;
    const seqVar = event.currentTarget.dataset.seq;
    addPasswordCellToSequence(event.currentTarget, seqVar);
}

function handlePasswordCellEnter(event) {
    if (isDragging) {
        const seqVar = event.currentTarget.dataset.seq;
        addPasswordCellToSequence(event.currentTarget, seqVar);
    }
}

function handlePasswordTouchStart(event) {
    event.preventDefault();
    isDragging = true;
    const touch = event.touches[0];
    const cell = document.elementFromPoint(touch.clientX, touch.clientY);
    const seqVar = event.currentTarget.dataset.seq;
    if (cell && cell.classList.contains('grid-cell') && cell.dataset.seq === seqVar) {
        addPasswordCellToSequence(cell, seqVar);
    }
}

function handlePasswordTouchMove(event) {
    if (!isDragging) return;
    event.preventDefault();
    const touch = event.touches[0];
    const cell = document.elementFromPoint(touch.clientX, touch.clientY);
    if (cell && cell.classList.contains('grid-cell')) {
        addPasswordCellToSequence(cell, cell.dataset.seq);
    }
}

function addPasswordCellToSequence(cell, seqVar) {
    const x = parseInt(cell.dataset.x);
    const y = parseInt(cell.dataset.y);
    const sequence = seqVar === 'current' ? currentSequence : seqVar === 'new' ? newSequence : confirmSequence;

    const existingIndex = sequence.findIndex(item => item.x === x && item.y === y);
    if (existingIndex !== -1) return;

    sequence.push({ x, y });
    updatePasswordGrid(cell.parentElement, sequence);
}

function updatePasswordGrid(container, sequence) {
    const cells = container.querySelectorAll('.grid-cell');
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
}

function clearPasswordSequence(sequence) {
    sequence.length = 0;
}

// Modal handlers
changePasswordBtn.addEventListener('click', (e) => {
    e.preventDefault();
    changePasswordModal.classList.add('active');
    resetPasswordChange();
    initPasswordGrid(currentGrid, 'current');
    initPasswordGrid(newGrid, 'new');
    initPasswordGrid(confirmGrid, 'confirm');
});

changePasswordClose.addEventListener('click', () => {
    changePasswordModal.classList.remove('active');
});

changePasswordModal.addEventListener('click', (e) => {
    if (e.target === changePasswordModal) {
        changePasswordModal.classList.remove('active');
    }
});

// Clear buttons
clearCurrentBtn.addEventListener('click', () => {
    clearPasswordSequence(currentSequence);
    updatePasswordGrid(currentGrid, currentSequence);
    passwordError.style.display = 'none';
});

clearNewBtn.addEventListener('click', () => {
    clearPasswordSequence(newSequence);
    updatePasswordGrid(newGrid, newSequence);
    passwordError.style.display = 'none';
});

clearConfirmBtn.addEventListener('click', () => {
    clearPasswordSequence(confirmSequence);
    updatePasswordGrid(confirmGrid, confirmSequence);
    passwordError.style.display = 'none';
});

// Verify current password
verifyCurrentBtn.addEventListener('click', async () => {
    if (currentSequence.length < 5) {
        showPasswordError('Please select at least 5 cells');
        return;
    }

    try {
        const response = await fetch(ROOT_PATH + '/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'verify_current', sequence: currentSequence })
        });

        const data = await response.json();
        if (data.valid) {
            step1.style.display = 'none';
            step2.style.display = 'block';
            passwordError.style.display = 'none';
        } else {
            showPasswordError('Current password is incorrect');
        }
    } catch (error) {
        showPasswordError('Error verifying password');
    }
});

// Set new password
setNewBtn.addEventListener('click', () => {
    if (newSequence.length < 5) {
        showPasswordError('Please select at least 5 cells');
        return;
    }
    step2.style.display = 'none';
    step3.style.display = 'block';
    passwordError.style.display = 'none';
});

// Confirm password change
confirmChangeBtn.addEventListener('click', async () => {
    if (confirmSequence.length < 5) {
        showPasswordError('Please select at least 5 cells');
        return;
    }

    if (newSequence.length !== confirmSequence.length) {
        showPasswordError('Patterns do not match - length is different');
        return;
    }

    for (let i = 0; i < newSequence.length; i++) {
        if (newSequence[i].x !== confirmSequence[i].x || newSequence[i].y !== confirmSequence[i].y) {
            showPasswordError('Patterns do not match');
            return;
        }
    }

    try {
        const response = await fetch(ROOT_PATH + '/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'change_password', new_sequence: newSequence })
        });

        const data = await response.json();
        if (data.success) {
            changePasswordModal.classList.remove('active');
            alert('Password changed successfully!');
        } else {
            showPasswordError(data.error || 'Error changing password');
        }
    } catch (error) {
        showPasswordError('Error changing password');
    }
});

function showPasswordError(message) {
    passwordError.textContent = message;
    passwordError.style.display = 'block';
}

function resetPasswordChange() {
    clearPasswordSequence(currentSequence);
    clearPasswordSequence(newSequence);
    clearPasswordSequence(confirmSequence);
    step1.style.display = 'block';
    step2.style.display = 'none';
    step3.style.display = 'none';
    passwordError.style.display = 'none';
}

// Touch events
document.addEventListener('mouseup', () => { isDragging = false; });
document.addEventListener('touchend', () => { isDragging = false; });
document.addEventListener('touchmove', handlePasswordTouchMove, { passive: false });
