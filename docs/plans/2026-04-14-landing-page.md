# Landing Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a static HTML/CSS/JS marketing landing page for servis.io hosted on GitHub Pages.

**Architecture:** Single `index.html` with a linked `style.css` and `script.js`. No build tools, no frameworks. Form submissions handled by Formspree (free). Deployed via GitHub Pages.

**Tech Stack:** HTML5, CSS3 (custom properties, flexbox, grid), vanilla JS, Google Fonts (Inter), Formspree for contact form.

---

### Task 1: Project scaffold

**Files:**
- Create: `landing/index.html`
- Create: `landing/style.css`
- Create: `landing/script.js`

**Step 1: Create the folder and base files**

```
landing/
  index.html
  style.css
  script.js
```

**Step 2: Write `landing/index.html` base shell**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>servis.io — Smart Replies for Growing Businesses</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="style.css" />
</head>
<body>

  <!-- NAV -->
  <!-- HERO -->
  <!-- SERVICES -->
  <!-- HOW IT WORKS -->
  <!-- PRICING -->
  <!-- CONTACT -->
  <!-- FOOTER -->

  <script src="script.js"></script>
</body>
</html>
```

**Step 3: Write `landing/style.css` CSS variables and reset**

```css
:root {
  --white: #FFFFFF;
  --pastel-blue: #A8C8E8;
  --pastel-blue-dark: #7AAFD4;
  --navy: #1B2A4A;
  --navy-light: #2E4170;
  --gray-light: #F4F7FB;
  --gray-mid: #CBD5E1;
  --gray-text: #64748B;
  --font: 'Inter', sans-serif;
  --radius: 12px;
  --shadow: 0 2px 16px rgba(27,42,74,0.08);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font);
  color: var(--navy);
  background: var(--white);
  line-height: 1.6;
}

a { text-decoration: none; color: inherit; }
img { max-width: 100%; display: block; }

.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px;
}

.btn {
  display: inline-block;
  padding: 12px 28px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  border: none;
}

.btn-primary {
  background: var(--pastel-blue);
  color: var(--navy);
}

.btn-primary:hover {
  background: var(--pastel-blue-dark);
  transform: translateY(-1px);
}

.btn-outline {
  background: transparent;
  border: 2px solid var(--pastel-blue);
  color: var(--navy);
}

.btn-outline:hover {
  background: var(--pastel-blue);
}

section {
  padding: 80px 0;
}

.section-label {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--pastel-blue-dark);
  margin-bottom: 12px;
}

.section-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 16px;
}

.section-sub {
  font-size: 1.05rem;
  color: var(--gray-text);
  max-width: 560px;
}
```

**Step 4: Write `landing/script.js` base**

```js
// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});

// Mobile nav toggle
const navToggle = document.getElementById('nav-toggle');
const navMenu = document.getElementById('nav-menu');
if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('open');
  });
}
```

**Step 5: Open `landing/index.html` in a browser to verify it loads with no errors**

**Step 6: Commit**

```bash
git add landing/
git commit -m "feat: scaffold landing page files"
```

---

### Task 2: Nav

**Files:**
- Modify: `landing/index.html` — replace `<!-- NAV -->` comment
- Modify: `landing/style.css` — append nav styles

**Step 1: Add nav HTML inside `<body>` replacing the `<!-- NAV -->` comment**

```html
<nav class="nav">
  <div class="container nav__inner">
    <a href="#" class="nav__logo">servis<span>.io</span></a>
    <button class="nav__toggle" id="nav-toggle" aria-label="Toggle menu">&#9776;</button>
    <ul class="nav__menu" id="nav-menu">
      <li><a href="#services">Services</a></li>
      <li><a href="#how-it-works">How It Works</a></li>
      <li><a href="#pricing">Pricing</a></li>
      <li><a href="#contact" class="btn btn-primary">Get Started</a></li>
    </ul>
  </div>
</nav>
```

**Step 2: Append nav styles to `style.css`**

```css
/* NAV */
.nav {
  position: sticky;
  top: 0;
  background: var(--white);
  border-bottom: 1px solid var(--gray-mid);
  z-index: 100;
  padding: 16px 0;
}

