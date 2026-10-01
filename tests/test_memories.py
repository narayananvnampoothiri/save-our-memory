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
from backend.storage import StorageService

def create_dummy_image():
    buf = io.BytesIO()
    img = Image.new('RGB', (100, 100), color=(100, 150, 200))
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf

class TestMemories(unittest.TestCase):
    def setUp(self):
        self.orig_db_path = Config.DATABASE_PATH
        self.test_db_path = BASE_DIR / 'storage' / 'test_memories_db.sqlite'
        Config.DATABASE_PATH = self.test_db_path
        self.app = create_app()
        self.client = self.app.test_client()

        # Register user
        res = self.client.post('/api/auth/register', json={
            'name': 'Memory Tester',
            'username': 'memtester',
            'email': 'mem@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        self.token = res.get_json()['token']

    def tearDown(self):
        Config.DATABASE_PATH = self.orig_db_path
        if self.test_db_path.is_file():
            try:
                self.test_db_path.unlink()
            except Exception:
                pass

    def test_memory_crud_filter_sort(self):
        # 1. Create Photo 1
        res1 = self.client.post(
            '/api/memories',
            headers={'Authorization': f'Bearer {self.token}'},
            data={
                'file': (create_dummy_image(), 'photo1.jpg'),
                'media_type': 'photo',
                'memory_date': '2026-02-14',
                'title': 'Valentine Day',
                'location': 'Bangalore',
                'description': 'Romantic sunrise trip',
                'privacy': 'private'
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(res1.status_code, 201)
        m1 = res1.get_json()['memory']

        # 2. Create Photo 2 (Different year and location)
        res2 = self.client.post(
            '/api/memories',
            headers={'Authorization': f'Bearer {self.token}'},
            data={
                'file': (create_dummy_image(), 'photo2.jpg'),
                'media_type': 'photo',
                'memory_date': '2025-11-20',
                'title': 'Autumn Walk',
                'location': 'Coorg',
                'description': 'Walking in coffee plantation',
                'privacy': 'private'
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(res2.status_code, 201)
        m2 = res2.get_json()['memory']

        # 3. Filter by Year 2026
        res_2026 = self.client.get(
            '/api/memories?year=2026',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        items_2026 = res_2026.get_json()['memories']
        self.assertEqual(len(items_2026), 1)
        self.assertEqual(items_2026[0]['id'], m1['id'])

        # 4. Filter by Location Coorg
        res_coorg = self.client.get(
            '/api/memories?location=Coorg',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        items_coorg = res_coorg.get_json()['memories']
        self.assertEqual(len(items_coorg), 1)
        self.assertEqual(items_coorg[0]['id'], m2['id'])

        # 5. Sorting: Memory Date ASC vs DESC
        res_asc = self.client.get(
            '/api/memories?sort=memory_asc',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        items_asc = res_asc.get_json()['memories']
        self.assertEqual(items_asc[0]['id'], m2['id'])  # 2025 comes before 2026

        res_desc = self.client.get(
            '/api/memories?sort=memory_desc',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        items_desc = res_desc.get_json()['memories']
        self.assertEqual(items_desc[0]['id'], m1['id'])  # 2026 comes first

        # 6. Update Memory
        update_res = self.client.put(
            f'/api/memories/{m1["id"]}',
            headers={'Authorization': f'Bearer {self.token}'},
            json={'title': 'Updated Valentine Day Title', 'location': 'Nandi Hills'}
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()['memory']['title'], 'Updated Valentine Day Title')

        # 7. Delete Memory & Verify Disk Cleanup
        storage_key = m1['storage_key']
        file_path_before = StorageService.find_media_path(storage_key)
        self.assertTrue(file_path_before is not None and file_path_before.is_file())

        del_res = self.client.delete(
            f'/api/memories/{m1["id"]}',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(del_res.status_code, 200)

        file_path_after = StorageService.find_media_path(storage_key)
        self.assertTrue(file_path_after is None)

if __name__ == '__main__':
    unittest.main()
