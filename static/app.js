/* ═══════════════════════════════════════════════════════════
   GroupsApp – Frontend Application Logic
   ═══════════════════════════════════════════════════════════ */

// ── URL del Backend ───────────────────────────────────────
// En desarrollo local: dejar vacío (same origin, FastAPI sirve todo)
// En producción AWS: URL del backend en EC2
// IMPORTANTE: Si la IP de EC2 cambia (reinicio del lab), actualizar aquí y re-subir a S3
const BACKEND_URL = 'http://3.91.64.185:8000';  // <-- IP pública de EC2 en Learner Lab
const API = BACKEND_URL;

// ── State ─────────────────────────────────────────────────
let state = {
    token: localStorage.getItem('token') || null,
    user: null,
    groups: [],
    currentGroupId: null,
    currentGroupName: '',
    channels: [],
    currentChatType: null, // 'channel' | 'dm'
    currentChatId: null,
    currentChatName: '',
    dmTargetUserId: null,
    messages: [],
    pollInterval: null,
    heartbeatInterval: null,
    conversationPollInterval: null,
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,
};

// ── API Helper ────────────────────────────────────────────
async function api(path, options = {}) {
    const headers = { ...options.headers };
    if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    const res = await fetch(`${API}${path}`, { ...options, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(err.detail || `Error ${res.status}`);
    }
    if (res.status === 204) return null;
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) return res.json();
    return res;
}

// ── DOM refs ──────────────────────────────────────────────
const $ = (sel) => {
    const el = document.querySelector(sel);
    if (!el && sel.startsWith('#')) {
        console.warn(`Elemento no encontrado: ${sel}`);
    }
    return el;
};
const $$ = (sel) => document.querySelectorAll(sel);

const authScreen = $('#auth-screen');
const appScreen = $('#app-screen');
const loginForm = $('#login-form');
const registerForm = $('#register-form');
const authError = $('#auth-error');

// ── Toast ─────────────────────────────────────────────────
function toast(msg, type = '') {
    const t = $('#toast');
    t.textContent = msg;
    t.className = `toast show ${type}`;
    setTimeout(() => t.className = 'toast hidden', 3000);
}

// ═══════════ AUTH ═══════════

$('#show-register').addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.classList.remove('active');
    registerForm.classList.add('active');
    authError.classList.add('hidden');
});

$('#show-login').addEventListener('click', (e) => {
    e.preventDefault();
    registerForm.classList.remove('active');
    loginForm.classList.add('active');
    authError.classList.add('hidden');
});

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userEl = $('#login-username');
    const passEl = $('#login-password');
    if (!userEl || !passEl) return;

    authError.classList.add('hidden');
    try {
        const data = await api('/auth/login', {
            method: 'POST',
            body: {
                username: userEl.value,
                password: passEl.value,
            },
        });
        state.token = data.access_token;
        localStorage.setItem('token', state.token);

        // Clear sensitive fields
        passEl.value = '';

        await enterApp();
    } catch (err) {
        authError.textContent = err.message;
        authError.classList.remove('hidden');
    }
});

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = $('#reg-username');
    const e_mail = $('#reg-email');
    const d = $('#reg-displayname');
    const p = $('#reg-password');
    if (!u || !e_mail || !d || !p) return;

    authError.classList.add('hidden');
    try {
        await api('/auth/register', {
            method: 'POST',
            body: {
                username: u.value,
                email: e_mail.value,
                display_name: d.value,
                password: p.value,
            },
        });

        toast('¡Registro exitoso! Inicia sesión', 'success');
        registerForm.classList.remove('active');
        loginForm.classList.add('active');

        // Fill login username automatically
        const loginU = $('#login-username');
        if (loginU) loginU.value = u.value;

        // Clear registration fields
        u.value = ''; e_mail.value = ''; d.value = ''; p.value = '';
    } catch (err) {
        authError.textContent = err.message;
        authError.classList.remove('hidden');
    }
});

$('#btn-logout').addEventListener('click', () => {
    state.token = null;
    state.user = null;
    localStorage.removeItem('token');
    clearInterval(state.pollInterval);
    clearInterval(state.heartbeatInterval);
    clearInterval(state.conversationPollInterval);
    appScreen.classList.add('hidden');
    authScreen.classList.remove('hidden');
    loginForm.classList.add('active');
    registerForm.classList.remove('active');
});

// ═══════════ ENTER APP ═══════════

