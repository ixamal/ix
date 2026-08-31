-- Specimen only. Review the process; do not run this against a live Music.app library.
-- Live copy (if any) stays off-repo: ~/local_tools/onetagger/
--
-- Why this exists (TODO 4a, 2026-08-30):
--   Music.app does not re-read file tags. Genre in Songs / the column browser
--   is the library database. Writing ID3/MP4 genre on disk left the UI unchanged.
--   File write + library write were both required.
--
-- Why one track at a time:
--   `set genre of (every track whose …)` failed on this Mac.
--   Looping tracks and setting `genre of t` worked.
--
-- What the 2026-08-30 pass did:
--   "EDM, Accapella" / "EDM, Acapella" / "Accapella" → "Acapella"
--   other "EDM, …" → drop the "EDM, " prefix ("EDM, House, Deep" → "House, Deep")
--   never .m4p (Apple Music streams)
--   never key, BPM, comments, or cues
--   Sync Library Off — keep it off
--
-- Cloud-download rows are library entries. Some have no local file.
-- They still need `set genre` if they show in the column browser.

tell application "Music"
	set edmTracks to (every track whose genre starts with "EDM, ")
	repeat with t in edmTracks
		set oldGenre to genre of t as text

		-- Skip Apple Music streams. Cloud-only library rows (no location) stay in the loop.
		set skipStream to false
		try
			set loc to location of t as text
			if loc ends with ".m4p" then set skipStream to true
		end try
		try
			set k to kind of t as text
			if k contains "protected" then set skipStream to true
		end try
		if skipStream then
			-- leave this track
		else if oldGenre is "EDM, Accapella" or oldGenre is "EDM, Acapella" or oldGenre is "Accapella" then
			set genre of t to "Acapella"
		else if oldGenre starts with "EDM, " then
			-- "EDM, " is 5 characters; AppleScript text is 1-indexed
			set genre of t to text 6 thru -1 of oldGenre
		end if
	end repeat
end tell
