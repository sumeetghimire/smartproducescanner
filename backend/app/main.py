from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import CONFIDENCE_THRESHOLD, FRONTEND_DIR
from .fruit_info import get_fruit_info, get_ripeness_note
from .inference import classify, decode_image
from .ripeness import estimate_ripeness
from .schemas import PredictionResponse

app = FastAPI(title="Smart Produce Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    raw_bytes = await file.read()

    try:
        image_bgr = decode_image(raw_bytes)
    except ValueError as exc:
        return PredictionResponse(accepted=False, message=str(exc))

    label, confidence = classify(image_bgr)

    if confidence < CONFIDENCE_THRESHOLD:
        return PredictionResponse(
            accepted=False,
            message=(
                "Image not recognised with enough confidence. Please try a "
                "clearer photo of a single apple or banana."
            ),
            confidence=confidence,
        )

    ripeness_result = estimate_ripeness(image_bgr, label)
    ripeness_stage = ripeness_result["stage"]
    ripeness_note = get_ripeness_note(label, ripeness_stage)
    info = get_fruit_info(label)

    article = "an" if label[0] in "aeiou" else "a"
    speech_text = (
        f"This looks like {article} {label} with {confidence * 100:.0f} percent confidence. "
        f"{ripeness_note} "
        f"It has about {info['nutrition']['calories_kcal']} calories per 100 grams."
    )

    return PredictionResponse(
        accepted=True,
        message="Prediction successful.",
        label=label,
        confidence=confidence,
        ripeness=ripeness_stage,
        ripeness_note=ripeness_note,
        ripeness_method=ripeness_result["method"],
        info=info,
        speech_text=speech_text,
    )


# Serve the browser frontend (static files) at the root path.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
