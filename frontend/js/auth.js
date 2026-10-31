async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {})
    }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function showFormError(error) {
  const message = document.getElementById("form-message");
  if (message) message.textContent = error.message || "Something went wrong.";
}

document.addEventListener("DOMContentLoaded", async () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(loginForm));
      try {
        await api("/api/auth/login", { method: "POST", body: JSON.stringify(values) });
        window.location.assign("/dashboard.html");
      } catch (error) {
        showFormError(error);
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(registerForm));
      try {
        await api("/api/auth/register", { method: "POST", body: JSON.stringify(values) });
        window.location.assign("/dashboard.html");
      } catch (error) {
        showFormError(error);
      }
    });
  }

  if (document.body.dataset.auth === "required") {
    try {
      const user = await api("/api/auth/me");
      const name = document.getElementById("user-name");
      const greeting = document.getElementById("greeting-name");
      if (name) name.textContent = user.name;
      if (greeting) greeting.textContent = `, ${user.name}`;
    } catch (error) {
      if (error.message === "Authentication required" || error.message === "Account not found") {
        window.location.replace("/login.html");
        return;
      }
      showFormError(error);
    }
  }

  document.querySelectorAll("[data-logout]").forEach((button) => {
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
