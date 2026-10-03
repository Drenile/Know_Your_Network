# Security Policy

Know Your Network scans home networks, so security and privacy bugs matter. Thank you
for helping keep its users safe.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately through GitHub instead:

1. Go to the **Security** tab of this repository.
2. Click **Report a vulnerability**.
3. Describe the problem, how to reproduce it, and what an attacker could do with it.

Once the problem is confirmed, a fix will be
prepared and released.

## What counts as a vulnerability

Beyond the usual (for example, code execution or unsafe file permissions), anything
that breaks the project's privacy promise is treated as a security bug:

- The app sends any data off the user's computer without explicit opt-in.
- The app scans or contacts an address outside the user's private home network.
- The app needs or asks for administrator or root rights.
- Data from the network (device names, banners) is shown without escaping, in the
  terminal or in an HTML report.
- Stored data can be read without the user's encryption key.

## Supported versions

The project is in early development. Only the latest code on `main` is supported.
