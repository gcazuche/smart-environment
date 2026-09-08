"use client";

import { useEffect, useRef, type ReactNode } from "react";

export function DashboardDialog({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const close = useRef(onClose);
  useEffect(() => { close.current = onClose; }, [onClose]);
  useEffect(() => {
    const previous = document.activeElement;
    const dialog = ref.current;
    dialog?.showModal();
    return () => { dialog?.close(); if (previous instanceof HTMLElement && previous.isConnected) previous.focus(); };
  }, []);
  return <dialog ref={ref} className="dashboard-dialog" aria-labelledby="dashboard-dialog-title" onCancel={(event) => { event.preventDefault(); close.current(); }}>
    <div className="dialog-heading"><h2 id="dashboard-dialog-title">{title}</h2><button className="modal-close" type="button" onClick={onClose} aria-label="Fechar janela">×</button></div>
    {children}
  </dialog>;
}
