from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Product, ProductCategory, Brand, Color  # Models using SQLAlchemy ORM
import os
import json
from sqlalchemy.sql import text  # Import the text function for SQL expressions
import unicodedata
from sqlalchemy.exc import SQLAlchemyError  # Import SQLAlchemyError


# from dotenv import load_dotenv

# load_dotenv()



app = Flask(__name__)

# Now access your environment variables
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_INSTANCE_CONNECTION_NAME = os.getenv('POSTGRES_INSTANCE_CONNECTION_NAME')


if None in [POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_INSTANCE_CONNECTION_NAME]:
    raise ValueError(f"""
                     Database configuration is incomplete. Please check environment variables: 
                     POSTGRES_USER: {POSTGRES_USER}
                     POSTGRES_PASSWORD: {POSTGRES_PASSWORD}
                     POSTGRES_DB: {POSTGRES_DB}
                     POSTGRES_PORT: {POSTGRES_PORT}
                     POSTGRES_INSTANCE_CONNECTION_NAME: {POSTGRES_INSTANCE_CONNECTION_NAME}
                     """, )

# Build the database URI
DATABASE_URI = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@/{POSTGRES_DB}?host=/cloudsql/{POSTGRES_INSTANCE_CONNECTION_NAME}"


engine = create_engine(DATABASE_URI, echo=True, future=True)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def normalize_gender(gender):
    if not gender:
        return None
    # Normalize and remove diacritics
    gender = unicodedata.normalize('NFD', gender)
    gender = ''.join(char for char in gender if unicodedata.category(char) != 'Mn').lower()

    # Map of genders to normalize various inputs to a standard output
    gender_map = {
        'mens': 'male',
        'male': 'male',
        'man': 'male',
        'men': 'male',
        'womens': 'female',
        'female': 'female',
        'woman': 'female',
        'women': 'female',
        'boy': 'kids',
        'boys': 'kids',
        'girl': 'kids',
        'girls': 'kids',
        'baby': 'baby',
        'unisex': 'unisex',
    }

    return gender_map.get(gender, 'none')  # Return 'none' if gender is not found in the map


def check_new_products(product_batch, session):
    """
    Identifies new and existing products from the batch.
    """
    try:
        urls = [product['productUrl'] for product in product_batch]
        # Retrieve existing products based on URLs.
        existing_products = session.query(Product).filter(Product.url.in_(urls)).all()
        existing_product_map = {product.url: product for product in existing_products}

        # Separate products into those to insert and those to update.
        products_to_insert = []
        products_to_update = []

        for product in product_batch:
            if product['productUrl'] in existing_product_map:
                # For existing products, include the database ID and original ID from the batch.
                updated_product = product.copy()
                updated_product['id'] = existing_product_map[product['productUrl']].id
                updated_product['originalProductId'] = product['productId']
                updated_product['type'] = 'update'  # Flag to indicate this is an existing product to update
                products_to_update.append(updated_product)
            else:
                # For new products, just append them to the insert list.
                
                insert_product = product.copy()
                insert_product['originalProductId'] = product['productId']
                insert_product['type'] = 'insert' # Flag to indicate this is a new product to insert
                products_to_insert.append(insert_product)

        return {'productsToInsert': products_to_insert, 'productsToUpdate': products_to_update}
    except Exception as e:
        print(f"Database error occurred: {str(e)}")
        raise e

def bulk_insert_categories(categories, session: Session):
    unique_category_names = {category.lower() for category in categories}
    try:
        existing_categories = session.query(ProductCategory).filter(ProductCategory.name.in_(list(unique_category_names))).all()
        existing_category_names = {category.name.lower() for category in existing_categories}

        new_categories = [{'name': name} for name in unique_category_names if name not in existing_category_names]
        if new_categories:
            session.bulk_insert_mappings(ProductCategory, new_categories)
            session.commit()
            print("Bulk insert new categories completed")
        else:
            print("No new categories to insert")
    except SQLAlchemyError as e:
        session.rollback()
        print("Failed to bulk insert new categories:", str(e))
        raise e
    return unique_category_names

def bulk_insert_brands(brands, session):
    unique_brand_names = {brand.lower() for brand in brands}
    # brand_ids = {}
    
    try:
        # Fetch existing brands from the database
        existing_brands = session.query(Brand).filter(Brand.name.in_(list(unique_brand_names))).all()
        existing_brand_dict = {brand.name.lower(): brand.id for brand in existing_brands}
        # brand_ids.update(existing_brand_dict)
        
        # Determine new brands that need to be inserted
        new_brands = [Brand(name=name) for name in unique_brand_names if name not in existing_brand_dict]
        
        if new_brands:
            session.add_all(new_brands)
            session.commit()  # Commit to ensure IDs are generated
            # Update dictionary with new brands and their generated IDs
            for brand in new_brands:
                existing_brand_dict[brand.name] = brand.id
            print("Bulk insert new brands completed")
        else:
            print("No new brands to insert")
    except SQLAlchemyError as e:
        session.rollback()
        print("Failed to bulk insert new brands:", str(e))
        raise e
    
    return existing_brand_dict

def bulk_insert_colors(colors, session: Session):
    unique_color_names = {color.lower() for color in colors }  # Normalize and deduplicate color names
    try:
        existing_colors = session.query(Color).filter(Color.name.in_(list(unique_color_names))).all()
        existing_color_names = {color.name.lower() for color in existing_colors}

        new_colors = [{'name': name} for name in unique_color_names if name not in existing_color_names]
        if new_colors:
            session.bulk_insert_mappings(Color, new_colors)
            session.commit()
            print("Bulk insert new colors completed")
        else:
            print("No new colors to insert")
    except SQLAlchemyError as e:
        session.rollback()
        print("Failed to bulk insert new colors:", str(e))
        raise e
    return unique_color_names

