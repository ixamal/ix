-- Specimen only. Review the process; do not run this against a live Music.app library.
-- Live TSV (if any) stays off-repo: ~/local_tools/crate/reports/industry-stems-artists-*.tsv
--
-- Why this exists (STEMIT Industry Stems, 2026-09-08):
--   Factory and Industry Stems WAVs live under ~/Music/stems_audio, not Songs.
--   Traktor ARTIST is collection.nml — Python ix_crate stemit --fix-industry-artists
--   patches that. Music.app does not re-read file tags, and we never mutagen-write
--   .wav (riff-repair). If a Songs row still shows artist "IndustryStems" /
--   "Industry Stems", set artist one track at a time from the TSV the Python
--   pass writes (posix_path, artist, album, title).
--
-- Why one track at a time:
--   `set artist of (every track whose …)` failed on this Mac for genre (TODO 4a).
--   Looping tracks and setting `artist of t` worked.
--
-- What the Python pass already did:
--   crate match (stems_audio Artist/Album) then iTunes/Deezer/MusicBrainz
--   never Discogs, never .wav tags, never Apple Music moves
--   STEMIT crates then keep one row per identity (Mashups / Spring Blossoms extras
--   stay on disk, drop out of the playlist)
--
-- Sync Library Off — keep it off. Never set key, BPM, comments, or cues.

property tsvPath : (POSIX path of (path to home folder)) & "local_tools/crate/reports/industry-stems-artists.tsv"

on readRows()
	set raw to read POSIX file tsvPath as «class utf8»
	set AppleScript's text item delimiters to linefeed
	set lines_ to text items of raw
	set AppleScript's text item delimiters to tab
	set rows to {}
	repeat with i from 2 to count of lines_
		set lineText to item i of lines_
		if lineText is not "" then
			set parts to text items of lineText
			if (count of parts) ≥ 4 then
				set end of rows to parts
			end if
		end if
	end repeat
	return rows
end readRows

tell application "Music"
	set hits to (every file track of library playlist 1 whose artist is "IndustryStems" or artist is "Industry Stems")
	repeat with t in hits
		set locText to ""
		try
			set locText to POSIX path of (location of t as alias)
		end try
		-- Match locText to a TSV posix_path, then:
		--   set artist of t to the TSV artist
		--   set album of t to the TSV album
		--   set name of t to the TSV title
		-- Skip .m4p / protected. Leave key, BPM, comments, cues.
	end repeat
end tell
