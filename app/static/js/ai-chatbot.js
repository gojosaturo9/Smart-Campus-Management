(function () {
  const root = document.querySelector("[data-ai-chatbot]");
  if (!root) return;

  const toggle = root.querySelector("[data-ai-chatbot-toggle]");
  const panel = root.querySelector("[data-ai-chatbot-panel]");
  const close = root.querySelector("[data-ai-chatbot-close]");
  const form = root.querySelector("[data-ai-chatbot-form]");
  const input = form ? form.querySelector("input[name='message']") : null;
  const messages = root.querySelector("[data-ai-chatbot-messages]");
  const micButton = root.querySelector("[data-ai-chatbot-mic]");
  const speakButton = root.querySelector("[data-ai-chatbot-speak]");
  const clearButton = root.querySelector("[data-ai-chatbot-clear]");
  const quickPrompts = root.querySelector("[data-ai-chatbot-prompts]");
  const status = root.querySelector("[data-ai-chatbot-status]");
  const bootstrap = window.chatbotBootstrap || {};
  let voiceEnabled = true;
  let recognition = null;
  let listening = false;

  function setOpen(open) {
    if (!panel) return;
    panel.hidden = !open;
    root.classList.toggle("is-open", open);
    if (open && input) input.focus();
  }

  function addMessage(text, type, actions) {
    if (!messages) return;
    const article = document.createElement("article");
    article.className = `ai-chatbot-message ${type}`;
    article.textContent = text;
    messages.appendChild(article);
    if (actions && actions.length) {
      const row = document.createElement("div");
      row.className = "ai-chatbot-actions";
      actions.forEach((action) => {
        const link = document.createElement("a");
        link.href = action.href;
        link.textContent = action.label;
        row.appendChild(link);
      });
      messages.appendChild(row);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  function renderPrompts(prompts) {
    if (!quickPrompts || !prompts || !prompts.length) return;
    quickPrompts.innerHTML = "";
    prompts.forEach((prompt) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = prompt;
      button.addEventListener("click", () => sendMessage(prompt));
      quickPrompts.appendChild(button);
    });
  }

  async function sendMessage(text) {
    const clean = String(text || "").trim();
    if (!clean) return;
    setOpen(true);
    addMessage(clean, "user");
    setStatus("Thinking...");
    try {
      const response = await fetch("/chatbot/message", {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: clean })
      });
      const payload = await readJson(response);
      if (!response.ok || !payload.ok) {
        addMessage(payload.reply || "I could not process that request.", "bot");
        return;
      }
      addMessage(payload.reply, "bot", payload.actions || []);
      renderPrompts(payload.quick_prompts || []);
      if (voiceEnabled) speak(payload.voice_reply || payload.reply || "");
    } catch (error) {
      addMessage("Could not reach the chatbot service.", "bot");
    } finally {
      setStatus("Ready");
    }
  }

  function setupRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (micButton) micButton.disabled = true;
      setStatus("Voice input unavailable in this browser");
      return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onstart = () => {
      listening = true;
      root.classList.add("is-listening");
      setStatus("Listening...");
    };
    recognition.onend = () => {
      listening = false;
      root.classList.remove("is-listening");
      setStatus("Ready");
    };
    recognition.onerror = () => setStatus("Voice input failed");
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0] ? result[0].transcript : "")
        .join(" ")
        .trim();
      if (transcript) sendMessage(transcript);
    };
  }

  function speak(text) {
    if (!voiceEnabled || !window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }

  function setStatus(text) {
    if (status) status.textContent = text;
  }

  if (toggle) toggle.addEventListener("click", () => setOpen(panel ? panel.hidden : true));
  if (close) close.addEventListener("click", () => setOpen(false));
  if (clearButton) {
    clearButton.addEventListener("click", () => {
      if (!messages) return;
      const intro = bootstrap.intro || "Ask me about your Smart Campus dashboard.";
      messages.innerHTML = "";
      addMessage(intro, "bot");
    });
  }
  if (speakButton) {
    speakButton.addEventListener("click", () => {
      voiceEnabled = !voiceEnabled;
      speakButton.classList.toggle("is-muted", !voiceEnabled);
      speakButton.textContent = voiceEnabled ? "Voice on" : "Voice off";
      if (!voiceEnabled && window.speechSynthesis) window.speechSynthesis.cancel();
    });
  }
  if (micButton) {
    micButton.addEventListener("click", () => {
      if (!recognition) return;
      if (listening) {
        recognition.stop();
        return;
      }
      recognition.start();
    });
  }
  if (form && input) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const text = input.value.trim();
      input.value = "";
      sendMessage(text);
    });
  }

  setupRecognition();
  async function readJson(response) {
    const text = await response.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (error) {
      return { ok: false, reply: response.redirected ? "Please login again, then retry." : "Server returned an invalid response." };
    }
  }

  renderPrompts(bootstrap.quick_prompts || []);
})();
