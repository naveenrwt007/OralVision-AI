from pathlib import Path
from uuid import uuid4

import numpy as np
import torch

from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import (
    show_cam_on_image,
)
from pytorch_grad_cam.utils.model_targets import (
    ClassifierOutputTarget,
)

from app.core.config import (
    IMAGE_SIZE,
    MEDICAL_DISCLAIMER,
    OUTPUT_DIR,
)
from app.services.model_loader import (
    CLASS_NAMES,
    DEVICE,
    IMAGE_TRANSFORM,
    MODEL,
)


def get_confidence_level(
    confidence: float,
) -> str:
    if confidence >= 0.90:
        return "high"

    if confidence >= 0.70:
        return "medium"

    return "low"


def get_screening_message(
    prediction: str,
) -> str:
    if prediction.upper() == "CANCER":
        return (
            "The image contains features that the AI model "
            "associated with the cancer class. Please consult "
            "a qualified medical professional."
        )

    return (
        "The image was classified as non-cancer by the AI model. "
        "This result does not rule out disease. Seek medical "
        "evaluation for persistent or suspicious symptoms."
    )


def prepare_image(
    image: Image.Image,
) -> tuple[Image.Image, torch.Tensor]:
    resized_image = image.resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    )

    input_tensor = IMAGE_TRANSFORM(
        image
    ).unsqueeze(0).to(DEVICE)

    return resized_image, input_tensor


def predict_image(
    image: Image.Image,
) -> dict:
    _, input_tensor = prepare_image(image)

    with torch.no_grad():
        output = MODEL(input_tensor)

        probabilities = torch.softmax(
            output,
            dim=1,
        )

        predicted_index = torch.argmax(
            probabilities,
            dim=1,
        ).item()

        confidence = probabilities[
            0,
            predicted_index,
        ].item()

    prediction = CLASS_NAMES[predicted_index]

    all_probabilities = {
        class_name: round(
            float(probabilities[0, index].item()),
            4,
        )
        for index, class_name in enumerate(
            CLASS_NAMES
        )
    }

    return {
        "prediction": prediction,
        "predicted_index": predicted_index,
        "confidence": round(confidence, 4),
        "confidence_percent": round(
            confidence * 100,
            2,
        ),
        "confidence_level": get_confidence_level(
            confidence
        ),
        "probabilities": all_probabilities,
        "message": get_screening_message(
            prediction
        ),
        "disclaimer": MEDICAL_DISCLAIMER,
    }


def generate_gradcam(
    image: Image.Image,
    predicted_index: int,
) -> dict:
    resized_image, input_tensor = prepare_image(
        image
    )

    target_layers = [
        MODEL.features[-1]
    ]

    cam = GradCAM(
        model=MODEL,
        target_layers=target_layers,
    )

    targets = [
        ClassifierOutputTarget(
            predicted_index
        )
    ]

    grayscale_cam = cam(
        input_tensor=input_tensor,
        targets=targets,
    )[0]

    rgb_image = np.array(
        resized_image
    ).astype(np.float32) / 255.0

    overlay = show_cam_on_image(
        rgb_image,
        grayscale_cam,
        use_rgb=True,
    )

    output_filename = (
        f"{uuid4().hex}_gradcam.png"
    )

    output_path = (
        OUTPUT_DIR
        / output_filename
    )

    Image.fromarray(
        overlay
    ).save(output_path)

    return {
        "filename": output_filename,
        "path": str(output_path),
        "url": f"/outputs/{output_filename}",
    }


def run_screening(
    image: Image.Image,
) -> dict:
    prediction_result = predict_image(image)

    gradcam_result = generate_gradcam(
        image=image,
        predicted_index=prediction_result[
            "predicted_index"
        ],
    )

    prediction_result.pop(
        "predicted_index"
    )

    prediction_result["gradcam"] = (
        gradcam_result
    )

    return prediction_result