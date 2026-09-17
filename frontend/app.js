const dropZone = document.getElementById("drop-zone");
const dropZoneText = document.getElementById("drop-zone-text");
const fileInput = document.getElementById("file-input");
const preview = document.getElementById("preview");
const scanBtn = document.getElementById("scan-btn");
const statusEl = document.getElementById("status");

const resultCard = document.getElementById("result-card");
const resultTitle = document.getElementById("result-title");
const resultConfidence = document.getElementById("result-confidence");
const ripenessNote = document.getElementById("ripeness-note");
const nutritionTable = document.getElementById("nutrition-table");
const healthList = document.getElementById("health-list");
const usageList = document.getElementById("usage-list");
const speakBtn = document.getElementById("speak-btn");

let selectedFile = null;
let lastSpeechText = "";

const NUTRITION_LABELS = {
  calories_kcal: "Calories",
  carbs_g: "Carbs",
  sugar_g: "Sugar",
  fiber_g: "Fibre",
  vitamin_c_mg: "Vitamin C",
  potassium_mg: "Potassium",
};

const NUTRITION_UNITS = {
  calories_kcal: "kcal",
  carbs_g: "g",
  sugar_g: "g",
  fiber_g: "g",
  vitamin_c_mg: "mg",
  potassium_mg: "mg",
};

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function handleFile(file) {
  if (!file || !file.type.startsWith("image/")) {
    setStatus("Please choose an image file.", true);
    return;
  }
  selectedFile = file;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  dropZoneText.textContent = file.name;
  scanBtn.disabled = false;
  setStatus("");
  resultCard.hidden = true;
}

dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});
fileInput.addEventListener("change", () => handleFile(fileInput.files[0]));

["dragenter", "dragover"].forEach((evt) =>
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
  })
);
dropZone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  handleFile(file);
});

scanBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  scanBtn.disabled = true;
  setStatus("Scanning…");
  resultCard.hidden = true;

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch("/api/predict", { method: "POST", body: formData });
    const data = await res.json();

    if (!data.accepted) {
      setStatus(data.message || "Could not identify the fruit.", true);
      scanBtn.disabled = false;
      return;
    }

    setStatus("");
    renderResult(data);
  } catch (err) {
    console.error(err);
    setStatus("Something went wrong talking to the server.", true);
  } finally {
    scanBtn.disabled = false;
  }
});

function renderResult(data) {
  resultTitle.textContent = `${data.label} — ${data.ripeness}`;
  resultConfidence.textContent = `${Math.round(data.confidence * 100)}% confident`;
  ripenessNote.textContent = data.ripeness_note || "";

  nutritionTable.innerHTML = "";
  Object.entries(data.info.nutrition).forEach(([key, value]) => {
    const label = NUTRITION_LABELS[key] || key;
    const unit = NUTRITION_UNITS[key] || "";
    const row = document.createElement("tr");
    row.innerHTML = `<td>${label}</td><td>${value} ${unit}</td>`;
    nutritionTable.appendChild(row);
  });

  healthList.innerHTML = "";
  data.info.health_benefits.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    healthList.appendChild(li);
  });

  usageList.innerHTML = "";
  data.info.usage_suggestions.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    usageList.appendChild(li);
  });

  lastSpeechText = data.speech_text || "";
  resultCard.hidden = false;
  resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

speakBtn.addEventListener("click", () => {
  if (!lastSpeechText) return;
  if (!("speechSynthesis" in window)) {
    setStatus("Speech output is not supported in this browser.", true);
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(lastSpeechText);
  window.speechSynthesis.speak(utterance);
});
