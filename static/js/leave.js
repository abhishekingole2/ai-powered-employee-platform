(function () {
  "use strict";
  const ui = window.PeopleDesk;

  function renderLeaves(leaves) {
    const list = document.getElementById("leave-list");
    if (!leaves.length) {
      list.innerHTML = '<div class="empty-state">No leave requests yet. Your requests will appear here.</div>';
      return;
    }
    list.innerHTML = `<table><thead><tr><th>Dates</th><th>Type</th><th>Reason</th><th>Status</th></tr></thead><tbody>${leaves.map((leave) => `
      <tr><td class="date-cell">${ui.formatDate(leave.start_date)}<span>to ${ui.formatDate(leave.end_date)}</span></td><td>${ui.escapeHTML(leave.leave_type)}</td><td>${ui.escapeHTML(leave.reason || "—")}</td><td><span class="status-badge status-${ui.escapeHTML(leave.status).toLowerCase()}">${ui.escapeHTML(leave.status)}</span></td></tr>
    `).join("")}</tbody></table>`;
  }

  async function loadLeaves() {
    try {
      renderLeaves(await ui.apiRequest("/leave-requests/me"));
    } catch (error) {
      renderLeaves([]);
      ui.showNotice("leave-notice", error.message);
    }
  }

  document.addEventListener("peopledesk:ready", () => {
    const form = document.getElementById("leave-form");
    if (!form) return;
    const errorBox = document.getElementById("leave-error");
    const submit = document.getElementById("leave-submit");
    loadLeaves();
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.hidden = true;
      const values = new FormData(form);
      const payload = {
        start_date: values.get("start_date"),
        end_date: values.get("end_date"),
        leave_type: values.get("leave_type"),
        reason: values.get("reason") || null,
      };
      if (payload.start_date > payload.end_date) {
        errorBox.textContent = "The end date must be on or after the start date.";
        errorBox.hidden = false;
        return;
      }
      submit.disabled = true;
      submit.textContent = "Submitting…";
      try {
        await ui.apiRequest("/leave-requests", { method: "POST", body: JSON.stringify(payload) });
        form.reset();
        ui.showNotice("leave-notice", "Your leave request was submitted.", "success");
        await loadLeaves();
      } catch (error) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      } finally {
        submit.disabled = false;
        submit.textContent = "Submit request";
      }
    });
  });
})();
