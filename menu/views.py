from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout

def index(request):
    if not request.user.is_authenticated:
        return redirect('app_menu:login')
    
    return redirect('app_menu:menu')
    
def login_user(request):
    if request.user.is_authenticated:
        return redirect('app_menu:menu')
    
    if 'username' not in request.POST or 'password' not in request.POST:
        return render(request, 'menu/login.html')

    username = request.POST['username']
    password = request.POST['password']

    if len(username) == 0 or len(password) == 0:
        return render(request, 'menu/login.html', {'msg': 'Insira usuário e senha'})

    user = authenticate(request, username=username, password=password)

    if user is None:
        return render(request, 'menu/login.html', {'msg': 'Credenciais inválidas'})

    login(request, user)
    session = request.session
    session['user_id'] = user.pk
    session['username'] = user.get_username()
    session['name'] = user.get_full_name()

    return redirect('app_menu:menu')

def logout_user(request):
    logout(request)
    return redirect('app_menu:login')

def menu(request):
    return render(request, 'menu/menu.html', {
        'name': request.user.get_full_name() or request.user.get_username()
    })