from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('run/', views.run_code, name='run_code'),
    path('save-code/', views.save_code, name='save_code'),
    path('get-group-codes/', views.get_group_codes, name='get_group_codes'),
    path('leave-group/', views.leave_group, name='leave_group'),  # 追加
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-groups/', views.admin_groups, name='admin_groups'),
    path('create-group/', views.create_group, name='create_group'),
    path('delete-group/<int:group_id>/', views.delete_group, name='delete_group'),
    path('view-member-code/<int:user_id>/', views.view_member_code, name='view_member_code'),
    path('home/', views.home, name ='home'),
    path('setting/', views.setting, name ='setting'),
    path('dictionally/', views.dictionally, name ='dictionally'),
]