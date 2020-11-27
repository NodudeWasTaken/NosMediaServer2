import os, re, hashlib, subprocess, json, threading, multiprocessing
from concurrent.futures.thread import ThreadPoolExecutor
from ffmpeg import FFMpeg

#Allowed video extensions
videxts = (
	".webm",
	".mkv",
	".flv",
	".vob",
	".ogv",".ogg",
	".drc",
	".mng",
	".avi",
	".mts",".m2ts",".ts",
	".mov",".qt",
	".wmv",
	".yuv",
	".rm",
	".rmvb",
	".asf",
	".amv",
	".mp4",".m4p",".m4v",
	".mpg",".mp2",".mpeg",".mpe",".mpv",
	".m2v",
	".svi",
	".3gp",
	".3g2",
	".mxf",
	".roq",
	".nsv",
	".flv",".f4v",".f4p",".f4a",".f4b",
	".gifv", #This is just a covername for a videotype, gifv is not a real media container type
)

#Allowed image extensions
imgexts = (
	".tif",".tiff",
	".bmp",
	".jpg",".jpeg",".jp2",".jpx",".mjpeg",".jfif",
	".gif",
	".png",".apng",
	".eps",
	".raw",".cr2",".nef",".orf",".sr2",
	".heic",".hevc",
)

def atoi(text):
	return int(text) if text.isdigit() else text
def natural_keys(text):
	'''
	alist.sort(key=natural_keys) sorts in human order
	http://nedbatchelder.com/blog/200712/human_sorting.html
	(See Toothy's implementation in the comments)
	'''
	return [ atoi(c) for c in re.split(r'(\d+)', text) ]
def getext(name):
	return name[name.rfind("."):].lower()
def ffprobe(file):
	try:
		return json.loads(subprocess.check_output([
			"ffprobe",
			"-show_format",
			"-show_streams",
			"-loglevel", "quiet",
			"-print_format", "json",
			file
		]).decode("utf-8"))
	except subprocess.CalledProcessError as e:
		return None

#Global variables LOL
service_folder = None
thumbnail_height = None

probes_folder = None
thumbnails_folder = None
codes_folder = None
avc_table = None
hevc_table = None

class MediaFile:
	def __init__(self, path, hash):
		self.path = path
		self.hash = hash
		self.data = None
		self.stored = os.path.join(probes_folder, self.hash) + ".json"

	def scan(self):
		if (self.data != None):
			return

		if (os.path.exists(self.stored)):
			with open(self.stored, "r") as f:
				self.data = json.load(f)
		else:
			self.data = ffprobe(self.path)
			if (self.data == None):
				return

			with open(self.stored, "w") as f:
				json.dump(self.data, f)
		
		self.generateThumbnail()

	def generateThumbnail(self):
		self.scan()

		return NotImplemented

	def getSize(self):
		self.scan()

		width = 0
		height = 0

		if (self.data == None):
			return (0,0)

		for i in self.data["streams"]:
			if (i["codec_type"] == "video"):
				width = i["width"]
				height = i["height"]
				break
		
		return (width, height)

	def getThumbnailPath(self):
		self.scan()
		self.generateThumbnail()
		return os.path.join(thumbnails_folder, self.hash + ".jpeg")


	def getPath(self):
		return self.path

	def start(self):
		self.scan()

		return NotImplemented

class VideoFile(MediaFile):
	def __init__(self, path, hash):
		super().__init__(path, hash)

	def generateThumbnail(self):
		super().generateThumbnail()
		file=os.path.join(thumbnails_folder, self.hash + ".png")
		file2=os.path.join(thumbnails_folder, self.hash + ".jpeg")

		if (os.path.exists(file2)):
			return

		#TODO: Remove this and only use convert, just set frame to fps*10
		time = 10
		dur = int(eval(self.data["format"]["duration"]))
		if (dur <= time):
			time = int(dur/2)

		if (not os.path.exists(file2)):
			#Extract frame
			res = subprocess.run([
				"ffmpeg",
				"-i", self.path,
				"-ss", str(time), #10 seconds in
				"-vframes", "1",
				file
			])
			if (res.returncode == 1):
				print(self.hash + "'s media is invalid!")
			else:
				#Resize and convert
				os.system("magick {0} -geometry x{1} {2} && rm -rf {0}".format(
						file, 
						thumbnail_height,
						file2
					)
				)

	def getScriptPath(self):
		#TODO: Shorten, at some point
		file_path = self.getPath()
		script_input = file_path[:file_path.rfind(".")]

		#TODO: ini and json support
		if (os.path.exists(script_input + ".csv")):
			return script_input + ".csv"
		elif (os.path.exists(script_input + ".funscript")):
			return script_input + ".funscript"
		else:
			return None

	def isHandy(self):
		return self.getScriptPath() != None


	def start(self, request):
		super().start()
		inst = FFMpeg(self, request.user_agent, codes_folder, avc_table, hevc_table)
		inst.process(request) 
		#TODO: Should the media itself keep track of the instances it has started?
		#Probably
		#Later
		#This would require us to remove this start and ask the MediaDirectory class to start a file
		return inst

