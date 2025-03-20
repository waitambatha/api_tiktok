import os
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

# Import TikTok API variables and functions
from .views import BASE_URL, TIKTOK_ADVERTISER_ID, HEADERS

def fetch_campaigns(page=1, page_size=100):
    """
    Fetch campaigns from TikTok API with pagination support.
    """
    url = f"{BASE_URL}/campaign/get/?advertiser_id={TIKTOK_ADVERTISER_ID}&page={page}&page_size={page_size}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            campaigns = data.get("data", {}).get("list", [])
            for camp in campaigns:
                camp["campaign_name"] = camp.get("campaign_name", "Unnamed Campaign")
                camp["last_updated"] = camp.get("modify_time", "Unknown")
            return campaigns
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching campaigns: {e}")
        return []

def fetch_campaign_details(campaign_id):
    """
    Return details for a single campaign from the list of all campaigns.
    """
    all_campaigns = fetch_campaigns()
    for camp in all_campaigns:
        if str(camp.get("campaign_id", "")) == str(campaign_id):
            return camp
    return None

def fetch_adgroups(page=1, page_size=100):
    """
    Fetch ad groups from TikTok API with pagination support.
    """
    url = f"{BASE_URL}/adgroup/get/?advertiser_id={TIKTOK_ADVERTISER_ID}&page={page}&page_size={page_size}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            adgroups = data.get("data", {}).get("list", [])
            for adgroup in adgroups:
                adgroup["adgroup_name"] = adgroup.get("adgroup_name", "Unnamed Ad Group")
                adgroup["budget"] = adgroup.get("budget", 0)
                adgroup["schedule_start_time"] = adgroup.get("schedule_start_time", "N/A")
                adgroup["schedule_end_time"] = adgroup.get("schedule_end_time", "N/A")
            return adgroups
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching ad groups: {e}")
        return []

def fetch_adgroup_details(adgroup_id):
    """
    Return details for a single ad group.
    """
    all_adgroups = fetch_adgroups()
    for adgroup in all_adgroups:
        if str(adgroup.get("adgroup_id", "")) == str(adgroup_id):
            return adgroup
    return None

def adgroup_detail(request, adgroup_id):
    """
    Displays details for a specific ad group.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    adgroup = fetch_adgroup_details(adgroup_id)
    if not adgroup:
        return redirect('adgroup_listing')

    return render(request, 'adgroup_detail.html', {'adgroup': adgroup})

def adgroup_delete(request, adgroup_id):
    """
    Deletes an ad group via the TikTok API.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    if request.method == 'POST':
        url = f"{BASE_URL}/v1.3/adgroup/update/status/"
        payload = {
            "advertiser_id": TIKTOK_ADVERTISER_ID,
            "adgroup_id": adgroup_id,
            "opt_type": "DELETE"
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        if response.status_code == 200:
            return redirect('adgroup_listing')
        return render(request, 'adgroup_delete.html', {
            'adgroup_id': adgroup_id,
            'error': "Failed to delete ad group."
        })

    return render(request, 'adgroup_delete.html', {'adgroup_id': adgroup_id})

def register(request):
    """
    Handles user registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'register.html', {'error': 'Passwords do not match.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username is already taken.'})

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('dashboard')

    return render(request, 'register.html')

def ui_login(request):
    """
    Handles user login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        return render(request, 'login.html', {'error': 'Invalid credentials.'})

    return render(request, 'login.html')

def ui_logout(request):
    django_logout(request)
    return redirect('ui_login')

def dashboard(request):
    """
    Displays the user dashboard with a paginated table of campaigns (100 per page).
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    page_number = request.GET.get('page', 1)
    campaigns = fetch_campaigns(page=page_number, page_size=100)
    paginator = Paginator(campaigns, 100)
    page_obj = paginator.get_page(page_number)

    no_campaigns = (len(campaigns) == 0)
    return render(request, 'dashboard.html', {
        'user': request.user,
        'page_obj': page_obj,
        'no_campaigns': no_campaigns
    })

def listing(request):
    """
    Displays a paginated list of campaigns with actions.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    page_number = request.GET.get('page', 1)
    campaigns = fetch_campaigns(page=page_number, page_size=100)
    paginator = Paginator(campaigns, 100)
    page_obj = paginator.get_page(page_number)

    return render(request, 'listing.html', {'page_obj': page_obj})

def campaign_detail(request, campaign_id):
    """
    Displays details for a specific campaign.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    campaign = fetch_campaign_details(campaign_id)
    if not campaign:
        return redirect('dashboard')

    return render(request, 'campaign_detail.html', {'campaign': campaign})

def campaign_update(request, campaign_id):
    """
    Updates only the budget of a selected campaign.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    campaign = fetch_campaign_details(campaign_id)
    if not campaign:
        return redirect('dashboard')

    if request.method == 'POST':
        budget = request.POST.get('budget')
        if not budget:
            return render(request, 'campaign_update.html', {
                'campaign': campaign,
                'error': "Please provide a new budget."
            })

        url = f"{BASE_URL}/campaign/update/"
        payload = {
            "advertiser_id": TIKTOK_ADVERTISER_ID,
            "campaign_id": campaign_id,
            "budget": float(budget)
        }
        response = requests.post(url, json=payload, headers=HEADERS)

        if response.status_code == 200:
            return redirect('campaign_listing')
        return render(request, 'campaign_update.html', {
            'campaign': campaign,
            'error': "Failed to update campaign."
        })

    return render(request, 'campaign_update.html', {'campaign': campaign})

def campaign_delete(request, campaign_id):
    """
    Deletes a campaign via the TikTok API.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    if request.method == 'POST':
        url = f"{BASE_URL}/campaign/update/status/"
        payload = {
            "advertiser_id": TIKTOK_ADVERTISER_ID,
            "campaign_id": campaign_id,
            "opt_type": "DELETE"
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        if response.status_code == 200:
            return redirect('dashboard')
        return render(request, 'campaign_delete.html', {
            'campaign_id': campaign_id,
            'error': "Failed to delete campaign."
        })

    return render(request, 'campaign_delete.html', {'campaign_id': campaign_id})

def bulk_update(request):
    """
    Handles bulk updates of campaign budgets.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    if request.method == 'POST':
        selected_campaigns = request.POST.getlist('campaign_ids')
        new_budget = request.POST.get('new_budget')

        if not new_budget:
            campaigns = fetch_campaigns()
            paginator = Paginator(campaigns, 100)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            return render(request, 'bulk_update.html', {
                'page_obj': page_obj,
                'error': "Please provide a new budget."
            })

        update_errors = []
        for camp_id in selected_campaigns:
            url = f"{BASE_URL}/campaign/update/"
            payload = {
                "advertiser_id": TIKTOK_ADVERTISER_ID,
                "campaign_id": camp_id,
                "budget": float(new_budget)
            }
            response = requests.post(url, json=payload, headers=HEADERS)
            if response.status_code not in [200, 204]:
                update_errors.append(camp_id)

        if not update_errors:
            return redirect('dashboard')
        campaigns = fetch_campaigns()
        paginator = Paginator(campaigns, 100)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'bulk_update.html', {
            'page_obj': page_obj,
            'error': f"Failed to update campaigns: {', '.join(update_errors)}"
        })

    campaigns = fetch_campaigns()
    paginator = Paginator(campaigns, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'bulk_update.html', {'page_obj': page_obj})

