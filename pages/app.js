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

function renderSummary(payload) {
  const sourceText = Array.isArray(payload.sources) ? payload.sources.join(" / ") : "";
  const quoteText = payload.quote || "暂无金句";

  document.getElementById("summary-panel").innerHTML = `
    <div class="summary-header">
      <p class="eyebrow">Preview Summary</p>
      <h2 class="summary-title">${escapeHtml(payload.title || payload.date || "")}</h2>
      <div class="summary-meta">发布日期 ${escapeHtml(payload.publish_date || "-")}</div>
    </div>
    <div class="summary-quote">${escapeHtml(quoteText)}</div>
    <div class="summary-list">
      <div class="summary-item">
        <div class="summary-label">Date</div>
        <div class="summary-value">${escapeHtml(payload.date || "-")}</div>
      </div>
      <div class="summary-item">
        <div class="summary-label">Sources</div>
        <div class="summary-value">${escapeHtml(sourceText || "未提供")}</div>
      </div>
      <div class="summary-item">
        <div class="summary-label">News Count</div>
        <div class="summary-value">${Array.isArray(payload.news) ? payload.news.length : 0} 条</div>
      </div>
    </div>
  `;
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

  document.getElementById("current-date-label").textContent = date;
  document.getElementById("stage-date-label").textContent = date;
  document.getElementById("preview-image").src = item.image_path;
  document.getElementById("open-image-link").href = item.image_path;
  document.getElementById("open-json-link").href = item.json_path;

  const response = await fetch(item.json_path);
  const payload = await response.json();
  renderSummary(payload);
  document.getElementById("json-panel").textContent = JSON.stringify(payload, null, 2);

  document.querySelectorAll(".date-link").forEach((element) => {
    element.classList.toggle("is-active", element.dataset.date === date);
  });
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

function renderDateList() {
  const container = document.getElementById("date-list");
  container.innerHTML = "";

  state.index.items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "date-link";
    button.dataset.date = item.date;
    button.textContent = item.date;
    button.addEventListener("click", () => renderDate(item.date));
    container.appendChild(button);
  });
}

async function loadIndex() {
  const response = await fetch("./data/index.json");
  return response.json();
}

async function bootstrap() {
  state.index = await loadIndex();
  renderDateList();
  bindNavigation();
  await renderDate(pickInitialDate(state.index));
}

bootstrap().catch((error) => {
  const summary = document.getElementById("summary-panel");
  if (summary) {
    summary.innerHTML = '<div class="summary-header"><p class="eyebrow">Error</p><h2 class="summary-title">预览加载失败</h2></div>';
  }
  document.getElementById("json-panel").textContent = String(error);
});
