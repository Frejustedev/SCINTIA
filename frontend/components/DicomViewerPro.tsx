"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from "react";

import {
  fetchPixels,
  getSeriesMeta,
  listSeries,
  type SeriesMeta,
  type SeriesRead,
} from "@/lib/api";

type Point = { x: number; y: number };
type Measure = { a: Point; b: Point };

const CT_PRESETS = [
  { label: "Os", ww: 1500, wc: 400 },
  { label: "Poumon", ww: 1500, wc: -600 },
  { label: "Cerveau", ww: 80, wc: 40 },
  { label: "Abdomen", ww: 400, wc: 40 },
  { label: "Médiastin", ww: 350, wc: 50 },
];

export function DicomViewerPro({ studyId }: { studyId: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const offscreenRef = useRef<HTMLCanvasElement | null>(null);
  const cacheRef = useRef<Map<number, Int16Array>>(new Map());
  const dragRef = useRef<{ mode: string; x: number; y: number; ww: number; wc: number } | null>(
    null,
  );

  const [series, setSeries] = useState<SeriesRead[]>([]);
  const [seriesId, setSeriesId] = useState<string | null>(null);
  const [meta, setMeta] = useState<SeriesMeta | null>(null);
  const [index, setIndex] = useState(0);
  const [pixels, setPixels] = useState<Int16Array | null>(null);
  const [ww, setWw] = useState(400);
  const [wc, setWc] = useState(40);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Point>({ x: 0, y: 0 });
  const [rotate, setRotate] = useState(0); // multiples of 90°
  const [invert, setInvert] = useState(false);
  const [measuring, setMeasuring] = useState(false);
  const [measures, setMeasures] = useState<Measure[]>([]);
  const [readout, setReadout] = useState<{ x: number; y: number; v: number } | null>(null);
  const [cine, setCine] = useState(false);
  const [size, setSize] = useState({ w: 600, h: 600 });
  const [error, setError] = useState<string | null>(null);

  const active = series.find((s) => s.id === seriesId) ?? null;
  const count = meta?.instances ?? active?.instances ?? 0;
  const cols = meta?.cols ?? 1;
  const rows = meta?.rows ?? 1;

  // ── Load series, then metadata for the active one ──
  useEffect(() => {
    listSeries(studyId)
      .then((list) => {
        setSeries(list);
        const usable = list.find((s) => !s.purged && s.instances > 0);
        if (usable) setSeriesId(usable.id);
        else setError("Aucune image à afficher.");
      })
      .catch((e) => setError((e as Error).message));
  }, [studyId]);

  useEffect(() => {
    if (!seriesId) return;
    cacheRef.current.clear();
    setMeasures([]);
    setIndex(0);
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setRotate(0);
    getSeriesMeta(studyId, seriesId)
      .then((m) => {
        setMeta(m);
        setWw(Math.max(1, Math.round(m.window_width)));
        setWc(Math.round(m.window_center));
        setInvert(m.inverted);
      })
      .catch((e) => setError((e as Error).message));
  }, [studyId, seriesId]);

  // ── Fetch pixels for the current slice (cached), prefetch neighbours ──
  useEffect(() => {
    if (!seriesId || count === 0) return;
    let cancelled = false;
    const load = async (i: number, apply: boolean) => {
      if (i < 0 || i >= count) return;
      let px = cacheRef.current.get(i);
      if (!px) {
        px = await fetchPixels(studyId, seriesId, i);
        cacheRef.current.set(i, px);
      }
      if (apply && !cancelled) setPixels(px);
    };
    load(index, true).catch((e) => setError((e as Error).message));
    void load(index + 1, false);
    void load(index - 1, false);
    return () => {
      cancelled = true;
    };
  }, [studyId, seriesId, index, count]);

  // ── Track container size ──
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setSize({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    setSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  // ── Cine playback ──
  useEffect(() => {
    if (!cine || count === 0) return;
    const id = window.setInterval(() => setIndex((i) => (i + 1) % count), 120);
    return () => window.clearInterval(id);
  }, [cine, count]);

  const baseScale = Math.min(size.w / cols, size.h / rows) || 1;
  const scale = baseScale * zoom;
  const theta = (rotate * Math.PI) / 2;
  const cos = Math.round(Math.cos(theta));
  const sin = Math.round(Math.sin(theta));
  const originX = size.w / 2 + pan.x;
  const originY = size.h / 2 + pan.y;

  const imgToScreen = useCallback(
    (ix: number, iy: number): Point => {
      const dx = ix - cols / 2;
      const dy = iy - rows / 2;
      return {
        x: originX + (dx * cos - dy * sin) * scale,
        y: originY + (dx * sin + dy * cos) * scale,
      };
    },
    [cols, rows, cos, sin, scale, originX, originY],
  );

  const screenToImg = useCallback(
    (sx: number, sy: number): Point => {
      const rx = (sx - originX) / scale;
      const ry = (sy - originY) / scale;
      return { x: rx * cos + ry * sin + cols / 2, y: -rx * sin + ry * cos + rows / 2 };
    },
    [cols, rows, cos, sin, scale, originX, originY],
  );

  // ── Render ──
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !meta || !pixels) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Offscreen holds the windowed grayscale at native resolution.
    let off = offscreenRef.current;
    if (!off || off.width !== cols || off.height !== rows) {
      off = document.createElement("canvas");
      off.width = cols;
      off.height = rows;
      offscreenRef.current = off;
    }
    const octx = off.getContext("2d");
    if (!octx) return;
    const img = octx.createImageData(cols, rows);
    const low = wc - ww / 2;
    const span = ww <= 0 ? 1 : ww;
    const data = img.data;
    for (let i = 0; i < pixels.length; i++) {
      let g = ((pixels[i] - low) / span) * 255;
      g = g < 0 ? 0 : g > 255 ? 255 : g;
      if (invert) g = 255 - g;
      const o = i * 4;
      data[o] = data[o + 1] = data[o + 2] = g;
      data[o + 3] = 255;
    }
    octx.putImageData(img, 0, 0);

    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, size.w, size.h);
    ctx.save();
    ctx.translate(originX, originY);
    ctx.rotate(theta);
    ctx.scale(scale, scale);
    ctx.imageSmoothingEnabled = zoom < 2.5;
    ctx.drawImage(off, -cols / 2, -rows / 2);
    ctx.restore();

    // Measurements (drawn in screen space).
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = "#7dd3fc";
    ctx.fillStyle = "#7dd3fc";
    ctx.font = "12px monospace";
    const spacing = meta.pixel_spacing_mm ? meta.pixel_spacing_mm[0] : null;
    for (const m of measures) {
      const a = imgToScreen(m.a.x, m.a.y);
      const b = imgToScreen(m.b.x, m.b.y);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
      const dpx = Math.hypot(m.a.x - m.b.x, m.a.y - m.b.y);
      const label = spacing ? `${(dpx * spacing).toFixed(1)} mm` : `${dpx.toFixed(0)} px`;
      ctx.fillText(label, (a.x + b.x) / 2 + 6, (a.y + b.y) / 2 - 6);
    }
  }, [
    meta,
    pixels,
    ww,
    wc,
    invert,
    cols,
    rows,
    size,
    scale,
    theta,
    originX,
    originY,
    zoom,
    measures,
    imgToScreen,
  ]);

  // ── Pointer interaction ──
  const onPointerDown = (e: ReactPointerEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    (e.target as Element).setPointerCapture(e.pointerId);
    if (measuring && e.button === 0) {
      const p = screenToImg(x, y);
      setMeasures((m) => [...m, { a: p, b: p }]);
      dragRef.current = { mode: "measure", x, y, ww, wc };
    } else if (e.button === 1 || e.button === 2 || e.shiftKey) {
      dragRef.current = { mode: "pan", x, y, ww, wc };
    } else if (e.button === 0) {
      dragRef.current = { mode: "wl", x, y, ww, wc };
    }
  };
  const onPointerMove = (e: ReactPointerEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const p = screenToImg(x, y);
    const ix = Math.round(p.x);
    const iy = Math.round(p.y);
    if (pixels && ix >= 0 && ix < cols && iy >= 0 && iy < rows) {
      setReadout({ x: ix, y: iy, v: pixels[iy * cols + ix] });
    } else setReadout(null);
    const d = dragRef.current;
    if (!d) return;
    if (d.mode === "wl") {
      setWw(Math.max(1, Math.round(d.ww + (x - d.x) * 4)));
      setWc(Math.round(d.wc - (y - d.y) * 4));
    } else if (d.mode === "pan") {
      setPan((prev) => ({ x: prev.x + e.movementX, y: prev.y + e.movementY }));
    } else if (d.mode === "measure") {
      setMeasures((m) => {
        const copy = m.slice();
        copy[copy.length - 1] = { a: copy[copy.length - 1].a, b: p };
        return copy;
      });
    }
  };
  const onPointerUp = () => {
    dragRef.current = null;
  };
  const onWheel = (e: ReactWheelEvent) => {
    if (e.ctrlKey) {
      setZoom((z) => Math.min(8, Math.max(0.2, z * (e.deltaY < 0 ? 1.1 : 0.9))));
    } else {
      setIndex((i) => Math.min(count - 1, Math.max(0, i + (e.deltaY < 0 ? -1 : 1))));
    }
  };

  const resetView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setRotate(0);
    if (meta) {
      setWw(Math.max(1, Math.round(meta.window_width)));
      setWc(Math.round(meta.window_center));
      setInvert(meta.inverted);
    }
  }, [meta]);

  // ── Keyboard ──
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowUp" || e.key === "ArrowLeft") setIndex((i) => Math.max(0, i - 1));
      else if (e.key === "ArrowDown" || e.key === "ArrowRight")
        setIndex((i) => Math.min(count - 1, i + 1));
      else if (e.key === "+" || e.key === "=") setZoom((z) => Math.min(8, z * 1.15));
      else if (e.key === "-") setZoom((z) => Math.max(0.2, z / 1.15));
      else if (e.key.toLowerCase() === "i") setInvert((v) => !v);
      else if (e.key.toLowerCase() === "r") resetView();
      else if (e.key === " ") setCine((c) => !c);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [count, resetView]);

  const toggleFullscreen = () => {
    const el = containerRef.current?.parentElement;
    if (!document.fullscreenElement) el?.requestFullscreen?.();
    else document.exitFullscreen?.();
  };

  if (error) {
    return (
      <p role="alert" className="text-sm text-crit">
        {error}
      </p>
    );
  }

  const btn =
    "rounded border border-border px-2 py-1 font-mono text-xs text-muted hover:text-ink-100";
  const btnOn = "rounded border border-iris bg-iris/15 px-2 py-1 font-mono text-xs text-ink-100";

  return (
    <div className="flex flex-col gap-3">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        {series.length > 1 &&
          series.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setSeriesId(s.id)}
              disabled={s.purged || s.instances === 0}
              className={s.id === seriesId ? btnOn : btn}
            >
              {s.kind} · {s.instances}
            </button>
          ))}
        <span className="mx-1 h-4 w-px bg-border" />
        {(meta?.modality === "CT" ? CT_PRESETS : []).map((p) => (
          <button
            key={p.label}
            type="button"
            className={btn}
            onClick={() => {
              setWw(p.ww);
              setWc(p.wc);
            }}
          >
            {p.label}
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-border" />
        <button type="button" className={btn} onClick={() => setZoom((z) => Math.min(8, z * 1.2))}>
          Zoom +
        </button>
        <button
          type="button"
          className={btn}
          onClick={() => setZoom((z) => Math.max(0.2, z / 1.2))}
        >
          Zoom −
        </button>
        <button
          type="button"
          className={measuring ? btnOn : btn}
          onClick={() => setMeasuring((v) => !v)}
        >
          Mesure
        </button>
        <button type="button" className={btn} onClick={() => setMeasures([])}>
          Effacer
        </button>
        <button type="button" className={invert ? btnOn : btn} onClick={() => setInvert((v) => !v)}>
          Inverser
        </button>
        <button type="button" className={btn} onClick={() => setRotate((r) => (r + 1) % 4)}>
          Pivoter
        </button>
        <button type="button" className={cine ? btnOn : btn} onClick={() => setCine((c) => !c)}>
          {cine ? "⏸" : "▶"} Ciné
        </button>
        <button type="button" className={btn} onClick={resetView}>
          Réinit.
        </button>
        <button type="button" className={btn} onClick={toggleFullscreen}>
          Plein écran
        </button>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        className="relative aspect-square w-full overflow-hidden rounded-md border border-border bg-black"
      >
        <canvas
          ref={canvasRef}
          width={size.w}
          height={size.h}
          className="h-full w-full touch-none select-none"
          style={{ cursor: measuring ? "crosshair" : "default" }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onWheel={onWheel}
          onContextMenu={(e) => e.preventDefault()}
        />
        {/* Overlays */}
        <div className="pointer-events-none absolute left-2 top-2 font-mono text-[11px] text-ink-100/80">
          {active?.kind?.toUpperCase()} · {meta?.modality}
          <br />
          coupe {count ? index + 1 : 0}/{count}
        </div>
        <div className="pointer-events-none absolute right-2 top-2 text-right font-mono text-[11px] text-ink-100/80">
          W {ww} · L {wc}
          <br />
          zoom {(zoom * 100).toFixed(0)}%
        </div>
        {readout && (
          <div className="pointer-events-none absolute bottom-2 left-2 font-mono text-[11px] text-ink-100/80">
            ({readout.x}, {readout.y}) = {readout.v}
            {meta?.modality === "CT" ? " UH" : ""}
          </div>
        )}
        <div className="pointer-events-none absolute bottom-2 right-2 font-mono text-[10px] text-muted">
          glisser = fenêtrage · molette = coupe · Ctrl+molette = zoom · Maj+glisser = déplacer
        </div>
      </div>

      {/* Slice slider */}
      <input
        type="range"
        min={0}
        max={Math.max(count - 1, 0)}
        value={index}
        onChange={(e) => setIndex(Number(e.target.value))}
        className="w-full accent-iris"
        aria-label="Coupe"
      />
    </div>
  );
}