async function enterApp() {
    try {
        state.user = await api('/auth/me');
        authScreen.classList.add('hidden');
        appScreen.classList.remove('hidden');
        $('#user-display-name').textContent = state.user.display_name;
        $('#user-avatar').textContent = state.user.display_name.charAt(0).toUpperCase();
        await loadGroups();
        loadConversations(); // Load chat history
        startHeartbeat();
        startConversationPolling(); // Real-time sidebar updates
    } catch {
        state.token = null;
        localStorage.removeItem('token');
        authScreen.classList.remove('hidden');
        appScreen.classList.add('hidden');
    }
}

// ═══════════ GROUPS ═══════════

async function loadGroups() {
    try {
        const data = await api('/groups');
        state.groups = data.groups;
        renderGroups();
    } catch (err) {
        toast(err.message, 'error');
    }
}

function renderGroups() {
    const list = $('#groups-list');
    if (state.groups.length === 0) {
        list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">No tienes grupos aún.<br>Crea uno con el botón ＋</div>';
        return;
    }
    list.innerHTML = state.groups.map(g => `
        <div class="chat-list-item ${state.currentGroupId === g.id ? 'active' : ''}" data-group-id="${g.id}" data-group-name="${esc(g.name)}">
            <div class="item-icon group">${g.name.charAt(0).toUpperCase()}</div>
            <div class="item-info">
                <div class="item-name">${esc(g.name)}</div>
                <div class="item-desc">${esc(g.description || 'Sin descripción')}</div>
            </div>
        </div>
    `).join('');

    list.querySelectorAll('.chat-list-item').forEach(item => {
        item.addEventListener('click', () => {
            const gid = item.dataset.groupId;
            const gname = item.dataset.groupName;
            openGroup(gid, gname);
        });
    });
}

// ── Create Group ──

$('#btn-new-group').addEventListener('click', () => {
    $('#modal-create-group').classList.remove('hidden');
});

$('#form-create-group').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        await api('/groups', {
            method: 'POST',
            body: {
                name: $('#group-name').value,
                description: $('#group-desc').value || null,
            },
        });
        $('#modal-create-group').classList.add('hidden');
        $('#group-name').value = '';
        $('#group-desc').value = '';
        toast('Grupo creado', 'success');
        await loadGroups();
    } catch (err) {
        toast(err.message, 'error');
    }
});

// ═══════════ CHANNELS ═══════════

async function openGroup(groupId, groupName) {
    state.currentGroupId = groupId;
    state.currentGroupName = groupName;

    // Check if user is admin
    const group = state.groups.find(g => g.id === groupId);
    state.currentGroupAdmin = group ? group.created_by : null;

    if (state.currentGroupAdmin === state.user.id) {
        $('#btn-delete-group').classList.remove('hidden');
    } else {
        $('#btn-delete-group').classList.add('hidden');
    }

    stopPolling();
    hideChat();
    renderGroups();

    $('#channel-group-name').textContent = groupName;
    $('#channel-panel').classList.remove('hidden');

    try {
        const data = await api(`/groups/${groupId}/channels`);
        state.channels = data.channels;
        renderChannels();
    } catch (err) {
        toast(err.message, 'error');
    }
}

function renderChannels() {
    const list = $('#channels-list');
    if (state.channels.length === 0) {
        list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">No hay canales.<br>Crea uno con ＃＋</div>';
        return;
    }
    list.innerHTML = state.channels.map(c => `
        <div class="chat-list-item" data-channel-id="${c.id}" data-channel-name="${esc(c.name)}">
            <div class="item-icon channel">#</div>
            <div class="item-info">
                <div class="item-name">${esc(c.name)}</div>
                <div class="item-desc">${esc(c.description || '')}</div>
            </div>
            ${state.currentGroupAdmin === state.user.id ? `<button class="icon-btn btn-danger btn-delete-channel" data-channel-id="${c.id}" title="Eliminar canal" style="width:28px;height:28px;font-size:14px;margin-right:8px;">🗑️</button>` : ''}
        </div>
    `).join('');

    list.querySelectorAll('.chat-list-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('.btn-delete-channel')) return;
            openChannelChat(item.dataset.channelId, item.dataset.channelName);
        });
    });

    list.querySelectorAll('.btn-delete-channel').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('¿Seguro que quieres eliminar este canal?')) return;
            try {
                await api(`/channels/${btn.dataset.channelId}`, { method: 'DELETE' });
                toast('Canal eliminado', 'success');
                openGroup(state.currentGroupId, state.currentGroupName);
            } catch (err) {
                toast(err.message, 'error');
            }
        });
    });
}

$('#btn-delete-group').addEventListener('click', async () => {
    if (!confirm('¿Seguro que quieres ELIMINAR todo el grupo? Esta acción no se puede deshacer.')) return;
    try {
        await api(`/groups/${state.currentGroupId}`, { method: 'DELETE' });
        toast('Grupo eliminado', 'success');
        $('#channel-panel').classList.add('hidden');
        state.currentGroupId = null;
        stopPolling();
        hideChat();
        await loadGroups();
    } catch (err) {
        toast(err.message, 'error');
    }
});

