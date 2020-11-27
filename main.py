from flask import Flask, request, render_template, abort, send_from_directory, send_file

from media import MediaFile, VideoFile, ImageFile, MediaDirectory
from ffmpeg import canHEVC, isImageSubtitle

import os, time, threading, sys

app = Flask(__name__)
app.config.from_json("config.json")

print(app.config["SETTINGS"])
res = MediaDirectory(
	app.config["SETTINGS"]["media_folders"],
	app.config["SETTINGS"]["temporary_folder"],
	app.config["SETTINGS"]["thumbnail_height"],
	app.config["SETTINGS"]["preprobe"],
	app.config["SETTINGS"]["accel_table"][app.config["SETTINGS"]["avc_accel"]],
	app.config["SETTINGS"]["accel_table"][app.config["SETTINGS"]["hevc_accel"]],
)

def app_basepath():
	if "X-Url-Base" in request.headers:
		return request.headers["X-Url-Base"]
	return "/"

def redirect(where):
	return "<script>window.location.replace('" + app_basepath() + where + "');</script>"

@app.route("/scan", methods=["POST"])
def scandir():
	res.scan()
	return "OK", 200

@app.route("/")
def first():
	print()
	return redirect("browse/")

@app.route("/browse/")
def browseaux():
	return browse("")
@app.route("/browse/<path:path>")
def browse(path):
	folders = []
	videos = []
	images = []

	brow = res.file_browser
	name = "Index"

	fpath =""
	for i in path.split("/"):
		if i != "":
			fpath = i + "/"
			name = i

			if (not i in brow):
				return abort(403)

			brow = brow[i]

	for i in brow:
		if (isinstance(brow[i], dict)):
			folders.append({
				"name": i,
				"link": i + "/",
			})
		else:
			#TODO: Move this
			hash = brow[i]
			if (hash in res.video_files): #Video
				t = {
					"cover": hash,
					"name": i
				}

				#TODO: Allow video as "popup" in frame instead
				#TODO: Implement gifv support (inline video)

				data = res.getMedia(hash)
				width = data.getSize()[0]
				height = data.getSize()[1]

				t["width"] = width
				t["height"] = height
				t["link"] = "select/" + hash
				t["has_handy"] = data.isHandy()

				videos.append(t)
			else: #Image
				#TODO: Implement youtube-dl and ripme support
				#TODO: Implement scrolller like interface, maybe

				data = res.getMedia(hash)
				width = data.getSize()[0]
				height = data.getSize()[1]

				images.append({
					"hash": hash,
					"name": i,
					"width": width,
					"height": height
				})

	#Get client information
	browser = request.user_agent.browser
	version = request.user_agent.version and int(request.user_agent.version.split(".")[0])
	platform = request.user_agent.platform
	uas = request.user_agent.string

	print(browser)
	print(version)
	print(platform)
	print(uas)
	print(request.user_agent)

	return render_template("index.html", 
		folder_name=name,
		folders=folders,
		videos=videos,
		images=images,
		basepath=app_basepath()
	)

@app.route("/select/<string:hash>")
def selection(hash):
	global res

	if hash in videos:
		return redirect("media/{}".format(hash))

	#TODO: Modulize this better
	media = res.getMedia(hash)
	if not media:
		return abort(418)

	subtitletracks = []
	subfix = 0 #Yeah ffmpeg is wierd
	codec_type=""

	media.scan()
	for i in media.data["streams"]:
		if (i["codec_type"] == "video"):
			codec_type=i["codec_name"]
		if (i["codec_type"] == "subtitle" and isImageSubtitle(i["codec_name"])):
			subtitletracks.append((i["index"],subfix))
			subfix = subfix + 1

	#Get client information
	browser = request.user_agent.browser
	version = request.user_agent.version and int(request.user_agent.version.split(".")[0])
	platform = request.user_agent.platform
	uas = request.user_agent.string

	print(browser)
	print(version)
	print(platform)
	print(uas)
	#print(request.headers.get("User-Agent"))

	#https://unix.stackexchange.com/a/284808
	subs = []
	for (sub, idx) in subtitletracks:
		subs.append({
			"id": idx,
			"url": "hardsub-track=" + str(idx),
			"text": "Subtitle: {} ({})".format(
				media.data["streams"][sub]["tags"]["title"] if "title" in media.data["streams"][sub]["tags"] else "Unknown",
				media.data["streams"][sub]["tags"]["language"] if "language" in media.data["streams"][sub]["tags"] else "Unknown",
			)
		})

	return render_template("select.html", basepath=app_basepath(), videoid=hash, subs=subs, canHEVC=str(canHEVC(request.user_agent)), codec_type=codec_type)

videos = {}
@app.route("/media/<hash>")
def media_content_mp4(hash):
	video = res.getMedia(hash)

	if (video == None):
		return abort(400)

	if (not hash in videos): #TODO: This should be media sided
		process = video.start(request)
		videos[hash] = {
			"time": time.time(),
			"video": video,
			"process": process
		}
	else:
		process = videos[hash]["process"]

	#TODO: Bring back custom videopath, as this would help workload offloading
	#as this is single threaded.
	#or just enable multithreading :)
	return render_template(
		"play.html", 
		basepath=app_basepath(), 
		videopath=app_basepath() + "video/", 
		videoid=hash, 
		subs=process.data["subs"],
		vrtype=process.data["VRType"],
		script_url=process.data["script_url"],
		should_handy=process.data["script_url"] != None #TODO: Not needed
	)

@app.route("/poll/<string:hash>", methods=["POST"])
def poll(hash):
	if hash in videos:
		videos[hash]["time"] = time.time()
		return "OK"
	else:
		return abort(400)

#Force clients to request files (streams are temporary)
#TODO: Is this needed?
@app.after_request
def add_header(response):
	response.headers["X-UA-Compatible"] = "IE=Edge,chrome=1"
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Pragma"] = "no-cache"
	response.headers["Expires"] = "0"
	return response

#Serve video
@app.route("/video/<path:filename>")
def serve_videos(filename):
	return send_from_directory(directory=os.path.join(app.config["SETTINGS"]["temporary_folder"], "encodes"), filename=filename, conditional=True)

#Serve static files like js and css
@app.route("/serve/<path:filename>")
def req(filename):
	return send_from_directory(directory="static/", filename=filename)

#Serve image
@app.route("/image/<string:hash>")
def serve_image(hash):
	#Wait this will serve literally any media
	#Also videos
	#LOL
	return send_file(res.getMedia(hash).getPath(), conditional=True)

#Serve thumbnails
@app.route("/thumbnail/<string:hash>.jpeg")
def serve_thumbnail(hash):
	#TODO: Sometimes FileNotFoundError
	#Do we care?
	return send_file(res.getMedia(hash).getThumbnailPath(), conditional=True)

should_stop = False
keepalive_thread = None
def check_old():
	while(not should_stop):
		for key in list(videos.keys()):
			try:
				i = videos[key]
				if (i["time"] + app.config["SETTINGS"]["ttl"] < time.time()):
					print("Removing inactive media {}".format(key))
					i["process"].stop()
					del videos[key]
			except:
				print("Removal of {} failed!".format(key))

		time.sleep(5)

def savecounter():
	global should_stop

	print("Builtin Exiting...")
	should_stop = True

	for key in list(videos.keys()):
		i = videos[key]
		i["process"].stop()
		del videos[key]

	keepalive_thread.join(10)

	sys.exit(0)

import atexit
atexit.register(savecounter)

keepalive_thread = threading.Thread(target=check_old)
keepalive_thread.start()

if __name__ == "__main__":
	app.run(host="0.0.0.0", threaded=True)
