from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import json
import random
import re
from pathlib import Path
from time import perf_counter
from typing import Any

import cv2
import numpy as np


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def read_image(path: Path, flags: int) -> np.ndarray:
    """Read through a buffer, including Unicode filenames on Windows."""
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), flags)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return image


def write_png(path: Path, image: np.ndarray) -> None:
    # Lossless compression reduces large tiled texture PNGs without changing
    # dimensions or alpha (unlike the former implicit 1000px downsampling).
    encoded_ok, encoded = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not encoded_ok:
        raise ValueError(f"Cannot encode PNG: {path}")
    encoded.tofile(str(path))


def safe_filename_component(value: str, fallback: str = "project") -> str:
    """Return a readable filesystem-safe component for generated filenames."""
    safe_value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value)
    safe_value = re.sub(r"\s+", "_", safe_value).strip(" ._") or fallback
    return re.sub(r"_+", "_", safe_value)[:80]


def dataset_filename_prefix(project_name: str, generation_batch: str) -> str:
    """Return a filesystem-safe ``project_date_batch`` prefix for generated files."""
    safe_project_name = safe_filename_component(project_name)
    safe_generation_batch = safe_filename_component(generation_batch, "batch")
    return f"{safe_project_name}_{safe_generation_batch}"


def write_jpeg(path: Path, image: np.ndarray, quality: int) -> None:
    """Write a JPEG through an encoded buffer so Unicode paths work on Windows."""
    encoded_ok, encoded_image = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not encoded_ok:
        raise ValueError(f"Cannot encode generated image: {path}")
    try:
        encoded_image.tofile(str(path))
    except OSError as exc:
        raise ValueError(f"Cannot write generated image: {path}") from exc


def list_image_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted([p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXTS])


def generate_arc_points(start_u, start_v, end_u, end_v, origin_u, origin_v, radius, sweep, amp_u, amp_v, num_points=20):
    if radius == 0 or sweep == 0:
        return [(end_u, end_v)]
    start_angle = np.arctan2(start_v - origin_v, start_u - origin_u)
    end_angle = np.arctan2(end_v - origin_v, end_u - origin_u)
    angle_diff = end_angle - start_angle
    while angle_diff > np.pi:
        angle_diff -= 2 * np.pi
    while angle_diff < -np.pi:
        angle_diff += 2 * np.pi
    if sweep > np.pi:
        angle_diff = angle_diff - 2 * np.pi if angle_diff > 0 else angle_diff + 2 * np.pi
    elif abs(amp_u) > 0.001 or abs(amp_v) > 0.001:
        mid_u = (start_u + end_u) / 2
        mid_v = (start_v + end_v) / 2
        alt_diff = angle_diff - 2 * np.pi if angle_diff > 0 else angle_diff + 2 * np.pi
        mid_angle_1 = start_angle + angle_diff / 2
        mid_angle_2 = start_angle + alt_diff / 2
        arc_mid_1 = np.array([origin_u + radius * np.cos(mid_angle_1), origin_v + radius * np.sin(mid_angle_1)])
        arc_mid_2 = np.array([origin_u + radius * np.cos(mid_angle_2), origin_v + radius * np.sin(mid_angle_2)])
        expected = np.array([amp_u, amp_v])
        center_mid = np.array([mid_u, mid_v])
        if float((arc_mid_2 - center_mid).dot(expected)) > float((arc_mid_1 - center_mid).dot(expected)):
            angle_diff = alt_diff
    num_pts = max(num_points, int(abs(angle_diff) * 8))
    angles = np.linspace(start_angle, start_angle + angle_diff, num_pts)
    return [(origin_u + radius * np.cos(angle), origin_v + radius * np.sin(angle)) for angle in angles[1:]]


def parse_contour_geometry(contour_text: str) -> list[tuple[float, float]]:
    start_u = re.search(r"START_U=([-\d.]+)", contour_text)
    start_v = re.search(r"START_V=([-\d.]+)", contour_text)
    if not start_u or not start_v:
        return []
    current_u = float(start_u.group(1))
    current_v = float(start_v.group(1))
    points = [(current_u, current_v)]
    segment_pattern = re.compile(
        r"AMP_U=([-\d.]+)\s*\n"
        r"AMP_V=([-\d.]+)\s*\n"
        r"AMP=([-\d.]+)\s*\n"
        r"RADIUS=([-\d.]+)\s*\n"
        r"SWEEP=([-\d.]+)\s*\n"
        r"ORIGIN_U=([-\d.]+)\s*\n"
        r"ORIGIN_V=([-\d.]+)\s*\n"
        r"U=([-\d.]+)\s*\n"
        r"V=([-\d.]+)"
    )
    for seg in segment_pattern.findall(contour_text):
        amp_u, amp_v, _amp, radius, sweep, origin_u, origin_v, end_u, end_v = map(float, seg)
        if radius > 0 and sweep > 0:
            points.extend(generate_arc_points(current_u, current_v, end_u, end_v, origin_u, origin_v, radius, sweep, amp_u, amp_v))
        else:
            points.append((end_u, end_v))
        current_u, current_v = end_u, end_v
    return points


