import sqlite3
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os

def setup_database_and_vector_store():
    # Connect to SQLite database
    conn = sqlite3.connect('products.db')
    c = conn.cursor()

    # Drop tables if they exist
    c.execute('DROP TABLE IF EXISTS retailers')
    c.execute('DROP TABLE IF EXISTS products')
    c.execute('DROP TABLE IF EXISTS categories')

    # Create tables - Note: NO price field in products table
    c.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Products table without price (price moved to retailers level)
    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            brand TEXT,
            model TEXT,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    ''')
    
    # Retailers table now has price, location, and contact info
    c.execute('''
        CREATE TABLE retailers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            product_id INTEGER,
            price REAL NOT NULL,
            stock INTEGER,
            location TEXT,
            contact TEXT,
            rating REAL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    # Insert categories
    categories = [('Electronics',), ('Books',), ('Home Goods',)]
    c.executemany('INSERT INTO categories (name) VALUES (?)', categories)

    # Insert products without price
    products = [
        (1, 'Laptop', 'A high-performance laptop suitable for gaming and professional work.', 1, 'TechPro', 'TP-2024'),
        (2, 'Smartphone', 'A latest-gen smartphone with a great camera and 5G connectivity.', 1, 'PhoneTech', 'PT-X12'),
        (3, 'Science Fiction Novel', 'A captivating novel about space travel and aliens.', 2, 'AuthorPress', 'Space Odyssey'),
        (4, 'Cookbook', 'A book full of delicious and easy-to-make recipes.', 2, 'CulinaryBooks', 'Easy Cook'),
        (5, 'Coffee Maker', 'A drip coffee maker with a programmable timer.', 3, 'BrewMaster', 'BM-Pro'),
        (6, 'Desk Chair', 'An ergonomic desk chair for your home office.', 3, 'OfficeComfort', 'OC-Ergo'),
        (7, 'Tablet', 'A versatile tablet perfect for reading and media consumption.', 1, 'TabletCorp', 'TC-Tab10'),
        (8, 'Headphones', 'Wireless noise-canceling headphones with premium sound quality.', 1, 'AudioTech', 'AT-Wireless'),
    ]
    c.executemany('INSERT INTO products (id, name, description, category_id, brand, model) VALUES (?, ?, ?, ?, ?, ?)', products)

    # Insert multiple retailers for each product with different prices
    retailers = [
        # Laptop retailers
        ('TechStore', 1, 1199.99, 50, 'New York, NY', 'contact@techstore.com', 4.5),
        ('GadgetHub', 1, 1249.99, 30, 'Los Angeles, CA', 'support@gadgethub.com', 4.2),
        ('ElectroMart', 1, 1179.99, 25, 'Chicago, IL', 'info@electromart.com', 4.7),
        ('TechWorld', 1, 1299.99, 15, 'Miami, FL', 'sales@techworld.com', 4.0),
        
        # Smartphone retailers
        ('MobileWorld', 2, 799.99, 100, 'San Francisco, CA', 'hello@mobileworld.com', 4.6),
        ('PhoneCenter', 2, 819.99, 75, 'Seattle, WA', 'contact@phonecenter.com', 4.3),
        ('GadgetHub', 2, 789.99, 60, 'Los Angeles, CA', 'support@gadgethub.com', 4.2),
        ('TechStore', 2, 829.99, 40, 'New York, NY', 'contact@techstore.com', 4.5),
        ('WirelessZone', 2, 795.99, 80, 'Austin, TX', 'info@wirelesszone.com', 4.4),
        
        # Science Fiction Novel retailers
        ('BookNook', 3, 15.99, 200, 'Portland, OR', 'books@booknook.com', 4.8),
        ('ReadersCorner', 3, 14.99, 150, 'Boston, MA', 'contact@readerscorner.com', 4.6),
        ('NovelWorld', 3, 16.99, 120, 'Denver, CO', 'support@novelworld.com', 4.4),
        ('BookMart', 3, 15.49, 180, 'Phoenix, AZ', 'info@bookmart.com', 4.5),
        
        # Cookbook retailers
        ('CookingBooks', 4, 25.50, 90, 'Nashville, TN', 'chef@cookingbooks.com', 4.7),
        ('ReadersCorner', 4, 24.99, 110, 'Boston, MA', 'contact@readerscorner.com', 4.6),
        ('KitchenReads', 4, 26.99, 70, 'Atlanta, GA', 'books@kitchenreads.com', 4.3),
        ('BookNook', 4, 25.99, 85, 'Portland, OR', 'books@booknook.com', 4.8),
        
        # Coffee Maker retailers
        ('KitchenPlus', 5, 49.99, 80, 'Dallas, TX', 'kitchen@kitchenplus.com', 4.5),
        ('HomeAppliances', 5, 52.99, 60, 'Minneapolis, MN', 'sales@homeappliances.com', 4.2),
        ('BrewStore', 5, 47.99, 90, 'Sacramento, CA', 'brew@brewstore.com', 4.6),
        ('KitchenWorld', 5, 54.99, 45, 'Tampa, FL', 'info@kitchenworld.com', 4.1),
        
        # Desk Chair retailers
        ('HomeEssentials', 6, 149.99, 40, 'Charlotte, NC', 'home@homeessentials.com', 4.4),
        ('OfficeDepot', 6, 159.99, 35, 'Indianapolis, IN', 'office@officedepot.com', 4.2),
        ('FurnitureMax', 6, 139.99, 50, 'Kansas City, MO', 'furniture@furnituremax.com', 4.6),
        ('ComfortSeating', 6, 169.99, 25, 'Louisville, KY', 'comfort@comfortseating.com', 4.3),
        
        # Tablet retailers
        ('TechStore', 7, 329.99, 45, 'New York, NY', 'contact@techstore.com', 4.5),
        ('GadgetHub', 7, 319.99, 55, 'Los Angeles, CA', 'support@gadgethub.com', 4.2),
        ('TabletWorld', 7, 339.99, 30, 'Orlando, FL', 'tablets@tabletworld.com', 4.4),
        ('ElectroMart', 7, 324.99, 40, 'Chicago, IL', 'info@electromart.com', 4.7),
        
        # Headphones retailers
        ('AudioStore', 8, 199.99, 70, 'Las Vegas, NV', 'audio@audiostore.com', 4.8),
        ('SoundWorld', 8, 189.99, 85, 'Detroit, MI', 'sound@soundworld.com', 4.5),
        ('TechStore', 8, 209.99, 50, 'New York, NY', 'contact@techstore.com', 4.5),
        ('MusicGear', 8, 194.99, 60, 'Nashville, TN', 'gear@musicgear.com', 4.6),
        ('GadgetHub', 8, 199.99, 45, 'Los Angeles, CA', 'support@gadgethub.com', 4.2),
    ]
    
    c.executemany('INSERT INTO retailers (name, product_id, price, stock, location, contact, rating) VALUES (?, ?, ?, ?, ?, ?, ?)', retailers)

    conn.commit()

    # Create enhanced vector store with more detailed documents
    docs = []
    for product in products:
        product_id, name, description, category_id, brand, model = product
        
        # Get category name
        c.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
        category_name = c.fetchone()[0]
        
        # Get price range from retailers
        c.execute('SELECT MIN(price), MAX(price), AVG(price) FROM retailers WHERE product_id = ?', (product_id,))
        price_info = c.fetchone()
        min_price, max_price, avg_price = price_info
        
        # Create enhanced document content
        enhanced_content = f"""
        Product: {name}
        Brand: {brand}
        Model: {model}
        Category: {category_name}
        Description: {description}
        Price Range: ${min_price:.2f} - ${max_price:.2f}
        Average Price: ${avg_price:.2f}
        
        This {name} is a {category_name.lower()} product from {brand}. {description}
        Available at multiple retailers with prices ranging from ${min_price:.2f} to ${max_price:.2f}.
        """
        
        doc = Document(
            page_content=enhanced_content,
            metadata={
                "product_id": product_id,
                "name": name,
                "brand": brand,
                "model": model,
                "category": category_name,
                "min_price": min_price,
                "max_price": max_price,
                "avg_price": avg_price
            }
        )
        docs.append(doc)

    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create and persist ChromaDB vector store
    persist_directory = "./chroma_db"
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)

    print("Creating ChromaDB vector store...")
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print("ChromaDB vector store created and persisted.")

    conn.close()
    print("Database and ChromaDB vector store created successfully.")
    print(f"Created {len(products)} products with {len(retailers)} retailer entries.")

if __name__ == "__main__":
    setup_database_and_vector_store()