
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
    throw new Error(body.error || `Request failed (${response.status})`);
  }

  return body;
}


function showFormError(error) {
  const message = document.getElementById("form-message");

  if (message) {
    message.textContent = error.message || "Something went wrong.";
  }
}


document.addEventListener("DOMContentLoaded", async () => {

  // LOGIN
  const loginForm = document.getElementById("login-form");

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const values = Object.fromEntries(new FormData(loginForm));

      try {
        const user = await api("/api/auth/login", {
          method: "POST",
          body: JSON.stringify(values)
        });

        // Redirect after successful login
        window.location.assign("/dashboard.html");

      } catch (error) {
        showFormError(error);
      }
    });
  }


  // CHECK AUTHENTICATION
  if (document.body.dataset.auth === "required") {
    try {
      const user = await api("/api/auth/me");

      const name = document.getElementById("user-name");
      const greeting = document.getElementById("greeting-name");

      if (name) {
        name.textContent = user.name;
      }

      if (greeting) {
        greeting.textContent = `, ${user.name}`;
      }

    } catch (error) {

      if (
        error.message === "Authentication required" ||
        error.message === "Account not found"
      ) {
        window.location.replace("/login.html");
        return;
      }

      showFormError(error);
    }
  }


  // LOGOUT
  document.querySelectorAll("[data-logout]").forEach((button) => {

    button.addEventListener("click", async () => {

      try {
        await api("/api/auth/logout", {
          method: "POST"
        });

        window.location.assign("/login.html");

      } catch (error) {
        window.alert(error.message);
      }

    });

  });

});
