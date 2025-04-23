final_project_backend/
├── docs/
│   ├── user_manual.md
│   └── api_reference.md
├── src/
│   ├── main.py         # Entry point aplikasi (mirip app.py di struktur sebelumnya)
│   ├── app/            # Package aplikasi Flask
│   │   ├── __init__.py   # Membuat app sebagai package
│   │   ├── models/       # Direktori untuk model database
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   └── ...
│   │   ├── views/        # Direktori untuk controller/route handlers (seperti blueprints)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── product.py
│   │   │   └── ...
│   │   ├── services/     # Direktori untuk business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── product_service.py
│   │   │   └── ...
│   │   ├── extensions.py # Inisialisasi ekstensi Flask
│   │   └── config.py     # Konfigurasi aplikasi
│   └── utils/
│       └── helper_functions.py
├── tests/
│   ├── unit/
│   │   └── test_main.py   # Contoh unit test
│   ├── integration/
│   │   └── test_api.py    # Contoh integration test
├── data/
│   ├── raw/
│   └── processed/
├── output/
│   ├── reports/
│   └── logs/
├── .env                 # Variabel lingkungan
├── requirements.txt     # Daftar dependensi
└── README.md


