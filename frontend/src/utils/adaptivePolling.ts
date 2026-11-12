/**
 * Poll quickly while work is in progress, slowly otherwise.
 *
 * Every `fastMs` the poller checks `isBusy()` (e.g. a document is still
 * processing, including one uploaded since the last fetch). It calls `load`
 * then, or at least every `slowMs` to pick up changes from other tabs.
 * Nothing is fetched while the browser tab is hidden.
 *
 * Returns a function that stops polling.
 */
export function startAdaptivePolling(
  load: () => Promise<void>,
  isBusy: () => boolean,
  fastMs = 3000,
  slowMs = 30000,
): () => void {
  let stopped = false;
  let lastLoad = 0;
  let timer: number | undefined;

  const tick = async () => {
    if (stopped) return;
    const now = Date.now();
    const due = lastLoad === 0 || isBusy() || now - lastLoad >= slowMs;
    if (due && !document.hidden) {
      lastLoad = now;
      try {
        await load();
      } catch (error) {
        console.error("Polling failed:", error);
      }
    }
    if (!stopped) timer = window.setTimeout(tick, fastMs);
  };

  timer = window.setTimeout(tick, 0);
  return () => {
    stopped = true;
    window.clearTimeout(timer);
  };
}

export function isProcessing(status: string): boolean {
  return status === "processing" || status === "uploaded";
}
