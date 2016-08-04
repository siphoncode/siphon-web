---
layout: post
draft: false

title: "Publishing a native mobile app should be as easy as deploying to the web"

excerpt: "Even the most grizzled, die-hard app developer will admit that pushing an app to the App Store is a real pain. You need to create certificates, juggle with provisioning profiles and somehow induce Xcode to build your binary correctly with just the right permutation of obscure options and settings."

cover_image: siphon-publish/cover.jpg

author:
  name: Siphon
---

It may seem obvious that at some point these two would converge, but the gap is still huge. For years we've had plenty of developer tools, most notably [Heroku](https://www.heroku.com/), that make it incredibly easy to deploy web applications.

Shipping a native mobile app, especially to the App Store, is not nearly so straightforward. There's no tool that lets you publish or update your mobile app like this:

`$ git push heroku master`

Even the most grizzled, die-hard app developer will admit that pushing an app to the App Store is a real pain. You need to create certificates, juggle with provisioning profiles and somehow induce Xcode to build your binary correctly with just the right permutation of obscure options and settings.

The almost week-long App Store approval process is a whole other hurdle on top of that. **Not only is it tricky to even submit updates, you also need to wait for a human to approve it.**

The App Store opened its doors in 2008 and yet, even now, very few developers have the time or resources to set up a decent development workflow. A lot of the process remains manual and time consuming, although continuous integration and delivery services like [Bitrise](https://www.bitrise.io/) and [Buddybuild](https://www.buddybuild.com/) are gradually improving the situation.

Thankfully the Play Store is more forgiving. It's relatively easy to package up your Android app and the approval process is minimal. But it's still another process and set of tools that takes time to figure out.

<!-- Fastlane section -->

![Fastlane](/blog/images/siphon-publish/fastlane.png)

But there is hope! Thanks to the amazing work of Felix Krause and others on [Fastlane](https://fastlane.tools/), we now have a neat set of tools for dealing with all of this nonsense.

Fastlane lets you specify a workflow like this:

![Fastlane configuration](/blog/images/siphon-publish/fastlane-config.png)

This is a huge improvement over building and submitting an app all by yourself. Fastlane contains tools for dealing with certificates, profiles, screenshots and everything else you might need to deliver an app.

But we're lazy developers; we don't want to even think about certificates and provisioning profiles. **These concepts should be abstracted away as much as possible.**

Also, Fastlane and similar tools do not remove the App Store approval queue from the equation. For that, we need another solution.

<!-- React Native section -->

![React Native](/blog/images/siphon-publish/react-native.png)

In a [previous post](https://getsiphon.com/blog/2016/01/20/future-of-app-development/) we discussed the history of cross-platform app development and argued that [React Native](https://facebook.github.io/react-native/) is going to win in a way that previous attempts did not.

Briefly, React Native uses a clever bridging technique to let you build your app in JavaScript such that it performs as well as a native app in the majority of cases. You get an iOS and Android app from the same codebase pretty much for free, with minimal porting effort, respecting the UI idioms of both platforms if needed.

As an added bonus, it's technically possible to push over-the-air updates to React Native apps without going through the approval queue every time, because Apple [explicitly allows](https://getsiphon.com/docs/faq/#is-this-allowed) hot pushes of JavaScript code. Although the standard React Native tools do not facilitate this very easily (more on this below).

This is all great news, but React Native still remains **very much tied to Xcode and Android Studio**. You get this awesome environment for rapidly developing and iterating on your apps, but the party ends as soon as you need to ship it, or send beta builds to your testers. Even [running it on your developer device](https://getsiphon.com/blog/2016/03/14/react-native-on-your-device/) is a pain.

The process of packaging and submitting a React Native app to the App Store and Play Store is pretty much **exactly the same** as it is for a standard app.

*Note that at this early stage there are still a lot of native OS features that require compiled modules to be added manually in Xcode and Android Studio, but we believe that this requirement will disappear over time.*

<!-- Siphon publish section -->

![Siphon to the rescue](/blog/images/siphon-publish/equation.png)

We think it should be far easier to ship apps and to update them over-the-air. So we built the tool that we would have wanted when we were creating mobile apps for a living.

[Siphon](https://getsiphon.com) takes the best parts of React Native and Fastlane and wraps them up in an ultra-convenient workflow. Now you can do this:

`$ siphon publish --platform ios`

You will still need to specify some required information, like keywords, an app description and the screenshots you want to display, but otherwise it's dead easy. Publishing an Android version of your app to the Play Store will be just as simple (we're still working on it).

The same `siphon publish` command enables you to publish an app for the first time **and** if you run it again when you app is already live, your users will be updated to the latest version of your app. No waiting in the approval queue.

[Learn more about publishing apps with Siphon](https://getsiphon.com/pricing/)

*Internally we use Fastlane to make this work, but we abstract away the platform-specific parts like generating certificates and provisioning profiles. Note that you still need an iOS developer account and Play Store publisher account to use this functionality.*

## Step-by-step guide

Here's a quick guide to publishing a React Native app with [Siphon](https://getsiphon.com). First make sure you have our lightweight [command-line tool](https://getsiphon.com/docs/quickstart/) installed on your machine. Then create a new Siphon app:

`$ siphon create my-app`

Test your app in the sandbox on [iOS](https://getsiphon.com/i) and [Android](https://getsiphon.com/a) devices, or in your [local simulator](https://getsiphon.com/blog/2016/02/17/introducing-siphon-play/). You can push your latest changes like this:

`$ siphon push`

When you're ready to publish:

`$ siphon publish --platform ios`

That's it! The tool will prompt you for any information we need (keywords, app description, etc.) and Siphon will take care of everything else.

*You will receive email updates as the status of your app submission changes.*
