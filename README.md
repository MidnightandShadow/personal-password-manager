<h1 id="top"> Personal Password Manager </h1>

  * [Background](#background)
  * [Installation](#installation)
  * [User Guide](#user-guide)
    + [Login/Signup](#loginsignup)
    + [Main Window](#main-window)
  * [Motivations](#motivations)
  * [Mini-Post Mortem](#mini-post-mortem)
    + [What went right?](#what-went-right)
      - [GUI](#gui)
      - [Database and Cryptography Utils](#database-and-cryptography-utils)
    + [What went wrong?](#what-went-wrong)
      - [Scoping](#scoping)
      - [Testing Coverage](#testing-coverage)
      - [Database Design/ORM vs. "No-RM"](#database-designorm-vs-no-rm)
      - [Implementation before sufficiently researching encryption methods](#implementation-before-sufficiently-researching-encryption-methods)
    + [What I learned](#what-i-learned)
      - [Soft skills/advice-to-self](#soft-skillsadvice-to-self)
      - [Hard skills](#hard-skills)
---
  
## Background
Personal Password Manager is a completely client-side password manager made using Python. All the information
you enter lives in a database file within the application installed on your device. It uses
[argon](https://argon2-cffi.readthedocs.io/en/stable/argon2.html)
to hash your manager password and 256-bit AES-GCM to encrypt your account passwords. Below are instructions
for installing and using the app. Even further below are some notes about why I created this app and what
I learned from it.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---


## Installation
Currently, there is only a Windows build. Simply download "Personal Password Manger.zip", extract the zip
to your directory of choice, and run "Personal Password Manger.exe". The exe must stay in the same directory
as the "_internal" file also included in the zip.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

## User Guide
### Login/Signup
When opening the program, it will as you to sign up or login. Although the password manager is personal
and completely client-side, this allows you to set up multiple profiles. For instance, you could use one
login for your personal accounts, another for your work accounts, another for someone else that uses
your same computer, etc. The mandated use of an "email" for login is simply to ease remembering your
login information.

As with any password manager, your password should be strong, as this password is what's used to protect
all your other passwords inside your account. A common suggestion is to try using a passphrase of around
four or more random words.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

### Main Window
The app is entirely controlled through the table display, the sidebar buttons, and the search bar at the
bottom. The table will have vertical and horizontal scrollbars available should it become too long or wide
to see everything at once in the window. To start, you could add accounts one-by-one, or you could import
them from a CSV. When using the sidebar buttons, you will be prompted accordingly depending on what
additional information is necessary to perform the action.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

## Motivations
- I currently use my browser to store some of my passwords and I'd like to migrate those to a proper password manager
- Some password managers have had database breaches recently, so I'd like to stay away from those
- Since my internship ended a few months ago, I haven't programmed much, so this would be a nice small project to ease
back into Fall semester

Best case: I create my own free, secure, easy-to-use password manager that can still autofill login fields in my
browser. I can migrate my passwords over and use it myself. Others could potentially use it or build on it.

Worst case: My password manager isn't convenient enough for me to migrate to it, but at least I've learned a bit about
what it takes to create one.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

## Mini-Post Mortem
### What went right?
#### GUI
Choosing customtkinter (a more modern-styled wrapper of tkinter) was a good choice.
Part of the reason I chose to use Python was because it seemed to have some pretty
simple yet effective GUI libraries. I hadn't used any of them before this project,
but it turns out my assumption about tkinter being relatively simple to use was
right.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

#### Database and Cryptography Utils
Choosing to abstract DB interactions and cryptographic-related functions
into their own utility classes was very helpful. Making most of them at
the start of the project helped to plan out my program and adding some
new DB utils as I found myself needing them was fairly easy.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

### What went wrong?
#### Scoping
By the time I started this project, I only had a little over a week before I needed to move back
to my dorm in Boston for the new school year. I would've started earlier in the Summer, but
I didn't get the idea for the project until two weeks away from the end. My scope had three issues:

1. I originally started the project by trying to create a Chrome extension that could autofill
login forms, which was initially simple until I started finding edge cases with form input
names, with forms that only appeared in the DOM tree after clicking on arbitrarily named
buttons, etc. I eventually realized that creating a consistently-working extension, to
ideally be paired with this password manager, was its own entire problem. I then put
the extension aside and realized I should probably start with the password manager first.

2. Considering I didn't spend my entire last week of Summer in my room programming
and also spent some time with my family, there was no way I could complete the program
using my desired thorough design and implementation process before the semester started.
Turns out, I couldn't even do it using my much lazier version of the process, as
I'm only pushing my first packaged build now, roughly three weeks into the semester.

3. Whoever said that some things need an outsider's perspective should get a raise.
Even though I was my own manager on this project, and I should have been aware of
how much time I had to complete it and how long it would take me, I scope-crept
the project. I scope-crept *myself!* As I was already implementing the project,
I of course ran into some unforeseen issues that I had to fix by adding some
additional components. However, I also started wish-listing and implementing
features that didn't need to be in a V1! I eventually came to my senses on
some of these and made them optional goals for potential future versions
of the application.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

#### Testing Coverage
When I was still in the Summer break portion of this project, I was optimistic
about how much time I had left to work on it before the Semester started and
consequently ramped up in workload. I carefully tested all my database and
cryptography utils. However, when later working on the GUI, I pulled a
(not-so) sneaky move and hid some functionalities in the GUI class as a way
to illogically reason that I could avoid creating unit tests for them.
I'd like to think I did this as an unconscious mistake, but that's probably
not the case: I should instinctively know better by now. Additionally,
I didn't bother with creating unit tests for my GUI at all. I only
tested it manually, which fills me with less confidence about my program
than if I unit-tested it. Lastly, I didn't really create any integration
nor total end-to-end tests. Although I'm claiming that this was because
of time constraints, making these tests might have saved me more time
in the long run due to some debugging that was a lot harder to figure
out from manually testing the GUI.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

#### Database Design/ORM vs. "No-RM"
Early on in the project, I did some refactoring for two reasons. Firstly,
I decided early on that since this program was small and there would be
few database models involved, I wasn't going to use an ORM. However,
I still started by making some Python class representations of the
data I'd put into the DB. I eventually refactored after realizing
that if I were to use these objects as an intermediary to the DB
without a true ORM, they would need to be created and destroyed
every time the program interacted with any DB value. I thought
this was gratuitous, so I instead opted to make utility methods
that were the sole way any other part of the program would
interact with the DB. At least this way SQL code would be
abstracted out from logical operations. Additionally,
this was my first time working with SQLite, so I had
to adjust a few pieces of my database design partway
through development.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

#### Implementation before sufficiently researching encryption methods
I originally used AES-CBC before further reading convinced me to switch
to AES-GCM. I could have saved some time if I had simply used GCM in the
first place.

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---

### What I learned
#### Soft skills/advice-to-self
- Time management (working on a personal programming project while starting a new semester)
- I should scope smaller (further iteration can come later)
- I should introspect to make sure I'm not secretly coercing myself to abandon best practices
  (i.e., some shortcuts are worse in the long-run)

<br>

#### Hard skills
- Tkinter
- Cryptography basics (hashing and encryption)
- SQLite

<div style="text-align: right"> <a href="#top">[ ↑ Back to top  ↑ ]</a> </div>

---
