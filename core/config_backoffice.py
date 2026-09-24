from django.urls import path , include



urlpatterns = [
 
    path('api/backoffice/', include('backoffice.urls')),

]