.nav__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav__logo {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--navy);
}

.nav__logo span {
  color: var(--pastel-blue-dark);
}

.nav__menu {
  display: flex;
  align-items: center;
  gap: 32px;
  list-style: none;
}

.nav__menu a {
  font-weight: 500;
  color: var(--navy);
  transition: color 0.2s;
}

.nav__menu a:hover { color: var(--pastel-blue-dark); }

.nav__toggle {
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--navy);
}

@media (max-width: 768px) {
  .nav__toggle { display: block; }
  .nav__menu {
    display: none;
    flex-direction: column;
    position: absolute;
    top: 64px;
    left: 0;
    right: 0;
    background: var(--white);
    padding: 24px;
    border-bottom: 1px solid var(--gray-mid);
    gap: 16px;
  }
  .nav__menu.open { display: flex; }
}
```

**Step 3: Open in browser — verify nav is sticky, logo shows, mobile toggle works**

**Step 4: Commit**

```bash
git add landing/
git commit -m "feat: add nav with mobile toggle"
```

---

### Task 3: Hero section

**Files:**
- Modify: `landing/index.html` — replace `<!-- HERO -->` comment
- Modify: `landing/style.css` — append hero styles

**Step 1: Add hero HTML**

```html
<section class="hero" id="hero">
  <div class="container hero__inner">
    <div class="hero__content">
      <p class="section-label">Facebook Automation for PH Businesses</p>
      <h1 class="hero__title">Every Message Answered.<br>Instantly.</h1>
      <p class="hero__sub">servis.io automates your Facebook Page replies using your own menu and pricing — so your customers always get a response, even at 2AM.</p>
      <a href="#contact" class="btn btn-primary hero__cta">Get Started Free</a>
    </div>
  </div>
</section>
```

**Step 2: Append hero styles to `style.css`**

```css
/* HERO */
.hero {
  background: linear-gradient(135deg, var(--white) 60%, var(--gray-light) 100%);
  padding: 100px 0 80px;
}

.hero__title {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 20px;
  color: var(--navy);
}

.hero__sub {
  font-size: 1.15rem;
  color: var(--gray-text);
  max-width: 520px;
  margin-bottom: 36px;
}

.hero__cta {
  font-size: 1.05rem;
  padding: 14px 36px;
}

@media (max-width: 768px) {
  .hero__title { font-size: 2rem; }
  .hero { padding: 60px 0; }
}
```

**Step 3: Open in browser — verify hero text is readable, CTA scrolls to contact**

**Step 4: Commit**

```bash
git add landing/
git commit -m "feat: add hero section"
```

---

### Task 4: Services section

**Files:**
- Modify: `landing/index.html` — replace `<!-- SERVICES -->` comment
- Modify: `landing/style.css` — append services styles

**Step 1: Add services HTML**

```html
<section class="services" id="services">
  <div class="container">
    <p class="section-label">What We Offer</p>
    <h2 class="section-title">Services</h2>
    <p class="section-sub">Automation tools built for online businesses that sell on Facebook.</p>

    <div class="services__grid">
      <div class="service-card">
        <div class="service-card__icon">💬</div>
        <h3>Facebook DM Auto-Reply</h3>
        <p>Automatically respond to every customer message with smart, catalog-aware replies in their language.</p>
        <span class="badge badge--live">Live</span>
      </div>
      <div class="service-card">
        <div class="service-card__icon">🗨️</div>
        <h3>Comment Auto-Reply</h3>
        <p>Reply to comments on your posts or send automated DMs to customers who engage with your content.</p>
        <span class="badge badge--live">Live</span>
      </div>
      <div class="service-card service-card--muted">
        <div class="service-card__icon">📸</div>
        <h3>Instagram Auto-Reply</h3>
        <p>Bring the same instant reply experience to your Instagram business account.</p>
        <span class="badge badge--soon">Coming Soon</span>
      </div>
      <div class="service-card service-card--muted">
        <div class="service-card__icon">📅</div>
        <h3>Post Scheduling</h3>
        <p>Plan and schedule your Facebook posts in advance without lifting a finger on posting day.</p>
        <span class="badge badge--soon">Coming Soon</span>
      </div>
    </div>
  </div>
