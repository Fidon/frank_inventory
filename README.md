# Frank Inventory Management System

## 1. Project Purpose
Frank Inventory is a Django-based inventory management system designed to help small and medium-sized businesses efficiently track products, sales, users, and shop operations. The system aims to streamline inventory control, user management, and reporting, making it ideal for shop owners, inventory managers, and staff who need a reliable, easy-to-use platform for daily operations.

## 2. System Architecture
The project follows Django's standard MVC (Model-View-Controller) architecture:
- **Apps**: Modular Django apps (`users`, `shops`, `crips`, `dashboard`) encapsulate business logic for user management, shop/product handling, inventory operations, and dashboard analytics.
- **Views**: Handle HTTP requests, process data, and render templates for user interaction.
- **Templates**: HTML files (in `templates/`) provide the UI, organized by app and feature.
-- **Static Files**: CSS, JS, images, and third-party libraries (Bootstrap, DataTables, FontAwesome) are stored in `static/` for frontend styling and interactivity. WhiteNoise is used for efficient static file serving in production, including compression and cache-busting.
- **Database**: Uses SQLite3 for local development, with models defined per app.
- **Custom Authentication**: Implements a custom backend (`password_backend.py`) for case-insensitive user authentication, and a custom user model (`users.Customuser`).
- **Middleware**: Standard Django middleware stack is used for security, sessions, CSRF, and more.
- **Uploads**: User-uploaded files are stored in the `uploads/` directory.
- **Utilities**: Common helper functions are in `utils/util_functions.py`.

### Request Flow
1. User requests a URL → Django routes via `urls.py`.
2. The appropriate view processes the request, interacts with models, and renders a template.
3. Static files are served for frontend assets; uploads are handled via MEDIA settings.
4. Authentication and permissions are enforced via middleware and custom backends.
5. Dashboard app provides analytics and summary views for quick insights.

## 3. Key Features
- **User Management**: Custom user model, registration, login, profile management, and permissions.
- **Shop & Product Management**: CRUD operations for shops, products, and inventory items.
- **Sales Tracking**: Record and report sales, generate sales reports.
- **Inventory Reporting**: View and export inventory status, item reports.
- **Dashboard Analytics**: Visual summaries and key metrics for inventory, sales, and users.
- **Role-Based Access**: Admin and staff roles with appropriate permissions.
- **Responsive UI**: Modern interface using Bootstrap and DataTables.
- **Custom Authentication**: Case-insensitive login and custom password validation.

## 4. Setup Instructions
### Prerequisites
- Python 3.10+
- pip (Python package manager)
- (Optional) Virtual environment tool (venv, virtualenv)

### Installation Steps
1. **Clone the repository**
   ```powershell
   git clone <repo-url>
   cd frank_inventory
   ```
2. **Create and activate a virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Apply migrations**
   ```powershell
   python manage.py migrate
   ```
5. **Create a superuser (admin account)**
   ```powershell
   python manage.py createsuperuser
   ```
6. **Run the development server**
   ```powershell
   python manage.py runserver
   ```
7. **Access the app**
   - Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

#### Static Files in Production (WhiteNoise)
- WhiteNoise is pre-configured for static file serving. To collect static files for deployment, run:
  ```powershell
  python manage.py collectstatic
  ```
- All static files will be gathered in the `staticfiles/` directory and served efficiently with compression and cache-busting.

## 5. Usage Notes and Quirks
- **Custom User Model**: All user-related features use `users.Customuser`. Update references if adding new user features.
- **Case-Insensitive Login**: Authentication backend allows case-insensitive usernames.
- **Static & Media Files**: Static files are in `static/`. For production, static files are served using WhiteNoise from the `staticfiles/` directory. Ensure `STATIC_ROOT` and `MEDIA_ROOT` are set appropriately.
- **Password Validation**: Minimum password length is set to 6 characters.
- **Time Zone**: Default is `Africa/Nairobi`. Change in `settings.py` if needed.
- **Templates Structure**: Organized by app and feature for clarity.
- **Known Quirks**:
  - Some static assets are included as full libraries (Bootstrap, DataTables, FontAwesome) for offline use.
  - If you add new apps, register them in `INSTALLED_APPS` and create migrations.
  - The login URL is set to `/` and redirects to `/dashboard/` after login.

- **apps/**: Contains Django apps (`users`, `shops`, `crips`, `dashboard`) for modular business logic and analytics.
- **frank_inventory/**: Main project settings, URLs, WSGI/ASGI config, custom authentication backend.
- **static/**: Frontend assets (CSS, JS, images, fonts, third-party libraries).
- **staticfiles/**: Directory for collected static files in production, served by WhiteNoise.
- **templates/**: HTML templates for all views, organized by app and feature (including dashboard views).
- **uploads/**: Directory for user-uploaded files (images, documents, etc.).
- **utils/**: Utility functions and helpers (`util_functions.py`).
- **manage.py**: Django's command-line utility for administrative tasks.
- **requirements.txt**: Python dependencies for the project.
- **frank_inventory_dbase.sqlite3**: Default SQLite database file.

---

For questions, issues, or contributions, please open an issue or submit a pull request.
