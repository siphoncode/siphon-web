---
layout: post
draft: true

title: "A challenge to Apple's walled garden"
subtitle: "Pithy subtitle goes here."
cover_image: walled-garden/cover.jpg

excerpt: "TODO: an excerpt to go on the blog index."

author:
  name: Siphon
  twitter: getsiphon
  bio: Ali Roberts & James Potter
---


TODO: next: need to reconcile draft bits at the end with this new structure!!!



For many years, the App Store approval process imposed by Apple was highly controversial. Probably the biggest point of contention with the developer community. It's easy to find quotes like this from 200X:

> [find some HN quote slamming the app store approval process]

Many thought that this was unsustainable, even prompting Paul Graham to pen an essay titled Apple's Mistake [link it]:

> The way Apple runs the App Store has harmed their reputation with programmers more than anything else they've ever done. Their reputation with programmers used to be great.

> It used to be the most common complaint you heard about Apple was that their fans admired them too uncritically. The App Store has changed that. Now a lot of programmers have started to see Apple as evil.

Then something interesting happened. Apple didn't budge, but many of the most stringent rules were gradually relaxed over time. We're now permitted to X and Y (bundle a runtime? alternate languages? background processing?).

From a developer's perspective the process looks almost identical. The approval process still takes just as long, but it hovers just on the boundary of being unacceptable.

[chart showing approval process over time]

We put up with it because they approve almost any app these days and you can't ignore the sole distribution channel to X million potential customers.


[Section: intro to the walled garden]

Developers have been chipping away at Apple's walled garden for years. Mostly notably, Apache Cordova (link) (also known as PhoneGap) lets you embed a web app inside a native app and call native APIs from it, for example to access the camera or file system. It's possible to update these apps over-the-air and therefore the App Store approval process. This seems to have been tolerated and the App Store rules now [explicitly allow it](https://getsiphon.com/docs/faq/#is-this-allowed) as long as only HTML and JavaScript are behind altered this way.

For those who are unfamiliar, the term *walled garden* is referring to Apple's end-to-end control of the iOS ecosystem. The App Store is the sole channel[^1] if you want to distribute apps and getting listed there means going through the 5-7 day approval process for every new app or update. Apps are bound by a strict set of rules[^2].

A new approach has appeared in the past year or so and it changes the dynamic [briefly explain what this is, next section goes into detail]. This time it's different.

[^1]: Other distribution methods do exist (enterprise apps, TestFlight, jailbreaking community) but these are a drop in the ocean in comparison to the App Store.

[^2]: Admittedly these rules have been relaxed somewhat over the years. But fundamentally apps remain strictly sandboxed and distribution is still very much bound to the App Store.

[Section: about this new approach]

* In last weeks post we gave a brief history[link] of the various ways to build cross-platform apps.
* how it works
* examples: RN, NativeScript, Rollout.io (JS + method swizzling? how does it work), others?

[Section: why is it being challenged?]

* URLs as a distribution method! imagine a new kind of browser, mention exponent which is trying to do this, mention how TestFlight-style distribution will be upended
* you could already do this with PhoneGap but it's not as interesting when we're dealing with essentially web apps (we already have the mobile web!)



**Why is this bad?**

The past X years have seen an unusual period of openness in the form of the web. The open nature of the web has evolved a ton of best practices: rapid iteration, A/B testing, continuous deployment [is this the right term?], what else?

It's tough to do A/B testing in this kind of environment. Libraries do exist but carry a penalty in time (?). Every time you submit an update to the App Store, you lose the star rating shown in your app listing (users can still read past reviews).

**Something is changing**

It started with the likes of PhoneGap. [how long has this been allowed?]

Mention the new Section 3.3.2 in the rules (when was it added? why? context.)

Mention how FB tried this with their hybrid app -- but mobile web browsers are too flawed and they
ditched it for mobile. [link to our first blog post]

Who is doing hot updates already? (outside of RN)

**Enter React Native**

Breifly what it is, how it works, and why that means we can do hot updates.

Who is already doing hot updates with it?

**Discoverability**

Should we mention this?

There has been talk for years of Apple improving discoverability in the App Store. They often tweak the design and search algorithm, but it has mostly remained fundamentally the same. There remains a culture of *having a relationship* with someone over at Apple who will feature your app.

[should we even mention this? don't want to piss off Apple]

The new deep linking goes a long way to address this (does it?) and Google now indexes these links if you X. [link to that github project that lets you post your app's link index to google]



* a history of the walled garden
    * it has got better over time
    * still damn slow to release update
    * android is basically fine

* the challenge:
    * why this is now feasible (RN, but mention that there are past technologies that have done this)
    * live JS updates without approval (who is already doing this? LinkedIn apparently)
        * Apple has been friendly so far
    * URLs for native apps
    * better distribution for testing (challenging TestFlight)



* "But it gets more interesting..."
* JS lets us do hot reloading
* mention how this threatens apple's walled garden (they seem to be OK with it so far + could do this before with Cordova) "Challenging the walled garden"
* mention that android doesn't suffer from this
* briefly mention a possible future direction: URLs for on-demand RN apps, a new kind of browser (link to Exponent as example of this)
* for now we believe that the standalone app approach is more pragmatic (don't want to risk apple's ire)
* more future directions: render a web site with same codebase (link to RN-web project), Apple Watch, Apple TV (link)
