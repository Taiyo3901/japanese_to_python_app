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
import re
import tempfile
from django.contrib.auth.decorators import login_required

def convert_to_python(japanese_code):
    replacements = [
        (r'そうでなくもし\s*(.*?)\s*ならば', r'elif \1:'), 
        (r'もし\s*(.*?)\s*ならば', r'if \1:'), 
        (r'そうでなければ', 'else:'),  
        (r'表示する\((.*?)\)', r'print(\1)'),  
        (r'入力する\((.*?)\)', r'input(\1)'),  
        (r'(\w+)を(\d+)から(\d+)まで(\d+)ずつ繰り返す', r'for \1 in range(\2, \3, \4):'),  
        (r'(\w+)を(\d+)から(\d+)まで繰り返す', r'for \1 in range(\2, \3):'),  
        (r'(\w+)が(.+?)の間繰り返す', r'while \1 \2:'),  
    ]
    

    python_code = []
    indent_level = 0
    indent_stack = []

    for line in japanese_code.split("\n"):
        original_line = line
        line = line.strip()

        for pattern, replacement in replacements:
            line = re.sub(pattern, replacement, line)

        if line.endswith(":"):
            if line.startswith(("elif", "else")):
                if indent_stack:
                    indent_level = indent_stack.pop()

            python_code.append("    " * indent_level + line)

            if not line.startswith(("elif", "else")):
                indent_stack.append(indent_level)

            indent_level += 1

        elif line:
            python_code.append("    " * indent_level + line)

        else:
            python_code.append(line)

        print(f"変換前: {original_line} → 変換後: {line}")

    result = "\n".join(python_code)

    if not result.strip():
        print("エラー: 変換後のPythonコードが空です！")

    return result


@csrf_exempt
def run_code(request):
    if request.method == 'POST':
        japanese_code = request.POST.get('japanese_code', '')

        try:
            print(f"受け取った日本語コード:\n{japanese_code}")  # 🛠 デバッグ: 入力確認

            # 日本語コードを Python に変換
            if re.search(r'[ぁ-んァ-ン一-龥]', japanese_code):
                python_code = convert_to_python(japanese_code)
            else:
                python_code = japanese_code  # Pythonコードならそのまま実行

            print(f"変換後のPythonコード:\n{python_code}")  # 🛠 デバッグ: 変換後のPython確認

            # もし python_code が空ならエラーを返す
            if not python_code.strip():
                return JsonResponse({'error': 'Pythonコードが空です。'}, status=400)

            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py', encoding='utf-8') as temp_file:
                temp_file.write(python_code)
                temp_file_path = temp_file.name

            # Python 3 で実行
            result = subprocess.run(
                ['python', temp_file_path],  # 環境によっては ['python', temp_file_path] に変更
                capture_output=True, text=True, shell=False
            )

            # 実行結果を取得
            output = result.stdout.strip()
            error_output = result.stderr.strip()

            # エラーがあれば、それも一緒に表示
            if error_output:
                output += "\n" + error_output

            print(f"標準出力:\n{output}")  # 🛠 デバッグ: 実行結果を確認

            return JsonResponse({'output': output})

        except Exception as e:
            print(f"エラー発生: {e}")  # 🛠 デバッグ: 例外処理のエラー確認
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