</section>
```

**Step 2: Append services styles to `style.css`**

```css
/* SERVICES */
.services { background: var(--gray-light); }

.services__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-top: 48px;
}

.service-card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 32px 24px;
  box-shadow: var(--shadow);
  transition: transform 0.2s;
}

.service-card:hover { transform: translateY(-4px); }

.service-card--muted { opacity: 0.6; }
.service-card--muted:hover { transform: none; }

.service-card__icon {
  font-size: 2rem;
  margin-bottom: 16px;
}

.service-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--navy);
}

.service-card p {
  font-size: 0.95rem;
  color: var(--gray-text);
  margin-bottom: 16px;
}

.badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 99px;
}

.badge--live {
  background: #D1FAE5;
  color: #065F46;
}

.badge--soon {
  background: var(--gray-light);
  color: var(--gray-text);
  border: 1px solid var(--gray-mid);
}
```

**Step 3: Verify cards display in a grid, coming soon cards are visually muted**

**Step 4: Commit**

```bash
git add landing/
git commit -m "feat: add services section"
```

---

### Task 5: How It Works section

**Files:**
- Modify: `landing/index.html` — replace `<!-- HOW IT WORKS -->` comment
- Modify: `landing/style.css` — append how-it-works styles

**Step 1: Add how it works HTML**

```html
<section class="how" id="how-it-works">
  <div class="container">
    <p class="section-label">Simple Setup</p>
    <h2 class="section-title">How It Works</h2>
    <p class="section-sub">Get your business replying automatically in three easy steps.</p>

    <div class="how__steps">
      <div class="how__step">
        <div class="how__number">1</div>
        <h3>Connect your Facebook Page</h3>
        <p>Link your page in one click using Facebook Login. No technical setup required.</p>
      </div>
      <div class="how__divider">→</div>
      <div class="how__step">
        <div class="how__number">2</div>
        <h3>Upload your catalog</h3>
        <p>Share your Google Sheet with your products and prices. We sync it automatically.</p>
      </div>
      <div class="how__divider">→</div>
      <div class="how__step">
        <div class="how__number">3</div>
        <h3>Go live</h3>
        <p>Your customers get instant, accurate replies 24/7 — in their own language.</p>
      </div>
    </div>
  </div>
</section>
```

**Step 2: Append how-it-works styles to `style.css`**

```css
/* HOW IT WORKS */
.how__steps {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-top: 56px;
}

.how__step {
  flex: 1;
  text-align: center;
  padding: 32px 20px;
}

.how__number {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--pastel-blue);
  color: var(--navy);
  font-size: 1.3rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.how__step h3 {
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--navy);
}

.how__step p {
  font-size: 0.95rem;
  color: var(--gray-text);
}

