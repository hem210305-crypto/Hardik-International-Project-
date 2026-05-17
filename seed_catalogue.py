import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import ProductCategory, Product

def seed():
    print("Starting orthopedic categories database seeding...")
    
    # 1. Clear existing products & categories to keep it perfectly clean
    Product.objects.all().delete()
    ProductCategory.objects.all().delete()
    
    # 2. Define the 15 categories from Figma
    categories_data = [
        {"name": "Locking Small Fragment Plates", "slug": "locking-small-fragment-plates"},
        {"name": "Locking Larg Fragment Plates", "slug": "locking-larg-fragment-plates"},
        {"name": "Non-Locking Small Fragment Plates", "slug": "non-locking-small-fragment-plates"},
        {"name": "Non-Locking Larg Fragment Plates", "slug": "non-locking-larg-fragment-plates"},
        {"name": "Nailing System Implants", "slug": "nailing-system-implants"},
        {"name": "Foot & Ancle", "slug": "foot-ancle"},
        {"name": "DHS & DCS Implants", "slug": "dhs-dcs-implants"},
        {"name": "Femoral Neck System", "slug": "femoral-neck-system"},
        {"name": "Maxillofacial Non Locking Implants", "slug": "maxillofacial-non-locking-implants"},
        {"name": "Maxillofacial Locking Implants", "slug": "maxillofacial-locking-implants"},
        {"name": "Hip Prothesis", "slug": "hip-prothesis"},
        {"name": "Arthroscopy Implants", "slug": "arthroscopy-implants"},
        {"name": "Wire & Pin Implants", "slug": "wire-pin-implants"},
        {"name": "Cage Implants", "slug": "cage-implants"},
        {"name": "Dynamic Rail Fixation", "slug": "dynamic-rail-fixation"},
    ]
    
    for cat_info in categories_data:
        cat, created = ProductCategory.objects.get_or_create(
            name=cat_info["name"],
            defaults={"slug": cat_info["slug"]}
        )
        print(f"Created Category: {cat.name}")

    print("Success! Orthopedic categories database seeding completed successfully.")

if __name__ == "__main__":
    seed()
