from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect


class CustomLoginView(auth_views.LoginView):
    """Custom login view with enhanced mobile-friendly template"""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Welcome back, {form.get_user().get_full_name() or form.get_user().username}!'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Invalid username or password. Please try again.'
        )
        return super().form_invalid(form)


class CustomLogoutView(auth_views.LogoutView):
    """Custom logout view with immediate redirect"""
    next_page = '/auth/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(
                request,
                'You have been successfully signed out.'
            )
        return super().dispatch(request, *args, **kwargs)


@require_POST
@csrf_protect
def logout_view(request):
    """Simple logout view that handles POST requests properly"""
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'Goodbye {user_name}! You have been successfully signed out.')
    
    return redirect('login')


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """User profile view"""
    template_name = 'registration/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