$('#btn-back-groups').addEventListener('click', () => {
    $('#channel-panel').classList.add('hidden');
    state.currentGroupId = null;
    stopPolling();
    hideChat();
});

// ── Create Channel ──

$('#btn-new-channel').addEventListener('click', () => {
    $('#modal-create-channel').classList.remove('hidden');
});

$('#form-create-channel').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        await api(`/groups/${state.currentGroupId}/channels`, {
            method: 'POST',
            body: {
                name: $('#channel-name').value,
                description: $('#channel-desc').value || null,
            },
        });
        $('#modal-create-channel').classList.add('hidden');
        $('#channel-name').value = '';
        $('#channel-desc').value = '';
        toast('Canal creado', 'success');
        await openGroup(state.currentGroupId, state.currentGroupName);
    } catch (err) {
        toast(err.message, 'error');
    }
});

// ── Add Member ──

$('#form-add-member').addEventListener('submit', (e) => e.preventDefault());

$('#btn-add-member').addEventListener('click', () => {
    $('#modal-add-member').classList.remove('hidden');
    $('#member-search').value = '';
    $('#member-search-results').innerHTML = '';
});

let searchTimeout;
$('#member-search').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const q = e.target.value.trim();
    if (q.length < 1) { $('#member-search-results').innerHTML = ''; return; }
    searchTimeout = setTimeout(() => searchUsersForMember(q), 300);
});

async function searchUsersForMember(query) {
    try {
        const data = await api(`/users/search?q=${encodeURIComponent(query)}`);
        const results = $('#member-search-results');
        results.innerHTML = data.users.filter(u => u.id !== state.user.id).map(u => `
            <div class="search-result-item" data-user-id="${u.id}">
                <div class="avatar small">${u.display_name.charAt(0).toUpperCase()}</div>
                <span class="item-name">${esc(u.display_name)} <small style="color:var(--text-muted)">@${esc(u.username)}</small></span>
                <button type="button" class="btn-add-member-to-group" data-user-id="${u.id}">Agregar</button>
            </div>
        `).join('') || '<div style="padding:12px;color:var(--text-muted);font-size:13px;">Sin resultados</div>';

        results.querySelectorAll('.btn-add-member-to-group').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    await api(`/groups/${state.currentGroupId}/members`, {
                        method: 'POST',
                        body: { user_id: btn.dataset.userId },
                    });
                    toast('Miembro agregado', 'success');
                    btn.textContent = '✓';
                    btn.disabled = true;
                } catch (err) {
                    toast(err.message, 'error');
                }
            });
        });
    } catch (err) {
        toast(err.message, 'error');
    }
}

// ── View Members ──

$('#btn-view-members').addEventListener('click', async () => {
    try {
        const data = await api(`/groups/${state.currentGroupId}/members`);
        const list = $('#members-list');

        // Fetch user details for each member
        const memberDetails = await Promise.all(
            data.members.map(async (m) => {
                try {
                    const user = await api(`/users/${m.user_id}`);
                    return { ...m, display_name: user.display_name, username: user.username };
                } catch {
                    return { ...m, display_name: 'Usuario', username: '?' };
                }
            })
        );

        list.innerHTML = memberDetails.map(m => `
            <div class="member-item">
                <div class="avatar small">${m.display_name.charAt(0).toUpperCase()}</div>
                <span class="item-name">${esc(m.display_name)} <small style="color:var(--text-muted)">@${esc(m.username)}</small></span>
                <span class="member-role ${m.role}">${m.role}</span>
                ${state.currentGroupAdmin === state.user.id && m.user_id !== state.user.id 
                    ? `<button class="icon-btn btn-danger btn-remove-member" data-user-id="${m.user_id}" title="Expulsar miembro" style="width:28px;height:28px;font-size:12px;margin-left:auto;">❌</button>` 
                    : ''}
            </div>
        `).join('');

        list.querySelectorAll('.btn-remove-member').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (!confirm('¿Seguro que quieres expulsar a este miembro?')) return;
                try {
                    await api(`/groups/${state.currentGroupId}/members/${btn.dataset.userId}`, { method: 'DELETE' });
                    toast('Miembro expulsado', 'success');
                    btn.closest('.member-item').remove();
                } catch (err) {
                    toast(err.message, 'error');
                }
            });
        });

        $('#modal-members').classList.remove('hidden');
    } catch (err) {
        toast(err.message, 'error');
    }
});

