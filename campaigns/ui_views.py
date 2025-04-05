import os
import requests
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from urllib.parse import quote  # For URL encoding

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
    Displays the user dashboard with a paginated table of ad groups (100 per page).
    """
    if not request.user.is_authenticated:
        return redirect('ui_login')

    page_number = request.GET.get('page', 1)
    adgroups = fetch_adgroups(page=page_number, page_size=100)
    paginator = Paginator(adgroups, 100)
    page_obj = paginator.get_page(page_number)

    no_adgroups = (len(adgroups) == 0)
    message = request.GET.get('message', None)
    error = request.GET.get('error', None)

    return render(request, 'dashboard.html', {
        'user': request.user,
        'page_obj': page_obj,
        'no_adgroups': no_adgroups,
        'message': message,
        'error': error
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
            page_number = request.GET.get('page', 1)
            adgroups = fetch_adgroups(page=page_number, page_size=100)
            paginator = Paginator(adgroups, 100)
            page_obj = paginator.get_page(page_number)
            return render(request, 'adgroup_bulk_update.html', {
                'page_obj': page_obj,
                'no_adgroups': len(adgroups) == 0,
                'error': "Please provide a new budget."
            })

        try:
            new_budget = float(new_budget)
            if new_budget < 0:
                raise ValueError("Budget cannot be negative.")
        except ValueError as e:
            page_number = request.GET.get('page', 1)
            adgroups = fetch_adgroups(page=page_number, page_size=100)
            paginator = Paginator(adgroups, 100)
            page_obj = paginator.get_page(page_number)
            return render(request, 'adgroup_bulk_update.html', {
                'page_obj': page_obj,
                'no_adgroups': len(adgroups) == 0,
                'error': f"Invalid budget value: {str(e)}"
            })

        update_errors = []
        for adgroup_id in selected_adgroups:
            url = f"{BASE_URL}/adgroup/update/"
            payload = {
                "advertiser_id": TIKTOK_ADVERTISER_ID,
                "adgroup_id": adgroup_id,
                "budget": new_budget,
            }
            try:
                response = requests.post(url, json=payload, headers=HEADERS)
                if response.status_code not in [200, 204]:
                    update_errors.append(adgroup_id)
            except requests.exceptions.RequestException as e:
                update_errors.append(f"{adgroup_id} (Request failed: {str(e)})")

        if not update_errors:
            return redirect('dashboard')
        page_number = request.GET.get('page', 1)
        adgroups = fetch_adgroups(page=page_number, page_size=100)
        paginator = Paginator(adgroups, 100)
        page_obj = paginator.get_page(page_number)
        return render(request, 'adgroup_bulk_update.html', {
            'page_obj': page_obj,
            'no_adgroups': len(adgroups) == 0,
            'error': f"Failed to update ad groups: {', '.join(update_errors)}"
        })

    # On GET, render the bulk update page with the ad group list
    page_number = request.GET.get('page', 1)
    adgroups = fetch_adgroups(page=page_number, page_size=100)
    paginator = Paginator(adgroups, 100)
    page_obj = paginator.get_page(page_number)
    return render(request, 'adgroup_bulk_update.html', {
        'page_obj': page_obj,
        'no_adgroups': len(adgroups) == 0
    })

def adgroup_update(request, adgroup_id):
    if not request.user.is_authenticated:
        return redirect('ui_login')

    adgroup = fetch_adgroup_details(adgroup_id)
    if not adgroup:
        return redirect('dashboard')

    now = datetime.now()

    if request.method == 'POST':
        # Collect and validate form inputs
        budget = request.POST.get('budget')
        end_str = request.POST.get('schedule_end')

        # Validate required fields
        if not all([budget, end_str]):
            return render(request, 'adgroup_update.html', {
                'adgroup': adgroup, 'current_datetime': now,
                'error': "Please provide budget and end time."
            })

        # Validate budget
        try:
            budget = float(budget)
            if budget < 0:
                raise ValueError("Budget cannot be negative.")
        except ValueError as e:
            return render(request, 'adgroup_update.html', {
                'adgroup': adgroup, 'current_datetime': now,
                'error': f"Invalid budget: {e}"
            })

        # Validate and parse end date (must be in the future)
        try:
            end_dt = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
            if end_dt <= now:
                raise ValueError("End time must be in the future.")
            # Ensure end time is after start time if start exists
            existing_start = adgroup.get('schedule_start_time', 'N/A')
            if existing_start != 'N/A':
                start_dt = datetime.strptime(existing_start, '%Y-%m-%d %H:%M:%S')
                if end_dt <= start_dt:
                    raise ValueError("End time must be after the existing start time.")
        except ValueError as e:
            return render(request, 'adgroup_update.html', {
                'adgroup': adgroup, 'current_datetime': now,
                'error': f"Invalid end date: {e}"
            })

        api_end = end_dt.strftime('%Y-%m-%d %H:%M:00')

        # Prepare payload for API (only update budget and end time)
        payload = {
            "advertiser_id": TIKTOK_ADVERTISER_ID,
            "adgroup_id": adgroup_id,
            "schedule_type": "SCHEDULE_START_END",
            "schedule_end_time": api_end,
            "budget": budget,
        }

        # Normal update
        response = requests.post(f"{BASE_URL}/adgroup/update/", json=payload, headers=HEADERS)
        if response.status_code in [200, 204] or (response.status_code == 200 and response.json().get("code") == 0):
            return redirect('dashboard')
        error_msg = response.json().get('message', response.text)
        return render(request, 'adgroup_update.html', {
            'adgroup': adgroup, 'current_datetime': now,
            'error': f"Update failed: {error_msg}"
        })

    # GET request: Render the form
    return render(request, 'adgroup_update.html', {
        'adgroup': adgroup,
        'current_datetime': now
    })

def adgroup_bulk_update_schedule(request):
    if not request.user.is_authenticated:
        return redirect('ui_login')

    if request.method == 'POST':
        selected_adgroups = request.POST.getlist('adgroup_ids')
        new_end = request.POST.get('schedule_end')

        # Validate input
        if not new_end:
            page_number = request.GET.get('page', 1)
            adgroups = fetch_adgroups(page=page_number, page_size=100)
            paginator = Paginator(adgroups, 100)
            page_obj = paginator.get_page(page_number)
            return render(request, 'adgroup_bulk_update_schedule.html', {
                'page_obj': page_obj,
                'no_adgroups': len(adgroups) == 0,
                'error': "Please provide an end time."
            })

        # Validate and parse end date (must be in the future)
        now = datetime.now()
        try:
            end_dt = datetime.strptime(new_end, '%Y-%m-%dT%H:%M')
            if end_dt <= now:
                raise ValueError("End time must be in the future.")
        except ValueError as e:
            page_number = request.GET.get('page', 1)
            adgroups = fetch_adgroups(page=page_number, page_size=100)
            paginator = Paginator(adgroups, 100)
            page_obj = paginator.get_page(page_number)
            return render(request, 'adgroup_bulk_update_schedule.html', {
                'page_obj': page_obj,
                'no_adgroups': len(adgroups) == 0,
                'error': str(e)
            })

        api_end = end_dt.strftime('%Y-%m-%d %H:%M:00')

        # Process updates
        update_errors = []
        for adgroup_id in selected_adgroups:
            adgroup = fetch_adgroup_details(adgroup_id)
            if not adgroup:
                update_errors.append(f"{adgroup_id} (Not found)")
                continue

            # Ensure end time is after start time if start exists
            existing_start = adgroup.get('schedule_start_time', 'N/A')
            if existing_start != 'N/A':
                try:
                    start_dt = datetime.strptime(existing_start, '%Y-%m-%d %H:%M:%S')
                    if end_dt <= start_dt:
                        update_errors.append(f"{adgroup_id} (End time must be after start time: {existing_start})")
                        continue
                except ValueError:
                    pass

            payload = {
                "advertiser_id": TIKTOK_ADVERTISER_ID,
                "adgroup_id": adgroup_id,
                "schedule_type": "SCHEDULE_START_END",
                "schedule_end_time": api_end,
            }
            try:
                response = requests.post(f"{BASE_URL}/adgroup/update/", json=payload, headers=HEADERS)
                if response.status_code not in [200, 204] or (response.status_code == 200 and response.json().get("code") != 0):
                    error_detail = response.json().get('message', response.text)
                    update_errors.append(f"{adgroup_id} ({error_detail})")
            except requests.exceptions.RequestException as e:
                update_errors.append(f"{adgroup_id} (Request failed: {str(e)})")

        # Handle results
        if not update_errors:
            return redirect('dashboard')
        page_number = request.GET.get('page', 1)
        adgroups = fetch_adgroups(page=page_number, page_size=100)
        paginator = Paginator(adgroups, 100)
        page_obj = paginator.get_page(page_number)
        return render(request, 'adgroup_bulk_update_schedule.html', {
            'page_obj': page_obj,
            'no_adgroups': len(adgroups) == 0,
            'error': f"Failed to update ad groups: {', '.join(update_errors)}"
        })

    # On GET, render the bulk update page
    page_number = request.GET.get('page', 1)
    adgroups = fetch_adgroups(page=page_number, page_size=100)
    paginator = Paginator(adgroups, 100)
    page_obj = paginator.get_page(page_number)
    return render(request, 'adgroup_bulk_update_schedule.html', {
        'page_obj': page_obj,
        'no_adgroups': len(adgroups) == 0
    })
