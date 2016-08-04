---
layout: post
draft: false

title: "Running a React Native app on your device (the easy way)"
cover_image: react-native-on-device/cover.jpg

excerpt: "Running a React Native app on your iPhone can be quite tricky. You need to configure Xcode correctly, provision your iPhone and then somehow point your device at the local packager running on your machine."

author:
  name: Siphon
---

Running a React Native app on your iPhone can be [quite tricky](https://facebook.github.io/react-native/docs/running-on-device-ios.html). You need to configure Xcode correctly, provision your iPhone and then somehow point your device at the local packager running on your machine.

We've been working hard on a much simpler solution. Now with Siphon you can run:

`$ siphon play --device`

Our [command-line tool](https://getsiphon.com/docs/quickstart/) will walk you through all the steps required to provision your device and download any missing dependencies. You don't need to open Xcode or even run the React Native packager.

*Please note that you need a Mac to run this command, but it will work on all platforms when we release Android support. You can also try the sandbox on [iOS](https://getsiphon.com/i) and [Android](https://getsiphon.com/a) devices.*