def parse_gen_file(gen_file: Path) -> list[dict[str, Any]]:
    content = gen_file.read_text(encoding="utf-8", errors="ignore")
    parts: list[dict[str, Any]] = []
    for block in content.split("PART_INFORMATION")[1:]:
        work_type = re.search(r"TYPE_OF_WORK=(.*?)\n", block)
        if work_type and work_type.group(1).strip() != "BURNING":
            continue
        name_match = re.search(r"PART_NAME=(.*?)\n", block)
        name = name_match.group(1).strip() if name_match else "Unknown_Part"
        contours = []
        for burn_block in block.split("BURNING_DATA")[1:]:
            shape_match = re.search(r"SHAPE=(.*?)\n", burn_block)
            shape_type = shape_match.group(1).strip() if shape_match else "UNKNOWN"
            if "HOOK" in shape_type or shape_type == "CUT_LINE":
                continue
            contour_match = re.search(r"START_OF_CONTOUR(.*?)END_OF_CONTOUR", burn_block, re.DOTALL)
            if not contour_match:
                continue
            points = parse_contour_geometry(contour_match.group(1))
            if len(points) >= 3:
                contours.append({"type": shape_type, "points": np.array(points, dtype=np.float32)})
        if contours:
            parts.append({"name": name, "contours": contours})
    return parts


def point_in_polygon(point: tuple[float, float], polygon: np.ndarray) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        denom = yj - yi if abs(yj - yi) > 1e-9 else 1e-9
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / denom + xi):
            inside = not inside
        j = i
    return inside


def hole_inside_outer(hole: np.ndarray, outer: np.ndarray, tolerance: float = 5.0) -> bool:
    h_min_x, h_min_y = hole.min(axis=0)
    h_max_x, h_max_y = hole.max(axis=0)
    o_min_x, o_min_y = outer.min(axis=0)
    o_max_x, o_max_y = outer.max(axis=0)
    if h_min_x < o_min_x - tolerance or h_max_x > o_max_x + tolerance:
        return False
    if h_min_y < o_min_y - tolerance or h_max_y > o_max_y + tolerance:
        return False
    centroid = tuple(hole.mean(axis=0))
    return point_in_polygon(centroid, outer) or point_in_polygon(tuple(hole[0]), outer)


