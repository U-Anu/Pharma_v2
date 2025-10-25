from collections import defaultdict
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from news.forms import NewsArticleForm
from news.models import NewsArticle

# ----------------------------- News Article List -----------------------------

def news_article_list(request):
    """List all news articles, grouped by category."""
    articles = NewsArticle.objects.all()
    # Group articles by category

    return render(request, 'news_article/news_article_list.html', {'articles': articles})



def news_article_feed(request):
    """List all news articles, grouped by category."""
    articles = NewsArticle.objects.select_related('category').order_by('-published_at')
    print('----',articles)
    # Group articles by category
    categorized_articles = defaultdict(list)
    for article in articles:
        if article.category:
            categorized_articles[article.category.name].append(article)
        print('----',categorized_articles)

    return render(request, 'news_feed.html', {'articles': dict(categorized_articles)})

# ----------------------------- News Article Create -----------------------------

def news_article_create(request):
    """Create a new news article."""
    if request.method == 'POST':
        form = NewsArticleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "News article created successfully!")
            return redirect('news_article_list')
        else:
            messages.error(request, "Error creating the article. Please check the form.")
    else:
        form = NewsArticleForm()

    return render(request, 'news_article/news_article_form.html', {'form': form})

# ----------------------------- News Article Update -----------------------------

def news_article_update(request, id):
    """Update an existing news article."""
    article = get_object_or_404(NewsArticle, id=id)
    if request.method == 'POST':
        form = NewsArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "News article updated successfully!")
            return redirect('news_article_list')
        else:
            messages.error(request, "Error updating the article. Please check the form.")
    else:
        form = NewsArticleForm(instance=article)

    return render(request, 'news_article/news_article_form.html', {'form': form, 'article': article})

# ----------------------------- News Article Delete -----------------------------

def news_article_delete(request, id):
    """Delete a news article."""
    article = get_object_or_404(NewsArticle, id=id)
    article.delete()
    messages.success(request, "News article deleted successfully!")
    return redirect('news_article_list')

# ----------------------------- News Article Detail -----------------------------

def news_article_detail(request, id):
    """View details of a single news article."""
    article = get_object_or_404(NewsArticle.objects.select_related('category'), id=id)
    return render(request, 'news_article/news_article_detail.html', {'article': article})
