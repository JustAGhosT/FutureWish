#!/usr/bin/env python3
"""
Script to populate sample features for testing the Feature Rating System
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from models import Feature, FeatureCategory, FeatureStatus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sample features data
SAMPLE_FEATURES = [
    {
        "title": "Dark Mode Theme",
        "description": "Add a dark mode theme option to reduce eye strain and provide a modern interface experience for users who prefer darker interfaces.",
        "category": FeatureCategory.UI_UX,
        "status": FeatureStatus.ACTIVE
    },
    {
        "title": "Real-time Notifications",
        "description": "Implement real-time push notifications for feature updates, rating responses, and system announcements to keep users engaged.",
        "category": FeatureCategory.INTEGRATION,
        "status": FeatureStatus.ACTIVE
    },
    {
        "title": "Mobile App Support",
        "description": "Develop a mobile application for iOS and Android to allow users to rate features and submit requests on the go.",
        "category": FeatureCategory.MOBILE,
        "status": FeatureStatus.UNDER_REVIEW
    },
    {
        "title": "Advanced Search Filters",
        "description": "Add advanced filtering options for features including category, status, rating score, and date ranges to help users find relevant content.",
        "category": FeatureCategory.UI_UX,
        "status": FeatureStatus.ACTIVE
    },
    {
        "title": "API Rate Limiting",
        "description": "Implement comprehensive rate limiting for all API endpoints to prevent abuse and ensure fair usage for all users.",
        "category": FeatureCategory.SECURITY,
        "status": FeatureStatus.ACTIVE
    },
    {
        "title": "Performance Optimization",
        "description": "Optimize database queries and implement caching to reduce page load times and improve overall system performance.",
        "category": FeatureCategory.PERFORMANCE,
        "status": FeatureStatus.ACTIVE
    },
    {
        "title": "Two-Factor Authentication",
        "description": "Add two-factor authentication support for enhanced account security, supporting SMS, email, and authenticator apps.",
        "category": FeatureCategory.SECURITY,
        "status": FeatureStatus.UNDER_REVIEW
    },
    {
        "title": "Bulk Feature Management",
        "description": "Allow administrators to manage multiple features at once, including bulk status updates and category changes.",
        "category": FeatureCategory.UI_UX,
        "status": FeatureStatus.ACTIVE
    },
    {
        "title": "REST API Documentation",
        "description": "Create comprehensive API documentation with examples and interactive testing capabilities for developers.",
        "category": FeatureCategory.API,
        "status": FeatureStatus.ACTIVE
    },
    {
        "title": "User Analytics Dashboard",
        "description": "Provide detailed analytics for user engagement, rating patterns, and feature popularity to help improve the platform.",
        "category": FeatureCategory.INTEGRATION,
        "status": FeatureStatus.ACTIVE
    }
]

async def populate_features():
    """Populate the database with sample features"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Check if features already exist
        existing_count = await db.features.count_documents({})
        if existing_count > 0:
            print(f"Found {existing_count} existing features. Skipping population.")
            return
        
        # Create admin user if not exists
        admin_user = await db.users.find_one({"email": "admin@engagemesh.com"})
        if not admin_user:
            admin_user = {
                "id": "admin-user-001",
                "email": "admin@engagemesh.com",
                "name": "EngageMesh Admin",
                "points": 0,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T00:00:00Z"
            }
            await db.users.insert_one(admin_user)
            print("Created admin user")
        
        # Insert sample features
        features_to_insert = []
        for feature_data in SAMPLE_FEATURES:
            feature = Feature(
                **feature_data,
                created_by=admin_user["id"]
            )
            features_to_insert.append(feature.dict())
        
        result = await db.features.insert_many(features_to_insert)
        print(f"Successfully inserted {len(result.inserted_ids)} features")
        
        # Print summary
        print("\n=== Sample Features Added ===")
        for i, feature in enumerate(SAMPLE_FEATURES, 1):
            print(f"{i}. {feature['title']} ({feature['category'].value})")
        
        print(f"\nTotal features: {len(SAMPLE_FEATURES)}")
        print("Features are ready for rating!")
        
    except Exception as e:
        print(f"Error populating features: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(populate_features())