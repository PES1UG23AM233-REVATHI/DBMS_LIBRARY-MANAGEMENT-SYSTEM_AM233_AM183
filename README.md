Library Management System

A complete Flask + MySQL based Library Management System that supports managing books, members, issuing/returning books, and handling penalties. Designed as an academic mini-project with clean modular code and simple UI.

Features
 Authentication

Admin login

Member login

Default password assigned when creating members

 Book Management

Add new books

Update book details

Delete books

View all available books

 Member Management

Add new members

Update member details

Delete members

Assign default password on creation

📖 Issue & Return System

Issue books to members

Track due dates

Automatically calculate penalties

Update book availability

 Automated Penalty Calculation

Based on overdue days

Stored procedures supported (MySQL)

 Frontend

HTML + CSS + Bootstrap

Jinja2 templating

Clean and simple UI

 Tech Stack
Layer	Technology
Backend	Flask (Python)
Database	MySQL
Templates	HTML, CSS, Bootstrap, Jinja2
Tools	SQL Procedures, Sessions, Routing
 Project Structure
library_app/
│
├── app.py               # Main Flask app
├── static/              # CSS, JS, images
├── templates/           # HTML templates
├── database/            # SQL scripts, procedures
└── README.md            # Project documentation

Installation & Setup
1. Clone the Repository
git clone https://github.com/your-username/library-management-system.git
cd library-management-system

2. Create Virtual Environment
python -m venv venv
venv\Scripts\activate    # On Windows

3. Install Dependencies
pip install -r requirements.txt

4. Setup MySQL Database

Create a database:

CREATE DATABASE library_management_db;


Import tables & data (your SQL files):

USE library_management_db;
SOURCE path/to/your.sql;

5. Update Database Credentials

Inside app.py, update:

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'yourpassword'
app.config['MYSQL_DB'] = 'library_management_db'

6. Run the Application
python app.py


Visit:

http://127.0.0.1:5000

 Default Credentials
Role	Username	Password
Admin	admin	admin123
Member	Auto-created	password123
📸 Screenshots

(Add your screenshots here)

/screenshots/home.png
/screenshots/login.png
/screenshots/books.png

 Future Enhancements

Add JWT-based authentication

Implement OTP-based member login

Add dashboard analytics

Add book categories & filtering

 Contributing

Pull requests are welcome.
You can open issues for bugs or feature requests.

 License

This project is open-source under the MIT License.