// ═══════════ CHAT ═══════════

function openChannelChat(channelId, channelName) {
    state.currentChatType = 'channel';
    state.currentChatId = channelId;
    state.currentChatName = channelName;
    state.dmTargetUserId = null;

    $('#channel-panel').classList.add('hidden'); // Fix: hide the channel list so chat is visible
    $('#chat-name').textContent = `# ${channelName}`;
    $('#chat-status').textContent = state.currentGroupName;
    showChat();
    loadMessages();
    startPolling();
}

function openDMChat(userId, displayName) {
    state.currentChatType = 'dm';
    state.currentChatId = userId;
    state.currentChatName = displayName;
    state.dmTargetUserId = userId;

    $('#chat-name').textContent = displayName;
    showChat();
    loadPresence(userId);
    loadMessages();
    startPolling();
}

function showChat() {
    $('#chat-welcome').classList.add('hidden');
    $('#messages-container').classList.remove('hidden');
    $('#message-input-bar').classList.remove('hidden');
    $('#btn-back-channels').style.display = state.currentChatType === 'dm' ? 'none' : '';
}

function hideChat() {
    $('#chat-welcome').classList.remove('hidden');
    $('#messages-container').classList.add('hidden');
    $('#message-input-bar').classList.add('hidden');
    $('#btn-back-channels').style.display = 'none'; // Hide the back button on the welcome screen
    $('#chat-name').textContent = 'Selecciona un chat'; // Reset header
    $('#chat-status').textContent = '';
    state.currentChatType = null;
    state.currentChatId = null;
}

$('#btn-back-channels').addEventListener('click', () => {
    stopPolling();
    hideChat();
});

// ── Load Messages ──

// Cache for fetched attachments so we don't re-fetch on every poll
const attachmentCache = {};

async function loadMessages() {
    try {
        let data;
        if (state.currentChatType === 'channel') {
            data = await api(`/channels/${state.currentChatId}/messages?limit=100`);
        } else {
            data = await api(`/users/${state.currentChatId}/messages?limit=100`);
        }
        const newMessages = data.messages.reverse(); // API returns desc, we want asc

        // Check if messages actually changed (compare IDs + statuses)
        const oldFingerprint = state.messages.map(m => m.id + (m.status || '')).join(',');
        const newFingerprint = newMessages.map(m => m.id + (m.status || '')).join(',');
        const hasChanged = oldFingerprint !== newFingerprint;

        if (!hasChanged) return; // No changes, skip re-render to avoid flicker / audio interruption

        state.messages = newMessages;

        // Mark incoming DM messages as read (fire-and-forget)
        if (state.currentChatType === 'dm') {
            for (const m of state.messages) {
                if (m.sender_id !== state.user.id) {
                    api(`/messages/${m.id}/read`, { method: 'POST' }).catch(() => {});
                }
            }
        }

        // Fetch attachments only for messages we haven't cached yet
        const msgIdsNeedingAttachments = state.messages
            .filter(m => (m.content.startsWith('📎 Archivo:') || m.content === '🎤 Audio') && !attachmentCache[m.id])
            .map(m => m.id);

        if (msgIdsNeedingAttachments.length > 0) {
            const attachmentPromises = msgIdsNeedingAttachments.map(async (msgId) => {
                try {
                    const atts = await api(`/messages/${msgId}/attachments`);
                    attachmentCache[msgId] = atts;
                    return { msgId, atts };
                } catch {
                    attachmentCache[msgId] = [];
                    return { msgId, atts: [] };
                }
            });
            await Promise.all(attachmentPromises);
        }

        // Attach cached attachments to messages
        for (const m of state.messages) {
            if (attachmentCache[m.id]) {
                m.attachments = attachmentCache[m.id];
            }
        }

        renderMessages();
    } catch (err) {
        toast(err.message, 'error');
    }
}

// Cache for user display names
const userNameCache = {};

async function getUserName(userId) {
    if (userId === state.user.id) return state.user.display_name;
    if (userNameCache[userId]) return userNameCache[userId];
    try {
        const u = await api(`/users/${userId}`);
        userNameCache[userId] = u.display_name;
        return u.display_name;
    } catch {
        return 'Usuario';
    }
}

function getStatusIcon(status) {
    if (!status) return '';
    switch (status) {
        case 'sent':
            return '<span class="msg-status sent">✓</span>';
        case 'delivered':
            return '<span class="msg-status delivered">✓✓</span>';
        case 'read':
            return '<span class="msg-status read">✓✓</span>';
        default:
            return '';
    }
}

