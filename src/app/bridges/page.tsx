import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { bridges, halls } from "@/lib/bridges";

export default function BridgesPage() {
  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col gap-3">
        <p className="text-[11px] tracking-[0.42em] text-primary uppercase">
          MCP · OSC · stdio
        </p>
        <h1 className="font-heading text-4xl sm:text-5xl">Halls and bridges</h1>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
          Public schemas live in /schemas. Live adapters live in
          ~/local_tools/mcp_adapters and are wired from ~/.cursor/mcp.json — never
          from this workspace.
        </p>
      </header>

      {halls
        .filter((hall) => hall.id !== "oracle")
        .map((hall) => (
          <section key={hall.id} id={hall.id} className="flex flex-col gap-4">
            <div>
              <p className="text-[11px] tracking-[0.28em] text-muted-foreground uppercase">
                {hall.epithet}
              </p>
              <h2 className="font-heading text-3xl">{hall.title}</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {bridges
                .filter((bridge) => bridge.hall === hall.id)
                .map((bridge) => (
                  <Card key={bridge.id}>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between gap-3">
                        {bridge.name}
                        <Badge variant="outline">{bridge.listen}</Badge>
                      </CardTitle>
                      <CardDescription>{bridge.protocol}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-2 text-sm leading-6 text-muted-foreground">
                      <p>{bridge.role}</p>
                      <p className="font-mono text-xs text-foreground">
                        {bridge.mcpHint}
                      </p>
                      <p>{bridge.statusHint}</p>
                    </CardContent>
                  </Card>
                ))}
            </div>
          </section>
        ))}
    </div>
  );
}
