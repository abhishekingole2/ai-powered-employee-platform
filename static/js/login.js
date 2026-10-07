(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", async () => {
    const ui = window.PeopleDesk;
    const form = document.getElementById("login-form");
    if (!form || !ui) return;
    const errorBox = document.getElementById("login-error");
    const submit = document.getElementById("login-submit");

    if (ui.getToken()) {
      try {
        await ui.apiRequest("/auth/me");
        window.location.replace("/dashboard");
        return;
      } catch (_error) {
        ui.clearToken();
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.hidden = true;
      submit.disabled = true;
      submit.textContent = "Signing in…";
      const formData = new FormData(form);
      try {
        const response = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: formData.get("username"), password: formData.get("password") }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Sign in failed. Check your credentials.");
        ui.setToken(result.access_token);
        form.reset();
        window.location.replace("/dashboard");
      } catch (error) {
        errorBox.textContent = error instanceof TypeError ? "Unable to reach the server. Check your connection and try again." : error.message;
        errorBox.hidden = false;
      } finally {
        submit.disabled = false;
        submit.textContent = "Sign in";
      }
    });
  });
})();