function getFileIcon(contentType, filename) {
    if (contentType.startsWith('image/')) return '🖼️';
    if (contentType.startsWith('audio/')) return '🎵';
    if (contentType.startsWith('video/')) return '🎬';
    if (contentType === 'application/pdf') return '📄';
    const ext = (filename || '').split('.').pop().toLowerCase();
    if (['doc', 'docx'].includes(ext)) return '📝';
    if (['xls', 'xlsx'].includes(ext)) return '📊';
    if (['ppt', 'pptx'].includes(ext)) return '📽️';
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return '🗜️';
    if (['txt', 'csv', 'log'].includes(ext)) return '📃';
    return '📎';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function renderAttachments(attachments) {
    if (!attachments || attachments.length === 0) return '';
    return attachments.map(att => {
        const ct = att.content_type || '';
        const downloadUrl = `${API}/attachments/${att.id}?token=${encodeURIComponent(state.token)}`;
        const name = esc(att.original_filename);
        const size = formatFileSize(att.file_size);

        if (ct.startsWith('image/')) {
            return `
                <div class="attachment-preview attachment-image">
                    <a href="${downloadUrl}" target="_blank" rel="noopener">
                        <img src="${downloadUrl}" alt="${name}" loading="lazy">
                    </a>
                </div>`;
        }
        if (ct.startsWith('audio/')) {
            const audioId = `audio-${att.id}`;
            return `
                <div class="attachment-preview attachment-audio-custom">
                    <audio id="${audioId}" preload="metadata" src="${downloadUrl}"></audio>
                    <button class="audio-play-toggle" data-audio-id="${audioId}" onclick="toggleAudioPlay('${audioId}')">
                        <svg class="play-icon" viewBox="0 0 24 24"><polygon points="6,3 20,12 6,21"/></svg>
                        <svg class="pause-icon hidden" viewBox="0 0 24 24"><rect x="5" y="3" width="4" height="18"/><rect x="15" y="3" width="4" height="18"/></svg>
                    </button>
                    <div class="audio-progress-area" data-audio-id="${audioId}" onclick="seekAudio(event, '${audioId}')">
                        <div class="audio-waveform">
                            <div class="audio-progress-bar" id="bar-${audioId}"></div>
                        </div>
                    </div>
                    <span class="audio-duration" id="dur-${audioId}">0:00</span>
                </div>`;
        }
        if (ct.startsWith('video/')) {
            return `
                <div class="attachment-preview attachment-video">
                    <video controls preload="metadata" src="${downloadUrl}"></video>
                    <div class="attachment-file-name">${name}</div>
                </div>`;
        }
        // PDF, docs, and generic files – open in new tab in native format
        const icon = getFileIcon(ct, att.original_filename);
        return `
            <div class="attachment-preview attachment-file">
                <a href="${downloadUrl}" target="_blank" rel="noopener" class="attachment-file-link">
                    <span class="attachment-file-icon">${icon}</span>
                    <div class="attachment-file-info">
                        <span class="attachment-file-name">${name}</span>
                        <span class="attachment-file-size">${size}</span>
                    </div>
                    <span class="attachment-download-icon">⬇</span>
                </a>
            </div>`;
    }).join('');
}

async function renderMessages() {
    const list = $('#messages-list');
    // Resolve all sender names
    const senderIds = [...new Set(state.messages.map(m => m.sender_id))];
    await Promise.all(senderIds.map(id => getUserName(id)));

    list.innerHTML = state.messages.map(m => {
        const isOwn = m.sender_id === state.user.id;
        const senderName = userNameCache[m.sender_id] || state.user.display_name;
        const time = new Date(m.created_at).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
        const statusHtml = isOwn && state.currentChatType === 'dm' ? getStatusIcon(m.status) : '';
        const hasAttachments = m.attachments && m.attachments.length > 0;
        const attachmentsHtml = renderAttachments(m.attachments);

        // Hide the placeholder text if message has real attachments
        const isFilePlaceholder = hasAttachments && m.content.startsWith('📎 Archivo:');
        const isAudioPlaceholder = hasAttachments && m.content === '🎤 Audio';
        const hideContent = isFilePlaceholder || isAudioPlaceholder;

        return `
            <div class="message-bubble ${isOwn ? 'own' : 'other'}">
                ${state.currentChatType === 'channel' ? `<div class="message-sender">${esc(senderName)}</div>` : ''}
                ${hideContent ? '' : `<div class="message-text">${esc(m.content)}</div>`}
                ${attachmentsHtml}
                <div class="message-time">${time} ${statusHtml}</div>
            </div>
        `;
    }).join('');

    // Scroll to bottom
    const container = $('#messages-container');
    container.scrollTop = container.scrollHeight;

    // Wire up custom audio player events
    wireAudioPlayers();
}

// ── Send Message ──

$('#btn-send').addEventListener('click', sendMessage);
$('#message-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const input = $('#message-input');
    const content = input.value.trim();
    if (!content || !state.currentChatId) return;

    input.value = '';
    try {
        if (state.currentChatType === 'channel') {
            await api(`/channels/${state.currentChatId}/messages`, {
                method: 'POST',
                body: { content },
            });
        } else {
            await api(`/users/${state.currentChatId}/messages`, {
                method: 'POST',
                body: { content },
            });
        }
        await loadMessages();
    } catch (err) {
        toast(err.message, 'error');
        input.value = content;
    }
}

// ── File Upload ──

$('#file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // First send a message about the file
    try {
        let msg;
        if (state.currentChatType === 'channel') {
            msg = await api(`/channels/${state.currentChatId}/messages`, {
                method: 'POST',
                body: { content: `📎 Archivo: ${file.name}` },
            });
        } else {
            msg = await api(`/users/${state.currentChatId}/messages`, {
                method: 'POST',
                body: { content: `📎 Archivo: ${file.name}` },
            });
        }

        // Upload the file as attachment
        const formData = new FormData();
        formData.append('file', file);
        await api(`/messages/${msg.id}/attachments`, {
            method: 'POST',
            body: formData,
        });

        toast('Archivo enviado', 'success');
        await loadMessages();
    } catch (err) {
        toast(err.message, 'error');
    }
    e.target.value = '';
});

