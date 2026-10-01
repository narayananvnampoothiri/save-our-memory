import sys
import unittest
import io
from pathlib import Path
from PIL import Image

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.config import Config

def create_dummy_image_bytes():
    buf = io.BytesIO()
    img = Image.new('RGB', (100, 100), color=(200, 100, 100))
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf

class TestPermissions(unittest.TestCase):
    def setUp(self):
        self.orig_db_path = Config.DATABASE_PATH
        self.test_db_path = BASE_DIR / 'storage' / 'test_permissions_db.sqlite'
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

    def test_strict_server_side_media_authorization(self):
        # 1. Register User A (Alice)
        res_a = self.client.post('/api/auth/register', json={
            'name': 'Alice',
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        token_a = res_a.get_json()['token']
        user_a_id = res_a.get_json()['user']['id']

        # 2. Register User B (Bob)
        res_b = self.client.post('/api/auth/register', json={
            'name': 'Bob',
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        token_b = res_b.get_json()['token']
        user_b_id = res_b.get_json()['user']['id']

        # 3. Register User C (Charlie)
        res_c = self.client.post('/api/auth/register', json={
            'name': 'Charlie',
            'username': 'charlie',
            'email': 'charlie@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        token_c = res_c.get_json()['token']
        user_c_id = res_c.get_json()['user']['id']

        # 4. Alice uploads a PRIVATE memory
        img_bytes = create_dummy_image_bytes()
        upload_res = self.client.post(
            '/api/memories',
            headers={'Authorization': f'Bearer {token_a}'},
            data={
                'file': (img_bytes, 'secret.jpg'),
                'media_type': 'photo',
                'memory_date': '2026-05-01',
                'title': 'Alice Private Secret',
                'privacy': 'private'
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(upload_res.status_code, 201)
        mem_data = upload_res.get_json()['memory']
        storage_key = mem_data['storage_key']
        memory_id = mem_data['id']

        # 5. Alice accesses her own media -> 200 OK
        res_owner = self.client.get(
            f'/api/media/{storage_key}',
            headers={'Authorization': f'Bearer {token_a}'}
        )
        self.assertEqual(res_owner.status_code, 200)

        # 6. Bob tries to access Alice's private media -> MUST return 403 Forbidden!
        res_unauth = self.client.get(
            f'/api/media/{storage_key}',
            headers={'Authorization': f'Bearer {token_b}'}
        )
        self.assertEqual(res_unauth.status_code, 403)

        # 7. Alice and Bob connect
        req_res = self.client.post(
            '/api/connections/request',
            headers={'Authorization': f'Bearer {token_a}'},
            json={'user_id': user_b_id}
        )
        conn_id = self.client.get('/api/connections', headers={'Authorization': f'Bearer {token_b}'}).get_json()['received'][0]['connection_id']
        self.client.post(f'/api/connections/{conn_id}/accept', headers={'Authorization': f'Bearer {token_b}'})

        # 8. Bob tries to access Alice's PRIVATE media AFTER connecting -> MUST STILL return 403!
        res_still_forbidden = self.client.get(
            f'/api/media/{storage_key}',
            headers={'Authorization': f'Bearer {token_b}'}
        )
        self.assertEqual(res_still_forbidden.status_code, 403)

        # 9. Alice changes privacy to 'connections'
        self.client.put(
            f'/api/memories/{memory_id}',
            headers={'Authorization': f'Bearer {token_a}'},
            json={'privacy': 'connections'}
        )

        # 10. Bob can now access -> 200 OK!
        res_bob_allowed = self.client.get(
            f'/api/media/{storage_key}',
            headers={'Authorization': f'Bearer {token_b}'}
        )
        self.assertEqual(res_bob_allowed.status_code, 200)

        # 11. Charlie (not connected) tries to access -> 403 Forbidden!
        res_charlie_denied = self.client.get(
            f'/api/media/{storage_key}',
            headers={'Authorization': f'Bearer {token_c}'}
        )
        self.assertEqual(res_charlie_denied.status_code, 403)

        # 12. Connect Charlie as well
        self.client.post(
            '/api/connections/request',
            headers={'Authorization': f'Bearer {token_c}'},
            json={'user_id': user_a_id}
        )
        c_conn_id = self.client.get('/api/connections', headers={'Authorization': f'Bearer {token_a}'}).get_json()['received'][0]['connection_id']
        self.client.post(f'/api/connections/{c_conn_id}/accept', headers={'Authorization': f'Bearer {token_a}'})

        # 13. Alice restricts memory to 'selected' people: ONLY Bob
        self.client.put(
            f'/api/memories/{memory_id}',
            headers={'Authorization': f'Bearer {token_a}'},
            json={'privacy': 'selected', 'selected_users': [user_b_id]}
        )

        # Bob has access -> 200
        self.assertEqual(self.client.get(f'/api/media/{storage_key}', headers={'Authorization': f'Bearer {token_b}'}).status_code, 200)

        # Charlie (connected, but not selected) MUST get 403!
        self.assertEqual(self.client.get(f'/api/media/{storage_key}', headers={'Authorization': f'Bearer {token_c}'}).status_code, 403)

        # 14. Alice removes connection with Bob
        alice_conns = self.client.get('/api/connections', headers={'Authorization': f'Bearer {token_a}'}).get_json()['accepted']
        bob_conn_id = next(c['connection_id'] for c in alice_conns if c['user']['id'] == user_b_id)
        self.client.delete(f'/api/connections/{bob_conn_id}/remove', headers={'Authorization': f'Bearer {token_a}'})

        # Bob immediately loses access -> 403 Forbidden!
        res_bob_revoked = self.client.get(
            f'/api/media/{storage_key}',
            headers={'Authorization': f'Bearer {token_b}'}
        )
        self.assertEqual(res_bob_revoked.status_code, 403)

if __name__ == '__main__':
    unittest.main()
