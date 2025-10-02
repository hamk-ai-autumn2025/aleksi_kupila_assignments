from django.http import HttpResponse, Http404, HttpResponseRedirect, request
from .models import Work, Artist, Loan, Tag
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from .myforms import LoanForm, ReturnForm, CustomLoginForm, CustomSignupForm
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from axes.decorators import axes_dispatch
from django.contrib import messages
from axes.helpers import get_lockout_message

class IndexView(generic.ListView):
    template_name = "lainaamo/index.html"
    context_object_name = "available_works"

    def get_queryset(self):

        queryset = Work.objects.all()
        try:
            tags = self.request.GET.getlist('tags')
            artist = self.request.GET.get('artist')
            searchresult = self.request.GET.get('search')
        except (TypeError, ValueError):
            tags = None
            artist = None
            searchresult = None

        if tags and tags[0] != "":
            queryset = queryset.filter(tags__id__in=tags).distinct()
        if artist:
            queryset = queryset.filter(artists__id=artist)
        if searchresult:
            queryset = queryset.filter(name__icontains=searchresult) 
        return queryset
    
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['tags_selected'] = Tag.objects.all()
        context['artists'] = Artist.objects.all()
        return context
    
class DetailView(generic.edit.FormMixin, generic.DetailView):
    model = Work
    template_name = "lainaamo/detail.html"
    form_class = LoanForm

    def get_form_kwargs(self):  # Overrides the default method to add the current work object 
        kwargs = super().get_form_kwargs()
        kwargs['work'] = self.object
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            # Prepopulate the LoanForm with the work object.
            context['form'] = self.get_form(initial={'work': self.object})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            start = form.cleaned_data.get('loan_start')
            end = form.cleaned_data.get('loan_end')
            if self.object.is_available_during(start, end):
                return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        
        loan = form.save(commit=False)
        loan.user = self.request.user
        loan.work=self.object
        Work.objects.filter(pk=self.object.pk).update(is_available=False)
        loan.save()
        return redirect('lainaamo:detail', pk=self.object.pk)
    
class MyLoansView(LoginRequiredMixin, generic.ListView, generic.edit.FormMixin):
    model = Loan
    template_name = 'lainaamo/my_loans.html'
    context_object_name = 'loans'
    form_class = ReturnForm

    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user, return_time__isnull=True)
    
    def post(self, request, *args, **kwargs):  # Called when return artwork button is pressed
        self.object_list = self.get_queryset()  
        form = self.get_form()
        return self.form_valid(form)
        
    def form_valid(self, form):
        loan_id = self.request.POST.get("loan_id")
        if loan_id:
            try:
                loan = Loan.objects.get(id=loan_id, user=self.request.user, return_time__isnull=True)
                loan_work = loan.work
                loan.delete()  
                Work.objects.filter(pk=loan_work.pk).update(is_available=True)  # Changes lended work to be available again

            except Loan.DoesNotExist:
                pass
        return HttpResponseRedirect("my_loans")

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = CustomLoginForm
    
    @axes_dispatch
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def form_invalid(self, form):  
        lockout_message = get_lockout_message()
        messages.error(self.request, lockout_message)  # Creates error message if user gets locked out by failed login attempts
        return super().form_invalid(form)

class CustomSignUpView(generic.FormView):
    form_class = CustomSignupForm
    success_url = reverse_lazy("lainaamo:login")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)