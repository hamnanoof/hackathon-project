// API fetch wrapper
async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {})
    }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return body;
}

// Currency formatting in INR
function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR"
  }).format(Number(amount) || 0);
}

// Date formatting
function formatDate(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return "Invalid date";
  return date.toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric"
  });
}

function formatDateTime(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return "Invalid date";
  return date.toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

// Role-based sidebar
function renderSidebar(role) {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  const menuItems = {
    admin: [
      { label: "Dashboard", href: "/dashboard.html", roles: ["admin", "staff", "customer"] },
      { label: "Reports", href: "/reports.html", roles: ["admin", "staff"] },
      { label: "Customers", href: "/customers.html", roles: ["admin", "staff"] },
      { label: "Products", href: "/products.html", roles: ["admin", "staff"] },
      { label: "Plans", href: "/plans.html", roles: ["admin", "staff"] },
      { label: "Subscriptions", href: "/subscriptions.html", roles: ["admin", "staff", "customer"] },
      { label: "Invoices", href: "/invoices.html", roles: ["admin", "staff", "customer"] },
      { label: "Payments", href: "/payments.html", roles: ["admin", "staff", "customer"] },
      { label: "Taxes", href: "/taxes.html", roles: ["admin", "staff"] },
      { label: "Discounts", href: "/discounts.html", roles: ["admin", "staff"] },
      { label: "Templates", href: "/templates.html", roles: ["admin", "staff"] },
      { label: "Users", href: "/users.html", roles: ["admin"] },
      { label: "Account", href: "/account.html", roles: ["admin", "staff", "customer"] }
    ],
    staff: [
      { label: "Dashboard", href: "/dashboard.html", roles: ["admin", "staff", "customer"] },
      { label: "Reports", href: "/reports.html", roles: ["admin", "staff"] },
      { label: "Customers", href: "/customers.html", roles: ["admin", "staff"] },
      { label: "Products", href: "/products.html", roles: ["admin", "staff"] },
      { label: "Plans", href: "/plans.html", roles: ["admin", "staff"] },
      { label: "Subscriptions", href: "/subscriptions.html", roles: ["admin", "staff", "customer"] },
      { label: "Invoices", href: "/invoices.html", roles: ["admin", "staff", "customer"] },
      { label: "Payments", href: "/payments.html", roles: ["admin", "staff", "customer"] },
      { label: "Account", href: "/account.html", roles: ["admin", "staff", "customer"] }
    ],
    customer: [
      { label: "Dashboard", href: "/dashboard.html", roles: ["admin", "staff", "customer"] },
      { label: "My Subscriptions", href: "/subscriptions.html", roles: ["admin", "staff", "customer"] },
      { label: "My Invoices", href: "/invoices.html", roles: ["admin", "staff", "customer"] },
      { label: "My Payments", href: "/payments.html", roles: ["admin", "staff", "customer"] },
      { label: "Account", href: "/account.html", roles: ["admin", "staff", "customer"] }
    ]
  };

  const items = menuItems[role] || menuItems.customer;

  sidebar.innerHTML = `
    <a class="brand" href="/dashboard.html">Subscript<span>.</span></a>
    <p class="nav-caption">WORKSPACE</p>
    <nav class="main-nav">
      ${items.map(item => `
        <a href="${item.href}">${item.label}</a>
      `).join("")}
    </nav>
    <div class="sidebar-bottom">
      <span id="user-name">Your workspace</span>
      <button class="logout-button" data-logout>Sign out</button>
    </div>
  `;
}

// Auth guard
function authGuard() {
  const body = document.body;
  const requiredRoles = body.dataset.roles ? body.dataset.roles.split(",") : null;

  api("/api/auth/me")
    .then(user => {
      if (requiredRoles && !requiredRoles.includes(user.role)) {
        window.location.replace("/dashboard.html");
        return;
      }

      // Render role-based sidebar
      renderSidebar(user.role);

      // Update user name
      const userName = document.getElementById("user-name");
      if (userName) userName.textContent = user.name;

      // Hide elements based on roles
      document.querySelectorAll("[data-roles]").forEach(el => {
        const allowedRoles = el.dataset.roles.split(",");
        if (!allowedRoles.includes(user.role)) {
          el.style.display = "none";
        }
      });
    })
    .catch(error => {
      if (error.message === "Authentication required" || error.status === 401) {
        window.location.replace("/login.html");
      }
    });
}

// Table helpers
function makeCell(value) {
  const cell = document.createElement("td");
  cell.textContent = value ?? "";
  return cell;
}

function emptyRow(body, columns, message) {
  const row = document.createElement("tr");
  const cell = makeCell(message);
  cell.colSpan = columns;
  cell.className = "empty-cell";
  row.append(cell);
  body.replaceChildren(row);
}

// Pager helper
function renderPager(container, pagination, onPageChange) {
  if (!container) return;

  const { page, pages, total } = pagination;

  container.innerHTML = `
    <div class="pager">
      <span>Page ${page} of ${pages} (${total} total)</span>
      <button ${page <= 1 ? "disabled" : ""} data-page="${page - 1}">Previous</button>
      <button ${page >= pages ? "disabled" : ""} data-page="${page + 1}">Next</button>
    </div>
  `;

  container.querySelectorAll("button[data-page]").forEach(btn => {
    btn.addEventListener("click", () => {
      const newPage = parseInt(btn.dataset.page);
      if (onPageChange) onPageChange(newPage);
    });
  });
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.auth === "required") {
    authGuard();
  }

  // Logout handler
  document.querySelectorAll("[data-logout]").forEach(button => {
    button.addEventListener("click", async () => {
      try {
        await api("/api/auth/logout", { method: "POST" });
        window.location.assign("/login.html");
      } catch (error) {
        window.alert(error.message);
      }
    });
  });
});
