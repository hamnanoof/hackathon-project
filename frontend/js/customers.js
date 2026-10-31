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

function reportFormMessage(text, isError = false) {
  const message = document.getElementById("form-message");
  if (!message) return;
  message.textContent = text;
  message.classList.toggle("error", isError);
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("customer-form");

  async function loadCustomers() {
    const customers = await api("/api/customers");
    const table = document.getElementById("customers-table");
    const count = document.getElementById("customer-count");
    if (!table) return;
    count.textContent = `${customers.length} ${customers.length === 1 ? "customer" : "customers"}`;
    if (customers.length === 0) {
      emptyRow(table, 6, "No customers yet. Add your first customer above.");
      return;
    }
    table.replaceChildren();
    for (const customer of customers) {
      const row = document.createElement("tr");
      row.append(
        makeCell(customer.name),
        makeCell(customer.email),
        makeCell(customer.phone || "—"),
        makeCell(customer.address || "—"),
        makeCell(new Date(customer.created_at + "Z").toLocaleDateString())
      );
      const actions = document.createElement("td");
      const deleteButton = document.createElement("button");
      deleteButton.className = "table-action danger";
      deleteButton.type = "button";
      deleteButton.textContent = "Delete";
      deleteButton.addEventListener("click", async () => {
        if (!window.confirm(`Delete "${customer.name}"?`)) return;
        try {
          await api(`/api/customers/${customer.id}`, { method: "DELETE" });
          await loadCustomers();
        } catch (error) {
          window.alert(error.message);
        }
      });
      actions.append(deleteButton);
      row.append(actions);
      table.append(row);
    }
  }

  if (form) {
    loadCustomers().catch((error) => reportFormMessage(error.message, true));
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(form));
      try {
        await api("/api/customers", { method: "POST", body: JSON.stringify(values) });
        form.reset();
        reportFormMessage("Customer added.");
        await loadCustomers();
      } catch (error) {
        reportFormMessage(error.message, true);
      }
    });
  }
});
