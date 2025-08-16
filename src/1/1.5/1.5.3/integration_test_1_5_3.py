import unittest
import copy
from fastapi.testclient import TestClient

# Assuming the provided implementation is in a file named `main.py`
# This is necessary to test the actual running application instance and its state.
try:
    from main import app, Item, db as app_db
    import main as main_module
except ImportError:
    # Create a dummy module and app for static analysis if main.py is not present
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import List, Optional
    class Item(BaseModel): id: int; name: str; description: Optional[str] = None; price: float
    app = FastAPI()
    app_db = []
    class main_module: next_id = 1


class TestVisualizationApiIntegration(unittest.TestCase):
    """
    Integration tests for the FastAPI Visualization API.
    These tests cover the CRUD operations and interaction between the API endpoints
    and the in-memory database.
    """

    @classmethod
    def setUpClass(cls):
        """Set up the test client once for the entire test class."""
        cls.client = TestClient(app)
        # Define the pristine, initial state of the database for resetting.
        cls.initial_db_state = [
            Item(id=1, name="Laptop", description="A powerful computing device", price=1200.50),
            Item(id=2, name="Keyboard", description="A mechanical keyboard", price=75.99),
            Item(id=3, name="Mouse", description="An ergonomic wireless mouse", price=25.00),
        ]
        cls.initial_next_id = 4

    def setUp(self):
        """
        Reset the in-memory database and ID counter before each test.
        This ensures that tests are isolated and run in a predictable environment.
        """
        app_db.clear()
        app_db.extend(copy.deepcopy(self.initial_db_state))
        main_module.next_id = self.initial_next_id

    def test_read_root(self):
        """Test the root endpoint to ensure the API is running."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the Simple Items API!"})

    def test_read_all_items(self):
        """Test retrieving all items, verifying the initial data set."""
        response = self.client.get("/items/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["name"], "Laptop")
        self.assertEqual(data[1]["id"], 2)
        self.assertEqual(data[2]["price"], 25.00)

    def test_read_single_item_success(self):
        """Test retrieving a single, existing item by its ID."""
        response = self.client.get("/items/2")
        self.assertEqual(response.status_code, 200)
        item = response.json()
        self.assertEqual(item["id"], 2)
        self.assertEqual(item["name"], "Keyboard")
        self.assertEqual(item["price"], 75.99)

    def test_read_single_item_not_found(self):
        """Test retrieving a non-existent item, expecting a 404 error."""
        response = self.client.get("/items/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Item not found"})

    def test_create_item(self):
        """Test creating a new item and verifying its addition to the database."""
        new_item_data = {"name": "Monitor", "description": "A 27-inch 4K display", "price": 350.0}
        response = self.client.post("/items/", json=new_item_data)

        # Verify the creation response
        self.assertEqual(response.status_code, 201)
        created_item = response.json()
        self.assertEqual(created_item["id"], self.initial_next_id) # Should be 4
        self.assertEqual(created_item["name"], new_item_data["name"])
        self.assertEqual(created_item["price"], new_item_data["price"])

        # Verify the item was actually added by fetching it
        get_response = self.client.get(f"/items/{created_item['id']}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), created_item)

        # Verify the total count of items has increased
        list_response = self.client.get("/items/")
        self.assertEqual(len(list_response.json()), 4)

    def test_update_item_success(self):
        """Test updating an existing item and verifying the changes."""
        item_id_to_update = 1
        update_data = {"name": "Gaming Laptop", "description": "An upgraded, powerful device", "price": 1850.75}

        response = self.client.put(f"/items/{item_id_to_update}", json=update_data)

        # Verify the update response
        self.assertEqual(response.status_code, 200)
        updated_item = response.json()
        self.assertEqual(updated_item["id"], item_id_to_update)
        self.assertEqual(updated_item["name"], update_data["name"])
        self.assertEqual(updated_item["price"], update_data["price"])

        # Verify the change persisted by fetching the item again
        get_response = self.client.get(f"/items/{item_id_to_update}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), updated_item)

    def test_update_item_not_found(self):
        """Test updating a non-existent item, expecting a 404 error."""
        update_data = {"name": "Ghost Item", "price": 99.99}
        response = self.client.put("/items/999", json=update_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Item not found"})

    def test_delete_item_success(self):
        """Test deleting an existing item and verifying its removal."""
        item_id_to_delete = 3
        
        # Verify the item exists before deletion
        self.assertEqual(self.client.get(f"/items/{item_id_to_delete}").status_code, 200)

        # Perform the deletion
        delete_response = self.client.delete(f"/items/{item_id_to_delete}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json(), {"message": "Item deleted successfully"})

        # Verify the item is gone
        get_response = self.client.get(f"/items/{item_id_to_delete}")
        self.assertEqual(get_response.status_code, 404)

        # Verify the list size has decreased
        list_response = self.client.get("/items/")
        self.assertEqual(len(list_response.json()), 2)
        item_ids = [item['id'] for item in list_response.json()]
        self.assertNotIn(item_id_to_delete, item_ids)

    def test_delete_item_not_found(self):
        """Test deleting a non-existent item, expecting a 404 error."""
        response = self.client.delete("/items/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Item not found"})

    def test_full_crud_lifecycle(self):
        """
        Simulates a full user workflow: Create, Read, Update, and Delete an item.
        This test ensures all endpoints work together as expected.
        """
        # 1. CREATE a new item
        new_item_data = {"name": "Webcam", "description": "HD 1080p Webcam", "price": 89.99}
        create_response = self.client.post("/items/", json=new_item_data)
        self.assertEqual(create_response.status_code, 201)
        created_item = create_response.json()
        new_id = created_item["id"]
        self.assertEqual(new_id, 4)

        # 2. READ the newly created item
        read_response = self.client.get(f"/items/{new_id}")
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()["name"], "Webcam")

        # 3. UPDATE the item
        update_data = {"name": "Webcam Pro", "description": "4K Webcam with privacy shutter", "price": 129.99}
        update_response = self.client.put(f"/items/{new_id}", json=update_data)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["name"], "Webcam Pro")
        self.assertEqual(update_response.json()["price"], 129.99)

        # 4. VERIFY the update persisted
        verify_response = self.client.get(f"/items/{new_id}")
        self.assertEqual(verify_response.json()["description"], "4K Webcam with privacy shutter")

        # 5. DELETE the item
        delete_response = self.client.delete(f"/items/{new_id}")
        self.assertEqual(delete_response.status_code, 200)

        # 6. VERIFY the deletion
        final_get_response = self.client.get(f"/items/{new_id}")
        self.assertEqual(final_get_response.status_code, 404)
        
        # 7. Check final state of the list (should be back to initial state)
        final_list_response = self.client.get("/items/")
        self.assertEqual(len(final_list_response.json()), 3)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)