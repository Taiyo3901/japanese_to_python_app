from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from .models import Group, GroupCode, UserGroup
from .forms import CustomUserCreationForm
import subprocess
from django.contrib.auth.decorators import login_required


def translate_japanese_code(japanese_code):
    """日本語コードをPythonコードに変換する"""
    lines = japanese_code.split('\n')
    python_code = []
    for line in lines:
        line = line.strip()
        if line.startswith('もし'):
            condition = line.replace('もし', '').replace('ならば', '').strip()
            python_code.append(f'if {condition}:')
        elif line.startswith('そうでなくもし'):
            condition = line.replace('そうでなくもし', '').replace('ならば', '').strip()
            python_code.append(f'elif {condition}:')
        elif line.startswith('そうでなければ'):
            python_code.append('else:')
        elif '表示する' in line:
            content = line.replace('表示する', '').strip().strip('()').strip('"').strip("'")
            python_code.append(f'print("{content}")')
        elif '入力する' in line:
            # 入力する("メッセージ") → input("メッセージ")
            content = line.replace('入力する', '').strip().strip('()').strip('"').strip("'")
            python_code.append(f'input("{content}")')
        elif '繰り返す' in line:
            if 'から' in line and 'まで' in line:
                var = line.split('を')[0].strip()
                start = line.split('から')[1].split('まで')[0].strip()
                step = line.split('ずつ')[0].split('まで')[1].strip()
                python_code.append(f'for {var} in range({start}, {step}):')
            else:
                condition = line.split('の間')[0].strip()
                python_code.append(f'while {condition}:')
        elif '=' in line:
            python_code.append(line)
        else:
            if line.startswith('|') or line.startswith('└'):
                python_code.append(f'    {line[1:].strip()}')
            else:
                python_code.append(line)
    return '\n'.join(python_code)

@csrf_exempt
def run_code(request):
    if request.method == 'POST':
        japanese_code = request.POST.get('japanese_code', '')
        try:
            python_code = translate_japanese_code(japanese_code)
            result = subprocess.run(['python', '-c', python_code], capture_output=True, text=True)
            output = result.stdout if result.returncode == 0 else result.stderr
            return JsonResponse({'output': output})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def save_code(request):
    if request.method == 'POST':
        user = request.user
        ip_address = request.POST.get('ip_address', '')
        japanese_code = request.POST.get('japanese_code', '')

        # グループを取得
        group = Group.objects.filter(ip_address=ip_address).first()
        if not group:
            return JsonResponse({'status': 'error', 'message': 'グループが存在しません'}, status=404)

        # コードを保存
        GroupCode.objects.update_or_create(
            user=user,
            group=group,
            defaults={'code': japanese_code}
        )

        # ユーザーがグループに参加していることを記録
        UserGroup.objects.get_or_create(user=user, group=group)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def get_group_codes(request):
    if request.method == 'POST':
        ip_address = request.POST.get('ip_address', '')
        user = request.user if request.user.is_authenticated else None

        if user:
            group = Group.objects.filter(ip_address=ip_address).first()
            if group:
                # グループに参加しているメンバーを取得
                members = UserGroup.objects.filter(group=group).values_list('user__username', flat=True)
                return JsonResponse({'status': 'success', 'members': list(members)})
            return JsonResponse({'status': 'error', 'message': 'Group not found'}, status=404)
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'アカウント {username} が作成されました。')
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'converter/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'ようこそ {username} さん！')
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'converter/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return redirect('index')

@staff_member_required
def admin_dashboard(request):
    groups = Group.objects.all().order_by('-created_at')
    for group in groups:
        # UserGroupからユーザーを直接取得
        group.members = User.objects.filter(
            id__in=UserGroup.objects.filter(group=group).values('user_id')
        )
    return render(request, 'converter/admin_dashboard.html', {'groups': groups})

@staff_member_required
def admin_groups(request):
    groups = Group.objects.all().order_by('-created_at')
    return render(request, 'converter/admin_groups.html', {'groups': groups})

@staff_member_required
def create_group(request):
    if request.method == 'POST':
        ip_address = request.POST.get('ip_address', '')
        if ip_address:
            group, created = Group.objects.get_or_create(ip_address=ip_address)
            if created:
                messages.success(request, f'グループ {ip_address} を作成しました。')
            else:
                messages.warning(request, f'グループ {ip_address} は既に存在します。')
            return redirect('admin_groups')
    return render(request, 'converter/create_group.html')

@staff_member_required
def delete_group(request, group_id):
    group = Group.objects.filter(id=group_id).first()
    if group:
        group.delete()
        messages.success(request, f'グループ {group.ip_address} を削除しました。')
    else:
        messages.error(request, 'グループが見つかりませんでした。')
    return redirect('admin_groups')

@staff_member_required
def view_member_code(request, user_id):
    # ユーザーを取得（存在しない場合は404エラー）
    target_user = get_object_or_404(User, id=user_id)
    
    # ユーザーが保存したコードを取得
    codes = GroupCode.objects.filter(user=target_user).select_related('group').order_by('-created_at')
    
    return render(request, 'converter/view_member_code.html', {
        'target_user': target_user,
        'codes': codes
    })
    
@csrf_exempt
@login_required
def leave_group(request):
    if request.method == 'POST':
        user = request.user
        ip_address = request.POST.get('ip_address', '')

        # グループを取得
        group = Group.objects.filter(ip_address=ip_address).first()
        if not group:
            return JsonResponse({'status': 'error', 'message': 'グループが存在しません'}, status=404)

        # ユーザーがグループから抜ける
        UserGroup.objects.filter(user=user, group=group).delete()
        GroupCode.objects.filter(user=user, group=group).delete()

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
def index(request):
    return render(request, 'converter/index.html')