.how__divider {
  font-size: 1.5rem;
  color: var(--pastel-blue-dark);
  padding-top: 40px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .how__steps { flex-direction: column; align-items: center; }
  .how__divider { transform: rotate(90deg); padding-top: 0; }
}
```

**Step 3: Verify 3 steps display horizontally on desktop, stack on mobile**

**Step 4: Commit**

```bash
git add landing/
git commit -m "feat: add how it works section"
```

---

### Task 6: Pricing section

**Files:**
- Modify: `landing/index.html` — replace `<!-- PRICING -->` comment
- Modify: `landing/style.css` — append pricing styles

**Step 1: Add pricing HTML**

```html
<section class="pricing" id="pricing">
  <div class="container">
    <p class="section-label">Simple Pricing</p>
    <h2 class="section-title">Choose Your Plan</h2>
    <p class="section-sub">No hidden fees. Cancel anytime.</p>

    <div class="pricing__grid">

      <div class="pricing-card">
        <h3>Starter</h3>
        <div class="pricing-card__price">₱999<span>/mo</span></div>
        <ul class="pricing-card__features">
          <li>✓ 1 Facebook Page</li>
          <li>✓ 500 messages/month</li>
          <li>✓ DM Auto-Reply</li>
          <li class="muted">✗ Comment Auto-Reply</li>
          <li class="muted">✗ Keyword Rules</li>
          <li class="muted">✗ Priority Support</li>
        </ul>
        <a href="#contact" class="btn btn-outline">Get Started</a>
      </div>

      <div class="pricing-card pricing-card--featured">
        <div class="pricing-card__badge">Most Popular</div>
        <h3>Growth</h3>
        <div class="pricing-card__price">₱1,999<span>/mo</span></div>
        <ul class="pricing-card__features">
          <li>✓ 3 Facebook Pages</li>
          <li>✓ 2,000 messages/month</li>
          <li>✓ DM Auto-Reply</li>
          <li>✓ Comment Auto-Reply</li>
          <li>✓ Keyword Rules</li>
          <li class="muted">✗ Priority Support</li>
        </ul>
        <a href="#contact" class="btn btn-primary">Get Started</a>
      </div>

      <div class="pricing-card">
        <h3>Pro</h3>
        <div class="pricing-card__price">₱3,999<span>/mo</span></div>
        <ul class="pricing-card__features">
          <li>✓ Unlimited Pages</li>
          <li>✓ Unlimited messages</li>
          <li>✓ DM Auto-Reply</li>
          <li>✓ Comment Auto-Reply</li>
          <li>✓ Keyword Rules</li>
          <li>✓ Priority Support</li>
        </ul>
        <a href="#contact" class="btn btn-outline">Contact Us</a>
      </div>

    </div>
  </div>
</section>
```

**Step 2: Append pricing styles to `style.css`**

```css
/* PRICING */
.pricing { background: var(--gray-light); }

.pricing__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  margin-top: 56px;
  align-items: start;
}

.pricing-card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 36px 28px;
  box-shadow: var(--shadow);
  position: relative;
}

.pricing-card--featured {
  border: 2px solid var(--pastel-blue);
  transform: scale(1.03);
}

.pricing-card__badge {
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--pastel-blue);
  color: var(--navy);
  font-size: 0.8rem;
  font-weight: 700;
  padding: 4px 16px;
  border-radius: 99px;
  white-space: nowrap;
}

.pricing-card h3 {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--navy);
}

.pricing-card__price {
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 24px;
}

.pricing-card__price span {
  font-size: 1rem;
  font-weight: 400;
  color: var(--gray-text);
}

.pricing-card__features {
  list-style: none;
  margin-bottom: 28px;
}

.pricing-card__features li {
  padding: 6px 0;
  font-size: 0.95rem;
  color: var(--navy);
  border-bottom: 1px solid var(--gray-light);
}

.pricing-card__features li.muted {
  color: var(--gray-mid);
}

.pricing-card .btn {
  width: 100%;
  text-align: center;
}

@media (max-width: 768px) {
  .pricing-card--featured { transform: none; }
}
```

**Step 3: Verify 3 cards show, Growth is highlighted and slightly larger**

**Step 4: Commit**

```bash
git add landing/
git commit -m "feat: add pricing section"
```

---

### Task 7: Contact form section

**Files:**
- Modify: `landing/index.html` — replace `<!-- CONTACT -->` comment
- Modify: `landing/style.css` — append contact styles

**Step 1: Sign up for a free Formspree account at formspree.io, create a new form, copy the form endpoint URL (format: `https://formspree.io/f/XXXXXXXX`)**

**Step 2: Add contact HTML — replace `YOUR_FORMSPREE_ID` with your actual Formspree endpoint**

