"""Validated, JSON-safe inference jobs. No host commands or shell text allowed."""
import math
from pathlib import Path

MOVIES = {".mov", ".mp4", ".mkv", ".avi", ".webm", ".m4v", ".mxf"}
IMAGES = {".png", ".jpg", ".jpeg"}


def number(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name}: Zahl zwischen {minimum} und {maximum} erforderlich")
    return value


def file_path(value, name, suffixes):
    if not isinstance(value, str) or len(value) > 8192 or not Path(value).is_absolute():
        raise ValueError(f"{name}: absoluter Dateipfad erforderlich")
    path = Path(value).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in suffixes:
        raise ValueError(f"{name}: Dateityp nicht unterstützt")
    return str(path)


def validate(params):
    defaults = dict(hint="", hint_video="", hint_quality=0.95, despill=0.5, low_vram=False,
                    preview=False, range_start=0.0, range_end=None, preview_seconds=2.0,
                    preview_scale=0.5, output_format="video", exr_dtype="half",
                    matte_black=0.0, matte_white=1.0, matte_expand=0, matte_feather=0.0,
                    keep_warm=True, context={}, layer_mask=None, keep_cache=True,
                    despill_color="green", core_strength=0.0, edge_strength=1.0, temporal_window=0,
                    reference_frame=None, mask_stack=None)
    if not isinstance(params, dict) or set(params) - (set(defaults) | {"input"}):
        raise ValueError("Unbekannte Auftragsoptionen")
    options = dict(defaults, **params)
    options["input"] = file_path(options.get("input"), "Video", MOVIES)
    for key, types in [("hint", IMAGES), ("hint_video", MOVIES)]:
        if not isinstance(options[key], str) or len(options[key]) > 8192: raise ValueError(key + ": Dateipfad erforderlich")
        if options[key]: options[key] = file_path(options[key], key, types)
    if options['despill_color'] not in ('green','blue','off'):raise ValueError('Invalid spill colour')
    number(options['core_strength'],'Core',0,1);number(options['edge_strength'],'Edges',0,2)
    number(options['temporal_window'],'Temporal window',0,80)
    if options['temporal_window'] not in (0,4,8,16,32,80):raise ValueError('Invalid temporal window')
    if options['reference_frame'] is not None:
        number(options['reference_frame'],'Reference frame',0,1e9)
        if options['reference_frame']!=int(options['reference_frame']):raise ValueError('Reference frame must be an integer')
    if options['mask_stack'] is not None:
        from mask_hint import validate_stack
        validate_stack(options['mask_stack'])
    if options["layer_mask"] is not None:
        from mask_hint import validate_mask
        validate_mask(options["layer_mask"])
    if sum(bool(options[k]) for k in ("hint", "hint_video", "layer_mask", "mask_stack")) > 1:
        raise ValueError("Startmaske oder Maskenvideo verwenden, nicht beides gleichzeitig")
    for key, lo, hi in [("hint_quality", 0, 1), ("despill", 0, 1), ("range_start", 0, 1e9),
                        ("preview_seconds", 0.04, 10), ("preview_scale", 0.25, 1),
                        ("matte_black", 0, 1), ("matte_white", 0, 1), ("matte_expand", -32, 32),
                        ("matte_feather", 0, 16)]:
        number(options[key], key, lo, hi)
    if options["matte_expand"] != int(options["matte_expand"]):
        raise ValueError("Kantenverschiebung muss eine ganze Pixelzahl sein")
    if options["matte_black"] >= options["matte_white"]:
        raise ValueError("Schwarzpunkt muss kleiner als Weißpunkt sein")
    if options["range_end"] is not None:
        number(options["range_end"], "range_end", 0, 1e9)
        if options["range_end"] <= options["range_start"]:
            raise ValueError("Der gewählte Zeitbereich ist leer")
    for key in ("low_vram", "preview", "keep_warm", "keep_cache"):
        if not isinstance(options[key], bool): raise ValueError(key + " muss ein Schalter sein")
    if options["output_format"] not in ("video", "exr") or options["exr_dtype"] not in ("half", "float"):
        raise ValueError("Ausgabeformat nicht unterstützt")
    context = options["context"]
    if not isinstance(context, dict) or set(context) - {"project", "comp", "layer", "name", "path", "fps", "native_fps", "start", "in", "out", "stretch", "trim_in", "trim_out"}:
        raise ValueError("Ungültiger Ebenenbezug")
    for key, value in context.items():
        if key in ("project", "path", "name"):
            if not isinstance(value, str) or len(value) > 8192: raise ValueError("Ungültiger Ebenenbezug")
        else: number(value, key, -1e12, 1e12)
    return options


def frame_range(fps, total_frames, start, end=None, preview=False, preview_seconds=2):
    """End exclusive, frame-aligned. Reject an out-of-source request."""
    first = int(math.floor(start * fps + 1e-6))
    last = min(total_frames, int(math.ceil(end * fps - 1e-6))) if end is not None else total_frames
    if preview: last = min(last, first + max(1, int(round(preview_seconds * fps))))
    if first < 0 or first >= last or first >= total_frames:
        raise ValueError("Der Zeitbereich enthält keine Bilder der Quelldatei")
    return first, last