// ═══════════ AUDIO RECORDING ═══════════

const micBtn = $('#btn-mic');
const recordingIndicator = $('#recording-indicator');
const cancelRecordBtn = $('#btn-cancel-record');

micBtn.addEventListener('mousedown', startRecording);
micBtn.addEventListener('mouseup', stopRecording);
micBtn.addEventListener('mouseleave', stopRecording);
// Touch support
micBtn.addEventListener('touchstart', (e) => { e.preventDefault(); startRecording(); });
micBtn.addEventListener('touchend', (e) => { e.preventDefault(); stopRecording(); });

cancelRecordBtn.addEventListener('click', cancelRecording);

async function startRecording() {
    if (state.isRecording || !state.currentChatId) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];

        state.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) state.audioChunks.push(e.data);
        };

        state.mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());
            if (state.audioChunks.length === 0) return;

            const blob = new Blob(state.audioChunks, { type: 'audio/webm' });
            await sendAudio(blob);
        };

        state.mediaRecorder.start();
        state.isRecording = true;
        micBtn.classList.add('recording');
        recordingIndicator.classList.remove('hidden');
    } catch (err) {
        toast('No se pudo acceder al micrófono', 'error');
    }
}

function stopRecording() {
    if (!state.isRecording || !state.mediaRecorder) return;
    state.mediaRecorder.stop();
    state.isRecording = false;
    micBtn.classList.remove('recording');
    recordingIndicator.classList.add('hidden');
}

function cancelRecording() {
    if (!state.isRecording || !state.mediaRecorder) return;
    state.audioChunks = []; // Clear so nothing is sent
    state.mediaRecorder.stop();
    state.isRecording = false;
    micBtn.classList.remove('recording');
    recordingIndicator.classList.add('hidden');
    toast('Grabación cancelada', '');
}

async function sendAudio(blob) {
    const formData = new FormData();
    formData.append('file', blob, 'audio.webm');

    try {
        let endpoint;
        if (state.currentChatType === 'channel') {
            endpoint = `/channels/${state.currentChatId}/messages/audio`;
        } else {
            endpoint = `/users/${state.currentChatId}/messages/audio`;
        }

        await fetch(`${API}${endpoint}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` },
            body: formData,
        });

        toast('Audio enviado', 'success');
        await loadMessages();
    } catch (err) {
        toast('Error enviando audio', 'error');
    }
}

// ── Polling ──

function startPolling() {
    stopPolling();
    state.pollInterval = setInterval(loadMessages, 5000);
}

function stopPolling() {
    if (state.pollInterval) {
        clearInterval(state.pollInterval);
        state.pollInterval = null;
    }
}

// ═══════════ DIRECT MESSAGES ═══════════

// Tab switching
$$('.sidebar-tabs .tab').forEach(tab => {
    tab.addEventListener('click', () => {
        $$('.sidebar-tabs .tab').forEach(t => t.classList.remove('active'));
        $$('.tab-content').forEach(tc => tc.classList.remove('active'));
        tab.classList.add('active');
        $(`#tab-${tab.dataset.tab}`).classList.add('active');

        // Close channel panel when switching tabs
        if (tab.dataset.tab === 'dms') {
            $('#channel-panel').classList.add('hidden');
            stopPolling();
            hideChat();
            loadConversations(); // Refresh conversations when switching to DMs
        }
    });
});

