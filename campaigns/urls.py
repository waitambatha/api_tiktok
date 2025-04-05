from django.urls import path
from . import ui_views
from . import views

urlpatterns = [
    # UI endpoints
path('register/', ui_views.register, name='register'),
    path('', ui_views.ui_login, name='ui_login'),
    path('logout/', ui_views.ui_logout, name='ui_logout'),
    path('dashboard/', ui_views.dashboard, name='dashboard'),
path('adgroups/detail/<str:adgroup_id>/', ui_views.adgroup_detail, name='adgroup_detail'),
    path('adgroups/delete/<str:adgroup_id>/', ui_views.adgroup_delete, name='adgroup_delete'),
    path('campaigns/listing/', ui_views.listing, name='campaign_listing'),
    path('campaign/detail/<str:campaign_id>/', ui_views.campaign_detail, name='campaign_detail'),
    path('campaign/update/<str:campaign_id>/', ui_views.campaign_update, name='campaign_update'),
    path('campaign/delete/<str:campaign_id>/', ui_views.campaign_delete, name='campaign_delete'),
    path('campaigns/bulk_update/', ui_views.bulk_update, name='campaign_bulk_update'),
    path('adgroups/', ui_views.adgroup_listing, name='adgroup_listing'),
    path('adgroups/update/<str:adgroup_id>/', ui_views.adgroup_update, name='adgroup_update'),
    path('adgroups/bulk_update/', ui_views.adgroup_bulk_update, name='adgroup_bulk_update'),
    # API endpoints
    path('api/login/', views.login_user, name='login_user_api'),
    path('api/campaigns/', views.fetch_campaigns, name='fetch_campaigns'),
path('adgroup/bulk-update-schedule/', ui_views.adgroup_bulk_update_schedule, name='adgroup_bulk_update_schedule'),
]
