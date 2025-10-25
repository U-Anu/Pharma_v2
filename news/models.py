from django.db import models

# Create your models here.
class NewsArticle(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey('Master.NewsCategory',related_name='%(class)s_news_articles', on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to="news_images/", blank=True, null=True)
    published_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)
    def __str__(self):
        return self.title