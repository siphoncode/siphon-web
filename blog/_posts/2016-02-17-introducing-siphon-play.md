---
layout: post
draft: false

title: "Introducing: Siphon Play"
cover_image: siphon-play/cover.jpg

excerpt: "Running your React Native apps in the simulator or on a developer device should be a straight-forward task, but it's still a little tricky.<br /><br />Today we're happy to announce a new Siphon command that takes care of everything for you"

author:
  name: Siphon
---

Running your React Native apps in the simulator or on a developer device should be a straight-forward task, but it's still a little tricky.

Today we're happy to announce a new Siphon command that takes care of everything for you:

`$ siphon play`

*Follow the [quickstart tutorial](https://getsiphon.com/docs/quickstart/) to update your client, or if you don't have our command-line tool installed yet.*

With a single command you can build and run your project as a standalone app. The tool will step you through installing any missing dependencies on your machine, and by default it will spin up an iOS simulator.

<div class="full"><img src="{{ site.baseurl }}/images/siphon-play/simulator-example.jpg" alt="Run your app in the iOS simulator."></div>

*Unfortunately to use the iOS simulator you will need to install Xcode, but it doesn't need to be running. The tool shows you how to install Xcode if it's missing on your machine.*

To make live changes to the app while it's running in the simulator, just type in:

`$ siphon push --watch`

Leave this command running and your app will update itself any time you change one of its files. You can also specify other simulator types like this:

`$ siphon play --simulator ipad2`

Please note that `siphon play` is only supported on Mac right now, but Android will be supported on all platforms. As an alternative you can also install the Siphon Sandbox app from the [App Store](https://getsiphon.com/i) or [Play Store](https://getsiphon.com/a) and run your apps there.

##More to come

Soon you will be able to run your app on a physical device (plugged in by USB) like this:

`$ siphon play --device ios`

We're also working hard to finish Siphon support for Android.

##Get started

Follow our [quickstart tutorial](https://getsiphon.com/docs/quickstart/) and learn how to download our command-line tool and get started writing Siphon apps.
