import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-heading text-3xl">No such hall</h1>
      <p className="text-sm text-muted-foreground">That path is not part of IX.</p>
      <Link href="/" className={cn(buttonVariants(), "w-fit")}>
        Return to Valhalla
      </Link>
    </div>
  );
}
