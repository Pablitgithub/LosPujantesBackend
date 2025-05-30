from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)
    class Meta:
        ordering=('id',)

    def __str__(self):
        return self.name
    

class Auction(models.Model):
    stock = models.IntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(Category, related_name='auctions', on_delete=models.CASCADE)
    thumbnail = models.URLField()
    creation_date = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateTimeField()

    auctioneer = models.ForeignKey(CustomUser, related_name='auctions', on_delete=models.CASCADE)

    class Meta:
        ordering=('id',)
        
    def __str__(self):
        return self.title
    
class Bid(models.Model):
    auction = models.ForeignKey(Auction, related_name='bids', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)
    bidder = models.ForeignKey(CustomUser, related_name='bids', on_delete=models.CASCADE)  # cambio clave aquí

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return f"Puja de {self.price}€ por {self.bidder}"
    
class Rating(models.Model):
    VALUE_CHOICES = [(i, i) for i in range(1, 6)]
    auction = models.ForeignKey(
        'Auction',
        related_name='ratings',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='ratings',
        on_delete=models.CASCADE
    )
    value = models.PositiveSmallIntegerField(choices=VALUE_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        unique_together = ('auction', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.auction.title}: {self.value}"
    
class Comment(models.Model):
    auction = models.ForeignKey(
        'Auction',
        related_name='comments',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=150)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.user.username} on {self.auction.title}: {self.title}"