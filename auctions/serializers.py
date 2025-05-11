from rest_framework import serializers
from django.utils import timezone
from .models import Category, Auction, Bid, Rating, Comment
from drf_spectacular.utils import extend_schema_field
from datetime import timedelta
from django.db.models import Avg


class CategoryListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name']

class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class AuctionListCreateSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ",read_only=True)
    closing_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    isOpen = serializers.SerializerMethodField(read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)

    def validate_closing_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Closing date must be greater than now.")
        
        creation = timezone.now()  
        if value - creation < timedelta(days=15):
            raise serializers.ValidationError("La subasta debe durar al menos 15 días.")
        
        return value

    class Meta:
        model = Auction
        fields = '__all__'

    @extend_schema_field(serializers.BooleanField()) 
    def get_isOpen(self, obj):
        return obj.closing_date > timezone.now()   

    @extend_schema_field(serializers.FloatField())
    def get_average_rating(self, obj):
        avg = obj.ratings.aggregate(avg=Avg('value'))['avg'] or 0
        return round(avg, 2)
    
    class Meta:
        model = Auction
        fields = '__all__' 
        
class AuctionDetailSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ",read_only=True)
    closing_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    isOpen = serializers.SerializerMethodField(read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)

    def validate_closing_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Closing date must be greater than now.")
        
        creation = self.instance.creation_date if self.instance else timezone.now()
        if value - creation < timedelta(days=15):
            raise serializers.ValidationError("La subasta debe tener una duración mínima de 15 días.")
        
        return value

    @extend_schema_field(serializers.BooleanField()) 
    def get_isOpen(self, obj):
        return obj.closing_date > timezone.now()
    
    @extend_schema_field(serializers.FloatField())
    def get_average_rating(self, obj):
        avg = obj.ratings.aggregate(avg=Avg('value'))['avg'] or 0
        return round(avg, 2)
    
    class Meta:
        model = Auction
        fields = '__all__'

class BidListCreateSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    bidder_username = serializers.CharField(source="bidder.username", read_only=True)

    class Meta:
        model = Bid
        fields = '__all__'
        read_only_fields = ('auction', 'bidder')



class BidDetailSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

    class Meta:
        model = Bid
        fields = '__all__'

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'auction', 'user', 'value']
        read_only_fields = ['user']

class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    created       = serializers.DateTimeField(read_only=True)
    updated       = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id','auction','user','user_username','title','body','created','updated']
        read_only_fields = ['user','auction']