def extract_gen_masks(
    gen_file: Path,
    output_dir: Path,
    scale: float = 5.0,
    padding: int = 20,
    min_width_mm: float = 10.0,
    min_height_mm: float = 10.0,
    min_area_mm2: float = 100.0,
    max_aspect_ratio: float = 20.0,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    parsed = parse_gen_file(gen_file)
    outer_contours: list[dict[str, Any]] = []
    hole_contours: list[dict[str, Any]] = []
    for part in parsed:
        for contour in part["contours"]:
            item = {"name": part["name"], "contour": contour}
            if "OUTER" in contour["type"]:
                outer_contours.append(item)
            else:
                hole_contours.append(item)

    saved: list[Path] = []
    matched_holes: set[int] = set()
    for outer_item in outer_contours:
        outer = outer_item["contour"]["points"]
        holes = []
        for idx, hole_item in enumerate(hole_contours):
            if idx in matched_holes:
                continue
            if hole_inside_outer(hole_item["contour"]["points"], outer):
                holes.append(hole_item["contour"]["points"])
                matched_holes.add(idx)

        min_x, min_y = outer.min(axis=0)
        max_x, max_y = outer.max(axis=0)
        width_mm = float(max_x - min_x)
        height_mm = float(max_y - min_y)
        area_mm2 = width_mm * height_mm
        aspect = max(width_mm, height_mm) / max(min(width_mm, height_mm), 1e-9)
        if width_mm < min_width_mm or height_mm < min_height_mm or area_mm2 < min_area_mm2 or aspect > max_aspect_ratio:
            continue

        img_w = max(1, int(width_mm * scale) + padding * 2)
        img_h = max(1, int(height_mm * scale) + padding * 2)
        mask = np.zeros((img_h, img_w), dtype=np.uint8)
        outer_pts = ((outer - [min_x, min_y]) * scale + padding).astype(np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [outer_pts], 255)
        for hole in holes:
            hole_pts = ((hole - [min_x, min_y]) * scale + padding).astype(np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(mask, [hole_pts], 0)

        safe = re.sub(r"[^A-Za-z0-9_\-\u4e00-\u9fff]+", "_", outer_item["name"])
        out = output_dir / f"{len(saved):04d}_{safe}.png"
        cv2.imwrite(str(out), mask)
        saved.append(out)
    return saved


def extract_edge_masks(
    edge_image_path: Path,
    output_dir: Path,
    min_area: int = 5000,
    dilation_size: int = 3,
    edge_polarity: str = "auto",
) -> list[Path]:
    """Fill closed cut outlines; nested cut loops alternate material and holes.

    ``dilation_size`` is retained for existing clients, but now controls gap
    closing (dilation followed by erosion), not permanent edge thickening.
    Open strokes are ignored. Outputs use source pixels, cropped with 5px
    padding clipped to the source canvas; they are never rescaled.
    """
    if min_area < 1:
        raise ValueError("min_area must be positive")
    if dilation_size < 1 or dilation_size > 21 or dilation_size % 2 == 0:
        raise ValueError("Gap repair size must be an odd number between 1 and 21")
    if edge_polarity not in {"auto", "white", "black"}:
        raise ValueError("edge_polarity must be auto, white or black")
    edge_img = read_image(edge_image_path, cv2.IMREAD_GRAYSCALE)
    if int(edge_img.min()) == int(edge_img.max()):
        raise ValueError("No edges found in the input image")
    _, edges = cv2.threshold(edge_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Thin cut lines normally occupy less of the canvas than the background.
    if edge_polarity == "black" or (edge_polarity == "auto" and cv2.countNonZero(edges) > edges.size / 2):
        edges = cv2.bitwise_not(edges)
    if dilation_size > 1:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (dilation_size, dilation_size))
        # Padding prevents morphology's default border handling from joining
        # nearby open strokes through the canvas boundary.
        edges = cv2.copyMakeBorder(edges, dilation_size, dilation_size, dilation_size, dilation_size, cv2.BORDER_CONSTANT, value=0)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = edges[dilation_size:-dilation_size, dilation_size:-dilation_size]

    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        raise ValueError("No closed outlines found; check edge polarity and gaps")
    tree = hierarchy[0]
    depths = []
    for entry in tree:
        depth, parent = 0, int(entry[3])
        while parent != -1:
            depth += 1
            parent = int(tree[parent][3])
        depths.append(depth)

    output_dir.mkdir(parents=True, exist_ok=True)
    h, w = edges.shape
    saved: list[Path] = []
    for index, contour in enumerate(contours):
        # Each closed stroke has an outside and inside contour. Material
        # boundaries are at depths 0, 4, ...; holes at depths 2, 6, ... .
        # Requiring an inside contour avoids filling an arbitrary open stroke.
        if depths[index] % 4 != 0 or tree[index][2] == -1:
            continue
        x, y, bw, bh = cv2.boundingRect(contour)
        x1, y1 = max(0, x - 5), max(0, y - 5)
        x2, y2 = min(w, x + bw + 5), min(h, y + bh + 5)
        mask = np.zeros((y2 - y1, x2 - x1), dtype=np.uint8)
        cv2.drawContours(mask, contours, index, 255, cv2.FILLED, offset=(-x1, -y1))
        interior = int(tree[index][2])
        while interior != -1:
            hole = int(tree[interior][2])
            while hole != -1:
                if tree[hole][2] != -1:
                    cv2.drawContours(mask, contours, hole, 0, cv2.FILLED, offset=(-x1, -y1))
                hole = int(tree[hole][0])
            interior = int(tree[interior][0])
        # Filter material components only. Small holes must stay transparent.
        if cv2.countNonZero(mask) < min_area:
            continue
        out = output_dir / f"{edge_image_path.stem}_part_{len(saved):04d}.png"
        write_png(out, mask)
        saved.append(out)
    if not saved:
        raise ValueError("No closed parts meet min_area; check edge polarity, gaps and minimum area")
    return saved


def detect_red_edges(image: np.ndarray, saturation_min: int = 80, value_min: int = 80) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, saturation_min, value_min])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, saturation_min, value_min])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    return cv2.bitwise_or(mask1, mask2)