// DM search
$('#btn-dm-search').addEventListener('click', () => searchDMUsers());
$('#dm-search-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        searchDMUsers();
    }
});

async function searchDMUsers() {
    const input = $('#dm-search-input');
    if (!input) return;
    const q = input.value.trim();
    if (!q) return;
    try {
        const data = await api(`/users/search?q=${encodeURIComponent(q)}`);
        const results = $('#dm-search-results');
        results.innerHTML = data.users.filter(u => u.id !== state.user.id).map(u => `
            <div class="chat-list-item" data-user-id="${u.id}" data-display-name="${esc(u.display_name)}">
                <div class="item-icon user">${u.display_name.charAt(0).toUpperCase()}</div>
                <div class="item-info">
                    <div class="item-name">${esc(u.display_name)}</div>
                    <div class="item-desc">@${esc(u.username)}</div>
                </div>
            </div>
        `).join('') || '<div style="padding:12px;text-align:center;color:var(--text-muted);font-size:13px;">Sin resultados</div>';

        results.querySelectorAll('.chat-list-item').forEach(item => {
            item.addEventListener('click', () => {
                openDMChat(item.dataset.userId, item.dataset.displayName);
            });
        });
    } catch (err) {
        toast(err.message, 'error');
    }
}

// ═══════════ CONVERSATIONS (Chat History in Sidebar) ═══════════

async function loadConversations() {
    try {
        const data = await api('/conversations');
        renderConversations(data.conversations);
    } catch (err) {
        // Silently fail if endpoint not ready
        console.warn('Could not load conversations:', err.message);
    }
}

function renderConversations(conversations) {
    const container = $('#dm-conversations');
    if (!container) return;

    if (!conversations || conversations.length === 0) {
        container.innerHTML = '<div style="padding:12px;text-align:center;color:var(--text-muted);font-size:13px;">No hay conversaciones recientes</div>';
        return;
    }

    container.innerHTML = conversations.map(c => {
        const time = new Date(c.last_message_time).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
        const lastMsg = c.last_message.length > 30 ? c.last_message.substring(0, 30) + '...' : c.last_message;
        const unreadBadge = c.unread_count > 0 ? `<span class="unread-badge">${c.unread_count}</span>` : '';
        const isSender = c.sender_id === state.user?.id;
        const prefix = isSender ? 'Tú: ' : '';

        return `
            <div class="chat-list-item conversation-item" data-user-id="${c.other_user_id}" data-display-name="${esc(c.display_name)}">
                <div class="item-icon user">${c.display_name.charAt(0).toUpperCase()}</div>
                <div class="item-info">
                    <div class="item-name-row">
                        <div class="item-name">${esc(c.display_name)}</div>
                        <span class="item-time">${time}</span>
                    </div>
                    <div class="item-preview-row">
                        <div class="item-desc">${prefix}${esc(lastMsg)}</div>
                        ${unreadBadge}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', () => {
            openDMChat(item.dataset.userId, item.dataset.displayName);
        });
    });
}

// ── Conversation Polling (Real-time sidebar updates) ──

function startConversationPolling() {
    stopConversationPolling();
    state.conversationPollInterval = setInterval(loadConversations, 5000);
}

function stopConversationPolling() {
    if (state.conversationPollInterval) {
        clearInterval(state.conversationPollInterval);
        state.conversationPollInterval = null;
    }
}

// ═══════════ PRESENCE ═══════════

async function loadPresence(userId) {
    try {
        const data = await api(`/users/${userId}/presence`);
        const statusEl = $('#chat-status');
        if (data.status === 'online') {
            statusEl.innerHTML = '<span class="presence-dot online"></span> En línea';
        } else {
            const lastSeen = new Date(data.last_seen).toLocaleString('es');
            statusEl.innerHTML = `<span class="presence-dot offline"></span> Últ. vez: ${lastSeen}`;
        }
    } catch {
        $('#chat-status').textContent = '';
    }
}

function startHeartbeat() {
    // Send immediately
    api('/presence/heartbeat', { method: 'POST' }).catch(() => { });
    // Then every 60 seconds
    state.heartbeatInterval = setInterval(() => {
        api('/presence/heartbeat', { method: 'POST' }).catch(() => { });
    }, 60000);
}

// ═══════════ SWIPE NAVIGATION ═══════════

(function initSwipe() {
    let touchStartX = 0;
    let touchStartY = 0;
    let isSwiping = false;
    const SWIPE_THRESHOLD = 80;

    const sidebar = $('#sidebar');
    const centerPanel = $('#center-panel');
    const channelPanel = $('#channel-panel');

    if (!centerPanel) return;

    centerPanel.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        isSwiping = true;
    }, { passive: true });

    centerPanel.addEventListener('touchmove', (e) => {
        if (!isSwiping) return;
        const dx = e.touches[0].clientX - touchStartX;
        const dy = e.touches[0].clientY - touchStartY;
        // Only horizontal swipes
        if (Math.abs(dy) > Math.abs(dx)) {
            isSwiping = false;
        }
    }, { passive: true });

    centerPanel.addEventListener('touchend', (e) => {
        if (!isSwiping) return;
        const dx = e.changedTouches[0].clientX - touchStartX;

        if (dx > SWIPE_THRESHOLD) {
            // Swipe right → go back
            if (state.currentChatType) {
                // In chat → go back to channels/sidebar
                stopPolling();
                hideChat();
            } else if (channelPanel && !channelPanel.classList.contains('hidden')) {
                // In channel list → go back to sidebar
                channelPanel.classList.add('hidden');
                state.currentGroupId = null;
            }
        } else if (dx < -SWIPE_THRESHOLD) {
            // Swipe left → go forward (no-op for now, user taps to go forward)
        }

        isSwiping = false;
    });

    // Sidebar swipe
    if (sidebar) {
        sidebar.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            isSwiping = true;
        }, { passive: true });

        sidebar.addEventListener('touchend', (e) => {
            if (!isSwiping) return;
            const dx = e.changedTouches[0].clientX - touchStartX;
            // Swipe left on sidebar → no action needed (tap to navigate)
            isSwiping = false;
        });
    }
})();

// ═══════════ MODALS ═══════════

// Close buttons
$$('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        const modalId = btn.dataset.close;
        $(`#${modalId}`).classList.add('hidden');
    });
});

