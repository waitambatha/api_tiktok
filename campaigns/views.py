import os
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token

# TikTok API Credentials
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
TIKTOK_ADVERTISER_ID = os.getenv("TIKTOK_ADVERTISER_ID")
BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"

HEADERS = {
    "Access-Token": TIKTOK_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

def fetch_campaigns():
    """
    Fetch campaigns from TikTok API.
    """
    url = f"{BASE_URL}/campaign/get/?advertiser_id={TIKTOK_ADVERTISER_ID}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            campaigns = data.get("data", {}).get("list", [])
            return campaigns if campaigns else []
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching campaigns: {e}")
        return []

def fetch_campaign_details(campaign_id):
    """
    Fetch detailed information for a specific campaign.
    """
    url = f"{BASE_URL}/campaign/get/?advertiser_id={TIKTOK_ADVERTISER_ID}&campaign_id={campaign_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            campaigns = data.get("data", {}).get("list", [])
            return campaigns[0] if campaigns else {}
        return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching campaign details: {e}")
        return {}

@api_view(['GET'])
@permission_classes([AllowAny])
def get_campaign_details(request, campaign_id):
    """
    API endpoint to fetch campaign details.
    """
    campaign = fetch_campaign_details(campaign_id)
    if campaign:
        return Response({"status": "success", "campaign": campaign}, status=status.HTTP_200_OK)
    return Response({"status": "error", "message": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Handles user login and returns available campaigns.
    """
    if request.method == 'GET':
        if request.user.is_authenticated:
            campaigns = fetch_campaigns()
            return Response({"status": "success", "campaigns": campaigns}, status=status.HTTP_200_OK)
        return Response({"status": "login_required", "csrf_token": get_token(request)}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"status": "error", "message": "Username and password are required"},
                            status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"status": "success", "message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"status": "error", "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
