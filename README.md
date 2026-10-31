# Vilio Shop — Modern E-Commerce Platform

A production-grade, full-stack e-commerce web application for contemporary men's apparel, engineered with **Python**, **Django**, and **PostgreSQL**.

Built with a focus on speed, seamless checkout flows, robust inventory management, and integrated digital marketing infrastructure (Razorpay & Meta Conversions API).

---

## Key Highlights & Features

### 🛒 High-Conversion Checkout & Cart Engine
- **Hybrid Guest & Authenticated Cart**: Unregistered shoppers can seamlessly add items to their session bag. Upon login or Google OAuth signup, guest items automatically merge into their persistent database cart without losing selections.
- **Direct "Buy Now" Checkout**: Instant checkout pipeline with automatic return-to-cart fallbacks and session preservation.
- **Smart Address Prefill**: Remembers previous shipping credentials via encrypted cookies and past order lookups to reduce checkout friction.
- **Flexible Payments**: Supports Razorpay online payments (Cards, UPI, Netbanking) and Cash on Delivery (COD) with automated COD fee calculation.
- **Orphan Order Cleanup**: Automatically cleans up abandoned pending orders when payment modals are dismissed.

### 🎨 Variant & Inventory Matrix
- **Multi-Color & Multi-Size Matrix**: Dynamically manages complex SKUs across colorways and size tiers (`XS` through `3XL` and numeric waist sizes).
- **Real-Time Stock Validation**: Prevents overselling with database-level validation during both checkout initiation and post-payment verification.
- **Dynamic Image Gallery**: Cloudinary CDN-backed multi-angle photography with asset deduplication and touch-optimized zoom modal.
- **Promotional Countdown Engine**: Automated flash-sale discount engine with real-time UI timer synchronization.

### 📊 Marketing & Analytics Infrastructure
- **Server-Side Meta Conversions API (CAPI)**: Direct server-to-server purchase event dispatching with SHA-256 hashed user signals (email, phone, address) for reliable conversion tracking resistant to ad-blockers.
- **Meta Pixel Client Integration**: Standard event coverage including `ViewContent`, `AddToCart`, `InitiateCheckout`, `AddPaymentInfo`, `Purchase`, `Search`, and `CompleteRegistration`.
- **Google Merchant Center Feed**: Automated `/product-feed/` endpoint exporting TSV catalog feeds compliant with Google Merchant specifications.
- **XML Sitemap**: Automated Django sitemap generator at `/sitemap.xml` for full search engine indexation.

### ⚡ Performance Optimizations
- **In-Memory Caching**: LocMemCache caching layer for homepage product displays, category trees, and product details (~15ms response times).
- **Database Connection Pooling**: Persistent PostgreSQL pooling with `CONN_MAX_AGE=600` on Supabase to eliminate per-request connection overhead.
- **Cloudinary CDN Integration**: Automatic image format conversion (`f_auto`) and quality optimization (`q_auto:eco`).
- **Asset Pipeline**: WhiteNoise compression and manifest caching for static assets.

### ⚙️ Enhanced Django Admin Dashboard
- **Live Color Stock Manager**: Custom inline stock editor allowing administrators to adjust sizes and inventory quantities directly from the list view without navigating into individual records.
- **Visual Product Changelist**: Real-time stock status summaries, key performance metrics, and single-click catalog visibility toggles.
- **User Management**: Integrated view displaying OAuth provider badges, order history, and saved address statuses.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Django 5.1 (Python 3.12) |
| **Database** | PostgreSQL (Supabase) |
| **Media & Static Storage** | Cloudinary CDN & WhiteNoise |
| **Authentication** | Django Auth + Django Allauth (Google OAuth2 + Email/Password) |
| **Payment Gateway** | Razorpay Python SDK |
| **Frontend** | Vanilla JavaScript (ES6+), CSS3 Flexbox/Grid, Semantic HTML5 |
| **Deployment Target** | Render / Gunicorn / WSGI |

---

## 📁 Project Architecture

```
myproject/
├── app1/                       # Core e-commerce application
│   ├── migrations/             # Database migrations
│   ├── static/                 # Static assets (fonts, icons, styles, JS)
│   ├── templates/              # HTML5 templates (storefront, auth, admin)
│   │   └── admin/              # Custom Django admin overrides
│   ├── admin.py                # Admin site configuration & stock editor
│   ├── apps.py                 # Application configuration
│   ├── context_processors.py   # Global cart counter & category tree
│   ├── meta_capi.py            # Meta Conversions API server-side dispatcher
│   ├── models.py               # Data models (Products, Variants, Orders, Cart)
│   ├── sitemaps.py             # SEO sitemap definitions
│   ├── tests.py                # Automated unit tests
│   ├── urls.py                 # Application routing
│   └── views.py                # View handlers and API controllers
├── myproject/                  # Django project root configuration
│   ├── asgi.py                 # ASGI configuration
│   ├── settings.py             # Project settings & third-party integrations
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI configuration for production servers
├── build.sh                    # Automated deployment build script
├── manage.py                   # Django management utility
├── requirements.txt            # Python dependencies
└── .env.example                # Template for environment configuration
```

---

## 🚀 Getting Started

### 1. Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/aiman001-ai/vilio-shop.git
cd vilio-shop
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project directory based on `.env.example`:

```bash
cp .env.example .env
```

Fill in your respective credentials:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL` or `DATABASE_*`: PostgreSQL connection credentials
- `CLOUDINARY_*`: Cloudinary cloud name, API key, and secret
- `RAZORPAY_*`: Razorpay key ID and key secret
- `EMAIL_*`: SMTP email settings for order notifications
- `META_*`: Meta Pixel and Access Token (optional for local testing)

### 4. Database Migrations & Static Files

```bash
python manage.py migrate
python manage.py collectstatic --no-input
```

### 5. Run the Local Development Server

```bash
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Running Automated Tests

Run the test suite using Django's test runner:

```bash
python manage.py test app1
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Aiman Khan**
- GitHub: [@aiman001-ai](https://github.com/aiman001-ai)
- Project Repository: [vilio-shop](https://github.com/aiman001-ai/vilio-shop)
