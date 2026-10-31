const billingMoney = (value) => new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD"
}).format(value);

function billingCell(value) {
  const cell = document.createElement("td");
  cell.textContent = value ?? "";
  return cell;
}

function billingStatus(value) {
  const cell = billingCell("");
  const badge = document.createElement("span");
  badge.className = `status-badge ${value}`;
  badge.textContent = value;
  cell.append(badge);
  return cell;
}

document.addEventListener("DOMContentLoaded", () => {
  const kind = document.body.dataset.billing;
  const message = document.getElementById("form-message");

  async function loadInvoices() {
    const invoices = await api("/api/invoices");
    const table = document.getElementById("invoices-table");
    const select = document.getElementById("payment-invoice");
    if (table) {
      if (invoices.length === 0) {
        const row = document.createElement("tr");
        const cell = billingCell("No invoices yet. Start a subscription to generate one.");
        cell.colSpan = 5;
        cell.className = "empty-cell";
        row.append(cell);
        table.replaceChildren(row);
      } else {
        table.replaceChildren();
        invoices.forEach((invoice) => {
          const row = document.createElement("tr");
          row.append(billingCell(invoice.invoice_number),
            billingCell(`${invoice.product_name} / ${invoice.plan_name}`),
            billingCell(billingMoney(invoice.amount)), billingCell(invoice.due_date),
            billingStatus(invoice.status));
          table.append(row);
        });
      }
    }
    if (select) {
      const unpaid = invoices.filter((invoice) => invoice.status === "pending");
      select.replaceChildren(new Option("Choose an invoice", ""));
      unpaid.forEach((invoice) => select.add(new Option(
        `${invoice.invoice_number} — ${billingMoney(invoice.amount)}`,
        invoice.id
      )));
      const requestedInvoice = new URLSearchParams(window.location.search).get("invoice");
      if (requestedInvoice && unpaid.some((invoice) => String(invoice.id) === requestedInvoice)) {
        select.value = requestedInvoice;
      }
    }
  }

  async function loadPayments() {
    const payments = await api("/api/payments");
    const table = document.getElementById("payments-table");
    if (!table) return;
    if (payments.length === 0) {
      const row = document.createElement("tr");
      const cell = billingCell("No payments recorded yet.");
      cell.colSpan = 5;
      cell.className = "empty-cell";
      row.append(cell);
      table.replaceChildren(row);
      return;
    }
    table.replaceChildren();
    payments.forEach((payment) => {
      const row = document.createElement("tr");
      row.append(billingCell(payment.invoice_number), billingCell(billingMoney(payment.amount)),
        billingCell(payment.method), billingCell(new Date(payment.paid_at + "Z").toLocaleString()),
        billingStatus(payment.status));
      table.append(row);
    });
  }

  Promise.all([loadInvoices(), loadPayments()]).catch((error) => {
    if (message) {
      message.textContent = error.message;
      message.classList.add("error");
    } else {
      window.alert(error.message);
    }
  });

  const form = document.getElementById("payment-form");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const values = Object.fromEntries(new FormData(form));
        await api("/api/payments", { method: "POST", body: JSON.stringify(values) });
        form.reset();
        message.textContent = "Payment recorded and invoice marked paid.";
        message.classList.remove("error");
        await Promise.all([loadInvoices(), loadPayments()]);
      } catch (error) {
        message.textContent = error.message;
        message.classList.add("error");
      }
    });
  }
});
