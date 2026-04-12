/* ===============================================
   CashPilot — Chat Interface
   =============================================== */

let chatOpen = false;

function toggleChat() {
    chatOpen = !chatOpen;
    const panel = document.getElementById('chatPanel');
    const toggle = document.getElementById('chatToggle');

    if (chatOpen) {
        panel.classList.add('open');
        toggle.style.display = 'none';
        document.getElementById('chatInput').focus();
    } else {
        panel.classList.remove('open');
        toggle.style.display = 'flex';
    }
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    const sendBtn = document.getElementById('chatSendBtn');
    sendBtn.disabled = true;
    input.value = '';

    // Add user message
    appendChatMessage(message, 'user');

    // Create AI response bubble
    const aiMsg = appendChatMessage('', 'ai');
    const bubble = aiMsg.querySelector('.chat-bubble');
    bubble.innerHTML = '<span class="chat-typing">Thinking...</span>';

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, transactions }),
        });

        if (!res.ok) {
            const err = await res.json();
            bubble.textContent = err.error || 'Something went wrong.';
            sendBtn.disabled = false;
            return;
        }

        // Handle streaming response (SSE)
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        bubble.textContent = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const payload = line.slice(6);
                    if (payload === '[DONE]') break;

                    try {
                        const parsed = JSON.parse(payload);
                        if (parsed.chunk) {
                            fullText += parsed.chunk;
                            bubble.innerHTML = formatChatResponse(fullText);
                            scrollChatToBottom();
                        }
                    } catch (e) {
                        // skip invalid JSON
                    }
                }
            }
        }

        // Final formatting
        bubble.innerHTML = formatChatResponse(fullText);

    } catch (err) {
        bubble.textContent = 'Failed to connect. Please try again.';
    } finally {
        sendBtn.disabled = false;
        input.focus();
        scrollChatToBottom();
    }
}

function appendChatMessage(text, role) {
    const container = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.textContent = text;

    msgDiv.appendChild(bubble);
    container.appendChild(msgDiv);
    scrollChatToBottom();
    return msgDiv;
}

function scrollChatToBottom() {
    const container = document.getElementById('chatMessages');
    container.scrollTop = container.scrollHeight;
}

function formatChatResponse(text) {
    // Basic markdown-like formatting
    let html = text
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Bullet points
        .replace(/^[-•]\s+(.*)/gm, '<li>$1</li>')
        // Numbered lists
        .replace(/^\d+\.\s+(.*)/gm, '<li>$1</li>')
        // Line breaks
        .replace(/\n/g, '<br>');

    // Wrap consecutive <li> elements in <ul>
    html = html.replace(/((?:<li>.*?<\/li><br>?)+)/g, '<ul>$1</ul>');
    // Clean up extra <br> inside <ul>
    html = html.replace(/<ul>(.*?)<\/ul>/gs, (match, inner) => {
        return '<ul>' + inner.replace(/<br>/g, '') + '</ul>';
    });

    return html;
}