// Click outside to close
$$('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });
});

// ═══════════ UTILITY ═══════════

function esc(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ═══════════ CUSTOM AUDIO PLAYER ═══════════

function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function toggleAudioPlay(audioId) {
    const audio = document.getElementById(audioId);
    if (!audio) return;

    const container = audio.closest('.attachment-audio-custom');
    const playIcon = container.querySelector('.play-icon');
    const pauseIcon = container.querySelector('.pause-icon');

    if (audio.paused) {
        // Pause all other audios first
        document.querySelectorAll('.attachment-audio-custom audio').forEach(a => {
            if (a.id !== audioId && !a.paused) {
                a.pause();
                const c = a.closest('.attachment-audio-custom');
                if (c) {
                    c.querySelector('.play-icon').classList.remove('hidden');
                    c.querySelector('.pause-icon').classList.add('hidden');
                }
            }
        });

        audio.play();
        playIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
    } else {
        audio.pause();
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    }
}

function seekAudio(event, audioId) {
    const audio = document.getElementById(audioId);
    if (!audio || !audio.duration) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const ratio = x / rect.width;
    audio.currentTime = ratio * audio.duration;
}

// Make functions global for onclick handlers
window.toggleAudioPlay = toggleAudioPlay;
window.seekAudio = seekAudio;

// Wire up audio events after rendering
function wireAudioPlayers() {
    document.querySelectorAll('.attachment-audio-custom audio').forEach(audio => {
        if (audio.dataset.wired) return; // Already wired
        audio.dataset.wired = '1';

        const audioId = audio.id;
        const durEl = document.getElementById(`dur-${audioId}`);
        const barEl = document.getElementById(`bar-${audioId}`);
        const container = audio.closest('.attachment-audio-custom');

        audio.addEventListener('loadedmetadata', () => {
            if (durEl) durEl.textContent = formatDuration(audio.duration);
        });

        audio.addEventListener('timeupdate', () => {
            if (barEl && audio.duration) {
                const pct = (audio.currentTime / audio.duration) * 100;
                barEl.style.width = pct + '%';
            }
            if (durEl) {
                const remaining = audio.duration - audio.currentTime;
                durEl.textContent = formatDuration(remaining > 0 ? remaining : audio.duration);
            }
        });

        audio.addEventListener('ended', () => {
            if (barEl) barEl.style.width = '0%';
            if (durEl) durEl.textContent = formatDuration(audio.duration);
            if (container) {
                container.querySelector('.play-icon').classList.remove('hidden');
                container.querySelector('.pause-icon').classList.add('hidden');
            }
        });
    });
}

// ═══════════ INIT ═══════════

document.addEventListener('DOMContentLoaded', async () => {
    if (state.token) {
        await enterApp();
    }
});
