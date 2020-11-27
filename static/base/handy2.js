class Hander {
	constructor() {
		//this.URL_BASE = "http://192.168.137.1:3000/";
		this.URL_BASE = "https://www.handyfeeling.com/";
		this.URL_API_ENDPOINT = "api/v1/";
		this.urlAPI = "";

		this.timeSyncMessage = 0;
		this.timeSyncAggregatedOffset = 0;
		this.timeSyncAverageOffset = 0;
		this.timeSyncInitialOffset = 0;
	}

	onReady(connectionkey, scriptUrl) {
		//URL_BASE can be local ip, but will browsers allow that?
		this.urlAPI = this.URL_BASE + this.URL_API_ENDPOINT + connectionkey;
		this.updateServerTime(); //Start time sync with the server

		//Prepare Handy by telling it where to download the script

		$.get({url: this.urlAPI + "/syncPrepare", data:{
			url: scriptUrl,
			timeout: 30000,
		}, context:this, success: function(result){
			document.getElementById("state").innerHTML += "<li>Machine reply to syncPrepare: " + JSON.stringify(result) + "</li>";
			console.log(result);
			if (result.success == true) {
				console.log("success");
			}
		}});
	}

	setOffset(ms) {
		console.log("offset",ms);

		$.get({url: this.urlAPI + "/syncOffset", data:{
			offset: ms,
			timeout: 30000,
		}, context:this, success: function(result){
			document.getElementById("state").innerHTML += "<li>Machine reply to syncOffset: " + JSON.stringify(result) + "</li>";
			console.log(result);
		}});
	}
	onPlay(videoTime) {
		videoTime = Math.round(videoTime*1000);
		console.log("playing",videoTime);

		$.get({url: this.urlAPI + "/syncPlay", data:{
			play: true,
			serverTime: this.getServerTime(),
			time: videoTime
		}, context:this, success: function(result){
			document.getElementById("state").innerHTML += "<li>Machine reply to syncPlay: " + JSON.stringify(result) + "</li>";
			console.log(result);
		}});
	}
	onPause() {
		console.log("pause");

		$.get({url: this.urlAPI + "/syncPlay", data:{
			play: false,
		}, context:this, success: function(result){
			document.getElementById("state").innerHTML += "<li>Machine reply to syncPlay: " + JSON.stringify(result) + "</li>";
			console.log(result);
		}});
	}

	/*
		sync time with server
	*/

	getServerTime(){
		let serverTimeNow = Date.now() + this.timeSyncAverageOffset + this.timeSyncInitialOffset;
		return Math.round(serverTimeNow);
	}

	updateServerTime() {
		let sendTime = Date.now();
		let url = this.urlAPI + "/getServerTime";
		// console.log("url:",url);

		$.get({url: url, context:this, success: function(result){
			// console.log(result);
			let now = Date.now();
			let receiveTime = now;
			let rtd = receiveTime - sendTime;
			let serverTime = result.serverTime;
			let estimatedServerTimeNow = serverTime + rtd /2;
			let offset = 0;
			if(this.timeSyncMessage == 0){
				this.timeSyncInitialOffset = estimatedServerTimeNow - now;
				console.log("timeSyncInitialOffset:",this.timeSyncInitialOffset);
			}else{
				offset = estimatedServerTimeNow - receiveTime- this.timeSyncInitialOffset;
				this.timeSyncAggregatedOffset += offset;
				this.timeSyncAverageOffset = this.timeSyncAggregatedOffset / this.timeSyncMessage;
			}
			console.log("Time sync reply nr " + this.timeSyncMessage + " (rtd, this offset, average offset):",rtd,offset,this.timeSyncAverageOffset);
			this.timeSyncMessage++;
			if(this.timeSyncMessage < 30){
				this.updateServerTime();
			}else{
				//Time in sync
				document.getElementById("state").innerHTML += "<li>Server time in sync. Average offset from client time: " + Math.round(this.timeSyncAverageOffset) + "ms</li>";
			}
		}});
	}
}