```html
<section class="contact" id="contact">
  <div class="container">
    <p class="section-label">Get In Touch</p>
    <h2 class="section-title">Ready to Get Started?</h2>
    <p class="section-sub">Fill out the form and we'll set up your account within 24 hours.</p>

    <form class="contact__form" action="https://formspree.io/f/YOUR_FORMSPREE_ID" method="POST">
      <div class="contact__row">
        <div class="form-group">
          <label for="name">Your Name</label>
          <input type="text" id="name" name="name" placeholder="Juan dela Cruz" required />
        </div>
        <div class="form-group">
          <label for="business">Business Name</label>
          <input type="text" id="business" name="business" placeholder="Bubble Tea Co." required />
        </div>
      </div>
      <div class="form-group">
        <label for="email">Email Address</label>
        <input type="email" id="email" name="email" placeholder="juan@yourbusiness.com" required />
      </div>
      <div class="form-group">
        <label for="message">Message</label>
        <textarea id="message" name="message" rows="4" placeholder="Tell us about your business and what you need..."></textarea>
      </div>
      <button type="submit" class="btn btn-primary contact__submit">Send Message</button>
    </form>
  </div>
</section>
```

**Step 3: Append contact styles to `style.css`**

```css
/* CONTACT */
.contact__form {
  max-width: 640px;
  margin-top: 48px;
}

.contact__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--navy);
}

.form-group input,
.form-group textarea {
  padding: 12px 16px;
  border: 1.5px solid var(--gray-mid);
  border-radius: 8px;
  font-family: var(--font);
  font-size: 0.95rem;
  color: var(--navy);
  transition: border-color 0.2s;
  background: var(--white);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--pastel-blue-dark);
}

.contact__submit {
  padding: 14px 40px;
  font-size: 1rem;
}

@media (max-width: 600px) {
  .contact__row { grid-template-columns: 1fr; }
}
```

**Step 4: Test form submission — fill it in and verify Formspree receives it**

**Step 5: Commit**

```bash
git add landing/
git commit -m "feat: add contact form with Formspree"
```

---

### Task 8: Footer

**Files:**
- Modify: `landing/index.html` — replace `<!-- FOOTER -->` comment
- Modify: `landing/style.css` — append footer styles

**Step 1: Add footer HTML**

```html
<footer class="footer">
  <div class="container footer__inner">
    <div class="footer__brand">
      <span class="nav__logo">servis<span>.io</span></span>
      <p>Smart replies for growing businesses.</p>
    </div>
    <p class="footer__copy">&copy; 2026 servis.io. All rights reserved.</p>
  </div>
</footer>
```

**Step 2: Append footer styles to `style.css`**

```css
/* FOOTER */
.footer {
  background: var(--navy);
  color: var(--white);
  padding: 48px 0;
}

.footer__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.footer__brand .nav__logo {
  color: var(--white);
  font-size: 1.3rem;
}

.footer__brand .nav__logo span {
  color: var(--pastel-blue);
}

.footer__brand p {
  font-size: 0.9rem;
  color: var(--gray-mid);
  margin-top: 4px;
}

.footer__copy {
  font-size: 0.85rem;
  color: var(--gray-mid);
}
```

**Step 3: Verify footer shows on dark navy background with correct colors**

**Step 4: Commit**

```bash
git add landing/
git commit -m "feat: add footer"
```

---

### Task 9: Final review and GitHub Pages deploy

**Step 1: Open `landing/index.html` in browser — scroll through all sections and verify:**
- Nav is sticky and mobile toggle works
- All section links scroll smoothly
- Pricing Growth card is highlighted
- Contact form fields are accessible
- Footer is visible on navy background
- Page looks correct on mobile (resize browser to 375px wide)

**Step 2: Initialize git repo if not already done**

```bash
cd C:/Users/jcndc/github/serbisyo.ai
git init
git add .
git commit -m "feat: initial project with landing page"
```

**Step 3: Push to GitHub**

```bash
git remote add origin https://github.com/YOUR_USERNAME/servis.io.git
git branch -M main
git push -u origin main
```

**Step 4: Enable GitHub Pages**
- Go to the repo on GitHub → Settings → Pages
- Source: Deploy from branch → `main` → `/landing` folder (if supported) or move files to root
- Note: GitHub Pages serves from `/` (root) or `/docs`. If needed, move `landing/` contents to root or a `docs/` folder.

**Step 5: Visit the live URL (format: `https://YOUR_USERNAME.github.io/servis.io`) and verify all sections load**

**Step 6: Final commit if any fixes were needed**

```bash
git add .
git commit -m "fix: landing page deploy adjustments"
git push
```
