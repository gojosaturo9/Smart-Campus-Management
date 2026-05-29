(function () {
  const data = window.mentorshipData || {};
  const workspace = document.querySelector("[data-mentor-workspace]");
  if (!workspace) return;

  const messagesEl = workspace.querySelector("[data-mentor-messages]");
  const chatTitle = workspace.querySelector("[data-chat-title]");
  const compose = workspace.querySelector("[data-mentor-compose]");
  const input = compose ? compose.querySelector("input[name='message']") : null;
  const connectionInput = compose ? compose.querySelector("[data-connection-input]") : null;
  const attachmentInput = compose ? compose.querySelector("[data-attachment-input]") : null;
  const attachmentName = compose ? compose.querySelector("[data-attachment-name]") : null;
  const clearChatButton = workspace.querySelector("[data-clear-chat]");
  let sendStatus = null;
  const messages = data.messages || {};
  let activeThread = data.active_connection_id || "";
  let pollingTimer = null;
  let isPolling = false;
  let openMenuId = "";

  function selectThread(button) {
    if (!button) return;
    workspace.querySelectorAll("[data-thread-id]").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    activeThread = button.dataset.threadId || "";
    if (connectionInput) connectionInput.value = activeThread;
    if (chatTitle) chatTitle.textContent = button.dataset.personName || "Mentorship Chat";
    if (input) input.disabled = !activeThread;
    if (attachmentInput) attachmentInput.disabled = !activeThread;
    const submitButton = compose ? compose.querySelector("button[type='submit']") : null;
    if (submitButton) submitButton.disabled = !activeThread;
    if (clearChatButton) clearChatButton.disabled = !activeThread;
    renderMessages();
    markRead();
    restartPolling();
  }

  function renderMessages() {
    if (!messagesEl) return;
    const rows = messages[activeThread] || [];
    if (!activeThread) {
      messagesEl.innerHTML = '<p class="muted">Create or accept a mentorship request to start a chat.</p>';
      return;
    }
    if (!rows.length) {
      messagesEl.innerHTML = '<p class="muted">No messages yet. Send the first guidance message.</p>';
      return;
    }
    messagesEl.innerHTML = rows
      .map((message) => {
        const own = message.sender_id === currentUserId() ? " own" : "";
        const sender = own ? "you" : "peer";
        const text = message.message ? `<p>${escapeHtml(message.message)}</p>` : "";
        const attachment = renderAttachment(message);
        const editAction = own ? `<button type="button" data-edit-message-id="${escapeHtml(message.id || "")}">Edit message</button>` : "";
        return [
          `<article class="mentor-message${own}" data-message-id="${escapeHtml(message.id || "")}">`,
          text,
          attachment,
          `<small>${sender} | ${escapeHtml(formatDateTime(message.created_at))}</small>`,
          `<div class="message-menu">`,
          `<button class="message-menu-toggle" type="button" data-message-menu-id="${escapeHtml(message.id || "")}" aria-label="Message options">...</button>`,
          `<div class="message-menu-popover ${openMenuId === message.id ? "is-open" : ""}" data-message-menu="${escapeHtml(message.id || "")}">`,
          editAction,
          `<button type="button" data-delete-message-id="${escapeHtml(message.id || "")}">Delete message</button>`,
          `</div>`,
          `</div>`,
          `</article>`
        ].join("");
      })
      .join("");
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendMessage(row) {
    if (!row || !activeThread) return;
    messages[activeThread] = messages[activeThread] || [];
    if (messages[activeThread].some((message) => message.id === row.id)) return;
    messages[activeThread].push(row);
    renderMessages();
  }

  async function deleteMessage(messageId) {
    if (!messageId || !activeThread) return;
    try {
      const response = await fetch(`/alumni/connect/message-actions/${encodeURIComponent(messageId)}/delete`, {
        method: "POST",
        headers: {
          "Accept": "application/json"
        }
      });
      const payload = await readJson(response);
      if (!response.ok || !payload.ok) {
        showInlineError(payload.message || "Could not delete message.");
        return;
      }
      messages[activeThread] = (messages[activeThread] || []).filter((message) => message.id !== messageId);
      renderMessages();
    } catch (error) {
      showInlineError("Could not reach the server.");
    }
  }

  async function editMessage(messageId) {
    if (!messageId || !activeThread) return;
    const current = (messages[activeThread] || []).find((message) => message.id === messageId);
    if (!current) return;
    const updatedText = window.prompt("Edit message", current.message || "");
    if (updatedText === null) return;
    const clean = updatedText.trim();
    if (!clean) return;
    try {
      const response = await fetch(`/alumni/connect/message-actions/${encodeURIComponent(messageId)}/edit`, {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: clean })
      });
      const payload = await readJson(response);
      if (!response.ok || !payload.ok) {
        showInlineError(payload.message || "Could not edit message.");
        return;
      }
      current.message = clean;
      openMenuId = "";
      renderMessages();
    } catch (error) {
      showInlineError("Could not reach the server.");
    }
  }

  async function clearChat() {
    if (!activeThread) return;
    const confirmed = window.confirm("Delete all messages in this chat?");
    if (!confirmed) return;
    try {
      const response = await fetch(`/alumni/connect/connections/${encodeURIComponent(activeThread)}/messages/delete`, {
        method: "POST",
        headers: {
          "Accept": "application/json"
        }
      });
      const payload = await readJson(response);
      if (!response.ok || !payload.ok) {
        showInlineError(payload.message || "Could not clear chat.");
        return;
      }
      messages[activeThread] = [];
      renderMessages();
    } catch (error) {
      showInlineError("Could not reach the server.");
    }
  }

  function currentUserId() {
    const connection = (data.connections || []).find((item) => item.id === activeThread);
    if (!connection) return "";
    return data.role === "alumni" ? connection.alumni_id : connection.student_id;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatDateTime(value) {
    if (!value) return "";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return String(value);
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true
    }).format(parsed);
  }

  function renderAttachment(message) {
    if (!message.attachment_filename || !message.id) return "";
    const size = formatFileSize(message.attachment_size || 0);
    const url = `/alumni/connect/messages/${encodeURIComponent(message.id)}/attachment`;
    return [
      `<a class="message-attachment" href="${url}" target="_blank" rel="noreferrer">`,
      `<strong>${escapeHtml(message.attachment_filename)}</strong>`,
      `<span>${escapeHtml(size)}</span>`,
      `</a>`
    ].join("");
  }

  function formatFileSize(bytes) {
    const size = Number(bytes || 0);
    if (!size) return "Attachment";
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  workspace.querySelectorAll("[data-thread-id]").forEach((button) => {
    button.addEventListener("click", () => {
      selectThread(button);
    });
  });

  if (messagesEl) {
    messagesEl.addEventListener("click", (event) => {
      const menuButton = event.target.closest("[data-message-menu-id]");
      if (menuButton) {
        const menuId = menuButton.dataset.messageMenuId || "";
        openMenuId = openMenuId === menuId ? "" : menuId;
        renderMessages();
        return;
      }
      const editButton = event.target.closest("[data-edit-message-id]");
      if (editButton) {
        editMessage(editButton.dataset.editMessageId || "");
        return;
      }
      const button = event.target.closest("[data-delete-message-id]");
      if (!button) return;
      deleteMessage(button.dataset.deleteMessageId || "");
    });
  }

  document.addEventListener("click", (event) => {
    if (!openMenuId || event.target.closest(".message-menu")) return;
    openMenuId = "";
    renderMessages();
  });

  if (clearChatButton) {
    clearChatButton.addEventListener("click", clearChat);
  }

  workspace.querySelectorAll("[data-mentor-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.mentorTab;
      workspace.querySelectorAll("[data-mentor-tab]").forEach((item) => item.classList.remove("is-active"));
      workspace.querySelectorAll("[data-mentor-panel]").forEach((panel) => {
        panel.classList.toggle("is-hidden", panel.dataset.mentorPanel !== tab);
      });
      button.classList.add("is-active");
      if (tab === "connections") {
        const activeButton = workspace.querySelector("[data-mentor-panel='connections'] [data-thread-id].is-active");
        const firstButton = workspace.querySelector("[data-mentor-panel='connections'] [data-thread-id]");
        selectThread(activeButton || firstButton);
      }
    });
  });

  workspace.querySelectorAll("[data-request-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.requestTab;
      workspace.querySelectorAll("[data-request-tab]").forEach((item) => item.classList.remove("is-active"));
      workspace.querySelectorAll("[data-request-panel]").forEach((panel) => {
        panel.classList.toggle("is-hidden", panel.dataset.requestPanel !== tab);
      });
      button.classList.add("is-active");
    });
  });

  workspace.querySelectorAll("[data-quick-reply]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!input || input.disabled) return;
      input.value = button.dataset.quickReply || "";
      input.focus();
    });
  });

  if (attachmentInput && attachmentName) {
    attachmentInput.addEventListener("change", () => {
      attachmentName.textContent = attachmentInput.files && attachmentInput.files.length ? attachmentInput.files[0].name : "";
    });
  }

  if (compose && input) {
    compose.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!activeThread || isPolling) return;
      
      const text = input.value.trim();
      const hasAttachment = attachmentInput && attachmentInput.files && attachmentInput.files.length > 0;
      if (!text && !hasAttachment) return;
      
      const submitButton = compose.querySelector("button[type='submit']");
      if (submitButton) submitButton.disabled = true;
      
      setSendStatus("Sending...");
      
      try {
        const formData = new FormData();
        formData.append("connection_id", activeThread);
        formData.append("message", text);
        if (hasAttachment) {
          formData.append("attachment", attachmentInput.files[0]);
        }

        // We use the JSON endpoint for AJAX sending
        const response = await fetch("/alumni/connect/messages.json", {
          method: "POST",
          body: formData
        });

        const payload = await readJson(response);
        
        if (!response.ok || !payload.ok) {
          showInlineError(payload.message || "Could not send message.");
          if (submitButton) submitButton.disabled = false;
          setSendStatus("");
          return;
        }

        // Clear input and attachment
        input.value = "";
        if (attachmentInput) attachmentInput.value = "";
        if (attachmentName) attachmentName.textContent = "";
        
        // Add message to UI
        if (payload.row) {
          appendMessage(payload.row);
        }
        
        setSendStatus("Sent");
        window.setTimeout(() => setSendStatus(""), 1600);
      } catch (error) {
        showInlineError("Could not reach the server.");
        console.error("Chat Error:", error);
      } finally {
        if (submitButton) submitButton.disabled = !activeThread;
      }
    });
  }

  async function pollMessages() {
    if (!activeThread || isPolling || document.hidden) return;
    isPolling = true;
    const rows = messages[activeThread] || [];
    const last = rows.length ? rows[rows.length - 1].id : "";
    try {
      const url = `/alumni/connect/messages/${encodeURIComponent(activeThread)}${last ? `?after_id=${encodeURIComponent(last)}` : ""}`;
      const response = await fetch(url, {
        headers: {
          "Accept": "application/json"
        }
      });
      if (!response.ok) return;
      const payload = await readJson(response);
      if (!payload.ok) return;
      (payload.messages || []).forEach(appendMessage);
      if ((payload.messages || []).length) markRead();
    } finally {
      isPolling = false;
    }
  }

  async function markRead() {
    if (!activeThread) return;
    try {
      await fetch(`/alumni/connect/messages/${encodeURIComponent(activeThread)}/read`, {
        method: "POST",
        headers: {
          "Accept": "application/json"
        }
      });
    } catch (error) {
      // Read receipts should never interrupt chat usage.
    }
  }

  function restartPolling() {
    if (pollingTimer) window.clearInterval(pollingTimer);
    if (!activeThread) return;
    pollingTimer = window.setInterval(pollMessages, 3500);
  }

  function showInlineError(message) {
    if (!messagesEl) return;
    const error = document.createElement("div");
    error.className = "alert mentor-inline-alert";
    error.textContent = message;
    messagesEl.appendChild(error);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setSendStatus(message) {
    if (!compose) return;
    if (!sendStatus) {
      sendStatus = document.createElement("small");
      sendStatus.className = "mentor-send-status";
      compose.appendChild(sendStatus);
    }
    sendStatus.textContent = message;
  }

  async function readJson(response) {
    const text = await response.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (error) {
      return {
        ok: false,
        message: response.redirected ? "Please login again, then retry." : `Server returned ${response.status}. Refresh and try again.`
      };
    }
  }

  renderMessages();
  markRead();
  restartPolling();
})();
