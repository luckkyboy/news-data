const state = {
  index: null,
  currentDate: "",
};

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

async function renderDate(date) {
  const item = getItemByDate(date);
  if (!item) {
    document.getElementById("json-panel").textContent = "预览数据不可用";
    return;
  }
  state.currentDate = date;
  writeUrl(date);

  document.getElementById("current-date-label").textContent = date;
  const stageDateLabel = document.getElementById("stage-date-label");
  if (stageDateLabel) {
    stageDateLabel.textContent = date;
  }
  document.getElementById("preview-image").src = item.image_path;
  const imageLink = document.getElementById("open-image-link");
  if (imageLink) {
    imageLink.href = item.image_path;
  }
  const jsonLink = document.getElementById("open-json-link");
  if (jsonLink) {
    jsonLink.href = item.json_path;
  }

  const response = await fetch(item.json_path);
  const payload = await response.json();
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
  document.getElementById("json-panel").textContent = String(error);
});
