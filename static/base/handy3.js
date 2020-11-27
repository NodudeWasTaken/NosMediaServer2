//Stolen from https://www.handyfeeling.com/
const getServerTime = (
    timeSyncAverageOffset,
    timeSyncInitialOffset
) => {
    let serverTimeNow =
        Date.now() + timeSyncAverageOffset + timeSyncInitialOffset;
    return Math.round(serverTimeNow);
};

/* TheHandy SDK Controller
------------------------------------------------ */
export var TheHandy = function (config) {
    // Constructor here
    this.config = {
        apiURL: config.apiURL,
        connectionKey: config.connectionKey,
        videoSelector: config.videoSelector,
        connected: false,
        debug: config.debug,
        onSuccess: config.onSuccess,
        onError: config.onError,
        requestTimeout: 300000,
        saveConnectionKeyToCookie: config.saveConnectionKeyToCookie
    };
}

TheHandy.prototype.connect = function (connectionKey, callbacks) {
    connectHandy(this, connectionKey, callbacks);
}

TheHandy.prototype.disconnect = function () {
    localStorage.removeItem('HandyConnectionKey');
    this.config.connected = false;
}

TheHandy.prototype.getStatus = function (connectionKey, callbacks) {
    getStatus(this, connectionKey, callbacks);
}

TheHandy.prototype.getVersion = function (connectionKey, callbacks) {
    checkHandyVersion(this, connectionKey, callbacks);
}

TheHandy.prototype.getServerTime = function (connectionKey, callbacks) {
    handleGetServerTime(this, connectionKey, callbacks);
}

TheHandy.prototype.syncVideoPlayer = function (connectionKey, callbacks) {
    syncVideoPlayer(this, callbacks)
}

TheHandy.prototype.syncPrepare = function (connectionKey, scriptUrl, callbacks) {
    syncPrepare(this, connectionKey, scriptUrl, callbacks)
}

TheHandy.prototype.syncPlay = function (connectionKey, requestParameters, callbacks) {
    syncPlay(this, connectionKey, requestParameters, callbacks)
}

TheHandy.prototype.syncAdjustTimestamp = function (connectionKey, requestParameters, callbacks) {
    syncAdjustTimestamp(this, connectionKey, requestParameters, callbacks)
}

TheHandy.prototype.syncOffset = function (connectionKey, offsetAmount, callbacks) {
    syncOffset(this, connectionKey, offsetAmount, callbacks)
}

TheHandy.prototype.resyncHandy = function (connectionKey, callbacks) {
    resyncHandy(this, connectionKey, callbacks)
}

TheHandy.prototype.toggleMode = function (connectionKey, params, callbacks) {
    toggleMode(this, connectionKey, params, callbacks)
}

TheHandy.prototype.stepStroke = function (connectionKey, params, callbacks) {
    stepStroke(this, connectionKey, params, callbacks)
}

TheHandy.prototype.setSpeed = function (connectionKey, params, callbacks) {
    setSpeed(this, connectionKey, params, callbacks)
}

TheHandy.prototype.setStroke = function (connectionKey, params, callbacks) {
    setStroke(this, connectionKey, params, callbacks)
}

TheHandy.prototype.stepSpeed = function (connectionKey, params, callbacks) {
    stepSpeed(this, connectionKey, params, callbacks)
}

TheHandy.prototype.getSettings = function (connectionKey, callbacks) {
    getSettings(this, connectionKey, callbacks)
}

TheHandy.prototype.remoteOta = function (connectionKey, params, callbacks) {
    remoteOta(this, connectionKey, params, callbacks)
}

TheHandy.prototype.getOtaProgress = function (connectionKey, params, callbacks) {
    getOtaProgress(this, connectionKey, params, callbacks)
}
TheHandy.prototype.convertFunscriptToCSV = function (headers, items, fileTitle, callbacks) {
    return convertFunscriptToCSV(headers, items, fileTitle, callbacks)
}

