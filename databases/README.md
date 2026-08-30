# databases

Local snapshots of DJ collections. Files stay on this Mac. Gitignores `*.nml`, `*.xml`, `*.db`, and backups — they embed `/Users/<name>/` paths.

After a DJCU2 run, copy the live files here (dated names). Do not commit them.

## Sources

| App | Live file |
| --- | --- |
| Traktor 4.5.1 | `~/Documents/Native Instruments/Traktor 4.5.1/collection.nml` |
| Rekordbox 7 Collection | `~/Library/Pioneer/rekordbox/master.db` |
| Rekordbox XML | `~/Music/PioneerDJ/rekordbox.xml` |

Example snapshot names: `20260830-traktor-collection.nml`, `20260830-rekordbox-master.db`, `20260830-rekordbox.xml`.

## DJCU2

The convert is [ATGR DJCU2](https://atgr.nl/). Process: `docs/djcu2.md`.

Export from Traktor (audio **unchecked**). Do not point DJCU2 at the live `collection.nml` if it offers that warning — use the export.
