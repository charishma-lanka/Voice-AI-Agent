// WebSocket connection
let ws = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let currentLanguage = 'english';

// DOM elements
const statusBadge = document.getElementById('statusBadge');
const statusText = document.getElementById('statusText');
const micButton = document.getElementById('micButton');
const recordingIndicator = document.getElementById('recordingIndicator');
const latencyValue = document.getElementById('latencyValue');
const latencyStatus = document.getElementById('latencyStatus');
const userMessageDiv = document.getElementById('userMessage');
const aiMessageDiv = document.getElementById('aiMessage');
const languageBadge = document.getElementById('languageBadge');
const timestampSpan = document.getElementById('timestamp');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');

// Connect to WebSocket
function connectWebSocket() {
    
    ws = new WebSocket('wss://voice-ai-agent-njcg.onrender.com/ws/123');
    ws.onopen = () => {
        console.log('✅ WebSocket connected');
        statusText.textContent = 'Connected';
        statusBadge.querySelector('.dot').className = 'dot connected';
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data);
        
        if (data.type === 'response') {
            // Update AI message
            aiMessageDiv.innerHTML = `
                <div class="message-role">🤖 AI AGENT</div>
                <div class="message-text">${escapeHtml(data.transcript)}</div>
            `;
            
            // Update latency
            const latencyMs = data.latency_ms;
            latencyValue.textContent = `${latencyMs.toFixed(0)}ms`;
            
            if (latencyMs < 450) {
                latencyValue.className = 'latency-value good';
                latencyStatus.innerHTML = '✅ Within target (<450ms)';
                latencyStatus.style.color = '#28a745';
            } else {
                latencyValue.className = 'latency-value bad';
                latencyStatus.innerHTML = '❌ Exceeds target (>450ms)';
                latencyStatus.style.color = '#dc3545';
            }
            
            // Update language badge
            const langMap = {
                english: '🇬🇧 English',
                hindi: '🇮🇳 हिन्दी',
                tamil: '🇮🇳 தமிழ்'
            };
            currentLanguage = data.language;
            languageBadge.innerHTML = langMap[data.language] || '🇬🇧 English';
            
            // Update timestamp
            timestampSpan.textContent = new Date().toLocaleTimeString();
            
            // Show appointment confirmation if exists
            if (data.appointment) {
                setTimeout(() => {
                    aiMessageDiv.innerHTML = `
                        <div class="message-role">🤖 AI AGENT</div>
                        <div class="message-text">
                            ${escapeHtml(data.transcript)}
                            <br><br>
                            📋 <strong>Appointment ID: ${data.appointment.appointment_id}</strong>
                        </div>
                    `;
                }, 500);
            }
        }
        
        if (data.type === 'error') {
            aiMessageDiv.innerHTML = `
                <div class="message-role">🤖 AI AGENT</div>
                <div class="message-text">⚠️ Error: ${escapeHtml(data.message)}</div>
            `;
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        statusText.textContent = 'Connection Error';
        statusBadge.querySelector('.dot').className = 'dot disconnected';
        aiMessageDiv.innerHTML = `
            <div class="message-role">🤖 AI AGENT</div>
            <div class="message-text">⚠️ Cannot connect to backend. Please make sure the server is running: python run.py</div>
        `;
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        statusText.textContent = 'Disconnected';
        statusBadge.querySelector('.dot').className = 'dot disconnected';
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
}

// Start recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const base64Audio = await blobToBase64(audioBlob);
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ audio: base64Audio }));
                userMessageDiv.innerHTML = `
                    <div class="message-role">👤 YOU</div>
                    <div class="message-text">🎙️ Voice input sent...</div>
                `;
                aiMessageDiv.innerHTML = `
                    <div class="message-role">🤖 AI AGENT</div>
                    <div class="message-text">⏳ Processing your voice...</div>
                `;
            }
            
            recordingIndicator.style.display = 'none';
            micButton.classList.remove('recording');
            isRecording = false;
        };
        
        mediaRecorder.start();
        isRecording = true;
        micButton.classList.add('recording');
        recordingIndicator.style.display = 'flex';
        
        // Auto stop after 5 seconds
        setTimeout(() => {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
            }
        }, 5000);
        
    } catch (error) {
        console.error('Microphone error:', error);
        alert('Please allow microphone access to use voice input');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
    }
}

// Convert blob to base64
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// Send text message
function sendMessage(text) {
    if (!text.trim()) return;
    
    userMessageDiv.innerHTML = `
        <div class="message-role">👤 YOU</div>
        <div class="message-text">${escapeHtml(text)}</div>
    `;
    
    aiMessageDiv.innerHTML = `
        <div class="message-role">🤖 AI AGENT</div>
        <div class="message-text">⏳ Thinking...</div>
    `;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ text: text }));
    } else {
        alert('WebSocket not connected. Please make sure backend is running!');
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
micButton.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

sendBtn.addEventListener('click', () => {
    if (textInput.value.trim()) {
        sendMessage(textInput.value);
        textInput.value = '';
    }
});

textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendBtn.click();
    }
});

// Example buttons
document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const text = btn.getAttribute('data-text');
        if (text) {
            sendMessage(text);
        }
    });
});

// Initialize connection
connectWebSocket();

console.log('Frontend initialized. Waiting for WebSocket connection...');