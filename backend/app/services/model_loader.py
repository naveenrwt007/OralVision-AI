import torch
import torch.nn as nn

from torchvision import models, transforms

from app.core.config import IMAGE_SIZE, MODEL_PATH


DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at: {MODEL_PATH}"
        )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
    )

    class_names = checkpoint.get("class_names")
    class_to_idx = checkpoint.get("class_to_idx")

    if class_names is None:
        raise KeyError(
            "The checkpoint does not contain 'class_names'."
        )

    model = models.efficientnet_b0(
        weights=None
    )

    input_features = model.classifier[1].in_features

    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(
            input_features,
            len(class_names),
        ),
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(DEVICE)
    model.eval()

    return model, class_names, class_to_idx


MODEL, CLASS_NAMES, CLASS_TO_IDX = load_model()


IMAGE_TRANSFORM = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])