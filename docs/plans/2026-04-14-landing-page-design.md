# servis.io — Landing Page Design

**Date:** 2026-04-14  
**Status:** Approved, ready for implementation  
**Type:** Static HTML/CSS/JS marketing page

---

## Overview

A clean, professional marketing landing page for servis.io targeting online food and snack businesses in the Philippines (milk tea shops, pastry brands, online food sellers). The goal is to present available services and convert visitors into leads via a contact form.

---

## Tech Stack

| | |
|---|---|
| **Type** | Static HTML/CSS/JS — no frameworks, no build tools |
| **Hosting** | GitHub Pages (free) |
| **Font** | Inter — Google Fonts |
| **Deployment** | Push to GitHub → auto-deploys |

---

## File Structure

```
landing/
  index.html    ← single page, all sections
  style.css     ← all styles
  script.js     ← smooth scroll, mobile nav toggle
```

---

## Visual Style

| Element | Value |
|---|---|
| Background | White `#FFFFFF` |
| Pastel blue accent | `#A8C8E8` |
| Navy headings/text | `#1B2A4A` |
| Font | Inter (Google Fonts) |
| Layout | Card-based, generous white space |
| Responsive | Yes — mobile first |

---

## Page Sections (top to bottom)

### 1. Nav
- servis.io logo (text-based, navy)
- "Get Started" button (pastel blue, right-aligned)
- Mobile: hamburger menu

### 2. Hero
- **Headline:** "Every Message Answered. Instantly."
- **Subheadline:** "servis.io automates your Facebook Page replies using your own menu and pricing — so your customers always get a response, even at 2AM."
- **CTA Button:** "Get Started Free" → scrolls to Contact section

### 3. Services
Four cards:

| Service | Status |
|---|---|
| Facebook Auto-Reply | Live |
| Comment Auto-Reply | Live |
| Instagram Auto-Reply | Coming Soon |
| Post Scheduling | Coming Soon |

"Coming Soon" cards are visually muted (greyed out badge).

### 4. How It Works
Three-step horizontal layout:

1. **Connect your Facebook Page** — Link your page in one click via Facebook Login
2. **Upload your catalog** — Share your Google Sheet with your products and prices
3. **Go live** — Your customers get instant, accurate replies 24/7

### 5. Pricing
Three-column card layout:

| | Starter | Growth | Pro |
|---|---|---|---|
| Price | ₱999/mo | ₱1,999/mo | ₱3,999/mo |
| Facebook Pages | 1 | 3 | Unlimited |
| Messages/mo | 500 | 2,000 | Unlimited |
| DM Auto-Reply | ✓ | ✓ | ✓ |
| Comment Auto-Reply | — | ✓ | ✓ |
| Keyword Rules | — | ✓ | ✓ |
| Priority Support | — | — | ✓ |
| CTA | Get Started | Get Started | Contact Us |

Growth tier is visually highlighted as "Most Popular".

### 6. Contact / Get Started
Simple form:
- Name
- Business Name
- Email
- Message
- Submit button ("Send Message")

No backend needed for MVP — form submits via [Formspree](https://formspree.io) (free, no server required).

### 7. Footer
- servis.io name + tagline: "Smart replies for growing businesses."
- Copyright line

---

## Behavior

- Smooth scroll when clicking nav links or CTA buttons
- Mobile nav toggles open/close on hamburger click
- No animations beyond basic hover states on buttons and cards

---

## Out of Scope

- Testimonials section (added later)
- Blog or resources
- Live chat widget
- Backend form processing (Formspree handles it)
