(function () {
  "use strict";
  const ui = window.PeopleDesk;

  async function getEmployee(user) {
    if (user.employee_id == null) return null;
    return ui.apiRequest(`/employees/${user.employee_id}`);
  }

  function projectRows(projects) {
    if (!projects.length) return '<div class="empty-state">No projects are assigned to your profile yet.</div>';
    return projects.slice(0, 4).map((project) => `
      <div class="compact-item"><span class="project-dot"></span><div class="compact-copy"><strong>${ui.escapeHTML(project.name)}</strong><span>${ui.escapeHTML(project.description || "No description")}</span></div><span class="status-badge">${ui.escapeHTML(project.status)}</span></div>
    `).join("");
  }

  function leaveTable(leaves) {
    if (!leaves.length) return '<div class="empty-state">No leave requests yet.</div>';
    return `<table><thead><tr><th>Dates</th><th>Type</th><th>Status</th></tr></thead><tbody>${leaves.slice(0, 5).map((leave) => `
      <tr><td>${ui.formatDate(leave.start_date)} – ${ui.formatDate(leave.end_date)}</td><td>${ui.escapeHTML(leave.leave_type)}</td><td><span class="status-badge status-${ui.escapeHTML(leave.status).toLowerCase()}">${ui.escapeHTML(leave.status)}</span></td></tr>
    `).join("")}</tbody></table>`;
  }

  async function renderDashboard(user) {
    const welcome = document.getElementById("welcome-heading");
    if (!welcome) return;
    welcome.textContent = `Welcome back, ${user.username}`;
    document.getElementById("user-role").textContent = user.role;
    try {
      const [employee, leaves] = await Promise.all([
        getEmployee(user),
        ui.apiRequest("/leave-requests/me").catch(() => []),
      ]);
      document.getElementById("leave-count").textContent = String(leaves.length);
      const profile = document.getElementById("employee-summary");
      if (employee) {
        profile.innerHTML = `<dl class="detail-list"><div><dt>Name</dt><dd>${ui.escapeHTML(employee.name)}</dd></div><div><dt>Email</dt><dd>${ui.escapeHTML(employee.email)}</dd></div><div><dt>Department</dt><dd>${ui.escapeHTML(employee.department.name)}</dd></div></dl>`;
      } else {
        profile.innerHTML = '<div class="empty-state">Your account is not linked to an employee profile yet.</div>';
      }
      let projects = [];
      if (employee) projects = await ui.apiRequest(`/employees/${employee.id}/projects`);
      document.getElementById("project-count").textContent = String(projects.length);
      document.getElementById("dashboard-projects").innerHTML = projectRows(projects);
      document.getElementById("dashboard-leaves").innerHTML = leaveTable(leaves);
    } catch (error) {
      ui.showNotice("dashboard-notice", error.message);
      document.getElementById("employee-summary").innerHTML = '<div class="empty-state">Profile information is temporarily unavailable.</div>';
      document.getElementById("dashboard-projects").innerHTML = '<div class="empty-state">Could not load projects.</div>';
      document.getElementById("dashboard-leaves").innerHTML = '<div class="empty-state">Could not load leave requests.</div>';
    }
  }

  async function renderProjects(user) {
    const list = document.getElementById("project-list");
    if (!list) return;
    try {
      const employee = await getEmployee(user);
      if (!employee) {
        list.innerHTML = '<div class="card empty-state">Your account is not linked to an employee profile yet.</div>';
        return;
      }
      const projects = await ui.apiRequest(`/employees/${employee.id}/projects`);
      if (!projects.length) {
        list.innerHTML = '<div class="card empty-state">No projects are assigned to your profile yet.</div>';
        return;
      }
      list.innerHTML = projects.map((project) => `
        <article class="card project-card"><div class="project-card-top"><span class="project-symbol">▧</span><span class="status-badge">${ui.escapeHTML(project.status)}</span></div><h2>${ui.escapeHTML(project.name)}</h2><p class="muted">${ui.escapeHTML(project.description || "No description provided.")}</p></article>
      `).join("");
    } catch (error) {
      list.innerHTML = `<div class="card empty-state">${ui.escapeHTML(error.message)}</div>`;
    }
  }

  async function renderEmployees() {
    const list = document.getElementById("employee-list");
    if (!list) return;
    try {
      const employees = await ui.apiRequest("/employees");
      const search = document.getElementById("employee-search");
      const count = document.getElementById("employee-result-count");
      const render = () => {
        const term = search.value.trim().toLowerCase();
        const filtered = employees.filter((employee) => [employee.name, employee.email, employee.department.name].some((value) => value.toLowerCase().includes(term)));
        count.textContent = `${filtered.length} ${filtered.length === 1 ? "employee" : "employees"}`;
        if (!filtered.length) {
          list.innerHTML = '<div class="card empty-state">No employees match your search.</div>';
          return;
        }
        list.innerHTML = filtered.map((employee) => {
          const initials = employee.name.split(/\s+/).slice(0, 2).map((part) => part[0] || "").join("").toUpperCase();
          return `<article class="card employee-card"><div class="employee-avatar">${ui.escapeHTML(initials)}</div><div class="employee-copy"><h2>${ui.escapeHTML(employee.name)}</h2><a href="mailto:${ui.escapeHTML(employee.email)}">${ui.escapeHTML(employee.email)}</a></div><span class="department-tag">${ui.escapeHTML(employee.department.name)}</span></article>`;
        }).join("");
      };
      search.addEventListener("input", render);
      render();
    } catch (error) {
      ui.showNotice("employees-notice", error.message);
      list.innerHTML = '<div class="card empty-state">Could not load the employee directory.</div>';
    }
  }

  document.addEventListener("peopledesk:ready", (event) => {
    const user = event.detail.user;
    renderDashboard(user);
    renderProjects(user);
    renderEmployees();
  });
})();
