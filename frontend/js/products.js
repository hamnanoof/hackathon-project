const formatMoney = (value) => new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD"
}).format(value);

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
  const productForm = document.getElementById("product-form");
  const planForm = document.getElementById("plan-form");

  async function loadProducts() {
    const products = await api("/api/products");
    const table = document.getElementById("products-table");
    const count = document.getElementById("product-count");
    if (!table) return products;
    count.textContent = `${products.length} ${products.length === 1 ? "product" : "products"}`;
    if (products.length === 0) {
      emptyRow(table, 4, "No products yet. Add your first product above.");
      return products;
    }
    table.replaceChildren();
    for (const product of products) {
      const row = document.createElement("tr");
      row.append(makeCell(product.name), makeCell(product.description || "—"),
        makeCell(new Date(product.created_at + "Z").toLocaleDateString()));
      const actions = document.createElement("td");
      const button = document.createElement("button");
      button.className = "table-action danger";
      button.type = "button";
      button.textContent = "Delete";
      button.addEventListener("click", async () => {
        if (!window.confirm(`Delete "${product.name}"?`)) return;
        try {
          await api(`/api/products/${product.id}`, { method: "DELETE" });
          await loadProducts();
        } catch (error) {
          window.alert(error.message);
        }
      });
      actions.append(button);
      row.append(actions);
      table.append(row);
    }
    return products;
  }

  async function loadPlans() {
    const [products, plans] = await Promise.all([
      api("/api/products"),
      api("/api/plans")
    ]);
    const select = document.getElementById("plan-product");
    const table = document.getElementById("plans-table");
    const count = document.getElementById("plan-count");
    if (!table) return;
    select.replaceChildren(new Option("Choose a product", ""));
    products.forEach((product) => select.add(new Option(product.name, product.id)));
    count.textContent = `${plans.length} ${plans.length === 1 ? "plan" : "plans"}`;
    if (plans.length === 0) {
      emptyRow(table, 5, "No plans yet. Create a product first, then add a plan.");
      return;
    }
    table.replaceChildren();
    for (const plan of plans) {
      const row = document.createElement("tr");
      row.append(makeCell(plan.name), makeCell(plan.product_name), makeCell(formatMoney(plan.price)),
        makeCell(plan.billing_interval === "month" ? "Monthly" : "Yearly"));
      const actions = document.createElement("td");
      const button = document.createElement("button");
      button.className = "table-action danger";
      button.type = "button";
      button.textContent = "Delete";
      button.addEventListener("click", async () => {
        if (!window.confirm(`Delete "${plan.name}"?`)) return;
        try {
          await api(`/api/plans/${plan.id}`, { method: "DELETE" });
          await loadPlans();
        } catch (error) {
          window.alert(error.message);
        }
      });
      actions.append(button);
      row.append(actions);
      table.append(row);
    }
  }

  if (productForm) {
    loadProducts().catch((error) => reportFormMessage(error.message, true));
    productForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(productForm));
      try {
        await api("/api/products", { method: "POST", body: JSON.stringify(values) });
        productForm.reset();
        reportFormMessage("Product added.");
        await loadProducts();
      } catch (error) {
        reportFormMessage(error.message, true);
      }
    });
  }

  if (planForm) {
    loadPlans().catch((error) => reportFormMessage(error.message, true));
    planForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(planForm));
      try {
        await api("/api/plans", { method: "POST", body: JSON.stringify(values) });
        planForm.reset();
        reportFormMessage("Plan created.");
        await loadPlans();
      } catch (error) {
        reportFormMessage(error.message, true);
      }
    });
  }
});
