# Hardik International Web Portal - Implementation Plan

This document outlines the step-by-step development flow for building the complete Distributor Web Portal and Admin Portal using Django. Our goal is to write high-quality, scalable, and secure Python code while meticulously matching the Figma UI designs.

## Phase 1: Architecture & Foundation (Backend Setup)

Before touching the UI, we must lay down a solid data foundation.

1.  **Custom User Model & Authentication**
    *   Extend Django's `AbstractUser` to create a unified authentication system.
    *   Define Roles: `Admin`, `Staff`, and `Distributor`.
    *   Implement robust login and password reset flows for both portals.

2.  **Database Modeling (The Core)**
    *   **`Distributor` Model**: Business name, GST, drug license, credit limit, payment terms, contact details.
    *   **`Product` Model**: Name, category, MRP, selling price, stock quantity, batch number, manufacturing/expiry dates.
    *   **`Order` & `OrderItem` Models**: Link distributors to products, track order status (Pending, Processing, Shipped, Delivered), and total amounts.
    *   **`Invoice` & `Ledger` Models**: Track billing, payments, and outstanding balances.
    *   **`Announcement` Model**: Title, content, category, and target audience.
    *   **`StaffPermission` Model**: Granular access control for internal staff.

## Phase 2: Core Backend Logic (Views & URLs)

Once the database is ready, we build the engine that serves data to our views.

1.  **Admin Portal Views (Class-Based Views)**
    *   CRUD operations for Products, Distributors, and Staff.
    *   Order management workflow (updating statuses).
    *   Analytics data aggregation queries.
2.  **Distributor Portal Views**
    *   Product catalog view with filtering/search.
    *   Shopping cart mechanism (Session-based or Database-backed).
    *   Checkout flow and order history viewing.

## Phase 3: Frontend Foundation & Design System

Translating the 18 Figma screens into a pixel-perfect, responsive UI.

1.  **CSS Architecture**
    *   Create a global `style.css` defining CSS variables for colors (Hardik Blue, Red, Grey), typography, and spacing to ensure consistency across the 18 screens.
2.  **Base Templates (`base.html`)**
    *   Create separate base layouts for the **Admin side** (Sidebar + Header) and **Distributor side** (Sidebar + Top nav).
3.  **Reusable UI Components**
    *   Design standard components: Cards, Badges (Status pills), Buttons, Form Inputs, and Tables.

## Phase 4: Page-by-Page UI Implementation

Building out the specific screens, ensuring they look exactly like the Figma designs.

1.  **Distributor Flow**
    *   Login & Dashboard (Overview cards).
    *   Product Catalogue & Place Order (Cart sidebar).
    *   Order History & Bills/Invoices.
2.  **Admin Flow**
    *   Admin Dashboard (Charts and metrics).
    *   Distributors & Products Management tables.
    *   **Complex Modals**: Build the multi-step "Add Distributor" and "Add Product" modals using JavaScript to handle step transitions cleanly.

## Phase 5: Interactivity, Polish & Security

Making the app feel alive and ensuring it is production-ready.

1.  **AJAX & Dynamic Actions**
    *   Use JavaScript (Fetch API) for smooth "Add to Cart" actions without page reloads.
    *   Dynamic filtering on the Products and Orders pages.
2.  **Security & Validations**
    *   Backend form validation (e.g., ensuring order amounts don't exceed credit limits).
    *   Permission checks on every view (e.g., Staff member A cannot view settings if not authorized).
3.  **Analytics Integrations**
    *   Implement Chart.js (or similar) on the Dashboards to render the Revenue Trend and Order Status charts.

---

### Suggested First Action
To begin, I recommend we tackle **Phase 1: Database Modeling**. I will create the `models.py` definitions for `Product`, `Distributor`, `Order`, and `Invoice` so we have our data structures ready to go.
