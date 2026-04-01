const EARLIEST_DATE = "2026-03-26";

const state = {
  currentDate: "",
  latestAvailableDate: "",
  latestCheckedDate: "",
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
const payloadCache = new Map();
const JSON_CDN_BASE = "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/news";
const IMAGE_CDN_BASE = "https://cdn.jsdmirror.com/gh/luckkyboy/news-data@main/static/images";
const beijingDateFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Shanghai",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

function parseDateParts(date) {
  const [year, month, day] = String(date)
    .split("-")
    .map((part) => Number.parseInt(part, 10));
  if (![year, month, day].every(Number.isInteger)) {
    return null;
  }
  return { year, month, day };
}

function formatDate(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function todayInBeijing() {
  const parts = beijingDateFormatter.formatToParts(new Date());
  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  const day = parts.find((part) => part.type === "day")?.value;
  if (!year || !month || !day) {
    return formatDate(new Date());
  }
  return `${year}-${month}-${day}`;
}

function pickInitialDate() {
  const params = new URLSearchParams(window.location.search);
  return params.get("date") || todayInBeijing();
}

function writeUrl(date) {
  const url = new URL(window.location.href);
  url.searchParams.set("date", date);
  window.history.replaceState({}, "", url);
}

function themeNameForDate(date) {
  const parts = parseDateParts(date);
  if (!parts) {
    return "cool";
  }
  const { year, month, day } = parts;
  const weekday = new Date(year, month - 1, day).getDay();
  return themeByWeekday[(weekday + 6) % 7] ?? "cool";
}

function clampDate(date) {
  const earliest = parseDateParts(EARLIEST_DATE);
  if (!earliest) {
    return date;
  }
  const earliestDate = new Date(earliest.year, earliest.month - 1, earliest.day);
  const todayParts = parseDateParts(todayInBeijing());
  if (!todayParts) {
    return date;
  }
  const today = new Date(todayParts.year, todayParts.month - 1, todayParts.day);
  const latestDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  if (date < earliestDate) {
    return earliestDate;
  }
  if (date > latestDate) {
    return latestDate;
  }
  return date;
}

function offsetDateString(date, days) {
  const parts = parseDateParts(date);
  if (!parts) {
    return date;
  }
  const next = new Date(parts.year, parts.month - 1, parts.day);
  next.setDate(next.getDate() + days);
  return formatDate(clampDate(next));
}

function buildPaths(date) {
  return {
    jsonPath: `${JSON_CDN_BASE}/${date}.json`,
    imagePath: `${IMAGE_CDN_BASE}/${date}.png`,
  };
}

async function loadPayload(date) {
  if (payloadCache.has(date)) {
    return payloadCache.get(date);
  }
  const { jsonPath, imagePath } = buildPaths(date);
  const response = await fetch(jsonPath, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`missing:${date}`);
  }
  const payload = await response.json();
  const payloadEntry = {
    payload,
    jsonPath,
    imagePath,
  };
  payloadCache.set(date, payloadEntry);
  return payloadEntry;
}

async function findAvailableDate(startDate, step) {
  const startParts = parseDateParts(startDate);
  const earliestParts = parseDateParts(EARLIEST_DATE);
  if (!startParts || !earliestParts) {
    return null;
  }
  const today = clampDate(new Date());
  let cursor = clampDate(new Date(startParts.year, startParts.month - 1, startParts.day));
  const earliest = new Date(earliestParts.year, earliestParts.month - 1, earliestParts.day);

  while (cursor >= earliest && cursor <= today) {
    const candidate = formatDate(cursor);
    try {
      await loadPayload(candidate);
      return candidate;
    } catch (error) {
      if (!(error instanceof Error) || !error.message.startsWith("missing:")) {
        throw error;
      }
    }
    cursor.setDate(cursor.getDate() + step);
  }
  return null;
}

function syncNavigationButtons() {
  const prevButton = document.getElementById("prev-button");
  const nextButton = document.getElementById("next-button");
  prevButton.disabled = state.currentDate <= EARLIEST_DATE;
  nextButton.disabled = state.currentDate >= (state.latestAvailableDate || state.currentDate);
}

async function refreshLatestAvailableDate() {
  const today = formatDate(clampDate(new Date()));
  if (state.latestCheckedDate === today && state.latestAvailableDate) {
    return state.latestAvailableDate;
  }

  state.latestCheckedDate = today;
  state.latestAvailableDate = (await findAvailableDate(today, -1)) || "";
  return state.latestAvailableDate;
}

async function renderDate(date) {
  const resolvedDate = await findAvailableDate(date, -1);
  if (!resolvedDate) {
    document.getElementById("json-panel").textContent = "预览数据不可用";
    return;
  }
  const { payload, jsonPath, imagePath } = await loadPayload(resolvedDate);

  state.currentDate = resolvedDate;
  const latestAvailableDate = await refreshLatestAvailableDate();
  if (!latestAvailableDate || resolvedDate > latestAvailableDate) {
    state.latestAvailableDate = resolvedDate;
  }
  writeUrl(resolvedDate);
  document.body.dataset.theme = themeNameForDate(resolvedDate);

  document.getElementById("stage-date-label").textContent = resolvedDate;
  document.getElementById("preview-image").src = imagePath;
  document.getElementById("open-image-link").href = imagePath;
  document.getElementById("open-json-link").href = jsonPath;
  document.getElementById("json-panel").textContent = JSON.stringify(payload, null, 2);
  syncNavigationButtons();
}

function bindNavigation() {
  document.getElementById("prev-button").addEventListener("click", async () => {
    await renderDate(offsetDateString(state.currentDate, -1));
  });

  document.getElementById("next-button").addEventListener("click", async () => {
    const nextDate = offsetDateString(state.currentDate, 1);
    try {
      await renderDate(nextDate);
    } catch (error) {
      document.getElementById("json-panel").textContent = String(error);
    }
  });
}

async function bootstrap() {
  bindNavigation();
  await renderDate(pickInitialDate());
}

bootstrap().catch((error) => {
  document.getElementById("json-panel").textContent = String(error);
});
