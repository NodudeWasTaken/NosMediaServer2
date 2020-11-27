import requests, json, sys, html
import urllib.request

#TODO: .json .ini and .js also exist
#scriptplayer can convert all of them, but i don't have a way of interfacing with it yet
def convert_script_funscript(input_file):
	#Handyfeeling rejects files over 2MB
	#So we convert to csv per default avoid that
	#Since it turns 2355KB into 127KB, and that script is an hour
	if (input_file.endswith(".funscript")):
		old_input_file = input_file
		input_file = input_file.replace(".funscript", ".csv")
		convert_funscript_to_csv(old_input_file, input_file)

	filename = input_file[input_file.rfind("/")+1:]

	multipart_form_data = {
		"syncFile": (filename, open(input_file, "rb")),
	}

	response = requests.post("https://www.handyfeeling.com/api/sync/upload", files=multipart_form_data)

	#413 Request entity too large
	if (response.status_code != 200):
		print(response.text)
		print(response.status_code)
		return None

	data = json.loads((response.content).decode("utf-8"))

	print(data, file=sys.stderr)

	return html.unescape(data["url"])

def convert_funscript_to_csv(input_file,output_file):
	with open(input_file) as fr:
		jsn = json.load(fr)
		with open(output_file, "w") as fw:
			fw.write("#Converted to CSV using script_converter.py")
			#BUT WHAT ABOUT MUH SETTINGS
			#fuckem
			for i in jsn["actions"]:
				fw.write("{},{}\r\n".format(i["at"],i["pos"]))

if __name__ == "__main__":
	print("Testing!")
	print(convert_script_funscript(
		"Z:\\extrafiles\\MBad2\\Interactive\\vids\\ch_descent_e2_v1.funscript"
	))