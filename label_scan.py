"""Read a cropped nutrition panel locally and suggest editable label values."""
import os
import re
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


def read_label(data):
    if len(data) > 12 * 1024 * 1024:
        raise ValueError("Choose a photo smaller than 12 MB.")
    with Image.open(BytesIO(data)) as image:
        if image.width * image.height > 32_000_000:
            raise ValueError("Crop the image to the nutrition panel and try again.")
        panel = ImageOps.exif_transpose(image).convert("RGB")
    panel.thumbnail((2500, 2500))
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "panel.png"
        panel.save(path)
        if shutil.which("tesseract"):
            command = ["tesseract", str(path), "stdout", "-l", "eng", "--psm", "6"]
        elif os.name == "nt":
            command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                       "-File", str(Path(__file__).with_name("read_label.ps1")), str(path)]
        else:
            raise ValueError("Install Tesseract with English language data to enable label scanning.")
        try:
            return subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", check=True, timeout=35).stdout
        except (subprocess.SubprocessError, OSError) as exc:
            raise ValueError("The OCR reader could not finish. Try a smaller crop or enter the values manually.") from exc


NAMES = {
    "fat_g": r"(?:total\s+)?fat",
    "trans_fat_g": r"trans\s+fat",
    "sugar_g": r"(?:total\s+)?sugars?",
    "protein_g": r"protein",
    "fibre_g": r"(?:dietary\s+)?fib(?:re|er)",
    "sodium_mg": r"sodium",
    "energy_kcal": r"(?:energy|calories)",
}
NUMBER = r"\d+(?:[.,]\d+)?"
UNIT = r"(?:kcal|mg|g)"


def parse_label(text):
    """Skip conflicting values, inequality signs and multi-column rows."""
    text = text.lower()
    found = {}
    for key, name in NAMES.items():
        values = set()
        target = key.split("_")[-1]
        pattern = (rf"^\s*{name}\s*(?:\(\s*({UNIT})\s*\))?\s*[:\-]?\s*"
                   rf"({NUMBER})\s*({UNIT})?\s*(?:\d+(?:\.\d+)?\s*%)?\s*$")
        for header_unit, number, unit in re.findall(pattern, text, re.M | re.I):
            if header_unit and unit and header_unit != unit:
                continue
            unit = unit or header_unit
            if not unit and key == "energy_kcal" and re.search(rf"^\s*calories\s+{re.escape(number)}\s*$", text, re.M):
                unit = "kcal"
            factors = {(target, target): 1, ("g", "mg"): 1000, ("mg", "g"): 0.001}
            if (unit, target) in factors:
                values.add(float(number.replace(",", ".")) * factors[unit, target])
        if len(values) == 1:
            found[key] = values.pop()

    serving = re.search(rf"serving\s+size[^\n]{{0,60}}?({NUMBER})\s*(ml|g)\b", text)
    per100 = re.search(r"\bper\s*100\s*(ml|g)\b", text)
    per_serving = re.search(r"\bper\s+(?:serving|serve|portion)\b", text)
    basis = None
    if per100 and not per_serving:
        basis = "Per 100"
    elif per_serving and not per100:
        basis = "Per serving"
    unit = per100[1] if per100 else serving[2] if serving else None
    return dict(values=found, basis=basis, unit=unit,
                serving=float(serving[1].replace(",", ".")) if serving else None)

