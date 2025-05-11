from django.urls import path
from .views import (CategoryListCreate, CategoryRetrieveUpdateDestroy, AuctionListCreate, AuctionRetrieveUpdateDestroy,
                     BidListCreate, BidRetrieveUpdateDestroy, UserAuctionListView, UserBidListView,RatingListCreate,
                     RatingRetrieveUpdateDestroy, CommentListCreate, CommentRetrieveUpdateDestroy)

app_name = "auctions"
urlpatterns = [
    path('ratings/', RatingListCreate.as_view(), name='rating-list-create'),
    path('ratings/<int:pk>/', RatingRetrieveUpdateDestroy.as_view(), name='rating-detail'),

    path('categories/', CategoryListCreate.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroy.as_view(), name='category-detail'),

    path('', AuctionListCreate.as_view(), name='auction-list-create'),
    path('<int:pk>/', AuctionRetrieveUpdateDestroy.as_view(), name='auction-detail'),

    path('<int:auction_id>/bid/', BidListCreate.as_view(), name='bid-list-create'),
    path('<int:auction_id>/bid/<int:pk>/', BidRetrieveUpdateDestroy.as_view(), name='bid-detail'),

    # comentarios
    path('<int:auction_id>/comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('<int:auction_id>/comments/<int:pk>/', CommentRetrieveUpdateDestroy.as_view(), name='comment-detail'),

    path('users/', UserAuctionListView.as_view(), name='action-from-users'),
    path('misPujas/', UserBidListView.as_view(), name='user-bids'),
]
