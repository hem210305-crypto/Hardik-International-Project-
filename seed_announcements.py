import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Announcement

def seed_announcements():
    print("Clearing existing announcements...")
    Announcement.objects.all().delete()

    print("Seeding new high-fidelity announcements from Figma mockup...")

    announcements_data = [
        {
            "title": "New Product: Variable Angle Olecranon Plate Now Available",
            "content": "An anatomically contoured, low-profile locking plate with variable-angle screw options, designed for stable fixation of simple to comminuted olecranon fractures and early elbow mobilization.",
            "published_at": date(2026, 1, 30),
            "is_featured": True,
            "tag_label": "Product Launch",
            "severity_label": "",
            "icon_type": "megaphone",
            "image_url": "/static/img/olecranon_plate.png",
            "status": Announcement.PublishStatus.PUBLISHED
        },
        {
            "title": "Upcoming Price Revision - February 2026",
            "content": "Please note that prices for select Arthroscopy Implants will be revised starting February 15, 2026. Updated price list will be sent via email. Contact support for details.",
            "published_at": date(2026, 1, 29),
            "is_featured": False,
            "tag_label": "Notice",
            "severity_label": "High",
            "icon_type": "megaphone",
            "image_url": "",
            "status": Announcement.PublishStatus.PUBLISHED
        },
        {
            "title": "Distributor Annual Meet - March 2026",
            "content": "Join us for our Annual Distributor Conference on March 15-16, 2026 at Hotel Grand Plaza, Mumbai. Registration now open. Network with industry leaders and learn about our expansion plans.",
            "published_at": date(2026, 1, 27),
            "is_featured": False,
            "tag_label": "Event",
            "severity_label": "Medium",
            "icon_type": "calendar",
            "image_url": "",
            "status": Announcement.PublishStatus.PUBLISHED
        },
        {
            "title": "System Maintenance Scheduled",
            "content": "The portal will undergo scheduled maintenance on February 5, 2026 from 2:00 AM to 6:00 AM IST. During this time, ordering and payment functions will be temporarily unavailable.",
            "published_at": date(2026, 1, 25),
            "is_featured": False,
            "tag_label": "Alert",
            "severity_label": "Medium",
            "icon_type": "bell",
            "image_url": "",
            "status": Announcement.PublishStatus.PUBLISHED
        },
        {
            "title": "Expo Announcement",
            "content": "We are excited to participate in the Pune Expo on 20th, 21st & 22nd February—visit us to explore our latest products and upcoming innovations.",
            "published_at": date(2026, 1, 22),
            "is_featured": False,
            "tag_label": "Product Launch",
            "severity_label": "High",
            "icon_type": "megaphone",
            "image_url": "",
            "status": Announcement.PublishStatus.PUBLISHED
        },
        {
            "title": "Payment Terms Update",
            "content": "Revised payment terms for all distributors: 30-day credit period with early payment discount of 2%. Late payment charges apply after due date. Effective from February 1, 2026.",
            "published_at": date(2026, 1, 20),
            "is_featured": False,
            "tag_label": "Notice",
            "severity_label": "High",
            "icon_type": "megaphone",
            "image_url": "",
            "status": Announcement.PublishStatus.PUBLISHED
        }
    ]

    for ann in announcements_data:
        a = Announcement.objects.create(
            title=ann["title"],
            content=ann["content"],
            published_at=ann["published_at"],
            is_featured=ann["is_featured"],
            tag_label=ann["tag_label"],
            severity_label=ann["severity_label"],
            icon_type=ann["icon_type"],
            image_url=ann["image_url"],
            status=ann["status"]
        )
        print(f"Created Announcement: {a.title} (Featured: {a.is_featured})")

    print("Success! High-fidelity announcements seeded successfully.")

if __name__ == "__main__":
    seed_announcements()
