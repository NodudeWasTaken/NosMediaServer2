#Known bugs
4K is broken
	https://github.com/videojs/http-streaming/issues/192
	Could be fixed by direct playback if the file is mp4 and supported by browser.
	Transcoding into mp4 is also possible, but i don't know how to make chrome and firefox recognize it, and Safari doesn't support it.
HTML UI's width is longer than it should be on Safari
	Yeah im bad at html
FFMpeg -c copy sometimes produces incompatible playlists
	I don't check compatibility well enough
HLS HEVC is broken on Edge
	https://github.com/videojs/http-streaming/issues/293
	While Edge does support HEVC playback, videojs http-streaming doesn't seem to work with HEVC