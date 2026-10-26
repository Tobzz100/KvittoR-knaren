let versions = [];
let currentEntry = null;
let cart = []; // item names in the order they were added, one entry per item

const versionSelect = document.getElementById("version-select");
const quirkBlurb = document.getElementById("quirk-blurb");
const inventoryField = document.getElementById("inventory-field");
const inventoryButtons = document.getElementById("inventory-buttons");
const cartList = document.getElementById("cart");
const listField = document.getElementById("list-field");
const momsField = document.getElementById("moms-field");
const shoppingList = document.getElementById("shopping-list");
const listHelp = document.getElementById("list-help");
const discountField = document.getElementById("discount-field");
const currencyField = document.getElementById("currency-field");
const currencyLabel = document.getElementById("currency-label");
const calcForm = document.getElementById("calc-form");
const resultDiv = document.getElementById("result");
const receiptPre = document.getElementById("receipt");
const runTestsButton = document.getElementById("run-tests");
const testStatus = document.getElementById("test-status");
const testOutput = document.getElementById("test-output");

function findVersion(key) {
  return versions.find((entry) => entry.key === key);
}

function formatKr(amount) {
  return `${Number(amount).toFixed(2).replace(".", ",")} kr`;
}

function renderCart() {
  cartList.innerHTML = "";
  if (cart.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "Varukorgen är tom";
    cartList.appendChild(empty);
    return;
  }

  const counts = new Map();
  for (const name of cart) {
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  for (const [name, count] of counts) {
    const row = document.createElement("li");
    const text = document.createElement("span");
    text.textContent = `${name} × ${count}`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "−";
    remove.title = `Ta bort en ${name}`;
    remove.addEventListener("click", () => {
      cart.splice(cart.lastIndexOf(name), 1);
      renderCart();
    });
    row.append(text, remove);
    cartList.appendChild(row);
  }
}

async function loadInventory(entry) {
  inventoryButtons.textContent = "Laddar varor...";
  const response = await fetch(`/api/inventory/${entry.key}`);
  const items = await response.json();
  if (currentEntry !== entry) {
    return; // the user switched version while loading
  }

  inventoryButtons.innerHTML = "";
  for (const item of items) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "item-button";
    const name = document.createElement("span");
    name.className = "item-name";
    name.textContent = item.name;
    const price = document.createElement("span");
    price.className = "item-price";
    price.textContent = `${formatKr(item.price)} · ${item.vat_percent} % moms`;
    button.append(name, price);
    button.addEventListener("click", () => {
      cart.push(item.name);
      renderCart();
    });
    inventoryButtons.appendChild(button);
  }
}

function renderForm(entry) {
  currentEntry = entry;
  quirkBlurb.textContent = entry.quirk;
  listHelp.textContent = entry.list_help;
  shoppingList.placeholder = entry.list_help;

  // with an inventory, price, VAT rate and currency all come from the version itself
  inventoryField.classList.toggle("hidden", !entry.uses_inventory);
  listField.classList.toggle("hidden", entry.uses_inventory);
  momsField.classList.toggle("hidden", entry.uses_inventory);
  discountField.classList.toggle("hidden", !entry.supports_discount);
  currencyField.classList.toggle("hidden", !entry.supports_currency || entry.uses_inventory);
  if (entry.supports_currency) {
    currencyLabel.textContent = entry.currency_param === "target_currency" ? "Målvaluta" : "Valuta";
  }

  cart = [];
  if (entry.uses_inventory) {
    renderCart();
    loadInventory(entry);
  }

  resultDiv.textContent = "";
  resultDiv.className = "";
  receiptPre.textContent = "";
  receiptPre.classList.add("hidden");
}

async function loadVersions() {
  const response = await fetch("/api/versions");
  versions = await response.json();

  versionSelect.innerHTML = "";
  for (const entry of versions) {
    const option = document.createElement("option");
    option.value = entry.key;
    option.textContent = entry.label;
    versionSelect.appendChild(option);
  }

  renderForm(versions[0]);
}

versionSelect.addEventListener("change", () => {
  renderForm(findVersion(versionSelect.value));
});

async function showReceipt() {
  const response = await fetch("/api/receipt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      version: currentEntry.key,
      items: cart,
      discount_code: document.getElementById("discount-code").value,
    }),
  });
  const data = await response.json();

  if (!response.ok) {
    resultDiv.textContent = `Fel: ${data.error}`;
    resultDiv.className = "error";
    receiptPre.classList.add("hidden");
    return;
  }

  resultDiv.textContent = data.messages.join("\n");
  resultDiv.className = data.messages.length ? "warning" : "";
  receiptPre.textContent = data.receipt;
  receiptPre.classList.remove("hidden");
}

calcForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (currentEntry.uses_inventory) {
    await showReceipt();
    return;
  }

  const payload = {
    version: currentEntry.key,
    shopping_list: shoppingList.value,
    moms: document.getElementById("moms").value,
  };
  if (currentEntry.supports_discount) {
    payload.discount_code = document.getElementById("discount-code").value;
  }
  if (currentEntry.supports_currency) {
    payload.currency = document.getElementById("currency").value;
  }

  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (response.ok) {
    resultDiv.textContent = `Totalt: ${data.result}`;
    resultDiv.className = "success";
  } else {
    resultDiv.textContent = `Fel: ${data.error}`;
    resultDiv.className = "error";
  }
});

runTestsButton.addEventListener("click", async () => {
  testStatus.textContent = "Kör tester...";
  testStatus.className = "";
  testOutput.textContent = "";

  const response = await fetch(`/api/test/${currentEntry.key}`, { method: "POST" });
  const data = await response.json();

  if (!response.ok) {
    testStatus.textContent = `Fel: ${data.error}`;
    testStatus.className = "fail";
    return;
  }

  testStatus.textContent = data.passed ? "Alla tester godkända" : "Tester misslyckades";
  testStatus.className = data.passed ? "pass" : "fail";
  testOutput.textContent = data.output;
});

loadVersions();
