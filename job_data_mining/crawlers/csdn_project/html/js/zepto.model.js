;
(function($) {
	function detect(ua, platform) {
		var os = this.os = {},
			browser = this.browser = {},
			webkit = ua.match(/Web[kK]it[\/]{0,1}([\d.]+)/),
			android = ua.match(/(Android);?[\s\/]+([\d.]+)?/),
			osx = !!ua.match(/\(Macintosh\; Intel /),
			ipad = ua.match(/(iPad).*OS\s([\d_]+)/),
			ipod = ua.match(/(iPod)(.*OS\s([\d_]+))?/),
			iphone = !ipad && ua.match(/(iPhone\sOS)\s([\d_]+)/),
			webos = ua.match(/(webOS|hpwOS)[\s\/]([\d.]+)/),
			win = /Win\d{2}|Windows/.test(platform),
			wp = ua.match(/Windows Phone ([\d.]+)/),
			touchpad = webos && ua.match(/TouchPad/),
			kindle = ua.match(/Kindle\/([\d.]+)/),
			silk = ua.match(/Silk\/([\d._]+)/),
			blackberry = ua.match(/(BlackBerry).*Version\/([\d.]+)/),
			bb10 = ua.match(/(BB10).*Version\/([\d.]+)/),
			rimtabletos = ua.match(/(RIM\sTablet\sOS)\s([\d.]+)/),
			playbook = ua.match(/PlayBook/),
			chrome = ua.match(/Chrome\/([\d.]+)/) || ua.match(/CriOS\/([\d.]+)/),
			firefox = ua.match(/Firefox\/([\d.]+)/),
			firefoxos = ua.match(/\((?:Mobile|Tablet); rv:([\d.]+)\).*Firefox\/[\d.]+/),
			ie = ua.match(/MSIE\s([\d.]+)/) || ua.match(/Trident\/[\d](?=[^\?]+).*rv:([0-9.].)/),
			webview = !chrome && ua.match(/(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/),
			safari = webview || ua.match(/Version\/([\d.]+)([^S](Safari)|[^M]*(Mobile)[^S]*(Safari))/)
		if(browser.webkit = !!webkit) browser.version = webkit[1]
		if(android) os.android = true, os.version = android[2]
		if(iphone && !ipod) os.ios = os.iphone = true, os.version = iphone[2].replace(/_/g, '.')
		if(ipad) os.ios = os.ipad = true, os.version = ipad[2].replace(/_/g, '.')
		if(ipod) os.ios = os.ipod = true, os.version = ipod[3] ? ipod[3].replace(/_/g, '.') : null
		if(wp) os.wp = true, os.version = wp[1]
		if(webos) os.webos = true, os.version = webos[2]
		if(touchpad) os.touchpad = true
		if(blackberry) os.blackberry = true, os.version = blackberry[2]
		if(bb10) os.bb10 = true, os.version = bb10[2]
		if(rimtabletos) os.rimtabletos = true, os.version = rimtabletos[2]
		if(playbook) browser.playbook = true
		if(kindle) os.kindle = true, os.version = kindle[1]
		if(silk) browser.silk = true, browser.version = silk[1]
		if(!silk && os.android && ua.match(/Kindle Fire/)) browser.silk = true
		if(chrome) browser.chrome = true, browser.version = chrome[1]
		if(firefox) browser.firefox = true, browser.version = firefox[1]
		if(firefoxos) os.firefoxos = true, os.version = firefoxos[1]
		if(ie) browser.ie = true, browser.version = ie[1]
		if(safari && (osx || os.ios || win)) {
			browser.safari = true
			if(!os.ios) browser.version = safari[1]
		}
		if(webview) browser.webview = true
		os.tablet = !!(ipad || playbook || (android && !ua.match(/Mobile/)) || (firefox && ua.match(/Tablet/)) || (ie && !ua.match(/Phone/) && ua.match(/Touch/)))
		os.phone = !!(!os.tablet && !os.ipod && (android || iphone || webos || blackberry || bb10 || (chrome && ua.match(/Android/)) || (chrome && ua.match(/CriOS\/([\d.]+)/)) || (firefox && ua.match(/Mobile/)) || (ie && ua.match(/Touch/))))
	}
	detect.call($, navigator.userAgent, navigator.platform)
	$.__detect = detect
})(Zepto);
(function($, undefined) {
	var prefix = '',
		eventPrefix, vendors = {
			Webkit: 'webkit',
			Moz: '',
			O: 'o'
		},
		testEl = document.createElement('div'),
		supportedTransforms = /^((translate|rotate|scale)(X|Y|Z|3d)?|matrix(3d)?|perspective|skew(X|Y)?)$/i,
		transform, transitionProperty, transitionDuration, transitionTiming, transitionDelay, animationName, animationDuration, animationTiming, animationDelay, cssReset = {}

	function dasherize(str) {
		return str.replace(/([a-z])([A-Z])/, '$1-$2').toLowerCase()
	}

	function normalizeEvent(name) {
		return eventPrefix ? eventPrefix + name : name.toLowerCase()
	}
	$.each(vendors, function(vendor, event) {
		if(testEl.style[vendor + 'TransitionProperty'] !== undefined) {
			prefix = '-' + vendor.toLowerCase() + '-'
			eventPrefix = event
			return false
		}
	})
	transform = prefix + 'transform'
	cssReset[transitionProperty = prefix + 'transition-property'] = cssReset[transitionDuration = prefix + 'transition-duration'] = cssReset[transitionDelay = prefix + 'transition-delay'] = cssReset[transitionTiming = prefix + 'transition-timing-function'] = cssReset[animationName = prefix + 'animation-name'] = cssReset[animationDuration = prefix + 'animation-duration'] = cssReset[animationDelay = prefix + 'animation-delay'] = cssReset[animationTiming = prefix + 'animation-timing-function'] = ''
	$.fx = {
		off: (eventPrefix === undefined && testEl.style.transitionProperty === undefined),
		speeds: {
			_default: 400,
			fast: 200,
			slow: 600
		},
		cssPrefix: prefix,
		transitionEnd: normalizeEvent('TransitionEnd'),
		animationEnd: normalizeEvent('AnimationEnd')
	}
	$.fn.animate = function(properties, duration, ease, callback, delay) {
		if($.isFunction(duration))
			callback = duration, ease = undefined, duration = undefined
		if($.isFunction(ease))
			callback = ease, ease = undefined
		if($.isPlainObject(duration))
			ease = duration.easing, callback = duration.complete, delay = duration.delay, duration = duration.duration
		if(duration) duration = (typeof duration == 'number' ? duration : ($.fx.speeds[duration] || $.fx.speeds._default)) / 1000
		if(delay) delay = parseFloat(delay) / 1000
		return this.anim(properties, duration, ease, callback, delay)
	}
	$.fn.anim = function(properties, duration, ease, callback, delay) {
		var key, cssValues = {},
			cssProperties, transforms = '',
			that = this,
			wrappedCallback, endEvent = $.fx.transitionEnd,
			fired = false
		if(duration === undefined) duration = $.fx.speeds._default / 1000
		if(delay === undefined) delay = 0
		if($.fx.off) duration = 0
		if(typeof properties == 'string') {
			cssValues[animationName] = properties
			cssValues[animationDuration] = duration + 's'
			cssValues[animationDelay] = delay + 's'
			cssValues[animationTiming] = (ease || 'linear')
			endEvent = $.fx.animationEnd
		} else {
			cssProperties = []
			for(key in properties)
				if(supportedTransforms.test(key)) transforms += key + '(' + properties[key] + ') '
			else cssValues[key] = properties[key], cssProperties.push(dasherize(key))
			if(transforms) cssValues[transform] = transforms, cssProperties.push(transform)
			if(duration > 0 && typeof properties === 'object') {
				cssValues[transitionProperty] = cssProperties.join(', ')
				cssValues[transitionDuration] = duration + 's'
				cssValues[transitionDelay] = delay + 's'
				cssValues[transitionTiming] = (ease || 'linear')
			}
		}
		wrappedCallback = function(event) {
			if(typeof event !== 'undefined') {
				if(event.target !== event.currentTarget) return
				$(event.target).unbind(endEvent, wrappedCallback)
			} else
				$(this).unbind(endEvent, wrappedCallback)
			fired = true
			$(this).css(cssReset)
			callback && callback.call(this)
		}
		if(duration > 0) {
			this.bind(endEvent, wrappedCallback)
			setTimeout(function() {
				if(fired) return
				wrappedCallback.call(that)
			}, ((duration + delay) * 1000) + 25)
		}
		this.size() && this.get(0).clientLeft
		this.css(cssValues)
		if(duration <= 0) setTimeout(function() {
			that.each(function() {
				wrappedCallback.call(this)
			})
		}, 0)
		return this
	}
	testEl = null
})(Zepto);
(function($) {
	var touch = {},
		touchTimeout, tapTimeout, swipeTimeout, longTapTimeout, longTapDelay = 750,
		gesture

	function swipeDirection(x1, x2, y1, y2) {
		return Math.abs(x1 - x2) >= Math.abs(y1 - y2) ? (x1 - x2 > 0 ? 'Left' : 'Right') : (y1 - y2 > 0 ? 'Up' : 'Down')
	}

	function longTap() {
		longTapTimeout = null
		if(touch.last) {
			touch.el.trigger('longTap')
			touch = {}
		}
	}

	function cancelLongTap() {
		if(longTapTimeout) clearTimeout(longTapTimeout)
		longTapTimeout = null
	}

	function cancelAll() {
		if(touchTimeout) clearTimeout(touchTimeout)
		if(tapTimeout) clearTimeout(tapTimeout)
		if(swipeTimeout) clearTimeout(swipeTimeout)
		if(longTapTimeout) clearTimeout(longTapTimeout)
		touchTimeout = tapTimeout = swipeTimeout = longTapTimeout = null
		touch = {}
	}

	function isPrimaryTouch(event) {
		return(event.pointerType == 'touch' || event.pointerType == event.MSPOINTER_TYPE_TOUCH) && event.isPrimary
	}

	function isPointerEventType(e, type) {
		return(e.type == 'pointer' + type || e.type.toLowerCase() == 'mspointer' + type)
	}
	$(document).ready(function() {
		var now, delta, deltaX = 0,
			deltaY = 0,
			firstTouch, _isPointerType
		if('MSGesture' in window) {
			gesture = new MSGesture()
			gesture.target = document.body
		}
		$(document).bind('MSGestureEnd', function(e) {
			var swipeDirectionFromVelocity = e.velocityX > 1 ? 'Right' : e.velocityX < -1 ? 'Left' : e.velocityY > 1 ? 'Down' : e.velocityY < -1 ? 'Up' : null;
			if(swipeDirectionFromVelocity) {
				touch.el.trigger('swipe')
				touch.el.trigger('swipe' + swipeDirectionFromVelocity)
			}
		}).on('touchstart MSPointerDown pointerdown', function(e) {
			if((_isPointerType = isPointerEventType(e, 'down')) && !isPrimaryTouch(e)) return
			firstTouch = _isPointerType ? e : e.touches[0]
			if(e.touches && e.touches.length === 1 && touch.x2) {
				touch.x2 = undefined
				touch.y2 = undefined
			}
			now = Date.now()
			delta = now - (touch.last || now)
			touch.el = $('tagName' in firstTouch.target ? firstTouch.target : firstTouch.target.parentNode)
			touchTimeout && clearTimeout(touchTimeout)
			touch.x1 = firstTouch.pageX
			touch.y1 = firstTouch.pageY
			if(delta > 0 && delta <= 250) touch.isDoubleTap = true
			touch.last = now
			longTapTimeout = setTimeout(longTap, longTapDelay)
			if(gesture && _isPointerType) gesture.addPointer(e.pointerId);
		}).on('touchmove MSPointerMove pointermove', function(e) {
			if((_isPointerType = isPointerEventType(e, 'move')) && !isPrimaryTouch(e)) return
			firstTouch = _isPointerType ? e : e.touches[0]
			cancelLongTap()
			touch.x2 = firstTouch.pageX
			touch.y2 = firstTouch.pageY
			deltaX += Math.abs(touch.x1 - touch.x2)
			deltaY += Math.abs(touch.y1 - touch.y2)
		}).on('touchend MSPointerUp pointerup', function(e) {
			if((_isPointerType = isPointerEventType(e, 'up')) && !isPrimaryTouch(e)) return
			cancelLongTap()
			if((touch.x2 && Math.abs(touch.x1 - touch.x2) > 30) || (touch.y2 && Math.abs(touch.y1 - touch.y2) > 30))
				swipeTimeout = setTimeout(function() {
					touch.el.trigger('swipe')
					touch.el.trigger('swipe' + (swipeDirection(touch.x1, touch.x2, touch.y1, touch.y2)))
					touch = {}
				}, 0)
			else if('last' in touch)
				if(deltaX < 30 && deltaY < 30) {
					tapTimeout = setTimeout(function() {
						var event = $.Event('tap')
						event.cancelTouch = cancelAll
						touch.el.trigger(event)
						if(touch.isDoubleTap) {
							if(touch.el) touch.el.trigger('doubleTap')
							touch = {}
						} else {
							touchTimeout = setTimeout(function() {
								touchTimeout = null
								if(touch.el) touch.el.trigger('singleTap')
								touch = {}
							}, 250)
						}
					}, 0)
				} else {
					touch = {}
				}
			deltaX = deltaY = 0
		}).on('touchcancel MSPointerCancel pointercancel', cancelAll)
		$(window).on('scroll', cancelAll)
	});
	['swipe', 'swipeLeft', 'swipeRight', 'swipeUp', 'swipeDown', 'doubleTap', 'tap', 'singleTap', 'longTap'].forEach(function(eventName) {
		$.fn[eventName] = function(callback) {
			return this.on(eventName, callback)
		}
	})
})(Zepto)
Touch = window.Touch || {};
(function(exports) {
	exports.getUrlParam = function(name) {
		var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
		var r = decodeURI(window.location.search).substr(1).match(reg);
		if(r != null) {
			return unescape(r[2]);
		}
		return '';
	};
	exports.getUrlParamEncode = function(name) {
		var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
		var sStr = decodeURI(window.location.search).substr(1);
		sStr = sStr.replace(/&/g, "&amp;");
		sStr = sStr.replace(/>/g, "&gt;");
		sStr = sStr.replace(/</g, "&lt;");
		sStr = sStr.replace(/"/g, "&quot;");
		sStr = sStr.replace(/'/g, "&apos;");
		sStr = sStr.replace(/=/g, "&#61;");
		sStr = sStr.replace(/`/g, "&#96;");
		var r = sStr.match(reg);
		if(r != null) {
			return unescape(r[2]);
		}
		return '';
	};
	exports.getUrlArgs = function() {
		var args = {},
			query = location.search.substring(1),
			pairs = query.split("&");
		for(var i = 0; i < pairs.length; i++) {
			var pos = pairs[i].indexOf('=');
			if(pos == -1) continue;
			var argname = pairs[i].substring(0, pos),
				value = pairs[i].substring(pos + 1);
			value = decodeURIComponent(value);
			args[argname] = value;
		}
		return args;
	};
	exports.getAllArgs = function() {
		var sStr = decodeURI(window.location.search).substr(1);
		sStr = sStr.replace(/&/g, "&amp;");
		sStr = sStr.replace(/>/g, "&gt;");
		sStr = sStr.replace(/</g, "&lt;");
		sStr = sStr.replace(/"/g, "&quot;");
		sStr = sStr.replace(/'/g, "&apos;");
		sStr = sStr.replace(/=/g, "&#61;");
		sStr = sStr.replace(/`/g, "&#96;");
		return sStr;
	};
})(Touch.Util = {});
Touch = window.Touch || {};
(function(exports) {
	exports.getUrlParam = function(name) {
		var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
		var r = decodeURI(window.location.search).substr(1).match(reg);
		if(r != null) {
			return unescape(r[2]);
		}
		return '';
	};
	exports.getUrlParamEncode = function(name) {
		var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
		var sStr = decodeURI(window.location.search).substr(1);
		sStr = sStr.replace(/&/g, "&amp;");
		sStr = sStr.replace(/>/g, "&gt;");
		sStr = sStr.replace(/</g, "&lt;");
		sStr = sStr.replace(/"/g, "&quot;");
		sStr = sStr.replace(/'/g, "&apos;");
		sStr = sStr.replace(/=/g, "&#61;");
		sStr = sStr.replace(/`/g, "&#96;");
		var r = sStr.match(reg);
		if(r != null) {
			return unescape(r[2]);
		}
		return '';
	};
	exports.getUrlArgs = function() {
		var args = {},
			query = location.search.substring(1),
			pairs = query.split("&");
		for(var i = 0; i < pairs.length; i++) {
			var pos = pairs[i].indexOf('=');
			if(pos == -1) continue;
			var argname = pairs[i].substring(0, pos),
				value = pairs[i].substring(pos + 1);
			value = decodeURIComponent(value);
			args[argname] = value;
		}
		return args;
	};
	exports.getAllArgs = function() {
		var sStr = decodeURI(window.location.search).substr(1);
		sStr = sStr.replace(/&/g, "&amp;");
		sStr = sStr.replace(/>/g, "&gt;");
		sStr = sStr.replace(/</g, "&lt;");
		sStr = sStr.replace(/"/g, "&quot;");
		sStr = sStr.replace(/'/g, "&apos;");
		sStr = sStr.replace(/=/g, "&#61;");
		sStr = sStr.replace(/`/g, "&#96;");
		return sStr;
	};
})(Touch.Util = {});

function global_check_wp() {
	var navigator = window.navigator;
	userAgent = navigator.userAgent;
	wp = userAgent.match(/(Windows\s+Phone)\s([\d\.]+)/);
	return wp;
}

function global_check_platform() {
	var platfrom = '0';
	if($.os) {
		if("undefined" != typeof($.os.android) && $.os.android == true) {
			platfrom = 14;
		} else if("undefined" != typeof($.os.ios) && $.os.ios == true) {
			platfrom = 15;
		}
	}
	if(platfrom == '' && check_wp()) {
		platfrom = 48;
	}
	return platfrom;
} /*  |xGv00|848930f89f834e9a70893e8c25d906af */