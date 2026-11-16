from django.urls import path # type: ignore

from . import views
from django.conf.urls.static import static # type: ignore

urlpatterns = [
      
    path("", views.index, name="index"),

    path('index/', views.index, name='index'),

    path('about/', views.about, name='about'),

    path('contact/', views.contact, name='contact'),

    path('login/', views.login_view, name='login'),

   path('signup/', views.signup, name='signup'),

   path('climateTempPrediction/', views.climateTempPrediction, name='climateTempPrediction'), 

   path('climateDisasterPrediction/', views.disasterPrediction, name='disaster_prediction'),

   path('carbon-prediction/', views.climateCarbonPrediction, name='carbon_prediction'),

   path('support/', views.support, name='support'),

   path('my-tickets/', views.my_tickets, name='my_tickets'),

   path('ticket/<int:id>/', views.ticket_detail, name='ticket_detail'),

   path('chatbot/', views.chatbot, name='chatbot_view'),
    
    # AJAX / JSON API endpoint used by JavaScript fetch
   path('chatbot/api/', views.chatbot, name='chat_api'),


]
