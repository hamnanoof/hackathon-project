document.addEventListener("DOMContentLoaded", async () => {
  try {
    const stats = await api("/api/dashboard");
    document.getElementById("stat-products").textContent = stats.products;
    document.getElementById("stat-subscriptions").textContent = stats.active_subscriptions;
    document.getElementById("stat-invoices").textContent = stats.pending_invoices;
    document.getElementById("stat-collected").textContent = new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: "USD"
    }).format(stats.collected);
  } catch (error) {
    window.alert(error.message);
  }
});
