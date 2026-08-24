import { OracleConsole } from "@/components/oracle-console";

export default function OraclePage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-[11px] tracking-[0.42em] text-primary uppercase">
          Off-repo · loopback
        </p>
        <h1 className="font-heading text-4xl sm:text-5xl">Ollama oracle</h1>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
          Contributors cloning this repo cannot see your models. Hackers pushing a
          poisoned commit cannot ship a binary into ~/local_tools. IX only probes
          127.0.0.1:11434.
        </p>
      </header>
      <OracleConsole />
    </div>
  );
}