def extract_redline_masks(
    image_path: Path,
    output_dir: Path,
    min_area: int = 3000,
    dilation_size: int = 5,
    dilation_iterations: int = 2,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Cannot read redline image: {image_path}")

    h, w = image.shape[:2]
    red_mask = detect_red_edges(image)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilation_size, dilation_size))
    red_mask = cv2.dilate(red_mask, kernel, iterations=dilation_iterations)
    non_red_mask = cv2.bitwise_not(red_mask)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(non_red_mask, connectivity=8)

    background_labels: set[int] = set()
    for label in range(1, num_labels):
        label_mask = labels == label
        if label_mask[0, :].any() or label_mask[-1, :].any() or label_mask[:, 0].any() or label_mask[:, -1].any():
            background_labels.add(label)
        if stats[label, cv2.CC_STAT_AREA] > h * w * 0.3:
            background_labels.add(label)

    saved: list[Path] = []
    base_name = image_path.stem.replace("_edge", "")
    for label in range(1, num_labels):
        if label in background_labels:
            continue
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        bw = int(stats[label, cv2.CC_STAT_WIDTH])
        bh = int(stats[label, cv2.CC_STAT_HEIGHT])
        margin = 5
        x1 = max(0, x - margin)
        y1 = max(0, y - margin)
        x2 = min(w, x + bw + margin)
        y2 = min(h, y + bh + margin)
        mask = ((labels == label).astype(np.uint8) * 255)[y1:y2, x1:x2]
        out = output_dir / f"{base_name}_part_{len(saved):04d}.png"
        cv2.imwrite(str(out), mask)
        saved.append(out)
    return saved


def resolve_texture_fit(texture_fit: str | None, random_crop: bool = True) -> str:
    """Explicit fill mode wins; retain the meaning of historical task params."""
    if texture_fit is None:
        return "tile" if random_crop else "stretch"
    if texture_fit not in ("tile", "stretch"):
        raise ValueError("texture_fit must be 'tile' or 'stretch'")
    return texture_fit


def texture_masks(
    mask_dir: Path,
    texture_path: Path,
    output_dir: Path,
    random_crop: bool = True,
    max_side_pixels: int = 0,
    project_name: str = "project",
    texture_fit: str | None = None,
) -> list[Path]:
    return texture_mask_files(
        list_image_files(mask_dir),
        texture_path,
        output_dir,
        random_crop,
        max_side_pixels,
        project_name,
        texture_fit=texture_fit,
    )