class ImageFile(MediaFile):
	def __init__(self, path, hash):
		super().__init__(path, hash)
		#TODO: "convert test.heic json:"?

	def generateThumbnail(self):
		super().generateThumbnail()
		file=os.path.join(thumbnails_folder, self.hash + ".jpeg")

		if (os.path.exists(file)):
			return

		if (not os.path.exists(file)):
			res = subprocess.run([
				"magick",
				self.path + "[0]", #[0] is for gif support
				"-geometry", "x{}".format(thumbnail_height),#25x = 25 width, x25 = 25 height
				file
			])
			if (res.returncode == 1):
				print(self.hash + "'s media is invalid!")

class MediaDirectory:
	def __init__(self, folders, service_folder_l, thumbnail_height_l, should_preprobe, avc_tbl, hevc_tbl):
		global service_folder
		global thumbnail_height
		global probes_folder
		global thumbnails_folder
		global codes_folder
		global avc_table
		global hevc_table

		service_folder = service_folder_l
		thumbnail_height = thumbnail_height_l

		probes_folder = os.path.join(service_folder, "media_probes")
		thumbnails_folder = os.path.join(service_folder, "covers")
		codes_folder = os.path.join(service_folder, "encodes")
		avc_table = avc_tbl
		hevc_table = hevc_tbl

		try:
			os.makedirs(probes_folder)
		except:
			pass
		try:
			os.makedirs(thumbnails_folder)
		except:
			pass
		try:
			os.makedirs(codes_folder)
		except:
			pass

		self.folders = folders

		self.file_browser = None
		self.video_files = None
		self.image_files = None
		self.scanning_thread = None
		self.should_preprobe = should_preprobe

		self.scan()
		print("Ready!")

	def scan(self):
		if (self.scanning_thread != None and self.scanning_thread.is_alive()):
			return True

		self.file_browser = {}
		self.video_files = {}
		self.image_files = {}

		for i in self.folders:
			name = i[i.rfind("/")+1:]
			self.file_browser[name] = {}
			self._traverse(self.file_browser[name],i)

		if (self.should_preprobe):
			self.scanning_thread = threading.Thread(target=self.preprobe, args=())
			self.scanning_thread.start()

		return False

	def preprobe(self):
		#TODO: max_workers should be amount of cores
		with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
			for i in self.video_files:
				executor.submit(self.video_files[i].scan)
			for i in self.image_files:
				executor.submit(self.image_files[i].scan)

		for i in os.listdir(probes_folder):
			path = os.path.join(probes_folder, i)
			hash = i[:i.rfind(".")]
			if not hash in self.video_files and not hash in self.image_files:
				os.remove(path)

		for i in os.listdir(thumbnails_folder):
			path = os.path.join(thumbnails_folder, i)
			hash = i[:i.rfind(".")]
			if not hash in self.video_files and not hash in self.image_files:
				os.remove(path)


	def _traverse(self,dict,folder):
		lsdir = os.listdir(folder)
		lsdir.sort(key=natural_keys)

		for name in lsdir:
			path = os.path.join(folder,name)

			if (os.path.isfile(path)):
				ext = getext(name)
				#Python sha256 is really slow LUL
				#Should switch back to sha1
				#TODO: Multi platform support (fix slashes between unix and windows)
				#Maybe by going by each seperator and feeding sha256
				#Also other places
				hash = hashlib.sha256(path.encode("utf8")).hexdigest()

				if (ext in videxts):
					dict[name] = hash
					self.video_files[hash] = VideoFile(path, hash)
				elif (ext in imgexts):
					dict[name] = hash
					self.image_files[hash] = ImageFile(path, hash)
			else:
				dict[name] = {}
				self._traverse(dict[name],path)

	def getMedia(self, hash):
		if hash in self.video_files:
			return self.video_files[hash]
		elif hash in self.image_files:
			return self.image_files[hash]
		else:
			return None

