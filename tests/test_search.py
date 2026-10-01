import unittest
from pathlib import Path
from werkzeug.security import generate_password_hash
from backend.app import create_app
from backend.config import Config
from backend.database import get_db
from backend.auth import generate_auth_token

BASE_DIR = Path(__file__).resolve().parent.parent

class TestUserSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_db_path = Config.DATABASE_PATH
        cls.test_db_path = BASE_DIR / 'storage' / 'test_search_db.sqlite'
        Config.DATABASE_PATH = cls.test_db_path

        cls.app = create_app()
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db = get_db()
            pw = generate_password_hash('TestPass123!')
            db.execute(
                "INSERT INTO users (id, name, username, email, password_hash) VALUES (1, 'Naran', 'naran123', 'nampoothiri@test.com', ?)",
                (pw,)
            )
            db.execute(
                "INSERT INTO users (id, name, username, email, password_hash) VALUES (2, 'Nandana', 'nandana', 'nandana@test.com', ?)",
                (pw,)
            )
            db.commit()

        cls.token_user1 = generate_auth_token(1)
        cls.token_user2 = generate_auth_token(2)
        cls.headers_u1 = {'Authorization': f'Bearer {cls.token_user1}'}
        cls.headers_u2 = {'Authorization': f'Bearer {cls.token_user2}'}

    @classmethod
    def tearDownClass(cls):
        Config.DATABASE_PATH = cls.orig_db_path
        if cls.test_db_path.is_file():
            try:
                cls.test_db_path.unlink()
            except Exception:
                pass

    def test_search_by_username(self):
        # User 1 searches for nandana
        resp = self.client.get('/api/users/search?q=nandana', headers=self.headers_u1)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        users = data['users']
        self.assertTrue(any(u['username'] == 'nandana' for u in users))
        found = next(u for u in users if u['username'] == 'nandana')
        self.assertEqual(found['name'], 'Nandana')
        self.assertNotIn('email', found) # Email is private!

    def test_search_by_at_username(self):
        # User 1 searches with @ prefix: @nandana
        resp = self.client.get('/api/users/search?q=@nandana', headers=self.headers_u1)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(any(u['username'] == 'nandana' for u in data['users']))

    def test_search_by_email(self):
        # User 1 searches for user 2 by email: nandana@test.com
        resp = self.client.get('/api/users/search?q=nandana@test.com', headers=self.headers_u1)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(any(u['username'] == 'nandana' for u in data['users']))
        # Ensure email is NOT exposed in response payload
        for u in data['users']:
            if u['id'] != 1:
                self.assertNotIn('email', u)

    def test_search_typo_with_trailing_numbers(self):
        # User 2 searches for naran111 (typo for naran123)
        resp = self.client.get('/api/users/search?q=naran111', headers=self.headers_u2)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(any(u['username'] == 'naran123' for u in data['users']))

    def test_search_self(self):
        # User 1 searches for naran123 -> returns self with status 'self'
        resp = self.client.get('/api/users/search?q=naran123', headers=self.headers_u1)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(any(u['id'] == 1 and u['connection_status'] == 'self' for u in data['users']))

    def test_search_with_whitespace(self):
        # Searching with leading/trailing spaces
        resp = self.client.get('/api/users/search?q=%20%20nandana%20%20', headers=self.headers_u1)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(any(u['username'] == 'nandana' for u in data['users']))

if __name__ == '__main__':
    unittest.main()
