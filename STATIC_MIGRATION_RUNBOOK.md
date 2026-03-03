# Static Migration Runbook (Django ➜ Static)

This runbook is tailored to your current project.

## Goal
Move the site to static hosting while keeping:
- Public pages (home, my-story, credibility, gallery, contact, booking portal)
- Circlecal embed on booking page
- Existing CSS/JS/images/service worker/PWA assets

And removing Django runtime dependency (server, auth, DB, Python app process).

---

## 1) Freeze Current State (Safety)
1. Make a full backup of the project folder.
2. Export any data you still care about from `db.sqlite3` (only needed if you plan to reuse old bookings/client data somewhere).
3. Keep current Django deployment alive during migration (no downtime cutover).

---

## 2) Contact Form Backend (Locked: Web3Forms)
You selected **Web3Forms** as the contact API. This fits static hosting and does not require Django for contact form submit.

### Implementation steps
1. Create/get your Web3Forms Access Key from the Web3Forms dashboard.
2. In `contact.html`, set form submit target to:
   - `action="https://api.web3forms.com/submit"`
   - `method="POST"`
3. Add hidden fields inside the form:
   - `access_key` (your Web3Forms key)
   - `subject` (default email subject)
   - `from_name` (site name)
4. Add anti-spam fields supported by Web3Forms:
   - `botcheck` hidden checkbox field
5. Keep your existing client-side required validation and success/fail UI.
6. Remove Django POST dependencies from contact page:
   - remove `&#123;% csrf_token %&#125;` and `&#123;&#123; csrf_token &#125;&#125;`
   - remove `fetch("&#123;% url 'contact' %&#125;")` logic
7. Replace with a static submit handler:
   - either plain HTML form submit to Web3Forms
   - or JS `fetch("https://api.web3forms.com/submit", { method: "POST", body: FormData(...) })`

> Do not include private backend keys in front-end code. Web3Forms should be the only contact submission endpoint.

---

## 3) Pick the Static Hosting Target (Locked: GitHub Pages)
You selected **GitHub Pages** as your static host.

Firebase remains in use only for media hosting (photos/videos URLs), which is fully compatible with GitHub Pages.

Recommended publishing source:
- `main pages/` (if this folder contains your final static pages)

Alternative publishing source:
- `/` (repo root), if you prefer site files at the root

---

## 4) Build Static File Structure
Use this structure in your chosen GitHub Pages publishing source:

- `index.html`
- `booking.html`
- `contact.html`
- `gallery.html`
- `my-story.html`
- `credibility.html`
- `404.html`
- `static/bookings/...` (copy from `bookings/static/bookings`)

Also add:
- `.nojekyll` (prevents GitHub Pages/Jekyll from ignoring folders that start with `_`)

If you want pretty URLs (`/contact` instead of `/contact.html`) on GitHub Pages, use folder-based pages:
- `contact/index.html`
- `gallery/index.html`
- `my-story/index.html`
- `credibility/index.html`
- `booking/index.html`

---

## 5) Convert Django Templates to Plain HTML
Your files in `bookings/templates/bookings` still contain Django template tags.

### Replace these globally in public-facing pages:
1. Remove `&#123;% load static %&#125;` lines.
2. Replace static references:
   - From: `&#123;% static 'bookings/...' %&#125;`
   - To: `/static/bookings/...`
3. Replace route tags:
   - `&#123;% url 'index' %&#125;` -> `/index.html`
   - `&#123;% url 'booking_portal' %&#125;` -> `/booking.html`
   - `&#123;% url 'my-story' %&#125;` -> `/my-story.html`
   - `&#123;% url 'credibility' %&#125;` -> `/credibility.html`
   - `&#123;% url 'contact' %&#125;` -> `/contact.html`
   - `&#123;% url 'gallery' %&#125;` -> `/gallery.html`
4. Remove `&#123;% csrf_token %&#125;` and any `&#123;&#123; csrf_token &#125;&#125;` usage.
5. Remove dynamic template vars like `&#123;&#123; RECAPTCHA_PUBLIC_KEY &#125;&#125;` and hardcode public key in HTML if still using reCAPTCHA.

### Keep/Drop by page
Keep as static pages:
- `index.html`, `booking.html`, `contact.html`, `gallery.html`, `my-story.html`, `credibility.html`

Drop (Django-auth/calendar flow you removed):
- `login.html`, `signup.html`, `booking_form.html`, `calendar.html`, `my_bookings.html`, `forgot_username.html`, `registration/*`, `client_menu.html`

---

## 6) Keep Circlecal Embed Intact
Your embed is already client-side iframe in `booking.html`. Keep as-is.

Validate after deploy:
- iframe loads over HTTPS
- no CSP/X-Frame-Options conflict
- mobile responsiveness still works

---

## 7) Service Worker + PWA Path Check
You currently register service worker like:
- `navigator.serviceWorker.register("/static/bookings/service-worker.js")`

That is fine **if** file exists at:
- `firebase_hosting/public/static/bookings/service-worker.js`

Also verify cached paths inside `service-worker.js` exist in static hosting.

---

## 8) Configure GitHub Pages Route Handling
GitHub Pages does not support Firebase-style rewrites.

Use one of these approaches:
1. **Simple approach**: link directly to `.html` pages (`/contact.html`, `/booking.html`, etc.)
2. **Pretty URL approach**: use folder/index pages (`/contact/` from `contact/index.html`)

Also keep custom `404.html` for unknown routes.

---

## 9) Deploy Static Site (GitHub Pages)
From GitHub:
1. Push final static files to your repo.
2. In GitHub repo settings, open **Pages**.
3. Set source branch/folder (for example: `main` + `/main pages`, or `main` + `/root`).
4. Save and wait for GitHub Pages to publish.

If using custom domain:
5. Add your domain in Pages settings.
6. Ensure DNS points to GitHub Pages and wait for HTTPS certificate provisioning.

---

## 10) Cut Over Domain
When static version is verified:
1. Point production domain to GitHub Pages target.
2. Keep Django host running for 24-48 hours as rollback.
3. Monitor errors (broken assets, missing links, contact submit errors).
4. Then decommission Django host.

---

## 11) Cleanup After Successful Cutover
- Remove Python/Django deployment pipeline and runtime env vars (SECRET_KEY, DB creds, Twilio, etc.)
- Keep repo archive branch/tag for historical rollback.
- Optionally split repo into:
  - `site-static` (active)
  - `django-archive` (read-only history)

---

## 12) What Will Break If Not Replaced
If you go fully static without replacement, these backend features will stop:
- Server-side contact email send via Brevo from Django view
- reCAPTCHA server verification in Django
- Any DB-based booking/user/admin flows
- Django admin panel

Circlecal booking still works because it is iframe-based hosted externally.

With Web3Forms configured, contact submission remains functional on static hosting.

---

## Practical Next Step (Recommended)
1. Migrate only these 6 pages first: home, my-story, credibility, gallery, booking, contact.
2. Wire contact page to Web3Forms (`https://api.web3forms.com/submit`) and remove old Django contact POST logic.
3. Deploy to GitHub Pages and test all links/assets before production cutover.

---

## If you want me to continue automatically
I can perform Phase 1 for you in this repo now:
- create `firebase_hosting/public` static copies of those 6 pages,
- convert Django template tags to static paths,
- update nav links,
- and prepare Firebase rewrites.

Then you only choose contact backend option and deploy.
Then you only add your Web3Forms access key and deploy.
