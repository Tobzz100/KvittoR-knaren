let versions = [];
let currentEntry = null;

const versionSelect = document.getElementById("version-select");
const quirkBlurb = document.getElementById("quirk-blurb");
const shoppingList = document.getElementById("shopping-list");
const listHelp = document.getElementById("list-help");
const discountField = document.getElementById("discount-field");
const currencyField = document.getElementById("currency-field");
const currencyLabel = document.getElementById("currency-label");
const calcForm = document.getElementById("calc-form");
const resultDiv = document.getElementById("result");
const runTestsButton = document.getElementById("run-tests");
const testStatus = document.getElementById("test-status");
const testOutput = document.getElementById("test-output");

function findVersion(key) {
  return versions.find((entry) => entry.key === key);
}

function renderForm(entry) {
  currentEntry = entry;
  quirkBlurb.textContent = entry.quirk;
  listHelp.textContent = entry.list_help;
  shoppingList.placeholder = entry.list_help;

  discountField.classList.toggle("hidden", !entry.supports_discount);
  currencyField.classList.toggle("hidden", !entry.supports_currency);
  if (entry.supports_currency) {
    currencyLabel.textContent = entry.currency_param === "target_currency" ? "Målvaluta" : "Valuta";
  }

  resultDiv.textContent = "";
  resultDiv.className = "";
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

calcForm.addEventListener("submit", async (event) => {
  event.preventDefault();

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
