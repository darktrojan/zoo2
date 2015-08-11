var XHR = {
	_makeRequest: function(aMethod, aURL, aSuccessCallback, aFailureCallback) {
		var request = new XMLHttpRequest();
		request._url = aURL;
		request.open(aMethod, aURL, true);
		request.onreadystatechange = function() {
			if (request.readyState == 4) {
				if (request.status >= 200 && request.status < 300) {
					aSuccessCallback(request);
				} else if (request.status) {
					aFailureCallback(request);
				}
			}
		};
		request.onerror = function() {
			aFailureCallback(request);
		};
		return request;
	},
	get: function(aURL, aSuccessCallback, aFailureCallback) {
		if (!aSuccessCallback)
			aSuccessCallback = this.defaultCallback;
		if (!aFailureCallback)
			aFailureCallback = this.defaultCallback;

		var request = this._makeRequest('GET', aURL, aSuccessCallback, aFailureCallback);
		request.send(null);
	},
	post: function(aURL, aData, aSuccessCallback, aFailureCallback, aContentType) {
		if (!aSuccessCallback)
			aSuccessCallback = this.defaultCallback;
		if (!aFailureCallback)
			aFailureCallback = this.defaultCallback;
		if (!aContentType)
			aContentType = 'application/x-www-form-urlencoded';

		var request = this._makeRequest('POST', aURL, aSuccessCallback, aFailureCallback);
		request.setRequestHeader('Content-Type', aContentType);
		request.setRequestHeader('Content-Length', aData.length);
		request.setRequestHeader('Connection', 'close');
		request.send(aData);
	},
	defaultCallback: function(aRequest) {
		var status = aRequest.status;
		var header = aRequest.getResponseHeader('Content-Type');
		var response = aRequest.responseText;

		if (status != 200 && console && 'error' in console)
			console.error('XHR to ' + aRequest._url + ' returned status ' + status);

		if (response) {
			if (header && header.indexOf('application/json') == 0)
				alert(JSON.parse(response));
			else
				alert(response);
		} else if (status != 200) {
			alert('An error has occurred.');
		}
	}
};

(function() {
	var signinLink = document.getElementById('sign_in');
	if (signinLink) {
		signinLink.onclick = function() {
			navigator.id.request();
			return false;
		};
	}

	var signoutLink = document.getElementById('sign_out');
	if (signoutLink) {
		signoutLink.onclick = function() {
			if (/(^|;)\s*persona_email=/.test(document.cookie)) {
				navigator.id.logout();
				return false;
			}
		};
	}
})();

navigator.id.watch({
	loggedInUser: (function() {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = cookies[i].trim();
			if (cookie) {
				var parts = cookie.split('=', 2);
				if (parts[0] == 'persona_email') {
					return decodeURIComponent(parts[1]).replace(/^"|"$/g, '');
				}
			}
		}
		return null;
	})(),
	onlogin: function(assertion) {
		XHR.post('/persona_auth', 'assertion=' + encodeURIComponent(assertion), function() {
			location.reload();
		});
	},
	onlogout: function() {
		XHR.get('/log_out', function() {
			location.reload();
		});
	}
});
