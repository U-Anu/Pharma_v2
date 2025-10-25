from django.urls import path,include
from . import views
urlpatterns = [
    

 # News Articles
    path('news-articles/', views.news_article_list, name='news_article_list'),
    path('news-articles-feed/', views.news_article_feed, name='news_feed'),
    path('news-articles_create/', views.news_article_create, name='news_article_create'),
    path('news_article_update/<int:id>/', views.news_article_update, name='news_article_update'),
    path('news_article_delete/<int:id>/', views.news_article_delete, name='news_article_delete'),
    path('news-articles/detail/<int:id>/', views.news_article_detail, name='news_article_detail'),
]
