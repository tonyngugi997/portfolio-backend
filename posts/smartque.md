"Why I Chose Flutter for SmarTQue (and When I'd Choose Something Else)"

**A technical post about framework decisions, trade-offs, and giving credit where it's due.**

---

## The Short Version

I chose Flutter for SmarTQue because:

- **One codebase** for iOS and Android 
- **Hot reload** saved us hours of waiting
- **Dart is actually good** (though by then i had less then 12 months experience with dart)
- **The widget system** made complex UIs (appointment cards, queue position polling) straightforward

But Flutter isn't always the answer. Here's when I'd pick something else — and why, for this project, Flutter was right.

---

## The Context

Brenda Kangacha -my coursemate at Muranga University of Technology came to me with an idea: a hospital queue management system. Patients book appointments, get queue numbers, pay via M-Pesa, and track their position in real-time.

The question wasn't *"what should we use?"* It was *"can we ship this ASAP?"*

---

## The Options We Considered

| Framework | Pros | Cons |
|-----------|------|------|
| **React Native** | Huge ecosystem, Brenda knew some JS | Metro bundler is slow, bridge can be a bottleneck, she'd need to learn React |
| **Native (Kotlin/Swift)** | Best performance, full platform access | Two codebases, twice the work, neither of us knew both languages well |
| **Flutter** | One codebase, hot reload, beautiful UIs out of the box | Larger APK size, younger ecosystem |
| **PWA** | No app store, works on anything | No M-Pesa STK Push integration, limited device features |

We eliminated React Native because I didn't want to debug Metro issues at 2 AM.

We eliminated native because neither of us had time to maintain two codebases.

We eliminated PWA because M-Pesa's STK Push requires a native app (Safaricom's SDK is Android/iOS only).

**Flutter was the only option left.**

---

## Why Flutter Won

### 1. One Codebase, Two Devices


Flutter meant we wrote UI once and it worked on both. No `if iOS` spaghetti. No separate teams. Just code.

### 2. Hot Reload Saved Our Grades


No waiting for builds. No "let me recompile and get back to you."

### 3. Brenda  found it easy learning Learned Dart

She knew Flutter but not Dart deeply. The language is simple enough that she was productive in days.

No "let me read 500 pages of documentation first." Just write code, see output, learn as you go.

### 4. The Widget System is Underrated

Building the appointment card — with status badges, queue numbers, time remaining, and action buttons — took us 2 hours in Flutter.

Same thing in React Native would have taken longer because of the mental overhead of JSX + styling + state.

Flutter's `Column`, `Row`, `Container`, and `Padding` are boring. That's the point. They just work.

### 5. M-Pesa Integration Was Still Possible

Safaricom's SDK is native. But Flutter has platform channels.

I wrote a small Kotlin bridge for STK Push. Brenda handled the Dart side. It took us a weekend. It wasn't fun. But it worked.

---

## Where Flutter Hurt Us

I'm not going to pretend Flutter is perfect. Here's where it caused pain:

### 1. APK Size is Embarrassing

Our release APK is 42 MB. For a hospital queue app. That's ridiculous.

We could optimize (split APKs, remove unused fonts, use `--split-per-abi`), but we were shipping, not optimizing.

If your users have old phones with limited storage, this is a real problem.

### 2. The M-Pesa Package Ecosystem is Sparse

There's no official M-Pesa Flutter package. We had to write our own platform channel.

If you're building in Kenya and need M-Pesa, be prepared to write native code or maintain a fork.

### 3. The fight we had With Firebase

We wanted push notifications. Flutter + Firebase worked... eventually. But the setup took longer than expected.

If you're doing complex background tasks, Flutter still leans on native code. Keep that in mind.

### 4. Certain Animations Were Clunky

The queue position counter (updating every 8 seconds) caused jank on ios.
We fixed it by debouncing the updates, but it shouldn't have been a problem in the first place.

---

## When I'd Choose Something Else

Based on this experience, here's when I'd **not** use Flutter:

### For a Tiny App (Under 5 Screens)

Use a PWA. Or even just a mobile-friendly website. Flutter is overkill.

**Example:** A simple "contact us" form. Just use HTML.

### For Heavy AR/VR or 3D Graphics

Flutter's 3D support is weak. Use native (Unity, ARKit, ARCore).

**Example:** A medical imaging app that renders 3D scans. Don't use Flutter.

### If Your Team Already Knows React Native

Don't switch just because Flutter is trendy. The cost of retraining isn't worth it.

**Example:** If Brenda had been a React Native expert, we would have used it.

### If APK Size is Your #1 Priority

Flutter ships with the entire Dart runtime. If you're targeting low-end devices with 1GB storage, consider native or PWA.

**Example:** An app for feature phones. Don't use Flutter.

---

## What I'd Do Differently Next Time

### 1. Use `--split-per-abi` from Day 1

I waited until release to optimize APK size. That was stupid. Do it early.

### 2. Write the M-Pesa Bridge First

We built half the app before testing payments. If M-Pesa integration had failed, we would have been screwed.

Test the riskiest part first. Always.

---

## The Final Verdict

Flutter was the right choice for SmarTQue.

- **One codebase** → Test on both android and iphone(if you have one)
- **Hot reload** → We shipped faster
- **Dart** → Simple enough for both of us
- **Widget system** → Complex UIs became simple

But it wasn't free. The APK is large. M-Pesa required native code. Some animations were janky.

If I were building a tiny app, an AR app, or a team that already knew React Native — I'd choose differently.

But for a cross-platform hospital queue system built by two students?

**Flutter delivered.**

---

## Credit Where It's Due

**Brenda Kangacha** built the Flutter UI alongside me. She learned Dart in two weeks. She designed the appointment card. She debugged the queue polling timer.

If you want to argue about Flutter vs React Native, talk to her. She's the one who actually wrote the code.

**Brenda's GitHub:** [github.com/brendakangacha](https://github.com/brendakangacha)

---

## The One-Liner

> "Flutter isn't perfect. But for two students building a hospital queue system in 6 months? It was perfect enough."

---

*— Tony Ngugi (KenyanCyber), with Brenda Kangacha*

*Muranga University of Technology, 2026*

---

