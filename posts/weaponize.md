
### Title: How I turned my Android phone into a weapon (and why you should too)

**Subtitle:** You don't need a KSH 50,000 laptop to learn to code. You need Termux, Neovim, and a little spite.

---

### The Problem

I was in a campus computer lab once. 40 students. 15 working computers. The rest were "being repaired" (they'd been "being repaired" for 8 months).

The students without laptops? They had phones. Every single one.

But every coding tutorial starts with "install VS Code" or "make sure you have a Unix terminal." Try doing that on a Tecno Spark. Try running Docker. Try not crying when your laptop-less friend asks "can I learn to code?"

I watched talented people give up because they didn't have the *right hardware*.

That pissed me off.

---

### The Question

What if a phone could be a professional development environment?

Not "mobile coding" apps that are just wrappers around web views. Not cloud IDEs that die when your internet drops. Not "learn to code" toys that teach you nothing about real development.

**A real terminal. A real editor. Real LSP servers. Real Git. All running locally. On a phone.**

Termux exists. Neovim exists. But out of the box, they're barebones. No autocomplete. No hover docs. No IDE features. Just a blinking cursor.

The pieces were there. Someone just had to assemble them.

---

### The Build

I spent weeks (nights, really — after work, when I should have been sleeping) figuring out:

- How to get LSP servers (Pyright, tsserver, rust_analyzer) running on Termux's filesystem (paths are weird on Android)
- How to make Neovim's Lua config work without breaking on mobile (small screen, touch input, different keyboard)
- How to auto-install everything so a beginner could run one command and have a working IDE
- How to make it *look* good (because if it looks like 1985, no one will use it)

The result is **weaponize** — a turnkey Neovim configuration that turns your Android phone into a god-mode IDE.

---

### What It Does

Clone the repo. Run `./install.sh`. Type `nvim`.

That's it.

You get:
- Autocomplete (type `os.` and see every method in Python's standard library)
- Hover documentation (press `K` on any function)
- Go to definition (`gd`)
- Find references (`gr`)
- Auto-pairing (quotes, brackets, parentheses close themselves)
- Indentation lines (so you never lose your place)
- File search (`Space + f`)
- Git integration
- A terminal that actually looks like a hacker's terminal (custom prompt, weapon emoji keys, your handle in the prompt)

All running locally. On your phone. No internet required after setup.

---

### Why This Matters

In Kenya, a laptop costs 50-80K KES. That's 2-3 months of rent. That's school fees. That's "maybe next year."

A phone? You already have one.

Weaponize isn't just a Neovim config. It's a statement: **skill > hardware.** You don't need a $2000 laptop to learn to code. You need curiosity, persistence, and the right tools.

If this helps one student in a campus computer lab with no working PCs write their first real program, it was worth it.

---

### What I Learned

- **Termux is underrated.** It's a full Linux environment on Android. More people should know about it.
- **Lua is actually beautiful.** Vimscript is legacy garbage. Lua configs are readable, maintainable, and fast.
- **Documentation is harder than code.** Writing the installation guide (Installation.md) took longer than writing the installer script. But it's worth it — users need to actually *use* your work.
- **Polish matters.** The boot animation, the accent color picker, the weapon emoji keys? Those are the difference between "a tool" and "a product."

---

### Try It Yourself

If you have an Android phone and a desire to code:

```bash
# Install Termux from F-Droid (NOT Play Store)
pkg install neovim git
git clone https://github.com/tonyngugi997/weaponize.git
cd weaponize
./install.sh
nvim
```

Full instructions in the [README](https://github.com/tonyngugi997/weaponize).

---

### The Final Word

You held the ember. You did not burn.

The temple accepts you.

You are weaponized.

Now go build something insane. From your phone.

---
