"""MCWebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from app01 import views
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^mainpage/(\w+)/', views.mainpage),
    url(r'^check_code/', views.check_code),
    url(r'^register/', views.register),
    url(r'^login/', views.login),
    url(r'^add_works/(\w+)/', views.add_works),
    url(r'^my_works/(\w+)/', views.my_works),
    url(r'^yesterday/(\w+)/', views.yesterday),
    url(r'^all_works/(\w+)/', views.all_works),
    url(r'^upgrate_mywork/(\w+)/', views.upgrate_mywork),
    url(r'^change_mywork/(\w+)/', views.change_mywork),
    url(r'^delete_mywork/(\w+)/', views.delete_mywork),
    url(r'^add_weekly_report/(\w+)/', views.add_weekly_report),
    url(r'^weekly_imgs/(\w+)/', views.weekly_imgs),
    url(r'^my_weekly_report/(\w+)/', views.my_weekly_report),
    url(r'^edit_weekly_report/(\w+)/(\w+)/', views.edit_weekly_report),
    url(r'^delete_weekly_report/(\w+)/(\w+)/', views.delete_weekly_report),
    url(r'^all_weekly_report/(\w+)/', views.all_weekly_report),
    url(r'^search_works/(\w+)/', views.search_works),
    url(r'^search_weekly_report/(\w+)/', views.search_weekly_report),
    url(r'^register_aggrement/', views.register_aggrement),
    url(r'^please_login/', views.please_login),

]
