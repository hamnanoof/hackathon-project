const subscriptionMoney = (value) => new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD"
}).format(value);

function subscriptionCell(value) {
  const cell = document.createElement("td");
  cell.textContent = value ?? "";
  return cell;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("subscription-form");
  const table = document.getElementById("subscriptions-table");
  const message = document.getElementById("form-message");

  async function loadSubscriptions() {
    const [plans, subscriptions] = await Promise.all([
      api("/api/plans"),
      api("/api/subscriptions")
    ]);
    const select = document.getElementById("subscription-plan");
    select.replaceChildren(new Option("Choose a plan", ""));
    plans.forEach((plan) => select.add(new Option(
      `${plan.product_name} — ${plan.name} (${subscriptionMoney(plan.price)}/${plan.billing_interval})`,
      plan.id
    )));
    if (subscriptions.length === 0) {
      const row = document.createElement("tr");
      const cell = subscriptionCell("No subscriptions yet. Create a plan to get started.");
      cell.colSpan = 6;
      cell.className = "empty-cell";
      row.append(cell);
      table.replaceChildren(row);
      return;
    }
    table.replaceChildren();
    for (const subscription of subscriptions) {
      const row = document.createElement("tr");
      row.append(subscriptionCell(subscription.product_name), subscriptionCell(subscription.plan_name),
        subscriptionCell(`${subscriptionMoney(subscription.price)}/${subscription.billing_interval}`),
        subscriptionCell(subscription.start_date));
      const status = subscriptionCell("");
      const badge = document.createElement("span");
      badge.className = `status-badge ${subscription.status}`;
      badge.textContent = subscription.status;
      status.append(badge);
      row.append(status);
      const actions = document.createElement("td");
      if (subscription.status === "active") {
        const cancel = document.createElement("button");
        cancel.className = "table-action danger";
        cancel.type = "button";
        cancel.textContent = "Cancel";
        cancel.addEventListener("click", async () => {
          try {
            await api(`/api/subscriptions/${subscription.id}`, {
              method: "PATCH",
              body: JSON.stringify({ status: "cancelled" })
            });
            await loadSubscriptions();
          } catch (error) {
            window.alert(error.message);
          }
        });
        actions.append(cancel);
      }
      row.append(actions);
      table.append(row);
    }
  }

  loadSubscriptions().catch((error) => {
    message.textContent = error.message;
    message.classList.add("error");
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const values = Object.fromEntries(new FormData(form));
      await api("/api/subscriptions", { method: "POST", body: JSON.stringify(values) });
      form.reset();
      message.textContent = "Subscription started and invoice created.";
      message.classList.remove("error");
      await loadSubscriptions();
    } catch (error) {
      message.textContent = error.message;
      message.classList.add("error");
    }
  });
});
