(function () {
  "use strict";

  const TOKEN_KEY = "peopleDeskAccessToken";

  class ApiError extends Error {
    constructor(status, message) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function detailMessage(detail) {
    if (Array.isArray(detail)) return detail.map((item) => item.msg || "Invalid value").join(" ");
    if (typeof detail === "string") return detail;
    return "The request could not be completed.";
  }

  async function apiRequest(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

    let response;
    try {
      response = await fetch(url, { ...options, headers });
    } catch (_error) {
      throw new ApiError(0, "Unable to reach the server. Check your connection and try again.");
    }

    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) {
      if (response.status === 401) {
        clearToken();
        if (window.location.pathname !== "/login") window.location.replace("/login");
      }
      let message = payload && typeof payload === "object" ? detailMessage(payload.detail) : "The request could not be completed.";
      if (response.status === 403) message = "You do not have permission to view this information.";
      if (response.status >= 500) message = "The server could not complete the request. Please try again.";
      throw new ApiError(response.status, message);
    }
    return payload;
  }

  function showNotice(elementOrId, message, type = "error") {
    const element = typeof elementOrId === "string" ? document.getElementById(elementOrId) : elementOrId;
    if (!element) return;
    element.textContent = message;
    element.className = `notice ${type === "success" ? "notice-success" : "notice-error"}`;
    element.hidden = false;
  }

  function hideNotice(elementOrId) {
    const element = typeof elementOrId === "string" ? document.getElementById(elementOrId) : elementOrId;
    if (element) element.hidden = true;
  }

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
  }

  function formatDate(value) {
    if (!value) return "—";
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
  }

  async function requireCurrentUser() {
    if (!getToken()) {
      window.location.replace("/login");
      return null;
    }
    try {
      return await apiRequest("/auth/me");
    } catch (error) {
      if (error.status !== 401) {
        const main = document.querySelector("main");
        if (main) {
          let notice = main.querySelector(".notice");
          if (!notice) {
            notice = document.createElement("div");
            notice.className = "notice";
            main.prepend(notice);
          }
          showNotice(notice, error.message);
        }
      }
      return null;
    }
  }

  window.PeopleDesk = {
    TOKEN_KEY, ApiError, apiRequest, getToken, setToken, clearToken,
    showNotice, hideNotice, escapeHTML, formatDate, requireCurrentUser,
  };

  document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".menu-toggle");
    const nav = document.querySelector(".main-nav");
    if (toggle && nav) {
      toggle.addEventListener("click", () => {
        const expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!expanded));
        nav.classList.toggle("nav-open", !expanded);
      });
    }

    document.querySelectorAll("[data-logout]").forEach((button) => button.addEventListener("click", () => {
      clearToken();
      sessionStorage.removeItem("peopleDeskChatState");
      window.location.replace("/login");
    }));

    if (document.body.dataset.protected === "true") {
      requireCurrentUser().then((user) => {
        if (!user) return;
        const navUser = document.getElementById("nav-user");
        if (navUser) navUser.textContent = user.username;
        document.dispatchEvent(new CustomEvent("peopledesk:ready", { detail: { user } }));
      });
    }
  });
})();
