function onLaunched(launchData) {
  chrome.app.window.create('index.html', {
    width: 400,
    height: 300
  });
}

chrome.app.runtime.onLaunched.addListener(onLaunched);
