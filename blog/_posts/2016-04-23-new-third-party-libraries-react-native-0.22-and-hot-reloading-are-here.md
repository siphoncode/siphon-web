---
layout: post
draft: false

title: "New third-party libraries, React Native 0.22 and Hot Reloading"

excerpt: "We've upgraded to React Native 0.22 and made some improvements. You can now run your app in the simulator using Siphon and take advantage of React Native's lightning-fast reload times. App logs and debugging have also been improved significantly."

cover_image: 0.22-hot-reloading/cover.jpg

author:
  name: Siphon
---

We've upgraded to React Native 0.22 and made some improvements. You can now run your app in the simulator using Siphon and take advantage of React Native's lightning-fast reload times. App logs and debugging have also been improved significantly.

*Follow the [quickstart tutorial](https://getsiphon.com/docs/quickstart/) to update your client, or if you don't have our command-line tool installed yet.*

## Hot Reloading

One of the most exciting features of React Native is now available using Siphon. Hot reloading lets you view changes to your app instantly, without triggering a complete refresh. To get started, make sure you have the latest version of the client installed and run:

`$ siphon develop`

*Please note that you need a Mac to run this command, but it will work on all platforms when we release Android support.*

This will download any dependencies that you need, start React Native's packager on your machine and open the iOS simulator. Your app's logs will stream to the terminal when the simulator has loaded.

To enable hot reloading, perform the shake gesture (ctrl + ⌘ + z) to open the developer menu, then select the hot reloading option. Any saved changes you make to your app should now appear instantly in the simulator.

[Learn more about Hot Reloading](https://facebook.github.io/react-native/blog/2016/03/24/introducing-hot-reloading.html)

## Improved logging

For more detailed logs and in-app warnings you can now enable/disable 'dev mode' in the sandbox app (available for both [iOS](https://getsiphon.com/i) and [Android](https://getsiphon.com/a)) by toggling the tool icon:

<div class="full"><img src="{{ site.baseurl }}/images/0.22-hot-reloading/dev-mode.png" width="450" alt="Run your app in the iOS simulator."></div>

To load an app on your device in 'dev mode', connect it to your computer and run the following command:

`$ siphon play --dev`

*Please note that you need a Mac to run this command, but it will work on all platforms when we release Android support.*

Click [here](https://getsiphon.com/blog/2016/03/14/react-native-on-your-device/) for more information about the `siphon play` command.

## New third-party libraries

Siphon apps now have access to the following modules, no installation required:

* [react-native-camera](https://github.com/lwansbrough/react-native-camera)
* [react-native-device-info](https://github.com/rebeccahughes/react-native-device-info)
* [react-native-fs](https://github.com/johanneslumpe/react-native-fs)
* [react-native-grid-view](https://github.com/lucholaf/react-native-grid-view)
* [react-native-linear-gradient](https://github.com/brentvatne/react-native-linear-gradient)
* [react-native-material-kit](https://github.com/xinthink/react-native-material-kit)
* [react-native-motion-manager](https://github.com/pwmckenna/react-native-motion-manager) (iOS only)
* [react-native-touch-id](https://github.com/naoufal/react-native-touch-id) (iOS only)
* [react-native-vector-icons](https://github.com/oblador/react-native-vector-icons)
* [react-native-video](https://github.com/brentvatne/react-native-video)
* [eact-native-youtube](https://github.com/paramaggarwal/react-native-youtube) (iOS only)

Simply import these into your project and you're good to go! We're going to be adding many more in the near future.

*Anything missing? Let us know if there are any other third-party libraries you would like us to include in future releases at <hello@getsiphon.com>.*

## What's next

In the next few weeks we'll be rolling out emulator and device support for Android apps. We're also working on some exciting new features that will enable you to share your apps with third parties before you publish them.
