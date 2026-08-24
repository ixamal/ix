"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Hall" },
  { href: "/telemetry", label: "Telemetry" },
  { href: "/oracle", label: "Oracle" },
  { href: "/bridges", label: "Bridges" },
  { href: "/security", label: "Isolation" },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <>
      {links.map((link) => {
        const active =
          link.href === "/"
            ? pathname === "/"
            : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            onClick={onNavigate}
            className={cn(
              "text-sm tracking-[0.18em] uppercase transition-colors",
              active
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {link.label}
          </Link>
        );
      })}
    </>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [onlineCount, setOnlineCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const response = await fetch("/api/status", { cache: "no-store" });
        const data = (await response.json()) as {
          probes?: Array<{ ok: boolean }>;
        };
        if (!cancelled) {
          setOnlineCount((data.probes ?? []).filter((probe) => probe.ok).length);
        }
      } catch {
        if (!cancelled) setOnlineCount(0);
      }
    };
    void tick();
    const id = setInterval(() => void tick(), 4000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-40 border-b border-primary/15 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-baseline gap-3">
            <span className="font-heading text-3xl tracking-[0.2em] text-primary">
              IX
            </span>
            <span className="hidden text-[11px] tracking-[0.32em] text-muted-foreground uppercase sm:inline">
              Valhalla
            </span>
          </Link>
          <nav className="hidden items-center gap-8 md:flex">
            <NavLinks />
          </nav>
          <div className="flex items-center gap-3">
            <span className="font-mono text-[11px] tracking-wider text-muted-foreground">
              {onlineCount == null ? "…" : `${onlineCount}/6 loopback`}
            </span>
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger
                render={
                  <Button
                    variant="ghost"
                    size="icon"
                    className="md:hidden"
                    aria-label="Open menu"
                  />
                }
              >
                <Menu />
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <SheetHeader>
                  <SheetTitle className="font-heading text-2xl tracking-[0.2em]">
                    IX
                  </SheetTitle>
                </SheetHeader>
                <nav className="mt-8 flex flex-col gap-5 px-4">
                  <NavLinks onNavigate={() => setOpen(false)} />
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
        <div className="ix-hairline h-px w-full" />
      </header>
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-8 sm:px-6 sm:py-10">
        {children}
      </main>
      <footer className="border-t border-primary/10 py-6">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-4 text-[11px] tracking-[0.18em] text-muted-foreground uppercase sm:flex-row sm:justify-between sm:px-6">
          <span>Loopback 127.0.0.1 · Ollama off-repo</span>
          <span>~/github/ixamal/ix</span>
        </div>
      </footer>
    </div>
  );
}