def texture_mask_files(
    mask_files: list[Path],
    texture_path: Path,
    output_dir: Path,
    random_crop: bool = True,
    max_side_pixels: int = 0,
    project_name: str = "project",
    texture_fit: str | None = None,
) -> list[Path]:
    """Fill using original texture pixels or stretch width/height to the mask."""
    fill_mode = resolve_texture_fit(texture_fit, random_crop)
    if max_side_pixels < 0:
        raise ValueError("max_side_pixels must be zero (original size) or positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    texture = read_image(texture_path, cv2.IMREAD_COLOR)

    saved: list[Path] = []
    for idx, mask_path in enumerate(mask_files, start=1):
        mask = read_image(mask_path, cv2.IMREAD_GRAYSCALE)
        h_mask, w_mask = mask.shape
        h_tex, w_tex = texture.shape[:2]

        if fill_mode == "tile":
            x0 = random.randint(0, w_tex - w_mask) if w_tex >= w_mask else random.randrange(w_tex)
            y0 = random.randint(0, h_tex - h_mask) if h_tex >= h_mask else random.randrange(h_tex)
            # Allocate only the required crop, rather than a much larger tiled
            # texture for long parts such as the 11992px Wuxue inputs.
            ys = (np.arange(h_mask) + y0) % h_tex
            xs = (np.arange(w_mask) + x0) % w_tex
            crop = texture[ys[:, None], xs[None, :]]
        else:
            crop = cv2.resize(texture, (w_mask, h_mask), interpolation=cv2.INTER_LINEAR)

        b, g, r = cv2.split(crop)
        rgba = cv2.merge([b, g, r, mask])
        max_side = max(rgba.shape[:2])
        if max_side_pixels and max_side > max_side_pixels:
            scale = max_side_pixels / max_side
            rgba = cv2.resize(rgba, (max(1, round(w_mask * scale)), max(1, round(h_mask * scale))), interpolation=cv2.INTER_AREA)

        out = output_dir / f"{safe_filename_component(project_name)}_part_{idx:04d}.png"
        write_png(out, rgba)
        saved.append(out)
    return saved


def ensure_rgba(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    if image.shape[2] == 4:
        return image
    alpha = np.full(image.shape[:2], 255, dtype=np.uint8)
    return cv2.merge([image[:, :, 0], image[:, :, 1], image[:, :, 2], alpha])


def rotate_image_with_alpha(img: np.ndarray, angle: float) -> np.ndarray:
    img = ensure_rgba(img)
    if angle % 360 == 0:
        return img
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    matrix[0, 2] += new_w / 2 - center[0]
    matrix[1, 2] += new_h / 2 - center[1]
    return cv2.warpAffine(img, matrix, (new_w, new_h), borderValue=(0, 0, 0, 0))


def overlay_image_alpha(background: np.ndarray, overlay: np.ndarray, x: int, y: int) -> np.ndarray:
    overlay = ensure_rgba(overlay)
    h, w = overlay.shape[:2]
    if x < 0 or y < 0 or x + w > background.shape[1] or y + h > background.shape[0]:
        return background
    alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0
    roi = background[y:y + h, x:x + w]
    blended = overlay[:, :, :3].astype(np.float32) * alpha + roi.astype(np.float32) * (1.0 - alpha)
    background[y:y + h, x:x + w] = blended.astype(np.uint8)
    return background


def tight_bbox_from_alpha(img: np.ndarray, alpha_thresh: int = 10) -> tuple[int, int, int, int] | None:
    img = ensure_rgba(img)
    ys, xs = np.where(img[:, :, 3] > alpha_thresh)
    if len(xs) == 0 or len(ys) == 0:
        return None
    xmin, xmax = int(xs.min()), int(xs.max())
    ymin, ymax = int(ys.min()), int(ys.max())
    return xmin, ymin, xmax - xmin + 1, ymax - ymin + 1


def check_collision(box: tuple[int, int, int, int], placed: list[tuple[int, int, int, int]]) -> bool:
    x1, y1, w1, h1 = box
    for x2, y2, w2, h2 in placed:
        if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
            return True
    return False


def yolo_hbb(img_w: int, img_h: int, box: tuple[int, int, int, int]) -> list[float]:
    x, y, w, h = box
    return [(x + w / 2) / img_w, (y + h / 2) / img_h, w / img_w, h / img_h]


def order_obb_points(points: np.ndarray) -> np.ndarray:
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    ordered = points[np.argsort(angles)]
    start_idx = np.argmin(ordered[:, 0] + ordered[:, 1])
    return np.roll(ordered, -start_idx, axis=0)


def local_obb_from_alpha(img: np.ndarray, alpha_thresh: int = 10) -> np.ndarray | None:
    img = ensure_rgba(img)
    _, binary = cv2.threshold(img[:, :, 3], alpha_thresh, 255, cv2.THRESH_BINARY)
    points = cv2.findNonZero(binary)
    if points is None or len(points) < 4:
        return None
    rect = cv2.minAreaRect(points)
    return order_obb_points(cv2.boxPoints(rect).astype(np.float32))


def yolo_obb(img_w: int, img_h: int, local_points: np.ndarray, x: int, y: int) -> list[float]:
    points = local_points.copy()
    points[:, 0] += x
    points[:, 1] += y
    points[:, 0] = np.clip(points[:, 0] / img_w, 0.0, 1.0)
    points[:, 1] = np.clip(points[:, 1] / img_h, 0.0, 1.0)
    return points.flatten().tolist()


def mask_to_coco_annotation(
    mask: np.ndarray,
    image_id: int,
    annotation_id: int,
    category_id: int = 0,
    offset_x: int = 0,
    offset_y: int = 0,
) -> dict[str, Any] | None:
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None or len(contours) == 0:
        return None
    segmentation: list[list[float]] = []
    for idx, contour in enumerate(contours):
        if cv2.contourArea(contour) < 20:
            continue
        epsilon = 0.001 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        points = approx.reshape(-1, 2)
        if len(points) < 3:
            continue
        is_outer = hierarchy[0][idx][3] == -1
        signed_area = cv2.contourArea(approx, oriented=True)
        if is_outer and signed_area > 0:
            points = points[::-1]
        if not is_outer and signed_area < 0:
            points = points[::-1]
        points = points.astype(float)
        points[:, 0] += offset_x
        points[:, 1] += offset_y
        segmentation.append(points.flatten().tolist())
    if not segmentation:
        return None
    x, y, w, h = cv2.boundingRect(mask)
    return {
        "id": annotation_id,
        "image_id": image_id,
        "category_id": category_id,
        "segmentation": segmentation,
        "area": float(np.count_nonzero(mask > 127)),
        "bbox": [float(x + offset_x), float(y + offset_y), float(w), float(h)],
        "iscrowd": 0,
    }


def prepare_part(source: Path | np.ndarray, angle: float, scale: float, max_w: int, max_h: int) -> np.ndarray | None:
    if isinstance(source, Path):
        img = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
        if img is None:
            return None
    else:
        img = source
    if scale <= 0 or max_w < 1 or max_h < 1:
        raise ValueError("Part scale and placement dimensions must be positive")
    img = rotate_image_with_alpha(img, angle)
    h, w = img.shape[:2]
    target_w, target_h = max(1, int(w * scale)), max(1, int(h * scale))
    if target_w > max_w or target_h > max_h:
        limit = min(max_w / target_w, max_h / target_h) * 0.95
        target_w, target_h = max(1, int(target_w * limit)), max(1, int(target_h * limit))
    # Compute the fitted size before allocating. A 11992px part at scale 10
    # must not become a 119920px intermediate merely to fit a 3648px canvas.
    if (target_w, target_h) != (w, h):
        img = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_AREA)
    return img


def placement_candidates(
    layout_mode: str,
    bg_w: int,
    bg_h: int,
    part_w: int,
    part_h: int,
    margins: dict[str, int],
    placed_boxes: list[tuple[int, int, int, int]] | None = None,
    compact_limit: int = 1200,
):
    left = margins["left"]
    top = margins["top"]
    right = bg_w - margins["right"] - part_w
    bottom = bg_h - margins["bottom"] - part_h
    if right < left or bottom < top:
        return []
    if layout_mode in {"compact", "mixed"}:
        candidates: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()

        def add_candidate(x: int, y: int) -> bool:
            if x < left or x > right or y < top or y > bottom or (x, y) in seen:
                return False
            seen.add((x, y))
            candidates.append((x, y))
            return len(candidates) >= compact_limit

        # Prefer positions adjacent to existing pieces. This produces a dense layout
        # without constructing an exhaustive grid for the entire background.
        add_candidate(left, top)
        for x, y, w, h in placed_boxes or []:
            for candidate in ((x + w, y), (x, y + h), (x + w, y + h), (x + w, y - part_h), (x - part_w, y + h)):
                if add_candidate(*candidate):
                    return candidates

        # A bounded scan keeps a fallback for irregular outlines and holes.
        for y in range(top, bottom + 1, 8):
            for x in range(left, right + 1, 8):
                if add_candidate(x, y):
                    return candidates
        return candidates
    return [(random.randint(left, right), random.randint(top, bottom)) for _ in range(100)]


def generate_dataset(
    parts_dir: Path,
    background_path: Path,
    output_dir: Path,
    part_files: list[Path] | None = None,
    num_images: int = 20,
    min_parts: int = 2,
    max_parts: int = 8,
    label_format: str = "yolo_hbb",
    layout_mode: str = "random",
    angle_min: float = 0.0,
    angle_max: float = 90.0,
    scale_min: float = 0.6,
    scale_max: float = 1.0,
    margin_top: int = 100,
    margin_bottom: int = 150,
    margin_left: int = 0,
    margin_right: int = 0,
    class_id: int = 0,
    class_name: str = "steel_part",
    jpeg_quality: int = 95,
    project_name: str = "project",
    generation_date: str | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict[str, Any]:
    run_started = perf_counter()
    background = cv2.imread(str(background_path), cv2.IMREAD_COLOR)
    if background is None:
        raise ValueError(f"Cannot read background image: {background_path}")
    part_files = part_files or list_image_files(parts_dir)
    if not part_files:
        raise ValueError(f"No part images found in: {parts_dir}")
    if min_parts < 1 or max_parts < min_parts:
        raise ValueError("Invalid part count range")
    if not 1 <= jpeg_quality <= 100:
        raise ValueError("JPEG quality must be between 1 and 100")
    filename_prefix = dataset_filename_prefix(project_name, generation_date or datetime.now().strftime("%Y%m%d"))

    # Source parts are reused many times. Loading them once avoids repeated disk I/O
    # when generating hundreds or thousands of synthetic images.
    part_cache: dict[Path, np.ndarray] = {}
    part_sizes: dict[Path, int] = {}
    for part_file in part_files:
        image = cv2.imread(str(part_file), cv2.IMREAD_UNCHANGED)
        if image is not None:
            part_cache[part_file] = image
            part_sizes[part_file] = part_file.stat().st_size
    part_files = list(part_cache)
    if not part_files:
        raise ValueError(f"No readable part images found in: {parts_dir}")
    preload_seconds = perf_counter() - run_started

    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    annotations_dir = output_dir / "annotations"
    metadata_dir = output_dir / "metadata"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    annotations_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    bg_h, bg_w = background.shape[:2]
    margins = {"top": margin_top, "bottom": margin_bottom, "left": margin_left, "right": margin_right}
    coco: dict[str, Any] = {"images": [], "annotations": [], "categories": [{"id": class_id, "name": class_name, "supercategory": "part"}]}
    annotation_id = 1
    placed_total = 0
    first_image_path: Path | None = None
    first_metadata_path: Path | None = None
    metadata_index: list[dict[str, Any]] = []
    composition_seconds = 0.0
    image_write_seconds = 0.0
    metadata_write_seconds = 0.0
    label_write_seconds = 0.0

    for image_idx in range(num_images):
        image_started = perf_counter()
        img = background.copy()
        placed_boxes: list[tuple[int, int, int, int]] = []
        yolo_lines: list[str] = []
        instance_parts: list[tuple[np.ndarray, int, int]] = []
        image_coco_annotations: list[dict[str, Any]] = []
        requested_count = random.randint(min_parts, max_parts)
        selected = random.choices(part_files, k=requested_count)
        placement_records: list[dict[str, Any]] = []
        if layout_mode in {"compact", "mixed"}:
            selected = sorted(selected, key=lambda p: part_sizes[p], reverse=True)

        for order, part_path in enumerate(selected):
            active_layout = "compact" if layout_mode == "mixed" and order < len(selected) // 2 else layout_mode
            angle = random.uniform(angle_min, angle_max)
            scale = random.uniform(scale_min, scale_max)
            max_w = max(1, bg_w - margin_left - margin_right)
            max_h = max(1, bg_h - margin_top - margin_bottom)
            part = prepare_part(part_cache[part_path], angle, scale, max_w, max_h)
            if part is None:
                continue
            ph, pw = part.shape[:2]
            tight = tight_bbox_from_alpha(part)
            if tight is None:
                continue
            obb = local_obb_from_alpha(part) if label_format == "yolo_obb" else None
            if label_format == "yolo_obb" and obb is None:
                continue

            placed = False
            candidates = placement_candidates(active_layout, bg_w, bg_h, pw, ph, margins, placed_boxes)
            if active_layout not in {"compact", "mixed"}:
                random.shuffle(candidates)
            gap = 2 if active_layout == "compact" else 12

            for x, y in candidates:
                tx, ty, tw, th = tight
                tight_global = (x + tx, y + ty, tw, th)
                collision_box = (tight_global[0] - gap, tight_global[1] - gap, tight_global[2] + gap * 2, tight_global[3] + gap * 2)
                if check_collision(collision_box, placed_boxes):
                    continue
                img = overlay_image_alpha(img, part, x, y)
                placed_boxes.append(collision_box)
                placed_total += 1

                if label_format == "yolo_obb":
                    coords = yolo_obb(bg_w, bg_h, obb, x, y)
                    yolo_lines.append(f"{class_id} " + " ".join(f"{v:.6f}" for v in coords))
                    label_data: dict[str, Any] = {"format": "yolo_obb", "coordinates": [round(v, 6) for v in coords]}
                elif label_format == "coco":
                    instance_parts.append((part, x, y))
                    label_data = {"format": "coco", "bbox_xywh": [int(v) for v in tight_global]}
                else:
                    coords = yolo_hbb(bg_w, bg_h, tight_global)
                    yolo_lines.append(f"{class_id} " + " ".join(f"{v:.6f}" for v in coords))
                    label_data = {"format": "yolo_hbb", "coordinates": [round(v, 6) for v in coords]}
                placement_records.append({
                    "source_part": part_path.name,
                    "rotation_degrees": round(angle, 4),
                    "scale": round(scale, 6),
                    "layout_mode": active_layout,
                    "placement_xy": [int(x), int(y)],
                    "render_size_wh": [int(pw), int(ph)],
                    "bbox_xywh": [int(v) for v in tight_global],
                    "label": label_data,
                })
                placed = True
                break
            if not placed:
                continue

        composition_seconds += perf_counter() - image_started

        # Images, labels and metadata deliberately share one base name so they
        # remain paired after export or when viewed outside the application.
        file_stem = f"{filename_prefix}_{image_idx + 1:05d}"
        image_filename = f"{file_stem}.jpg"
        image_path = images_dir / image_filename
        image_write_started = perf_counter()
        write_jpeg(image_path, img, jpeg_quality)
        image_write_seconds += perf_counter() - image_write_started
        if first_image_path is None:
            first_image_path = image_path

        metadata_path = metadata_dir / f"{file_stem}.txt"
        image_metadata = {
            "image_file": image_filename,
            "background_file": background_path.name,
            "image_size_wh": [int(bg_w), int(bg_h)],
            "requested_part_count": requested_count,
            "placed_part_count": len(placement_records),
            "label_format": label_format,
            "jpeg_quality": jpeg_quality,
            "layout_mode": layout_mode,
            "rotation_range_degrees": [angle_min, angle_max],
            "scale_range": [scale_min, scale_max],
            "margins": margins,
            "placements": placement_records,
        }
        metadata_write_started = perf_counter()
        metadata_path.write_text(json.dumps(image_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        metadata_write_seconds += perf_counter() - metadata_write_started
        metadata_index.append({
            "image_file": image_filename,
            "metadata_file": metadata_path.name,
            "placed_part_count": len(placement_records),
        })
        if first_metadata_path is None:
            first_metadata_path = metadata_path

        if label_format == "coco":
            label_write_started = perf_counter()
            coco["images"].append({"id": image_idx, "file_name": image_filename, "width": bg_w, "height": bg_h})
            for part, x, y in instance_parts:
                alpha = ensure_rgba(part)[:, :, 3]
                local_mask = np.where(alpha > 10, 255, 0).astype(np.uint8)
                annotation = mask_to_coco_annotation(local_mask, image_idx, annotation_id, class_id, x, y)
                if annotation:
                    coco["annotations"].append(annotation)
                    image_coco_annotations.append(annotation)
                    annotation_id += 1
            # Keep one matching text file for gallery viewing and downstream per-image use.
            (labels_dir / f"{file_stem}.txt").write_text(
                json.dumps({"image_file": image_filename, "annotations": image_coco_annotations}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            label_write_seconds += perf_counter() - label_write_started
        else:
            label_write_started = perf_counter()
            (labels_dir / f"{file_stem}.txt").write_text("\n".join(yolo_lines) + ("\n" if yolo_lines else ""), encoding="utf-8")
            label_write_seconds += perf_counter() - label_write_started
        if progress_callback:
            percent = 10 + int(((image_idx + 1) / max(num_images, 1)) * 85)
            progress_callback(min(percent, 95), f"已生成 {image_idx + 1}/{num_images} 张图片")

    finalize_started = perf_counter()
    if label_format == "coco":
        (annotations_dir / "instances_train.json").write_text(json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8")
    metadata_manifest_path = metadata_dir / "index.txt"
    metadata_manifest_path.write_text(json.dumps(metadata_index, ensure_ascii=False, indent=2), encoding="utf-8")
    data_yaml = [
        f"path: {output_dir.as_posix()}",
        "train: images",
        "val: images",
    ]
    if label_format == "coco":
        data_yaml.append("train_json: annotations/instances_train.json")
    data_yaml.extend(["names:", f"  {class_id}: {class_name}", ""])
    (output_dir / "data.yaml").write_text("\n".join(data_yaml), encoding="utf-8")
    finalize_seconds = perf_counter() - finalize_started
    total_seconds = perf_counter() - run_started
    performance = {
        "preload_seconds": round(preload_seconds, 4),
        "composition_seconds": round(composition_seconds, 4),
        "image_write_seconds": round(image_write_seconds, 4),
        "metadata_write_seconds": round(metadata_write_seconds, 4),
        "label_write_seconds": round(label_write_seconds, 4),
        "finalize_seconds": round(finalize_seconds, 4),
        "total_seconds": round(total_seconds, 4),
        "average_image_seconds": round(total_seconds / max(num_images, 1), 4),
        "images_per_second": round(num_images / total_seconds, 4) if total_seconds else None,
    }

    return {
        "images": num_images,
        "placed_parts": placed_total,
        "label_format": label_format,
        "layout_mode": layout_mode,
        "file_name_pattern": f"{filename_prefix}_{{sequence:05d}}",
        "output_dir": str(output_dir),
        "images_dir": str(images_dir),
        "labels_dir": str(labels_dir),
        "annotations_dir": str(annotations_dir),
        "metadata_dir": str(metadata_dir),
        "metadata_manifest_path": str(metadata_manifest_path),
        "first_image_path": str(first_image_path) if first_image_path else None,
        "first_metadata_path": str(first_metadata_path) if first_metadata_path else None,
        "performance": performance,
    }
