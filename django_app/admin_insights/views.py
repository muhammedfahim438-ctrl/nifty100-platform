from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required(login_url='accounts:login')
def executive_summary(request):
    return HttpResponse("<h1>Admin Insights Dashboard</h1><p>Work-in-progress placeholder.</p>")
