import sys
import unittest
from pathlib import Path

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.database import get_direct_db
from backend.config import Config

class TestAuth(unittest.TestCase):
    def setUp(self):
        # Use an isolated test database
        self.orig_db_path = Config.DATABASE_PATH
        self.test_db_path = BASE_DIR / 'storage' / 'test_database.sqlite'
        Config.DATABASE_PATH = self.test_db_path
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        Config.DATABASE_PATH = self.orig_db_path
        if self.test_db_path.is_file():
            try:
                self.test_db_path.unlink()
            except Exception:
                pass

    def test_registration_validation(self):
        # 1. Successful registration
        res = self.client.post('/api/auth/register', json={
            'name': 'Test User',
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'testuser')

        # 2. Duplicate username
        res = self.client.post('/api/auth/register', json={
            'name': 'Another User',
            'username': 'testuser',
            'email': 'another@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.assertEqual(res.status_code, 409)

        # 3. Duplicate email
        res = self.client.post('/api/auth/register', json={
            'name': 'Another User',
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.assertEqual(res.status_code, 409)

        # 4. Mismatched passwords
        res = self.client.post('/api/auth/register', json={
            'name': 'Mismatch User',
            'username': 'mismatch',
            'email': 'mismatch@example.com',
            'password': 'Password123!',
            'confirm_password': 'Different123!'
        })
        self.assertEqual(res.status_code, 400)

        # 5. Weak password
        res = self.client.post('/api/auth/register', json={
            'name': 'Weak User',
            'username': 'weakuser',
            'email': 'weak@example.com',
            'password': 'weak',
            'confirm_password': 'weak'
        })
        self.assertEqual(res.status_code, 400)

    def test_login(self):
        # Register user
        self.client.post('/api/auth/register', json={
            'name': 'Login Tester',
            'username': 'logintester',
            'email': 'login@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })

        # Login with username
        res1 = self.client.post('/api/auth/login', json={
            'login': 'logintester',
            'password': 'Password123!'
        })
        self.assertEqual(res1.status_code, 200)
        self.assertIn('token', res1.get_json())

        # Login with email
        res2 = self.client.post('/api/auth/login', json={
            'login': 'login@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(res2.status_code, 200)

        # Invalid password
        res3 = self.client.post('/api/auth/login', json={
            'login': 'logintester',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(res3.status_code, 401)

    def test_forgot_and_reset_password(self):
        # Register user
        self.client.post('/api/auth/register', json={
            'name': 'Reset Tester',
            'username': 'resettester',
            'email': 'reset@example.com',
            'password': 'OldPassword123!',
            'confirm_password': 'OldPassword123!'
        })

        # Request forgot password
        res = self.client.post('/api/auth/forgot-password', json={
            'email': 'reset@example.com'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        code = data.get('dev_verification_code')
        self.assertTrue(code is not None and len(code) == 6)

        # Reset password with correct code
        reset_res = self.client.post('/api/auth/reset-password', json={
            'email': 'reset@example.com',
            'code': code,
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        self.assertEqual(reset_res.status_code, 200)

        # Verify old password fails and new password works
        fail_login = self.client.post('/api/auth/login', json={
            'login': 'resettester',
            'password': 'OldPassword123!'
        })
        self.assertEqual(fail_login.status_code, 401)

        success_login = self.client.post('/api/auth/login', json={
            'login': 'resettester',
            'password': 'NewPassword123!'
        })
        self.assertEqual(success_login.status_code, 200)

if __name__ == '__main__':
    unittest.main()