TheHandy.prototype.fileUpload = function (url, data, callbacks) {
    fileUpload(url, data, callbacks)
}

function connectHandy(handy, connectionKey, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/getVersion?timeout=${handy.config.requestTimeout}`)
        .then(response => response.json())
        .then(data => {
            handy.config.connected = data.connected;

            if (data.success) {
                if (handy.config.saveConnectionKeyToCookie) {
                    localStorage.setItem('HandyConnectionKey', handy.config.connectionKey);
                }

                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }

                if (handy.config.debug) {
                    console.log("connect response data: ", data);
                }

            } else {
                if (handy.config.debug) {
                    console.error("connect response data: ", data);
                }
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
            }
        })
        .catch((err) => {
            console.error('Could not connect to your handy device!');
            if (callbacks) {
                if (callbacks.onError) {
                    callbacks.onError(err);
                }
            }
        });
}

function checkHandyVersion(handy, connectionKey, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/getVersion?timeout=${handy.config.requestTimeout}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log("version response data: ", data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("version response error: ", data)
                }
            }
        })
        .catch((err) => {
            console.error(err);
        });
}

function getStatus(handy, connectionKey, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/getStatus?timeout=${handy.config.requestTimeout}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("status response error: ", data)
                }
            } else {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log("status response data: ", data);
                }
            }
        });
}

function syncPrepare(handy, connectionKey, scriptUrl, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/syncPrepare?` + new URLSearchParams({
        url: scriptUrl,
        timeout: handy.config.requestTimeout
    }))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log("syncPrepare response: ", data)
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("syncPrepare error: ", data)
                }
            }
        })
        .catch((err) => {
            console.error(err);
            if (handy.config.debug) {
                console.error("status response error: ", err)
            }
        });
}

function syncVideoPlayer(handy, callbacks) {
    let timeSyncMessage = 0;
    let timeSyncAggregatedOffset = 0;
    let timeSyncAverageOffset = 0;
    let timeSyncInitialOffset = 0;
    const handyInitialOffset = Number(getCookie("handyInitialOffset"));
    const handyAverageOffset = Number(getCookie("handyAverageOffset"));

    function updateServerTime() {
        const sendTime = Date.now();

        fetch(`${handy.config.apiURL}/${handy.config.connectionKey}/getServerTime?timeout=${handy.config.requestTimeout}`)
            .then(response => response.json())
            .then(data => {
                let now = Date.now();
                let receiveTime = now;
                let rtd = receiveTime - sendTime;
                let serverTime = data.serverTime;
                let estimatedServerTimeNow = serverTime + rtd / 2;
                let offset = 0;

                if (timeSyncMessage === 0) {
                    timeSyncInitialOffset = estimatedServerTimeNow - now;
                } else {
                    offset =
                        estimatedServerTimeNow - receiveTime - timeSyncInitialOffset;
                    timeSyncAggregatedOffset += offset;
                    timeSyncAverageOffset = timeSyncAggregatedOffset / timeSyncMessage;
                }

                console.log('getServerTime', rtd, offset, timeSyncAverageOffset);

                timeSyncMessage++;
                if (timeSyncMessage < 30) {
                    updateServerTime();
                }
                if (timeSyncMessage === 30) {
                    setCookie("handyAverageOffset", timeSyncAverageOffset);
                    setCookie("handyInitialOffset", timeSyncInitialOffset);
                }
            });
    }

    if (!handyInitialOffset && !handyAverageOffset && handy.config.connectionKey) {
        updateServerTime();
    }

    const serverTime = getServerTime(
        handyAverageOffset,
        handyInitialOffset
    );

    handy.videoElement = document.querySelector(handy.config.videoSelector);

    handy.videoElement.addEventListener('playing', function () {
        const videoTime = Math.round(this.currentTime * 1000);
        console.log("videoTime: ", videoTime);

        fetch(`${handy.config.apiURL}/${handy.config.connectionKey}/syncPlay?` + new URLSearchParams({
            play: true,
            serverTime: serverTime,
            time: videoTime,
            timeout: handy.config.requestTimeout
        }))
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (callbacks) {
                        if (callbacks.onSuccess) {
                            callbacks.onSuccess(data);
                        }
                    }
                } else {
                    if (callbacks) {
                        if (callbacks.onError) {
                            callbacks.onError(data);
                        }
                    }
                }
            })
            .catch((err) => {
                console.error(err);
            });
    });

    handy.videoElement.addEventListener('pause', function () {
        fetch(`${handy.config.apiURL}/${handy.config.connectionKey}/syncPlay?` + new URLSearchParams({
            play: false,
            timeout: handy.config.requestTimeout
        }))
            .then(response => response.json())
            .then(data => console.log("syncPlay: ", data))
            .catch((err) => {
                console.log(err);
            });
    });
}

