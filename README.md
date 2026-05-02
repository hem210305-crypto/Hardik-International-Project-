# Admin Panel Project

## Project Structure

```
Hardik Project/
├── authapp/              # Authentication app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── core/                 # Core app (Dashboard, Clients, Users)
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── static/               # Static files
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── img/
│
├── templates/            # HTML templates
│   ├── base.html
│   ├── authapp/
│   └── core/
│       ├── index.html
│       ├── clients.html
│       └── users.html
│
├── manage.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

4. Run development server:
   ```bash
   python manage.py runserver
   ```

## Features

- Dashboard with overview
- Client management
- User management
- Dark theme UI
- Responsive design
