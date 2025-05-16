const socket = io();

const loginContainer = document.getElementById('login-container');
const usernameInput = document.getElementById('username-input');
const loginBtn = document.getElementById('login-btn');
const gameContainer = document.getElementById('game-container');
const statusContainer = document.getElementById('status-container');
let username = '';

loginBtn.addEventListener('click', () => {
    username = usernameInput.value;
    console.log('username:', username);
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: username })
    }).then(response => response.json())
      .then(data => {
            if (data.status === 'success') {
                  socket.emit('login', { username: username });
              }
          }).catch(error => {
              console.error('Error:', error);
          });
  });

// Listen for login_success event
socket.on('login_success', (data) => {
    console.log(data.message);
    statusContainer.innerHTML = `<p>${data.message}</p>`;
    loginContainer.style.display = 'none';
    statusContainer.style.display = 'block';
});



// Listen for pairing_success event
socket.on('game__start', (data) => {
    console.log(data);
    message = data.message;
    players = data.players;
    for (let i = 0; i < players.length; i++) {
        if (players[i] === username) {
            continue;
        }
        message += ` with ${players[i]}`;
    }
    statusContainer.innerHTML = `<p>${message}</p>`;
    gameContainer.style.display = 'flex';
//    statusContainer.style.display = 'none';
});
