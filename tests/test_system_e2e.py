import unittest
from pathlib import Path
from backend.app import create_app
from backend.config import Config
from backend.seed import seed

BASE_DIR = Path(__file__).resolve().parent.parent

class TestEndToEndApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_db_path = Config.DATABASE_PATH
        cls.test_db_path = BASE_DIR / 'storage' / 'test_e2e_db.sqlite'
        Config.DATABASE_PATH = cls.test_db_path
        seed()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        Config.DATABASE_PATH = cls.orig_db_path
        if cls.test_db_path.is_file():
            try:
                cls.test_db_path.unlink()
            except Exception:
                pass

    def test_complete_flow(self):
        # 1. Login as Narayanan
        resp = self.client.post('/api/auth/login', json={
            'login': 'narayanan',
            'password': 'LoveStory2026!'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        token_n = data['token']
        headers_n = {'Authorization': f'Bearer {token_n}'}

        # 2. Check stats
        stats_resp = self.client.get('/api/dashboard/stats', headers=headers_n)
        self.assertEqual(stats_resp.status_code, 200)
        stats = stats_resp.get_json()
        self.assertEqual(stats['photo_count'], 4)
        self.assertEqual(stats['video_count'], 1)
        self.assertEqual(stats['connection_count'], 1)

        # 3. Get memories
        mem_resp = self.client.get('/api/memories', headers=headers_n)
        self.assertEqual(mem_resp.status_code, 200)
        memories = mem_resp.get_json()['memories']
        self.assertEqual(len(memories), 5)

        # 4. Get thumbnail of first memory
        th_key = memories[0]['thumbnail_key']
        th_resp = self.client.get(f'/api/media/thumbnail/{th_key}?token={token_n}')
        self.assertEqual(th_resp.status_code, 200)

        # 5. Check connections
        conn_resp = self.client.get('/api/connections', headers=headers_n)
        self.assertEqual(conn_resp.status_code, 200)
        conns = conn_resp.get_json()
        self.assertEqual(len(conns['accepted']), 1)
        self.assertEqual(len(conns['received']), 1)

        # 6. Login as Anu Maria
        resp_a = self.client.post('/api/auth/login', json={
            'login': 'anumaria',
            'password': 'LoveStory2026!'
        })
        self.assertEqual(resp_a.status_code, 200)
        token_a = resp_a.get_json()['token']
        headers_a = {'Authorization': f'Bearer {token_a}'}

        # 7. Check Shared With Me for Anu Maria
        shared_resp = self.client.get('/api/shared', headers=headers_a)
        self.assertEqual(shared_resp.status_code, 200)
        shared_mems = shared_resp.get_json()['memories']
        self.assertEqual(len(shared_mems), 3)

        # 8. Check Anu's own memories
        anu_mems_resp = self.client.get('/api/memories', headers=headers_a)
        self.assertEqual(anu_mems_resp.status_code, 200)
        anu_mems = anu_mems_resp.get_json()['memories']
        self.assertEqual(len(anu_mems), 3)

if __name__ == '__main__':
    unittest.main()