function syncPlay(handy, connectionKey, requestParameters, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/syncPlay?` + new URLSearchParams({
        play: requestParameters.play,
        serverTime: requestParameters.serverTime,
        time: requestParameters.time,
        timeout: handy.config.requestTimeout
    }))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }

                if (handy.config.debug) {
                    console.log("syncPlay response data: ", data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }

                if (handy.config.debug) {
                    console.error("syncPlay response error: ", data);
                }
            }
        })
        .catch((err) => {
            console.error(err);

            if (handy.config.debug) {
                console.error("connect response err: ", err);
            }
        });
}

function syncAdjustTimestamp(handy, connectionKey, requestParameters, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/syncAdjustTimestamp?` + new URLSearchParams({
        currentTime: requestParameters.currentTime,
        serverTime: requestParameters.serverTime
    }))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }

                if (handy.config.debug) {
                    console.log("syncPlayTimestamp response data: ", data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }

                if (handy.config.debug) {
                    console.error("syncPlayTimestamp response error: ", data);
                }
            }
        })
        .catch((err) => {
            console.error(err);

            if (handy.config.debug) {
                console.error("syncPlayTimestamp response err: ", err);
            }
        });
}

function syncOffset(handy, connectionKey, offsetAmount, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/syncOffset?` + new URLSearchParams({
        offset: offsetAmount
    }))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function resyncHandy(handy, connectionKey, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/reSync`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("resync response error: ", data)
                }
            } else {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log("resync response data: ", data);
                }
            }
        });
}

function toggleMode(handy, connectionKey, params, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/toggleMode?` + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function stepStroke(handy, connectionKey, params, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/stepStroke?` + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function stepSpeed(handy, connectionKey, params, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/stepSpeed?` + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function setStroke(handy, connectionKey, params, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/setStroke?` + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function setSpeed(handy, connectionKey, params, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/setSpeed?` + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function getSettings(handy, connectionKey, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/getSettings`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("getSettings error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function remoteOta(handy, connectionKey, params, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/remoteOta?` + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function getOtaProgress(handy, connectionKey, params, callbacks) {
    fetch(`${handy.config.apiURL}/${connectionKey}/getOtaProgress?` + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (callbacks) {
                    if (callbacks.onSuccess) {
                        callbacks.onSuccess(data);
                    }
                }
                if (handy.config.debug) {
                    console.log(data);
                }
            } else {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(data);
                    }
                }
                if (handy.config.debug) {
                    console.error("response error: ", data)
                }
            }
        })
        .catch((err) => {
            if (handy.config.debug) {
                console.error(err);
            }
        });
}