def adgroup_listing(request):
    """
    Displays a paginated list of ad groups.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    page_number = request.GET.get('page', 1)
    adgroups = fetch_adgroups(page=page_number, page_size=100)
    if not adgroups:
        print("No ad groups returned from fetch_adgroups")
    paginator = Paginator(adgroups, 100)
    page_obj = paginator.get_page(page_number)

    return render(request, 'adgroup_listing.html', {
        'page_obj': page_obj,
        'no_adgroups': len(adgroups) == 0
    })

def adgroup_update(request, adgroup_id):
    """
    Updates budget and schedule of a selected ad group.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    adgroup = fetch_adgroup_details(adgroup_id)
    if not adgroup:
        return redirect('adgroup_listing')

    if request.method == 'POST':
        budget = request.POST.get('budget')
        schedule_start = request.POST.get('schedule_start')
        schedule_end = request.POST.get('schedule_end')

        if not all([budget, schedule_start, schedule_end]):
            return render(request, 'adgroup_update.html', {
                'adgroup': adgroup,
                'error': "Please provide all fields."
            })

        url = f"{BASE_URL}/v1.3/adgroup/update/"
        payload = {
            "advertiser_id": TIKTOK_ADVERTISER_ID,
            "adgroup_id": adgroup_id,
            "budget": float(budget),
            "schedule_start_time": schedule_start,
            "schedule_end_time": schedule_end,
        }
        response = requests.post(url, json=payload, headers=HEADERS)

        if response.status_code == 200:
            return redirect('adgroup_listing')
        return render(request, 'adgroup_update.html', {
            'adgroup': adgroup,
            'error': "Failed to update ad group."
        })

    return render(request, 'adgroup_update.html', {'adgroup': adgroup})

def adgroup_bulk_update(request):
    """
    Handles bulk updates of ad group budgets.
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    if request.method == 'POST':
        selected_adgroups = request.POST.getlist('adgroup_ids')
        new_budget = request.POST.get('new_budget')

        if not new_budget:
            return redirect('adgroup_listing')

        for adgroup_id in selected_adgroups:
            url = f"{BASE_URL}/v1.3/adgroup/update/"
            payload = {
                "advertiser_id": TIKTOK_ADVERTISER_ID,
                "adgroup_id": adgroup_id,
                "budget": float(new_budget),
            }
            requests.post(url, json=payload, headers=HEADERS)

        return redirect('adgroup_listing')

    return redirect('adgroup_listing')