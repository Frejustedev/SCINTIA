"use client";

import { useEffect, useRef, useState } from "react";

import { fetchFrame, listSeries, type SeriesRead } from "@/lib/api";
import { useT } from "@/lib/locale";

/**
 * Lightweight DICOM viewer: scrolls server-rendered PNG frames with window/level.
 * The richer Cornerstone3D viewer (voxel mask editing) is the production target
 * (DECISIONS.md); this works today without a client-side DICOM decoder.
 */
export function DicomViewer({ studyId }: { studyId: string }) {
  const t = useT();
  const [series, setSeries] = useState<SeriesRead[]>([]);
  const [seriesId, setSeriesId] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [windowWidth, setWindowWidth] = useState(400);
  const [level, setLevel] = useState(40);
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const urlRef = useRef<string | null>(null);

  const active = series.find((s) => s.id === seriesId) ?? null;
  const count = active?.instances ?? 0;

  useEffect(() => {
    listSeries(studyId)
      .then((list) => {
        setSeries(list);
        const usable = list.find((s) => !s.purged && s.instances > 0);
        if (usable) setSeriesId(usable.id);
        else if (list.some((s) => s.purged))
          setError("Données DICOM brutes supprimées (rétention).");
        else setError("Aucune image à afficher.");
      })
      .catch((e) => setError((e as Error).message));
  }, [studyId]);

  useEffect(() => {
    setIndex(0);
  }, [seriesId]);

  useEffect(() => {
    if (!seriesId || count === 0) return undefined;
    let cancelled = false;
    fetchFrame(studyId, seriesId, index, windowWidth, level)
      .then((next) => {
        if (cancelled) {
          URL.revokeObjectURL(next);
          return;
        }
        if (urlRef.current) URL.revokeObjectURL(urlRef.current);
        urlRef.current = next;
        setUrl(next);
      })
      .catch((e) => setError((e as Error).message));
    return () => {
      cancelled = true;
    };
  }, [studyId, seriesId, index, windowWidth, level, count]);

  useEffect(
    () => () => {
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    },
    [],
  );

  if (error) {
    return (
      <p role="alert" className="text-sm text-crit">
        {error}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {series.length > 1 ? (
        <div className="flex gap-2">
          {series.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setSeriesId(s.id)}
              disabled={s.purged || s.instances === 0}
              className={`rounded-md border px-3 py-1 font-mono text-xs uppercase tracking-[0.1em] ${
                s.id === seriesId
                  ? "border-iris bg-iris/10 text-ink-100"
                  : "border-border text-muted hover:text-ink-200"
              } disabled:opacity-40`}
            >
              {s.kind} · {s.instances}
            </button>
          ))}
        </div>
      ) : null}

      <div className="flex aspect-square w-full items-center justify-center overflow-hidden rounded-md border border-border bg-black">
        {url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={url}
            alt={`Coupe ${index + 1} / ${count}`}
            className="h-full w-full object-contain"
          />
        ) : (
          <span className="font-mono text-xs text-muted">{t("common.loading")}</span>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <label className="flex items-center justify-between font-mono text-xs text-muted">
          <span>{t("viewer.slice")}</span>
          <span className="tabular-nums text-ink-200">
            {count ? index + 1 : 0} / {count}
          </span>
        </label>
        <input
          type="range"
          min={0}
          max={Math.max(count - 1, 0)}
          value={index}
          onChange={(e) => setIndex(Number(e.target.value))}
          className="w-full accent-iris"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="flex flex-col gap-1 font-mono text-xs text-muted">
          <span>
            {t("viewer.window")} : {windowWidth}
          </span>
          <input
            type="range"
            min={1}
            max={2000}
            value={windowWidth}
            onChange={(e) => setWindowWidth(Number(e.target.value))}
            className="accent-iris"
          />
        </label>
        <label className="flex flex-col gap-1 font-mono text-xs text-muted">
          <span>
            {t("viewer.level")} : {level}
          </span>
          <input
            type="range"
            min={-1000}
            max={1000}
            value={level}
            onChange={(e) => setLevel(Number(e.target.value))}
            className="accent-iris"
          />
        </label>
      </div>

      <p className="text-xs text-muted">
        Visualiseur de relecture. Correction des volumes par organe via la page résultats ; édition
        voxel des masques prévue avec le visualiseur Cornerstone3D (masques GPU).
      </p>
    </div>
  );
}
