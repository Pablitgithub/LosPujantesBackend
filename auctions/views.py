from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from .models import Category, Auction, Bid, Rating, Comment
from .serializers import (
    CategoryListCreateSerializer, CategoryDetailSerializer,
    AuctionListCreateSerializer, AuctionDetailSerializer,
    BidListCreateSerializer, BidDetailSerializer, RatingSerializer, CommentSerializer
)
from .permissions import IsOwnerOrAdmin  

# --- Categorías ---
class CategoryListCreate(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListCreateSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

class CategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer
    permission_classes = [permissions.IsAdminUser]

    
# --- Subastas ---
class AuctionListCreate(generics.ListCreateAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionListCreateSerializer

    def get_queryset(self):
        queryset = Auction.objects.all()
        params = self.request.query_params

        # Filtro por búsqueda de texto
        search = params.get("search")
        if search:
            if len(search) < 3:
                raise ValidationError({"search": "La búsqueda debe tener al menos 3 caracteres."})
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

        # Filtro por categoría (puede ser ID o nombre exacto)
        category = params.get("category")
        if category:
            if category.isdigit():
                queryset = queryset.filter(category__id=int(category))
            else:
                if not Category.objects.filter(name=category).exists():
                    raise ValidationError({"category": f"La categoría '{category}' no existe."})
                queryset = queryset.filter(category__name=category)

        # Filtro por rango de precios
        min_price = params.get("min_price")
        max_price = params.get("max_price")

        if min_price:
            try:
                min_price_val = float(min_price)
                if min_price_val <= 0:
                    raise ValidationError({"min_price": "El precio mínimo debe ser mayor que 0."})
                queryset = queryset.filter(price__gte=min_price_val)
            except ValueError:
                raise ValidationError({"min_price": "Debe ser un número válido."})

        if max_price:
            try:
                max_price_val = float(max_price)
                if max_price_val <= 0:
                    raise ValidationError({"max_price": "El precio máximo debe ser mayor que 0."})
                if min_price and float(min_price) >= max_price_val:
                    raise ValidationError({"max_price": "El precio máximo debe ser mayor que el mínimo."})
                queryset = queryset.filter(price__lte=max_price_val)
            except ValueError:
                raise ValidationError({"max_price": "Debe ser un número válido."})

        return queryset



class AuctionRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrAdmin] 
    queryset = Auction.objects.all()
    serializer_class = AuctionDetailSerializer

# --- Pujas (Bids) ---
class BidListCreate(generics.ListCreateAPIView):
    serializer_class = BidListCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_auction(self):
        return get_object_or_404(Auction, pk=self.kwargs["auction_id"])

    def get_queryset(self):
        auction = self.get_auction()
        return Bid.objects.filter(auction=auction).order_by('-price')

    def perform_create(self, serializer):
        auction = self.get_auction()

        # Validación de subasta abierta
        if auction.closing_date <= timezone.now():
            raise ValidationError("No se puede pujar. La subasta ya ha cerrado.")

        # Validación de precio mayor a la puja anterior
        last_bid = Bid.objects.filter(auction=auction).order_by('-price').first()
        new_price = serializer.validated_data.get('price')
        if new_price <= 0:
            raise ValidationError("La puja debe ser un número positivo.")

        if last_bid and new_price <= last_bid.price:
            raise ValidationError(f"La puja debe ser mayor que la actual: {last_bid.price}€.")

        # Guardar la puja
        serializer.save(auction=auction, bidder=self.request.user)

class BidRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BidDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        self.auction = get_object_or_404(Auction, pk=self.kwargs["auction_id"])
        return Bid.objects.filter(auction=self.auction, bidder=self.request.user)

    def perform_update(self, serializer):
        # Solo permitir editar si la subasta sigue abierta
        if self.auction.closing_date <= timezone.now():
            raise ValidationError("No puedes editar la puja. La subasta ya ha cerrado.")

        last_bid = Bid.objects.filter(auction=self.auction).exclude(pk=self.get_object().pk).order_by('-price').first()
        new_price = serializer.validated_data.get('price')

        if new_price <= 0:
            raise ValidationError("La puja debe ser un número positivo.")

        if last_bid and new_price <= last_bid.price:
            raise ValidationError(f"La puja debe ser mayor que la actual: {last_bid.price}€.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.auction.closing_date <= timezone.now():
            raise ValidationError("No puedes eliminar la puja. La subasta ya ha cerrado.")
        instance.delete()


class UserAuctionListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Obtener las subastas del usuario autenticado
        user_auctions = Auction.objects.filter(auctioneer=request.user)
        serializer = AuctionListCreateSerializer(user_auctions, many=True)
        return Response(serializer.data)
    
class UserBidListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_bids = Bid.objects.filter(bidder=request.user).order_by('-price')
        serializer = BidListCreateSerializer(user_bids, many=True)
        return Response(serializer.data)

class RatingListCreate(generics.ListCreateAPIView):
    """
    GET  /api/ratings/?auction=<id>  → lista el rating del usuario para esa subasta (o vacío)
    POST /api/ratings/               → crea un rating (user se añade en perform_create)
    """
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Rating.objects.filter(user=self.request.user)
        auction_id = self.request.query_params.get('auction')
        if auction_id:
            qs = qs.filter(auction_id=auction_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RatingRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE  /api/ratings/<pk>/  → operaciones sobre el rating propio
    """
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)
    
class CommentListCreate(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Listado de comentarios de una subasta concreta
        auction = get_object_or_404(Auction, pk=self.kwargs['auction_id'])
        return Comment.objects.filter(auction=auction)

    def perform_create(self, serializer):
        auction = get_object_or_404(Auction, pk=self.kwargs['auction_id'])
        serializer.save(user=self.request.user, auction=auction)


class CommentRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        auction = get_object_or_404(Auction, pk=self.kwargs['auction_id'])
        return Comment.objects.filter(auction=auction)