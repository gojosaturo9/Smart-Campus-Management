(function () {
  const data = window.mentorshipData || {};
  const workspace = document.querySelector("[data-mentor-workspace]");
  if (!workspace) return;

  const messagesEl = workspace.querySelector("[data-mentor-messages]");
  const chatTitle = workspace.querySelector("[data-chat-title]");
  const compose = workspace.querySelector("[data-mentor-compose]");
  const input = compose ? compose.querySelector("input[name='message']") : null;
  const connectionInput = compose ? compose.querySelector("[data-connection-input]") : null;
  let sendStatus = null;
  const messages = data.messages || {};
  let activeThread = data.active_connection_id || "";
  let pollingTimer = null;
  let isPolling = false;

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
        return [
          `<article class="mentor-message${own}">`,
          `<p>${escapeHtml(message.message)}</p>`,
          `<small>${sender} | ${escapeHtml(formatDateTime(message.created_at))}</small>`,
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

  workspace.querySelectorAll("[data-thread-id]").forEach((button) => {
    button.addEventListener("click", () => {
      workspace.querySelectorAll("[data-thread-id]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      activeThread = button.dataset.threadId || "";
      if (connectionInput) connectionInput.value = activeThread;
      if (chatTitle) chatTitle.textContent = button.dataset.personName || "Mentorship Chat";
      if (input) input.disabled = !activeThread;
      const submitButton = compose ? compose.querySelector("button[type='submit']") : null;
      if (submitButton) submitButton.disabled = !activeThread;
      renderMessages();
      markRead();
      restartPolling();
    });
  });

  workspace.querySelectorAll("[data-mentor-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.mentorTab;
      workspace.querySelectorAll("[data-mentor-tab]").forEach((item) => item.classList.remove("is-active"));
      workspace.querySelectorAll("[data-mentor-panel]").forEach((panel) => {
        panel.classList.toggle("is-hidden", panel.dataset.mentorPanel !== tab);
      });
      button.classList.add("is-active");
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

  if (compose && input) {
    compose.addEventListener("submit", async (event) => {
      if (!activeThread) return;
      event.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      const submitButton = compose.querySelector("button[type='submit']");
      if (submitButton) submitButton.disabled = true;
      setSendStatus("Sending...");
      try {
        const response = await fetch("/alumni/connect/messages.json", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            connection_id: activeThread,
            message: text
          })
        });
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
          showInlineError(payload.message || "Could not send message.");
          return;
        }
        input.value = "";
        appendMessage(payload.row);
        setSendStatus("Sent");
        window.setTimeout(() => setSendStatus(""), 1600);
      } catch (error) {
        showInlineError("Could not reach the server.");
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
      const payload = await response.json();
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

  renderMessages();
  markRead();
  restartPolling();
})();
