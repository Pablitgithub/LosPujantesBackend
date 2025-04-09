from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from .models import Category, Auction, Bid
from .serializers import (
    CategoryListCreateSerializer, CategoryDetailSerializer,
    AuctionListCreateSerializer, AuctionDetailSerializer,
    BidListCreateSerializer, BidDetailSerializer
)
from django.db.models import Q
from rest_framework.exceptions import ValidationError


# --- Categorías ---
class CategoryListCreate(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListCreateSerializer

class CategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer

# --- Subastas ---
class AuctionListCreate(generics.ListCreateAPIView):
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
    queryset = Auction.objects.all()
    serializer_class = AuctionDetailSerializer

# --- Pujas (Bids) ---
class BidListCreate(generics.ListCreateAPIView):
    serializer_class = BidListCreateSerializer

    def get_queryset(self):
        self.auction = get_object_or_404(Auction, pk=self.kwargs["auction_id"])
        return Bid.objects.filter(auction=self.auction)

    def perform_create(self, serializer):
        serializer.save(auction=self.auction)

class BidRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BidDetailSerializer

    def get_queryset(self):
        self.auction = get_object_or_404(Auction, pk=self.kwargs["auction_id"])
        return Bid.objects.filter(auction=self.auction)
