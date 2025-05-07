import os
import unittest
from flask import current_app
# Assuming your app factory is in a package named 'your_app_package'
# Adjust the import based on your project structure
from src.app import create_app
from src.app.config import config_by_name

class TestConfig(unittest.TestCase):

    def test_app_is_testing(self):
        """Test if the application uses the TestingConfig."""
        # Ensure FLASK_ENV is set to 'testing' for this test
        # You might set this globally for your test suite or per test like this
        os.environ['FLASK_ENV'] = 'testing'
        app = create_app() # create_app should load config based on FLASK_ENV

        # Check if the TESTING flag is True
        self.assertTrue(app.config['TESTING'])
        # Check if the correct database URI is loaded
        self.assertEqual(
            app.config['SQLALCHEMY_DATABASE_URI'],
            config_by_name['testing'].SQLALCHEMY_DATABASE_URI # Compare with the explicit TestingConfig URI
        )
        # Check if CSRF is disabled for testing
        self.assertFalse(app.config.get('WTF_CSRF_ENABLED', True)) # Default to True if not set

    def test_app_is_development(self):
         """Test if the application uses the DevelopmentConfig."""
         # Set environment to 'development'
         os.environ['FLASK_ENV'] = 'development'
         app = create_app()

         self.assertFalse(app.config['TESTING'])
         self.assertTrue(app.config['DEBUG'])
         self.assertEqual(
            app.config['SQLALCHEMY_DATABASE_URI'],
            config_by_name['development'].SQLALCHEMY_DATABASE_URI # Compare with the explicit DevelopmentConfig URI
        )

    # Add similar tests for ProductionConfig if needed,
    # being careful about environment variables like SECRET_KEY and DATABASE_URL

    # Clean up environment variable after tests if set within tests
    def tearDown(self):
        if 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']

if __name__ == '__main__':
    unittest.main()