from django.contrib import admin
from .models import Category, Auction, Bid, Rating
from django.utils import timezone

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "auctioneer", "price", "is_open")
    list_filter = ("category", "auctioneer", "closing_date")
    search_fields = ("title", "description")
    readonly_fields = ("creation_date",)
    
    def is_open(self, obj):
        return obj.closing_date > timezone.now()
    is_open.boolean = True
    is_open.short_description = "Abierta?"

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "auction", "bidder", "price", "creation_date")
    list_filter = ("auction", "bidder")
    readonly_fields = ("creation_date",)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("id", "auction", "user", "value", "created")
    list_filter = ("auction", "user", "value")
    readonly_fields = ("created",)
