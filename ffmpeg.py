from script_converter import convert_script_funscript
import subprocess, os, time, json


def isImageSubtitle(codec_name):
	#https://trac.ffmpeg.org/wiki/ExtractSubtitles
	return codec_name in [
		"dvb_subtitle",
		"dvd_subtitle",
		"hdmv_pgs_subtitle",
	]

#TODO: Check version https://caniuse.com/#feat=hevc
def canHEVC(user_agent):
	browser = user_agent.browser
	version = user_agent.version and int(user_agent.version.split(".")[0])
	platform = user_agent.platform
	uas = user_agent.string

	#edge and ie depends on hw support, so we don't know
	#edge's hevc also works badly LOL
	#or ("Edg/" in uas or "EdgA/" in uas) 
	#Edge hevc does not work on playlists, but works on direct mp4
	return browser == "safari" or browser == "ie" or platform == "iphone"# or platform == "android"


class FFMpeg:
	def __init__(self, vid, ua, folder, accel_avc, accel_hevc):
		#TODO: Acceleration
		self.vid = vid
		self.ua = ua
		self.folder = folder
		self.accel_avc = accel_avc
		self.accel_hevc = accel_hevc
		self.active_process = None
		self.data = {
			"subs": [],
			"script_url": None,
			"VRType": "NONE",
		}

		self.vid.scan()

		for i in self.vid.data["streams"]:
			if i["codec_type"] == "audio":
				self.audio_type=i["codec_name"]
			if i["codec_type"] == "video":
				self.video_type=i["codec_name"]
				self.pixel_format=i["pix_fmt"]

	def nvenc_sizeadjust(self, is_hevc):
		#Max width in nvenc is 4096, some video's exceed this, so limit

		size = self.vid.getSize()
		width = size[0]
		height = size[1]

		#TODO: This is a per generation limit
		#Also pix_fmt limits
		#nvenc_h264: 4096x4096
		#nvenc_h265: 8192x8192 if Pascal>=Architecture else 4096x4096

		if (is_hevc):
			if (width > 8192 or height > 8192):
				if (width > height):
					return [
						"-vf", "scale=8192:-1"
					]
				else:
					return [
						"-vf", "scale=-1:8192"
					]
			return []
		else:
			if (width > 4096 or height > 4096):
				if (width > height):
					return [
						"-vf", "scale=4096:-1"
					]
				else:
					return [
						"-vf", "scale=-1:4096"
					]
			return []

		return []


	def getH264Args(self):
		"""
		V..... libx264              libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (codec h264)
		V..... libx264rgb           libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 RGB (codec h264)
		V..... h264_nvenc           NVIDIA NVENC H.264 encoder (codec h264)
		V..... h264_omx             OpenMAX IL H.264 video encoder (codec h264)
		V..... h264_qsv             H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (Intel Quick Sync Video acceleration) (codec h264)
		V..... h264_v4l2m2m         V4L2 mem2mem H.264 encoder wrapper (codec h264)
		V..... h264_vaapi           H.264/AVC (VAAPI) (codec h264)
		V..... nvenc                NVIDIA NVENC H.264 encoder (codec h264)
		V..... nvenc_h264           NVIDIA NVENC H.264 encoder (codec h264)
		"""
		video_h264 = self.accel_avc
		if ("h264_nvenc" in video_h264):
			video_h264.extend(self.nvenc_sizeadjust(False))

		return video_h264

	def getH265Args(self):
		"""
		V..... libx265              libx265 H.265 / HEVC (codec hevc)
		V..... nvenc_hevc           NVIDIA NVENC hevc encoder (codec hevc)
		V..... hevc_nvenc           NVIDIA NVENC hevc encoder (codec hevc)
		V..... hevc_qsv             HEVC (Intel Quick Sync Video acceleration) (codec hevc)
		V..... hevc_v4l2m2m         V4L2 mem2mem HEVC encoder wrapper (codec hevc)
		V..... hevc_vaapi           H.265/HEVC (VAAPI) (codec hevc)
		V..... libsvt_hevc          SVT-HEVC(Scalable Video Technology for HEVC) encoder (codec hevc)
		"""
		#TODO: Bring back custom h265 encoders
		video_h265 = self.accel_hevc
		if ("hevc_nvenc" in video_h265):
			video_h265.extend(self.nvenc_sizeadjust(True))

		return video_h265

	def stop(self):
		self.active_process.terminate()
		os.system("rm -rf {}".format(os.path.join(self.folder, self.vid.hash)))

	def process(self, request):
		audiorate = request.args.get("audio-rate")
		forced_transcode = request.args.get("force-transcode")
		forced_codec = request.args.get("video-codec")
		videorate = request.args.get("video-rate")
		subtrack = request.args.get("hardsub-track")

		if (self.active_process != None and self.active_process.poll() == None): #poll() == None means alive, it's dumb.
			return

		#FFMpeg process
		arguments = [
			"ffmpeg",
			"-hwaccel", "auto", #Automatic decoding acceleration
			#-hwaccel cuda -hwaccel_output_format cuda #BROKEN WITH b-frames and pix_fmt setting, no full gpu transcoding for you :)
			"-i",self.vid.path,
			"-strict", "experimental",
		]
		
		#Audio processing
		audio_aac = [
			"-c:a","aac",
		]
		audio_cp = [
			"-c:a","copy",
		]

		try:
			os.makedirs(os.path.join(self.folder, self.vid.hash))
		except:
			pass

		if (audiorate != None):
			#TODO: Fix audio_aac bitrate
			audio_aac.extend(["-b:a",audiorate])
		else:
			audio_aac.extend(["-b:a","128k"])

		for i in self.vid.data["streams"]:
			if (i["codec_type"] == "audio"):
				#WARNING: hls does not support audio track names, so not a bug
				#TODO: Broken in edge, adds some soundhandler
				arguments.extend([
					"-map","0:{}".format(i["index"]),
				])
				#BUG: Force Stereo dosen't work with copy, so we might aswell just process the audio
				#it takes like 5 seconds anyway
				arguments.extend(audio_aac)
				#Force Stereo (because HLS dosen't work with more than 2 channels)
				arguments.extend(["-ac", "2"])


		#Video Processing
		shouldprocess = False
		hls_videos = ["h264","h265","avc","hevc"]

		#Hardcoded subtitles
		for i in self.vid.data["streams"]:
			#Default track
			if (i["codec_type"] == "video"): # and i["disposition"]["default"] == 1
				#Add bitmap based subtitles
				if (subtrack != None):
					subtrack=int(subtrack)
					arguments.extend([
						"-filter_complex", "[0:v:{}][0:s:{}]overlay[v]".format(i["index"],subtrack),
						"-map", "[v]",
						"-force_key_frames","0:" + str(i["index"]) #TODO: Why?
					])
					#You cannot use streamcopy with filter_complex
					shouldprocess = True
				else:
					arguments.extend([
						"-map","0:" + str(i["index"]),
						"-force_key_frames","0:" + str(i["index"])
					])

		#TODO: Better pixel_format handling
		video_h264 = self.getH264Args()
		video_h265 = self.getH265Args()

		video_cp = [
			"-c:v","copy",
		]

		#TODO: Retain fps?

		#Really anyone with native, i think chrome and firefox for android too
		if (canHEVC(self.ua)): 
			for i in self.vid.data["streams"]:
				if (i["codec_type"] == "video"):
					args = []

					def addifexist(probe, arg):
						if (probe in i):
							args.extend([
								arg, i[probe], 
							])

					#Pixel format
					addifexist("pix_fmt", "-pix_fmt")
					#HDR Support
					addifexist("color_range", "-color_range")
					addifexist("color_space", "-colorspace")
					addifexist("color_transfer", "-color_trc")
					addifexist("color_primaries", "-color_primaries")

					video_h264.extend(args)
					video_h265.extend(args)
					break
		else: #Anyone with OpenH264
			args = [
				"-pix_fmt", "yuv420p"
			]
			#TODO: Comply with level requirements and such

			video_h264.extend(args)
			video_h265.extend(args)


		#TODO: Seperate function
		if (forced_codec != None and forced_codec in hls_videos):
			if (forced_codec == "h265" and (not self.IsHEVC() or forced_transcode != None)):
				arguments.extend(video_h265)
				print("Forcibly transcoding media as H265!")
			elif (forced_codec == "h264" and (not self.IsAVC() or forced_transcode != None)):
				arguments.extend(video_h264)
				print("Forcibly transcoding media as H264!")
			else:
				arguments.extend(video_cp)
				print("Forcibly copying media!")
		else:
			#TODO: Better detection for odd video settings that browsers can't handle

			"""
			https://en.wikipedia.org/wiki/HTML5_video
			Wtf is Android browser, it supports everything
			I want that

			Chrome, Firefox and alot more probably
				just use Cisco OpenH264 (https://github.com/cisco/openh264)
				This supports h264 baseline profile upto level 5.2 and yuv420p only
				audio is unknown, probably pr. browser, just guess aac

			Safari
				Apple us usually really good about documenting stuff, so search
				https://developer.apple.com/documentation/webkit/safari_tools_and_features/delivering_video_content_for_safari

				https://developer.apple.com/documentation/http_live_streaming/hls_authoring_specification_for_apple_devices
				Some interesting takes:
				1.3b. * Profile and Level for H.264 MUST be less than or equal to High Profile, Level 5.2.
				1.6b. Profile, Level, and Tier for HEVC MUST be less than or equal to Main 10 Profile, Level 5.1, High Tier.
				1.7. High Dynamic Range (HDR) HEVC video MUST be HDR10, HLG, or DolbyVision.
				1.14. All interlaced source content MUST be deinterlaced.
				1.21. Streams SHOULD use a single color space—one of either Rec. 601, Rec. 709, DCI-P3, or Rec. 2020.
				There is a recommended bitrate table for each resolution pr framerate
				2.2. Stereo audio formats are:
					AAC-LC
					HE-AAC v1
					HE-AAC v2
					xHE-AAC
					Apple Lossless
					FLAC
					Multichannel formats that only carry stereo
				#Thats hls though, not direct Safari support, thought it might also be that

			Edge
				i really don't know, unlike Apple and Mozilla, Microsoft and Google suck at documenting
				Theoratically they support h264 and h265* 
				https://docs.microsoft.com/en-us/microsoft-edge/#microsoft-edge-for-developers
				But it doesn't say anything about it
				It can be MS Media Foundation: 
				https://docs.microsoft.com/en-us/windows/win32/medfound/h-264-video-decoder
				but it can be with the flag #edge-mf-clear-playback-win10 in edge://flags
				#edge-playready-drm-win10 is also a thing
				So its not that, necessarily
				https://docs.microsoft.com/en-us/openspecs/ie_standards/ms-html5/4257eddd-d92e-4ef0-88d5-b7accc73e094

			"""

			#Detect if we should process video
			if (not shouldprocess):
				if (not self.video_type in hls_videos): #Not HLS Compatible
					shouldprocess = True
				else: #HLS Compatible
					if (self.IsHEVC()):
						print("Is hevc")
						if (canHEVC(self.ua)):
							print("Can hevc")
							#TODO: HEVC for Edge and perhaps Safari checks here
							shouldprocess = False
						else:
							print("Can't hevc")
							shouldprocess = True
					else:
						#TODO: OpenH264 checks here
						shouldprocess = False

			if (shouldprocess):
				print("Incompatible video_type: {} for {}".format(self.video_type, self.ua.browser))

			if (forced_transcode or videorate != None):
				shouldprocess = True
				print("Forced transcoding on!")

			"""
			See: https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Video_codecs
			"""
			
			#Process if needed
			if (shouldprocess):
				if (canHEVC(self.ua)):
					arguments.extend(video_h265)
					print("Transcoding media as H265")
				else:
					arguments.extend(video_h264)
					print("Transcoding media as H264")
			else:
				#TODO: If this is the case, just serve the file directly instead of doing this
				#Only if mp4 though
				print("Copying media!")
				arguments.extend(video_cp)
				
			if (videorate != None):
				arguments.extend("-b:v",videorate)


			#TODO: Render at constant speed?
			#https://stackoverflow.com/questions/46602042/keep-ffmpeg-render-as-constant-speed-3x

			"""
			-tune
				film – use for high quality movie content; lowers deblocking
				animation – good for cartoons; uses higher deblocking and more reference frames
				grain – preserves the grain structure in old, grainy film material
				stillimage – good for slideshow-like content
				fastdecode – allows faster decoding by disabling certain filters
				zerolatency – good for fast encoding and low-latency streaming
				psnr – ignore this as it is only used for codec development
				ssim – ignore this as it is only used for codec development 
			"""

		#TODO: Allow setting if movie is animation or film
		arguments.extend([
			#"-tune","fastdecode",
		])

		#DASH Settings
		#TODO: Consider using Shaka Packager
		arguments.extend([
			"-f","dash",
			"-dash_segment_type", "mp4",
			"-seg_duration","10",

			#"-single_file","1",
			#"-use_template","1",
			#"-index_correction","1",
			#"-streaming","1",

			"-hls_playlist","1", #Name: master.m3u8
			os.path.join(self.folder, self.vid.hash, "master.mpd")
		])
		"""arguments.extend([
			"-f","hls",
			"-hls_time","10", #Recommended is 10
			#"-hls_allow_cache","1",
			"-hls_segment_type","fmp4",
			#"-hls_flags","single_file",#append_list+discont_start+temp_file+split_by_time+iframes_only+single_file
			"-hls_playlist_type","event",
			#"-var_stream_map","v:0,a:0,s:0,sgroup:subtitle",
			os.path.join(self.folder, self.vid.hash, "master.m3u8")
		])"""
		#Segment muxer
		#


		#Subtitle processing
		for i in self.vid.data["streams"]:
			if (i["codec_type"] == "subtitle" and not isImageSubtitle(i["codec_name"])):
				file = "sub{}.vtt".format(i["index"])

				arguments.extend([
					"-map","0:" + str(i["index"]),
					#"-f","vtt",
					os.path.join(self.folder, self.vid.hash, file)
				])
				title = i["tags"]["title"] if "title" in i["tags"] else None
				lang = i["tags"]["language"].replace("eng","en") if "language" in i["tags"] else None

				#Title not set
				if (title == None and lang != None):
					title=lang

				if (lang == None):
					lang="unknown"
				if (title == None):
					title="unknown"

				self.data["subs"].append({
					"default": i["disposition"]["default"] == 1,
					"title": title,
					"lang": lang,
					"file": file
				})

		#Convert existing srt (in directory or in subdirectory Subs) files to webvtt
		def addsub(folder,i):
			name = i[:i.rfind(".")]
			name = name[name.rfind("/")+1:]

			arguments.extend([
				"-i", os.path.join(folder, i),
				"-map", "{}:0".format(idx),
				os.path.join(self.folder, self.vid.hash, name + ".vtt")
			])

			self.data["subs"].append({
				"default": False,
				"title": name,
				"lang": "unk",
				"file": name + ".vtt"
			})

		idx = 1

		file_path = self.vid.path
		file_name = file_path[file_path.rfind("/")+1:]
		file_folder = file_path[:file_path.rfind("/")]

		for i in os.listdir(file_folder):
			ext = i[i.rfind("."):]
			if (ext in [
				".ass",
				".srt",
				".ssa",
			]):
				addsub(file_folder,i)
				idx = idx + 1

		_folder = os.path.join(file_folder,"Subs")
		if (os.path.exists(_folder)):
			for i in os.listdir(_folder):
				ext = i[i.rfind("."):]
				if (ext in [
					".ass",
					".srt",
					".ssa",
				]):
					addsub(_folder,i)
					idx = idx + 1



		#TODO: Limit ffmpeg speed if too far ahead
		#Perhaps use ionice to set priority lower the further it gets
		#Also monitor progress from client and ffmpeg

		#Run FFMPEG
		print(arguments)
		try:
			#TODO: Detect errors
			self.active_process = subprocess.Popen(arguments)#, stderr=subprocess.PIPE),
		except subprocess.CalledProcessError:
			print("Process failed!")
			return True

		#FIX: Flushes any print statements, to output messages in gunicorn
		print("",flush=True)

		#Fix short video
		"""try:
			dur = int(eval(self.getVideoInfo(hash)["format"]["duration"]))
			if (dur <= 10):
				file = "chunk-stream0-00001.m4s"
		except:
			print("Generic error that you didn't want to fix happened")
			pass"""

		#Handy support
		#.json .ini and .js also exist
		if self.vid.isHandy():
			self.data["script_url"] = convert_script_funscript(self.vid.getScriptPath())

		#VR support
		"""
			https://github.com/videojs/videojs-vr#user-content-projection
			180, 
			(360, Sphere, equirectangular), 
			(Cube, 360_CUBE),
			NONE,
			AUTO,
			360_LR,
			360_TB,
			EAC,
			EAC_LR,
		"""
		#Filename rules
		#https://forum.skybox.xyz/d/157-filename-rules-for-vr-format
		if ("_180" in file_name):
			self.data["VRType"] = "180"
		if ("_360" in file_name or "_180x180" in file_name):
			self.data["VRType"] = "360"
		if ("cube" in file_name):
			self.data["VRType"] = "Cube"
		if ("_3dv" in file_name):
			self.data["VRType"] = "360_TB"
		if ("_3dh" in file_name):
			self.data["VRType"] = "360_LR"
		#No fisheye support, there's an open PR, but not merged
		#F180, VR180
		if ("_EAC360" in file_name):
			self.data["VRType"] = "EAC"
		if ("_EAC360_LR" in file_name): #This is not the official name
			self.data["VRType"] = "EAC_LR"

		#Wait for stream to be ready
		until = time.time()+10 #Max 20 seconds
		#If HLS	: stream1.m4s
		#If DASH: chunk-stream0-00002.m4s
		#file = "chunk-stream0-00002.m4s"

		while (
			(
				not os.path.exists(os.path.join(self.folder, self.vid.hash, "master.m3u8"))
				and
				not os.path.exists(os.path.join(self.folder, self.vid.hash, "master.mp4"))
			)
			and until > time.time()
		):
			time.sleep(1)

		return False

	def IsHEVC(self):
		return self.video_type == "h265" or self.video_type == "hevc"

	def IsAVC(self):
		return self.video_type == "h264" or self.video_type == "avc"
