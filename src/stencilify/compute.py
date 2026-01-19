"""Compute backend adapter for CPU/GPU operations."""

import logging
from enum import Enum

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to import GPU dependencies
try:
    import kornia  # type: ignore[import-not-found]
    import torch  # type: ignore[import-not-found]

    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    torch = None
    kornia = None


class Device(str, Enum):
    """Compute device options."""

    CPU = "cpu"
    CUDA = "cuda"
    AUTO = "auto"


def get_device(device: Device) -> str:
    """
    Determine compute device to use.

    Args:
        device: Requested device (cpu, cuda, or auto)

    Returns:
        Device string: "cpu" or "cuda"
    """
    if device == Device.CPU:
        return "cpu"

    if device == Device.CUDA:
        if not GPU_AVAILABLE:
            logger.warning(
                "CUDA requested but GPU dependencies (torch, kornia) not available. "
                "Falling back to CPU. Install with: uv sync --extra gpu"
            )
            return "cpu"

        if not torch.cuda.is_available():
            logger.warning(
                "CUDA requested but no CUDA device found. Falling back to CPU."
            )
            return "cpu"

        logger.info("Using CUDA device")
        return "cuda"

    # AUTO mode
    if device == Device.AUTO:
        if GPU_AVAILABLE and torch.cuda.is_available():
            logger.info("Auto-detected CUDA device")
            return "cuda"
        else:
            logger.info("Using CPU device (CUDA not available)")
            return "cpu"

    return "cpu"


def bilateral_filter(
    image: np.ndarray,
    d: int,
    sigma_color: float,
    sigma_space: float,
    device: str = "cpu",
) -> np.ndarray:
    """
    Apply bilateral filter for edge-preserving smoothing.

    Uses GPU acceleration if available and device is "cuda", otherwise falls back to OpenCV.

    Args:
        image: Input image [H, W, 3] uint8
        d: Diameter of pixel neighborhood
        sigma_color: Filter sigma in color space
        sigma_space: Filter sigma in coordinate space
        device: Device to use ("cpu" or "cuda")

    Returns:
        Filtered image [H, W, 3] uint8
    """
    if device == "cuda" and GPU_AVAILABLE and torch.cuda.is_available():
        try:
            # Convert to torch tensor [H, W, 3] -> [1, 3, H, W]
            img_tensor = torch.from_numpy(image).float().permute(2, 0, 1).unsqueeze(0)
            img_tensor = img_tensor.to("cuda") / 255.0

            # Apply bilateral filter
            filtered = kornia.filters.bilateral_blur(
                img_tensor,
                kernel_size=(d, d),
                sigma_color=sigma_color,
                sigma_space=(sigma_space, sigma_space),
            )

            # Convert back to numpy [1, 3, H, W] -> [H, W, 3]
            result = (filtered.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(
                np.uint8
            )

            logger.debug(f"Applied bilateral filter on GPU (d={d})")
            return result  # type: ignore[no-any-return]

        except Exception as e:
            logger.warning(f"GPU bilateral filter failed: {e}. Falling back to CPU.")
            # Fall through to CPU implementation

    # CPU fallback using OpenCV
    result = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
    logger.debug(f"Applied bilateral filter on CPU (d={d})")
    return result


def gaussian_blur(
    image: np.ndarray,
    kernel_size: int,
    sigma: float,
    device: str = "cpu",
) -> np.ndarray:
    """
    Apply Gaussian blur.

    Uses GPU acceleration if available and device is "cuda", otherwise falls back to OpenCV.

    Args:
        image: Input image [H, W, 3] or [H, W] uint8
        kernel_size: Size of Gaussian kernel (must be odd)
        sigma: Gaussian kernel standard deviation
        device: Device to use ("cpu" or "cuda")

    Returns:
        Blurred image, same shape as input, uint8
    """
    if device == "cuda" and GPU_AVAILABLE and torch.cuda.is_available():
        try:
            # Handle both grayscale and RGB
            is_gray = image.ndim == 2
            img_for_gpu = image[:, :, np.newaxis] if is_gray else image

            # Convert to torch tensor [H, W, C] -> [1, C, H, W]
            img_tensor = (
                torch.from_numpy(img_for_gpu).float().permute(2, 0, 1).unsqueeze(0)
            )
            img_tensor = img_tensor.to("cuda") / 255.0

            # Apply Gaussian blur
            filtered = kornia.filters.gaussian_blur2d(
                img_tensor,
                kernel_size=(kernel_size, kernel_size),
                sigma=(sigma, sigma),
            )

            # Convert back to numpy [1, C, H, W] -> [H, W, C]
            result = (filtered.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(
                np.uint8
            )

            if is_gray:
                result = result[:, :, 0]

            logger.debug(f"Applied Gaussian blur on GPU (kernel={kernel_size})")
            return result  # type: ignore[no-any-return]

        except Exception as e:
            logger.warning(f"GPU Gaussian blur failed: {e}. Falling back to CPU.")
            # Fall through to CPU implementation

    # CPU fallback using OpenCV
    result = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
    logger.debug(f"Applied Gaussian blur on CPU (kernel={kernel_size})")
    return result


def rgb_to_lab_batch(rgb_batch: np.ndarray, device: str = "cpu") -> np.ndarray:
    """
    Convert RGB to Lab color space (batch processing).

    Uses GPU acceleration if available, otherwise falls back to OpenCV.

    Note: SLIC superpixels, connected components, and contouring remain on CPU
    because they have complex dependencies and CPU implementations are well-optimized.

    Args:
        rgb_batch: RGB images [B, H, W, 3] float32 in range [0, 1]
        device: Device to use ("cpu" or "cuda")

    Returns:
        Lab images [B, H, W, 3] float32
    """
    if device == "cuda" and GPU_AVAILABLE and torch.cuda.is_available():
        try:
            # Convert to torch tensor [B, H, W, 3] -> [B, 3, H, W]
            rgb_tensor = torch.from_numpy(rgb_batch).float().permute(0, 3, 1, 2)
            rgb_tensor = rgb_tensor.to("cuda")

            # Convert RGB to Lab
            lab_tensor = kornia.color.rgb_to_lab(rgb_tensor)

            # Convert back to numpy [B, 3, H, W] -> [B, H, W, 3]
            result = lab_tensor.permute(0, 2, 3, 1).cpu().numpy()

            logger.debug(f"Converted RGB to Lab on GPU (batch_size={rgb_batch.shape[0]})")
            return result  # type: ignore[no-any-return]

        except Exception as e:
            logger.warning(f"GPU RGB to Lab conversion failed: {e}. Falling back to CPU.")
            # Fall through to CPU implementation

    # CPU fallback using OpenCV
    result = np.zeros_like(rgb_batch)
    for i in range(rgb_batch.shape[0]):
        # OpenCV expects BGR, not RGB
        bgr = cv2.cvtColor((rgb_batch[i] * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab)
        result[i] = lab.astype(np.float32) / [255.0, 255.0, 255.0]

    logger.debug(f"Converted RGB to Lab on CPU (batch_size={rgb_batch.shape[0]})")
    return result
