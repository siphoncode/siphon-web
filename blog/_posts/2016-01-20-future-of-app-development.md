---
layout: post
draft: false

title: "Thoughts on the future of mobile app development"
subtitle: "A look at the history of cross-platform mobile apps and why we're betting on React Native."
cover_image: future-of-apps/future-of-apps.jpg

excerpt: "Arriving from a web development background, building native apps for iOS and Android feels like traveling back in time.<br /><br />Near-instant browser refreshes are replaced by slow compilation times, your trusty text editor has been switched with a powerful but bloated IDE, and deploying new features is suddenly a week-long process (for iOS, at least)."

author:
  name: Siphon
  twitter: getsiphon
  bio: Ali Roberts & James Potter
---

Arriving from a web development background, building native apps for iOS and Android feels like traveling back in time.

Near-instant browser refreshes are replaced by slow compilation times, your trusty text editor has been switched with a powerful but bloated IDE, and deploying new features is suddenly a week-long process (for iOS, at least).

The mobile web has not lived up to its promise. For non-trivial apps it remains incredibly difficult to emulate a native look-and-feel in mobile browsers. We won't rehash the arguments here, but despite years of effort the mobile web remains fundamentally limited by what you can do.

<div class="full"><img src="{{ site.baseurl }}/images/future-of-apps/android-ios.png" alt="iOS and Android dominate mobile."></div>

And yet we find ourselves in a world dominated by two major mobile platforms with their own distinct user interface idioms, capabilities and quirks. Targeting both platforms with a single codebase is clearly a desirable goal. It costs less, and developers love efficiency.

The developer ecosystem is awash with frameworks aimed at building cross-platform mobile apps. But none of these has yet been able to materially challenge the officially sanctioned tools. In each case the primary aim has always been to reduce engineering time, but the overall goal should always be to provide the best end-user experience.

We think that [React Native](https://facebook.github.io/react-native/) is a viable alternative to the status quo. But first, some history.

## Cross-platform apps (a hand-wavy history)

![Apache Cordova](/blog/images/future-of-apps/cordova.png)

**PhoneGap / Apache Cordova (2009)**

One of the first attempts at code reusability across mobile platforms. Write your app as you would for the mobile web; define the layout using HTML/CSS and add interactivity with JavaScript.

The difference is that your app runs in a web view embedded inside a native app. The web view is augmented with a few extra APIs that expose native device capabilities, like the device's camera.

Cordova is a good compromise if you can sacrifice performance and a native feel for your app, but it suffers from a lot of the same downsides as the mobile web; namely it's slow, clunky and you don't get access to most platform-specific UI components such as switches and table views.

![Appcelerator Titanium](/blog/images/future-of-apps/appcelerator.png)

**Appcelerator Titanium (2009)**

Write your project in JavaScript targeting the Titanium API and it will generate an app for both major platforms. At app launch time, your code runs inside an interpreter (it gets pre-processed somewhat to speed things up) which is bridged to the native Titanium API.

Titanium is open source, but is culturally much closer to a commercial product and keeping up with API changes on both major platforms is a lot of work for one company. Third-party modules do exist but the community has waned somewhat in the past few years.

It also has a reputation for being buggy, although this is said to have improved since the bad old days.

![Xamarin](/blog/images/future-of-apps/xamarin.png)

**Xamarin (2011)**

Write your app in C# and target all the major platforms. Your code is compiled (or runs in MonoVM in the case of Android) and you get more-or-less native apps. As a language C# is well regarded but remains relatively niche compared to JavaScript.

As with Titanium, you get access to platform-specific UI components. You can also call the underlying native APIs if you need them (e.g. UIKit classes on iOS).

Somewhat cheaper than Appcelerator Titanium. Also unfortunately shares its <a href="https://gist.github.com/anonymous/38850edf6b9105ee1f8a">buggy</a> <a href="https://blog.tommyparnell.com/xamarin-for-android-the-ugly-part-3-of-4/">reputation</a>.

![Ionic](/blog/images/future-of-apps/ionic.png)

**Ionic (2013)**

Built on top of Apache Cordova and AngularJS. It uses a few tricks (less DOM manipulation, CSS3 animations) to speed things up.

You get a slick visual editor in the form of <a href="http://ionic.io/products/creator">Ionic Creator</a> that comes with companion iOS and Android apps for rapid prototyping.

It has a good reputation and plenty of traction, but you're still ultimately building inside a web view and the same limitations apply here; non-trivial features (e.g. photo manipulation) are going to be a challenge.

----------------------------------

What if you could take all of the lessons learned by the above and throw them all together?

![React Native](/blog/images/future-of-apps/react-native.png)

[React Native](https://facebook.github.io/react-native/) is an open source project by Facebook. In their own words:

> React Native enables you to build world-class application experiences on native platforms using a consistent developer experience based on JavaScript and React.

> The focus of React Native is on developer efficiency across all the platforms you care about — learn once, write anywhere. Facebook uses React Native in multiple production apps and will continue investing in React Native.

It's still very early, though. Facebook [open sourced](https://github.com/facebook/react-native) React Native in March 2015 and it's still under heavy development. That being said, it's [growing like crazy](https://www.google.com/trends/explore#q=react%20native) and Facebook already has [twenty engineers](https://www.reddit.com/r/IAmA/comments/3wyb3m/we_are_the_team_working_on_react_native_ask_us/cxzw2us) working on the project.

**React as a foundation**

React Native is powered by [React](https://facebook.github.io/react/) under-the-hood. It's not immediately obvious, but this is a large distinguishing feature from the likes of Titanium.

React was in-part designed to minimise expensive interaction with the browser's DOM. Interacting with the React Native bridge is similarly costly and being able to treat it like the DOM is crucial for improving performance.

We also get CSS *flexbox* for layouts. Good news if you've ever had to grapple with Auto Layout in iOS.

<!-- It's used by Facebook, Airbnb, Dropbox, Instagram and [plenty of others](https://github.com/facebook/react/wiki/Sites-Using-React). -->

**Choice of language**

For a framework to go mainstream it needs a popular, well-established language that is accessible and easy to learn.

For all its warts, nothing comes close to JavaScript in terms of the sheer number of developers out there who know the language.

**Learn once, write anywhere**

Many existing approaches to cross-platform development fall into the "write once, run anywhere" trap, encouraging you to define a single layout for all platforms.
[From the team at Facebook:](https://code.facebook.com/posts/1014532261909640/react-native-bringing-modern-web-techniques-to-mobile/)

> It's worth noting that we're not chasing “write once, run anywhere.”

> Different platforms have different looks, feels, and capabilities, and as such, we should still be developing discrete apps for each platform, but the same set of engineers should be able to build applications for whatever platform they choose, without needing to learn a fundamentally different set of technologies for each. We call this approach “learn once, write anywhere.”

A switch component should not look identical across iOS and Android.

**Distribution**

Building your app with an interpreted language opens up a ton of new possibilities, including over-the-air updates. More on this in a future post.

**Conclusion**

It's still early days but the community is growing fast. We're convinced that React Native is going to become the de facto framework for building fast, cross-platform mobile apps over the coming years.

<!-- In the next post, we'll talk about some of the challenges that Apple faces to it's walled garden from these new approaches to app development. -->

<a href="https://twitter.com/getsiphon">Follow us on Twitter for more posts like this</a>
