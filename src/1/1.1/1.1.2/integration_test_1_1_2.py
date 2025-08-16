import unittest
import datetime

# --- Start: Hypothetical Implementations ---
# These classes represent the core data models. In a real application,
# these would be imported from other files (e.g., from models.user import User).
# They are defined here to create a self-contained, runnable test file.

class User:
    """Represents a user of the system."""
    def __init__(self, user_id, username, email):
        self.user_id = user_id
        self.username = username
        self.email = email

class Product:
    """Represents a product available for purchase."""
    def __init__(self, product_id, name, price, stock):
        if price < 0 or stock < 0:
            raise ValueError("Price and stock cannot be negative.")
        self.product_id = product_id
        self.name = name
        self.price = float(price)
        self.stock = int(stock)

    def update_stock(self, quantity_change):
        """Reduces stock by a given quantity. A negative change would increase stock."""
        if self.stock - quantity_change < 0:
            raise ValueError(f"Not enough stock for {self.name}.")
        self.stock -= quantity_change

class OrderItem:
    """Represents a single line item within an Order."""
    def __init__(self, product, quantity):
        if not isinstance(product, Product):
            raise TypeError("item must be a Product instance.")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        self.product = product
        self.quantity = quantity

    @property
    def item_total(self):
        """Calculates the total price for this line item."""
        return self.product.price * self.quantity

class Order:
    """Represents a customer's order, linking a User to multiple Products."""
    def __init__(self, user, order_id):
        if not isinstance(user, User):
            raise TypeError("user must be a User instance.")
        self.order_id = order_id
        self.user = user
        self.order_date = datetime.datetime.now()
        self.items = []
        self._is_placed = False

    def add_item(self, product, quantity):
        """
        Adds a product to the order, creating an OrderItem.
        This integration point checks the Product's stock before adding.
        """
        if self._is_placed:
            raise PermissionError("Cannot add items to an already placed order.")
        if quantity > product.stock:
            raise ValueError(f"Not enough stock for {product.name}. Requested: {quantity}, Available: {product.stock}")

        order_item = OrderItem(product, quantity)
        self.items.append(order_item)

    def calculate_total(self):
        """
        Calculates the total price by integrating over all OrderItems.
        """
        return sum(item.item_total for item in self.items)

    def place_order(self):
        """
        Finalizes the order. This integration point updates the stock
        on all associated Product models.
        """
        if not self.items:
            raise ValueError("Cannot place an empty order.")
        if self._is_placed:
            raise PermissionError("Order has already been placed.")

        # A final check of stock for all items before committing
        for item in self.items:
            if item.quantity > item.product.stock:
                raise ValueError(f"Stock for {item.product.name} changed. Not enough to fulfill order.")

        # If all checks pass, update stock for all items
        for item in self.items:
            item.product.update_stock(item.quantity)

        self._is_placed = True
        return True

# --- End: Hypothetical Implementations ---


class TestCoreDataModelIntegration(unittest.TestCase):

    def setUp(self):
        """Set up common objects for all tests to ensure a clean state."""
        self.user = User(user_id=1, username="testuser", email="test@example.com")
        self.product_laptop = Product(product_id=101, name="Laptop", price=1200.50, stock=10)
        self.product_mouse = Product(product_id=102, name="Mouse", price=25.00, stock=50)
        self.product_keyboard = Product(product_id=103, name="Keyboard", price=75.75, stock=0)

    def test_order_creation_and_total_price_calculation(self):
        """
        Tests the primary integration: creating an Order for a User, adding
        OrderItems with Products, and calculating the total price.
        """
        # 1. Create an Order for a specific User
        order = Order(user=self.user, order_id=5001)
        self.assertIs(order.user, self.user)
        self.assertEqual(len(order.items), 0)
        self.assertEqual(order.calculate_total(), 0)

        # 2. Add items to the order, linking Products
        order.add_item(self.product_laptop, 2)  # 2 * 1200.50 = 2401.00
        order.add_item(self.product_mouse, 5)   # 5 * 25.00   =  125.00
        
        self.assertEqual(len(order.items), 2)
        self.assertIs(order.items[0].product, self.product_laptop)
        self.assertEqual(order.items[0].quantity, 2)
        self.assertIs(order.items[1].product, self.product_mouse)
        self.assertEqual(order.items[1].quantity, 5)

        # 3. Test the integrated calculation
        expected_total = 2401.00 + 125.00
        self.assertAlmostEqual(order.calculate_total(), expected_total)

    def test_placing_order_integrates_with_product_stock(self):
        """
        Tests that the 'place_order' action correctly interacts with and
        updates the stock attribute of the related Product models.
        """
        initial_stock_laptop = self.product_laptop.stock
        initial_stock_mouse = self.product_mouse.stock
        
        order = Order(user=self.user, order_id=5002)
        order.add_item(self.product_laptop, 3)
        order.add_item(self.product_mouse, 10)
        
        # Verify stock is unchanged before placing the order
        self.assertEqual(self.product_laptop.stock, initial_stock_laptop)
        self.assertEqual(self.product_mouse.stock, initial_stock_mouse)

        # Action: Place the order, triggering the stock update
        is_placed = order.place_order()
        self.assertTrue(is_placed)

        # Assert that the stock for each Product has been correctly decremented
        self.assertEqual(self.product_laptop.stock, initial_stock_laptop - 3)
        self.assertEqual(self.product_mouse.stock, initial_stock_mouse - 10)

    def test_adding_item_with_insufficient_stock_raises_error(self):
        """
        Tests the business rule that an item cannot be added to an order
        if the product's stock is too low. This tests the Order-Product interaction.
        """
        order = Order(user=self.user, order_id=5003)
        
        # Test with a product that has some stock, but not enough
        with self.assertRaisesRegex(ValueError, "Not enough stock for Laptop"):
            order.add_item(self.product_laptop, self.product_laptop.stock + 1)
            
        # Test with a product that is completely out of stock
        with self.assertRaisesRegex(ValueError, "Not enough stock for Keyboard"):
            order.add_item(self.product_keyboard, 1)

    def test_placing_order_fails_if_stock_changes_after_adding(self):
        """
        Tests the race condition scenario where stock is depleted between adding
        an item to the order and finalizing the purchase.
        """
        order = Order(user=self.user, order_id=5004)
        order.add_item(self.product_laptop, 5)
        
        # Simulate another process depleting the stock
        self.product_laptop.update_stock(8) # Stock is now 10 - 8 = 2
        
        # The order for 5 laptops should now fail upon placement
        with self.assertRaisesRegex(ValueError, "Stock for Laptop changed. Not enough to fulfill order."):
            order.place_order()
            
        # Verify that the failed order did not change the stock
        self.assertEqual(self.product_laptop.stock, 2)

    def test_order_modification_after_placement_is_disallowed(self):
        """
        Tests that once an Order is placed, its state is locked and
        no more OrderItems can be added.
        """
        order = Order(user=self.user, order_id=5005)
        order.add_item(self.product_mouse, 1)
        order.place_order()

        # Attempt to add another item
        with self.assertRaises(PermissionError):
            order.add_item(self.product_laptop, 1)

        # Attempt to place the order again
        with self.assertRaises(PermissionError):
            order.place_order()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)