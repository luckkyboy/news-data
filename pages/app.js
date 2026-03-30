const state = {
  index: null,
  currentDate: "",
};

const themeByWeekday = [
  "cool",
  "forest",
  "navy",
  "terracotta",
  "rose",
  "warm",
  "citrus",
];

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function getItemByDate(date) {
  return state.index.items.find((item) => item.date === date) ?? null;
}

function pickInitialDate(index) {
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("date");
  return index.items.find((item) => item.date === requested)?.date ?? index.latest;
}

function writeUrl(date) {
  const url = new URL(window.location.href);
  url.searchParams.set("date", date);
  window.history.replaceState({}, "", url);
}

function themeNameForDate(date) {
  const [year, month, day] = String(date)
    .split("-")
    .map((part) => Number.parseInt(part, 10));
  if (![year, month, day].every(Number.isInteger)) {
    return "cool";
  }
  const weekday = new Date(year, month - 1, day).getDay();
  return themeByWeekday[(weekday + 6) % 7] ?? "cool";
}

async function renderDate(date) {
  const item = getItemByDate(date);
  if (!item) {
    document.getElementById("json-panel").textContent = "预览数据不可用";
    return;
  }
  state.currentDate = date;
  writeUrl(date);
  document.body.dataset.theme = themeNameForDate(date);

  document.getElementById("stage-date-label").textContent = date;
  document.getElementById("preview-image").src = item.image_path;
  document.getElementById("open-image-link").href = item.image_path;
  document.getElementById("open-json-link").href = item.json_path;

  const response = await fetch(item.json_path);
  const payload = await response.json();
  document.getElementById("json-panel").textContent = JSON.stringify(payload, null, 2);
}

function bindNavigation() {
  document.getElementById("prev-button").addEventListener("click", () => {
    const items = state.index.items;
    const currentIndex = items.findIndex((item) => item.date === state.currentDate);
    if (currentIndex > 0) {
      renderDate(items[currentIndex - 1].date);
    }
  });

  document.getElementById("next-button").addEventListener("click", () => {
    const items = state.index.items;
    const currentIndex = items.findIndex((item) => item.date === state.currentDate);
    if (currentIndex >= 0 && currentIndex < items.length - 1) {
      renderDate(items[currentIndex + 1].date);
    }
  });
}

async function loadIndex() {
  const response = await fetch("./data/index.json");
  return response.json();
}

async function bootstrap() {
  state.index = await loadIndex();
  bindNavigation();
  await renderDate(pickInitialDate(state.index));
}

bootstrap().catch((error) => {
  document.getElementById("json-panel").textContent = String(error);
});
