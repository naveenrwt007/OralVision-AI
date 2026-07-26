from io import BytesIO

import cv2
import numpy as np

from PIL import Image, UnidentifiedImageError


def validate_image_bytes(
    image_bytes: bytes,
) -> Image.Image:
    try:
        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        image.load()

        return image

    except UnidentifiedImageError as error:
        raise ValueError(
            "The uploaded file is not a valid image."
        ) from error

    except Exception as error:
        raise ValueError(
            f"Unable to read uploaded image: {error}"
        ) from error


def calculate_blur_score(
    image: Image.Image,
) -> float:
    image_array = np.array(image)

    gray_image = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY,
    )

    blur_score = cv2.Laplacian(
        gray_image,
        cv2.CV_64F,
    ).var()

    return float(blur_score)


def assess_image_quality(
    image: Image.Image,
) -> dict:
    width, height = image.size
    blur_score = calculate_blur_score(image)

    issues = []

    if width < 224 or height < 224:
        issues.append(
            "Image resolution is lower than recommended."
        )

    if blur_score < 40:
        issues.append(
            "The image appears blurry."
        )

    quality_status = (
        "acceptable"
        if not issues
        else "warning"
    )

    return {
        "status": quality_status,
        "width": width,
        "height": height,
        "blur_score": round(blur_score, 2),
        "issues": issues,
    }