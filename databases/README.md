# databases

Local snapshots of DJ collections. The files stay on this Mac.

Do **not** commit `collection.nml`, Rekordbox `master.db`, or `rekordbox.xml`. They embed `/Users/<name>/` paths and the crate layout. Gitignores those extensions.

## Traktor

Live file (do not point DJCU2 at this if it can see it is the original):

`~/Documents/Native Instruments/Traktor 4.5.1/collection.nml`

DJCU2 wants a **Traktor export**, not a copy of that file:

1. Open Traktor.
2. File → Export Collection (or Export → Collection).
3. Destination: `~/Documents` (or this folder).
4. **Uncheck** export audio files.
5. In DJCU2, choose that exported NML.

A Finder copy of `collection.nml` still counts as the original NML and trips the same warning.
