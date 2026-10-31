
const billingMoney = (value) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR"
  }).format(Number(value) || 0);


function billingCell(value) {
  const cell = document.createElement("td");
  cell.textContent = value ?? "";
  return cell;
}


function billingStatus(value) {
  const cell = billingCell("");
  const badge = document.createElement("span");

  const allowedStatuses = [
    "pending",
    "paid",
    "failed",
    "cancelled"
  ];

  const status = allowedStatuses.includes(value)
    ? value
    : "unknown";

  badge.className = `status-badge ${status}`;
  badge.textContent = status;

  cell.append(badge);
  return cell;
}


function billingDate(value) {
  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Invalid date";
  }

  return date.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  });
}


document.addEventListener("DOMContentLoaded", () => {

  const kind = document.body.dataset.billing;
  const message = document.getElementById("form-message");


  function showMessage(text, isError = false) {
    if (!message) return;

    message.textContent = text;
    message.classList.toggle("error", isError);
  }


  async function loadInvoices() {
    const invoices = await api("/api/invoices");

    const table = document.getElementById("invoices-table");
    const select = document.getElementById("payment-invoice");

    if (table) {
      if (!invoices.length) {
        const row = document.createElement("tr");
        const cell = billingCell(
          "No invoices yet. Start a subscription to generate one."
        );

        cell.colSpan = 6;
        cell.className = "empty-cell";

        row.append(cell);
        table.replaceChildren(row);

      } else {
        table.replaceChildren();

        invoices.forEach((invoice) => {
          const row = document.createElement("tr");

          row.append(
            billingCell(invoice.invoice_number),
            billingCell(invoice.customer_name || "—"),
            billingCell(
              `${invoice.product_name} / ${invoice.plan_name}`
            ),
            billingCell(billingMoney(invoice.amount)),
            billingCell(invoice.due_date),
            billingStatus(invoice.status)
          );

          table.append(row);
        });
      }
    }


    if (select) {
      const unpaid = invoices.filter(
        (invoice) => invoice.status === "pending"
      );

      select.replaceChildren(
        new Option("Choose an invoice", "")
      );

      unpaid.forEach((invoice) => {
        select.add(
          new Option(
            `${invoice.invoice_number} — ${billingMoney(invoice.amount)}`,
            invoice.id
          )
        );
      });

      const requestedInvoice =
        new URLSearchParams(window.location.search).get("invoice");

      if (
        requestedInvoice &&
        unpaid.some(
          (invoice) => String(invoice.id) === requestedInvoice
        )
      ) {
        select.value = requestedInvoice;
      }
    }
  }


  async function loadPayments() {
    const payments = await api("/api/payments");

    const table = document.getElementById("payments-table");

    if (!table) return;

    if (!payments.length) {
      const row = document.createElement("tr");

      const cell = billingCell(
        "No payments recorded yet."
      );

      cell.colSpan = 5;
      cell.className = "empty-cell";

      row.append(cell);
      table.replaceChildren(row);

      return;
    }


    table.replaceChildren();

    payments.forEach((payment) => {
      const row = document.createElement("tr");

      row.append(
        billingCell(payment.invoice_number),
        billingCell(billingMoney(payment.amount)),
        billingCell(payment.method),
        billingCell(billingDate(payment.paid_at + "Z")),
        billingStatus(payment.status)
      );

      table.append(row);
    });
  }


  async function refreshBilling() {
    await Promise.all([
      loadInvoices(),
      loadPayments()
    ]);
  }


  refreshBilling().catch((error) => {
    showMessage(
      `Unable to load billing information: ${error.message || "Please try again."}`,
      true
    );
  });


  const form = document.getElementById("payment-form");

  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const submitButton = form.querySelector(
        '[type="submit"]'
      );

      if (submitButton?.disabled) return;

      if (submitButton) {
        submitButton.disabled = true;
      }

      try {
        const values = Object.fromEntries(
          new FormData(form)
        );

        await api("/api/payments", {
          method: "POST",
          body: JSON.stringify(values)
        });

        form.reset();

        showMessage(
          "Payment recorded and invoice marked paid."
        );

        await refreshBilling();

      } catch (error) {
        showMessage(
          error.message || "Payment failed. Please try again.",
          true
        );

      } finally {
        if (submitButton) {
          submitButton.disabled = false;
        }
      }
    });
  }

});
