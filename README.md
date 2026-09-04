# ix

Primary planetary code base for machines and humans. This is Valhalla: Cursor, a local Ollama oracle, Unreal Engine 5, DCC, DAW, and DJ tools meet here. The destination is **Elysium**.

Public git: [github.com/ixamal/ix](https://github.com/ixamal/ix)

Mac clone path: `~/github/ixamal/ix`

## Where we are

Written for a non-technical read. Detail and next steps: `docs/TODO.md`.

### Latest — 2026-09-04 (whew)

The migration drive came home. Then the ghosts came with it. Then we sent the ghosts packing. Music.app is a crate again: **21,824** file tracks, all under `~/Music`, **0** leftover `!`, **0** leftover `EDM,`.

- **Copy first, relink second.** Audio that had been living on Terrarum is back in `~/Music`. Never point Music.app at a USB volume — those rows go `!` the second you unplug.
- **`EDM, House` is a cockroach.** Cleared it (229). Recovered tracks from the drive. It came back (66). Same command, two layers: write the file *and* tell Music.app, because Music does not re-read tags. Click off the stale genre in the column or the list still looks haunted.
- **Replicants.** Same recording, two filenames (`Track.m4a` and iTunes' helpful `Track 1.m4a`). Byte compare lies after a retag. Decode the audio, then drop the extra *row*. Playlist copy wins so a crate slot never goes empty. 622 extras gone; real variants stayed.
- **WAV vs ID3.** A tag write prepended `ID3` where `RIFF` belongs. Music.app said *invalid start code*. The clean original got copied in as `(2)` then `(3)`. Never write ID3 on WAV/AIFF. `riff-repair` put RIFF back and deleted the twins.
- **Ghosts evicted.** If it was not on Terrarum `MIGRATION_MASTER`, we stopped hunting. 425 Songs rows with no file (and one leftover iTunes LP package) deleted. The missing Aphex / Collide / Orb cuts wait for another day — they are not library ghosts anymore.

The Python for all of that lives in `crate/`. Dry-run is the default. Reports stay off git in `~/local_tools/crate/reports`. How and why: `docs/crate.md`.

### Crate toolkit — steal these

This is not a product. It is a crate that got sick of being a warehouse job, written down so another DJ (or another agent) can steal the ideas and leave the Mac-specific scars.

| Command | The idea |
| --- | --- |
| `music-dupes` | Two Songs rows, **one file**. Delete the extra *row*. If Music.app bins the file, restore from Trash and stop. |
| `music-replicants` | Two Songs rows, **two files**, same *sound*. Compare decoded audio (ffmpeg MD5), not tag bytes. Alternate takes stay. |
| `music-genre` | `EDM, House` → `House`. File **and** library. Never mutagen-write `.wav` or `.m4p`. Slash genres (`Funk / Soul / Disco`) are real — leave them. |
| `music-repair` | Locate `!` by a unique artist/title hit on disk. Fill empty identity only. Do not move Apple Music. |
| `music-reconcile` | Same `!`, but from the iTunes XML persistent-ID map. Exact, not a guess. Copy into `~/Music` before you relink. Never relink to `/Volumes`. |
| `consolidate` | Pull a migration tree home as Artist / Album. Tags decide the folder, not the mangled exFAT path. iTunes `Track 1` is a duplicate marker, not a new track. |
| `riff-repair` | ID3-headed WAV is trash. Restore RIFF from a sibling or the backup drive. Delete `(2)` / `(3)` only when the audio matches. |
| `music-cull` | When the hunt is over, drop rows with no file or unreadable media. Valid audio stays. DRM `.m4p` stays even if ffmpeg sulks. |
| `music-fix` / `stemit` | Identify a playlist by sound (AcoustID, then Shazam). STEMIT hardlinks a mix into `stems_audio` and runs the factory — the library never grows a copy. |

Hard-won rules, if you adapt this for your own crate:

1. **Dry-run first.** Every command writes a JSON report. Read it. Then `--execute`.
2. **Music.app is a database.** Writing tags on the file does nothing to Songs / the column browser. Tell Music itself.
3. **AppleScript lists lie.** `location of file tracks i thru j` must be coerced `as list`, or one-track batches explode and every row looks dead.
4. **Editing a row reorders the library.** Capture persistent IDs. Re-check before you write. `--passes` until it converges.
5. **Title-only match will collide.** “24 Hours” is not unique. Persistent ID or decoded audio. Never attach Bizen to Agent Sumo because the titles rhyme.
6. **WAV is not MP3.** EasyID3 on a `.wav` prepends `ID3` and the file will not play. Skip RIFF/AIFF. That is how we got `(2)` and `(3)`.
7. **The DJ crate stays local.** Sync Library Off. Bind nothing to `0.0.0.0`. Audio never enters git.

```bash
cd ~/github/ixamal/ix
PYTHONPATH=crate python3 -m ix_crate music-cull          # dry-run
PYTHONPATH=crate python3 -m ix_crate music-cull --execute
```

### 2026-09-03

- **The library names itself now.** A tool listens to each track's own audio (fingerprinting, plus Shazam for the hard ones) and writes the real artist and album. 263 tracks came out of the "Various Artists" junk drawer. Nothing is guessed; anything it cannot prove is left alone.
- **Mix CDs read correctly.** Send a screenshot of one album and its real per-track artists get written, filed under the DJ who mixed it — Danny Tenaglia's Global Underground, Mark Farina's Mushroom Jazz 7, Lazy Dog. One album at a time, on purpose.
- **Drag and drop into Music works again.** New Beatport and Traxsource downloads were failing with a "duplicate file name" error. A leftover shortcut inside the media folder was pointing at itself, so every copy landed on a path that already existed. Replaced with a real folder; confirmed working.
- **STEMIT.** One command takes a playlist out of Music and turns every track into DJ stems: vocals, instrumental, and the four-deck Traktor file. First run was the 50th playlist — 21 tracks, all 21 finished, no failures, 78 minutes. One track had no separable vocal, so it correctly kept the mix and skipped the pair.
- **Nothing was copied or moved.** The stem factory reads the same bytes as Apple Music through a hardlink, so the library never grows a duplicate and Traktor / Rekordbox never lose a path.

### From the start

- Stood up **ix** as the home base: Cursor directs, a local AI stays on this Mac, Unreal is for live visuals, DJ tools stay DJ tools.
- Kept the dangerous stuff off the public site (real library, models, hardware wiring).
- Installed a local AI on the Mac and used it to identify mystery tracks.
- Built a stem factory and ran the first big pass on the crate.
- Got the piano (S88) into Traktor on one fader (Channel D). That fight is won.
- Cleaned Unknown Album, mashups, and the inbox. Leftovers have a real home.
- Relinked Traktor so it still finds the files after the move.
- Converted Traktor → Rekordbox. Playlists and folders landed. It works.
- Confirmed the same songs live at the same place in Traktor, Rekordbox, and Music.
- Fixed genres: “Accapella” and thousands of “EDM, …” labels are now real names (House, Techno, and so on). Music.app matches the files. iCloud sync stayed off on purpose.
- Learned: Music.app does not pick up tag changes from files. We had to tell Music itself.
- Agreed not to let Beets become the library.
- Cleaned up the Music app itself: 625 duplicate entries pointing at one file removed, 375 broken “!” entries relinked to the real audio. The audio was never touched.
- Taught the crate to identify tracks by sound, then made mix CDs and compilations read correctly.
- Named the stem job **STEMIT** and ran a real playlist through it end to end.
- Stripped `EDM, …` off the tracks that came back from the migration drive (twice — it is a cockroach), dropped replicant rows, un-ID3'd the WAVs, and evicted the leftover `!` ghosts. The crate is playable. The fights are written down.

### Still ahead (not done)

- Run the remaining genre batches through STEMIT (Alternative is next, 3 tracks first as a check).
- Fill *empty* genres when Beatport works again. Do not blast the old EDM set.
- While processing, stamp owned songs with whatever we already know or can look up (artist, album, title, genre, length, BPM, key, comments, cues). Python module; same kind of store databases OneTagger uses. Do not smash STEM files or overwrite Mixed in Key / ReCK when those are already set. For STEMs, keep that data beside the file as JSON in the same folder tree, so Traktor’s four decks stay intact.
- Wire the DJ decks into Unreal so the visuals follow the music.
- Bigger audio path, then sampling decks into Maschine / S88 — written down, not wired.

### Where we are headed — Elysium

Valhalla is the mead-hall of the work. The crate wars, the relinks, the genre pass: fights won in the hall of the slain, seat earned, then the next horn sounds. We do not stay. The hall is for conquest. The destination is **Elysium** — the green field after the last fight, where the worthy rest and the living work begins.

In Elysium the process holds itself. The library is stable. Hands leave the warehouse and go to the floor:

- Creative visuals — Unreal, light, the sim that follows the drop.
- DJing — the crate as an instrument, not a cleanup job.
- Music manipulation and creation — stems, samples, Maschine, the S88, making rather than mending.

The still-ahead list above is the last ships to burn before that shore. Elysium is not a new repo. It is ix when the fights are written down and the nights are for sight and sound.

## What this repo is

A **control plane**. It holds architecture, OSC contracts, abstract MCP schemas, a rehearsal hall for Niagara cache scrubbing, and a loopback OSC runtime.

It does **not** hold Ollama, model weights, live MCP configs, or hardware adapters. Those live outside git:

| Off-repo | Purpose |
| --- | --- |
| `~/local_tools/ollama` | Ollama prefix and models |
| `~/local_tools/mcp_adapters` | Rekordbox, Ableton, Houdini, … |
| `~/.cursor/mcp.json` | Global Cursor MCP |

Every socket this project opens binds `127.0.0.1`. `0.0.0.0` is rejected.

## Run

```bash
mkdir -p ~/github/ixamal
git clone git@github.com:ixamal/ix.git ~/github/ixamal/ix
cd ~/github/ixamal/ix
npm install
./scripts/install-local-tools.sh
npm run dev          # http://127.0.0.1:47241
npm run runtime      # OSC 127.0.0.1:9000
```

Ollama is installed off-repo (Homebrew CLI + LaunchAgent). Bind loopback only:

```bash
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS=~/local_tools/ollama/models
```

Point Cursor Models at `http://127.0.0.1:11434/v1`. Full steps: `docs/local-setup.md`.

## Halls

- **Engine** — UE 5.x Niagara 3D fluids + 15s sim cache, OSC scrub
- **Forge** — Blender / Maya / Houdini (optional HDAs later)
- **Stage** — Ableton / Reaper OSC with a command allowlist
- **Floor** — Rekordbox / Traktor / Pro DJ Link
- **Oracle** — local Ollama, never vendored here

## Docs

- `.cursor/context.md` — notes for desktop and iPhone Cloud Agents
- `docs/architecture.md`
- `docs/security.md`
- `docs/local-setup.md`
- `docs/crate.md` — crate identity, Music.app toolkit (`music-*`, consolidate, riff-repair, STEMIT), and the scars we do not want to earn twice
- `docs/djcu2.md` — Traktor ↔ Rekordbox via [ATGR DJCU2](https://atgr.nl/)
- `docs/onetagger.md` — genre pass (files + Music.app); not an LLM
- `docs/examples/music-set-genre.applescript` — generic Music.app `set genre` specimen (do not run)
- `docs/TODO.md` — ordered checklist (crate, tagging, Floor, NI)
- `docs/notes.md` — crate / tagging / hardware parking lot (do not execute from it)
- [ixamal/blackhole](https://github.com/ixamal/blackhole) — S8 / S88 / BlackHole routing (off this repo)
- [ixamal/ix_bangers](https://github.com/ixamal/ix_bangers) — Bangers MCP catalog, dry mode (off this repo)

Apache-2.0. See `LICENSE`.
