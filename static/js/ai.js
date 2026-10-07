(function () {
  "use strict";
  const ui = window.PeopleDesk;
  const STATE_KEY = "peopleDeskChatState";

  function loadState() {
    try { return JSON.parse(sessionStorage.getItem(STATE_KEY) || "{}"); }
    catch (_error) { return {}; }
  }

  function saveState() {
    sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
  }

  let state = loadState();

  function addBubble(role, text, options = {}) {
    const container = document.getElementById("chat-messages");
    const empty = document.getElementById("chat-empty");
    if (empty) empty.remove();
    const bubble = document.createElement("div");
    bubble.className = `message-row ${role === "user" ? "message-user" : "message-assistant"}${options.loading ? " message-loading" : ""}`;
    if (role !== "user") {
      const avatar = document.createElement("span");
      avatar.className = "assistant-avatar small-avatar";
      avatar.textContent = "P";
      bubble.appendChild(avatar);
    }
    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;
    bubble.appendChild(content);
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return bubble;
  }

  function restoreMessages() {
    const messages = Array.isArray(state.messages) ? state.messages : [];
    if (!messages.length) return;
    messages.forEach((message) => addBubble(message.role, message.content));
  }

  document.addEventListener("peopledesk:ready", () => {
    const form = document.getElementById("chat-form");
    if (!form) return;
    const input = document.getElementById("chat-input");
    const send = document.getElementById("chat-send");
    restoreMessages();

    document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => {
      input.value = button.dataset.prompt;
      form.requestSubmit();
    }));

    document.getElementById("new-chat").addEventListener("click", () => {
      state = { conversationId: null, messages: [] };
      saveState();
      window.location.reload();
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      ui.hideNotice("ai-notice");
      state.messages = Array.isArray(state.messages) ? state.messages : [];
      state.messages.push({ role: "user", content: message });
      addBubble("user", message);
      input.value = "";
      send.disabled = true;
      const loadingBubble = addBubble("assistant", "Thinking…", { loading: true });
      try {
        const result = await ui.apiRequest("/ai/chat", {
          method: "POST",
          body: JSON.stringify({ message, conversation_id: state.conversationId || null }),
        });
        state.conversationId = result.conversation_id;
        state.messages.push({ role: "assistant", content: result.message });
        loadingBubble.remove();
        addBubble("assistant", result.message);
        saveState();
      } catch (error) {
        loadingBubble.remove();
        addBubble("assistant", error.message);
        ui.showNotice("ai-notice", error.message);
        // Keep the conversation ID and rendered user message available for retry.
        saveState();
      } finally {
        send.disabled = false;
        input.focus();
      }
    });
  });
})();
