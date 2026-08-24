import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getRigStatus } from "@/lib/status";

export const dynamic = "force-dynamic";

export default async function SecurityPage() {
  const rig = await getRigStatus();

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-[11px] tracking-[0.42em] text-primary uppercase">
          Public git · private Mac
        </p>
        <h1 className="font-heading text-4xl sm:text-5xl">Isolation map</h1>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
          The open-source tree is allowed to know that Ollama and MCP exist. It is
          not allowed to host them. Status below checks for presence, never dumps
          ~/.cursor/mcp.json.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {rig.probes.map((probe) => (
          <Card key={probe.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3">
                {probe.label}
                <Badge variant={probe.ok ? "default" : "outline"}>
                  {probe.ok ? "present" : "absent"}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-sm text-muted-foreground">
              <p>{probe.detail}</p>
              <p className="font-mono text-xs tracking-wider uppercase text-primary">
                {probe.location}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Hard rules</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm leading-6 text-muted-foreground">
          <p>1. Bind 127.0.0.1. Refuse 0.0.0.0.</p>
          <p>2. MCP config is global: ~/.cursor/mcp.json.</p>
          <p>3. Adapters and Ollama live in ~/local_tools.</p>
          <p>4. Circuit-break DAW/DCC/UE commands. Cap volume at 0 dB.</p>
          <p>5. Mac clone path: {rig.clonePath}</p>
        </CardContent>
      </Card>
    </div>
  );
}