def get_gender_ids(gender_set):
    # Hardcoded gender IDs based on your specific requirements
    gender_id_map = {
        'female': 1,
        'male': 3,
        'none': 4,
        'unisex': 7,
        'baby': 8,
        'kids': 9
    }
    return {gender: gender_id_map.get(gender, 4) for gender in gender_set}  # Default to 'none' ID if not found

def bulk_insert_products(products, session):
    """
    Inserts a list of product dictionaries into the database using SQLAlchemy.
    
    Args:
    products (list of dict): List of product data to insert.
    session (Session): SQLAlchemy session bound to a transaction.
    
    Returns:
    list: List of inserted Product objects.
    """
    try:
        # Create Product instances from the product dictionaries
        product_objects = [
            Product(
                title=product['title'],
                description=product['description'],
                url=product['url'],
                brandId=product['brandId'],
                genderId=product['genderId'],
                retailerId=product['retailerId'],
                originalProductId=product['originalProductId'],
            )
            for product in products
        ]
        # Bulk insert using SQLAlchemy
        session.add_all(product_objects)  # Add all product objects to the session
        session.commit()  # Commit the transaction to insert and retrieve IDs
        return product_objects
    except Exception as e:
        print(f"Failed to bulk insert products: {str(e)}")
        session.rollback()  # Rollback the transaction in case of error
        raise e


def update_products(products_to_update, brand_ids, gender_ids, session):
    """
    Update existing products in the database.
    
    Args:
    products_to_update (list of dict): Products data to update.
    brand_ids (dict): Dictionary mapping brand names to their IDs.
    gender_ids (dict): Dictionary mapping normalized gender names to their IDs.
    session (Session): SQLAlchemy session object bound to a transaction.
    """
    try:

        # Iterate over each product and update its attributes

        for product in products_to_update:
            # Fetch the product from the database using the provided 'id'
            prod = session.query(Product).filter_by(id=product['id']).one()

            # Update product attributes from the provided data
            prod.title = product['productName']
            prod.description = product['description']
            prod.url = product['productUrl']
            prod.brandId = brand_ids.get(product['brandName'].lower())
            prod.genderId = gender_ids.get(normalize_gender(product['gender']))
            prod.toDelete = False

            # Optionally update other fields if needed
            if 'category' in product:
                prod.category = product['category']
            if 'subCategory' in product:
                prod.subCategory = product['subCategory']


        # Commit the session to save changes
        session.commit()
        print("All products updated successfully.")



    except Exception as e:
        # Rollback in case of any error
        session.rollback()
        print(f"Failed to update products: {str(e)}")
        raise e





def process_batch(product_batch, session):

    result = check_new_products(product_batch, session)
    products_to_insert = result['productsToInsert']
    products_to_update = result['productsToUpdate']

    all_products = products_to_insert + products_to_update
    category_set = set()
    brand_set = set()
    color_set = set()
    gender_set = set()

    for product in all_products:
        if 'category' in product:
            category_set.add(product['category'])
        if 'subCategory' in product:
            category_set.add(product['subCategory'])
        if 'brandName' in product:
            brand_set.add(product['brandName'].lower())
        for color_dict in product.get('colors', []):
            for color in color_dict.keys():
                color_set.add(color)
        gender_set.add(normalize_gender(product.get('gender', 'none')))

    try:
        with Session() as s:
            # Insert new categories, brands, colors, and genders
            bulk_insert_categories(category_set, s)
            brand_ids = bulk_insert_brands(brand_set, s)
            bulk_insert_colors(color_set, s)

            gender_ids = get_gender_ids(gender_set)


            if products_to_insert:
                # Insert new products

                # Prepare the product data for insertion
                mapped_products = [{
                    'title': product['productName'],
                    'description': product['description'],
                    'url': product['productUrl'],
                    'brandId': brand_ids.get(product['brandName'].lower()),
                    'genderId': gender_ids.get(normalize_gender(product['gender']), None),
                    'retailerId': product['retailerId'],
                    'originalProductId': product['productId'],
                    'toDelete': False,
                } for product in products_to_insert]


                # Bulk insert the products  
                inserted_products = bulk_insert_products(mapped_products, s)
                
                for product, data in zip(inserted_products, products_to_insert):
                    data['id'] = product.id 
                    
            if products_to_update:
                update_products(products_to_update, brand_ids, gender_ids, s)


            

            s.commit() 
        return products_to_insert + products_to_update

    except Exception as e:
        print(f"Failed to process data: {str(e)}")
        session.rollback()
        raise e
    



@app.route('/', methods=['POST'])
def process_data():
    # Attempt to read lines from the request's body
    try:
        #lines = request.data.decode('utf-8').splitlines()
        products = request.json
        if not products:
            print("No data provided")
            return jsonify({"error": "No data provided"}), 400

        # The remaining lines are product data
        #products = [json.loads(line) for line in lines]

        # Now you can proceed to process these products
        session = Session()
        try:
            results = process_batch(products, session)
            session.commit()
            print("Data processed successfully")
            return jsonify({"results": results}), 200
        except Exception as e:
            session.rollback()
            
            print(f"Failed to process data: {str(e)}")
            return jsonify({"error": f"Failed to process data: {str(e)}"}), 500
        finally:
            session.close()
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {str(e)}")
        return jsonify({"error": f"Invalid JSON format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