function handleGetServerTime(handy, connectionKey, callbacks) {
    let timeSyncMessage = 0;
    let timeSyncAggregatedOffset = 0;
    let timeSyncAverageOffset = 0;
    let timeSyncInitialOffset = 0;
    const handyInitialOffset = Number(getCookie("handyInitialOffset"));
    const handyAverageOffset = Number(getCookie("handyAverageOffset"));

    function updateServerTime() {
        const sendTime = Date.now();
        fetch(`${handy.config.apiURL}/${connectionKey}/getServerTime?timeout=${handy.config.requestTimeout}`)
            .then(response => response.json())
            .then(data => {
                let now = Date.now();
                let receiveTime = now;
                let rtd = receiveTime - sendTime;
                let serverTime = data.serverTime;
                let estimatedServerTimeNow = serverTime + rtd / 2;
                let offset = 0;

                if (timeSyncMessage === 0) {
                    timeSyncInitialOffset = estimatedServerTimeNow - now;
                } else {
                    offset =
                        estimatedServerTimeNow - receiveTime - timeSyncInitialOffset;
                    timeSyncAggregatedOffset += offset;
                    timeSyncAverageOffset = timeSyncAggregatedOffset / timeSyncMessage;
                }

                timeSyncMessage++;
                if (timeSyncMessage < 30) {
                    updateServerTime();
                }
                if (timeSyncMessage === 30) {
                    setCookie("handyAverageOffset", timeSyncAverageOffset);
                    setCookie("handyInitialOffset", timeSyncInitialOffset);
                }

                if (callbacks) {
                    if (callbacks.onSuccess) {
                        const serverTime = getServerTime(
                            handyAverageOffset,
                            handyInitialOffset
                        );
                        callbacks.onSuccess(data, serverTime, rtd);
                    }
                }
            })
            .catch((err) => {
                if (callbacks) {
                    if (callbacks.onError) {
                        callbacks.onError(err);
                    }
                }
            });
    }

    updateServerTime();
}

function convertFunscriptToCSV(headers, items, fileTitle, callbacks) {
    try {
        // Convert Object to JSON
        const jsonObject = JSON.stringify(items);

        const csv = asCsv(jsonObject);

        const exportedFilename =
            fileTitle.split('.funscript').join('') + '.csv' || 'export.csv';

        const blob = new Blob(
            [`#Converted to CSV using handyfeeling.com on ${new Date()} \n`, csv],
            {
                type: 'text/csv;charset=utf-8;',
            }
        );

        if (navigator.msSaveBlob) {
            // IE 10+
            navigator.msSaveBlob(blob, exportedFilename);
        } else {
            const link = document.createElement('a');
            if (link.download !== undefined) {
                // feature detection
                // Browsers that support HTML5 download attribute
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', exportedFilename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        }

        return true;
    } catch (error) {
        console.log(error);
        return error;
    }
}

function fileUpload(url, data, callbacks) {
    fetch(url, {
        method: 'POST', // or 'PUT'
        headers: {
            'Content-Type': 'multipart/form-data;',
        },
        body: JSON.stringify(data),
    })
        .then(response => response.json())
        .then(data => {
            if (callbacks) {
                if (callbacks.onSuccess) {
                    callbacks.onSuccess(data);
                }
            }
        })
        .catch((error) => {
            if (callbacks) {
                if (callbacks.onError) {
                    callbacks.onError(data);
                }
            }
        });
}

export function asCsv(content, lineTerminator) {
    let funscript
    if (typeof content === 'string') {
        try {
            funscript = JSON.parse(content)
        } catch (e) {
            console.error(`Failed parsing script content ${content.substring(0, 50)}${content.length > 50 ? `... ${content.length - 50} more chars.` : ''}`)
        }
    } else if (typeof content === 'object') {
        funscript = content
    }
    if (funscript?.actions?.length > 0) {
        if (!lineTerminator) {
            lineTerminator = '\r\n' // Defaulting to Windows CSV line terminator.
        }
        let csv = ''
        funscript.actions.forEach((a) => {
            csv += a.at + ',' + a.pos + lineTerminator
        })
        return csv
    }
    throw new Error('Not a valid funscript')
}

function setCookie(cname, cvalue) {
    var now = new Date();
    var time = now.getTime();
    time += 3600 * 1000;
    now.setTime(time);
    var expires = "expires=" + now.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
