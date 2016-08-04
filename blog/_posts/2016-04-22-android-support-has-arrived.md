---
layout: post
draft: false

title: "Android support has arrived"

excerpt: "Today we're excited to announce the release of Siphon Sandbox for Android. You can now push your React Native apps to both iOS and Android devices and view your changes on both simultaneously."

cover_image: android-sandbox/cover.jpg

author:
  name: Siphon
---

Today we're excited to announce the release of [Siphon Sandbox for Android](https://getsiphon.com/a). You can now push your React Native apps to both iOS and Android devices and view your changes on both simultaneously.

<iframe width="620" height="360" src="https://www.youtube.com/embed/-KZaflS-Lk8" frameborder="0"> </iframe>

*Follow the [quickstart tutorial](https://getsiphon.com/docs/quickstart/) to update your client, or if you don't have our command-line tool installed yet.*

If you're new to Siphon, please follow the steps in our [quickstart tutorial](https://getsiphon.com/docs/quickstart/) to create your first app.

## Upgrade an existing project

If you would like to make an existing project compatible with Android, update the `"base_version"` parameter in your app's Siphonfile to `"0.4"` and rename the `index.ios.js` file to `index.js`. Then run:

`$ siphon push`

Your project will now be available in the sandbox on both [iOS](https://getsiphon.com/i) and [Android](https://getsiphon.com/a) devices.

If you require separate entry files for your project for each platform, simply name the Android entry file `index.android.js` and the iOS entry file `index.ios.js` then push your project.

*Note: If you have only one of these files your app will be built for the specified platform only.*

## Publish your app

When you're ready to publish your app to the Play Store, make sure the `"display_name"` is set in your app's Siphonfile and run:

`$ siphon publish --platform android`

We'll prompt you for a few details and take it from there.

## More to come

In the coming weeks we'll be rolling out emulator support for Android complete with Hot Reloading and Chrome debugging. We'll also be adding standalone device support.
