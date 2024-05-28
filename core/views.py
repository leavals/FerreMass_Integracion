from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, Category, Order, OrderItem, Payment, User
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer, OrderItemSerializer, PaymentSerializer, UserSerializer, RegisterSerializer
from .permissions import IsClienteOrAdmin, IsVendedorOrBodeguero, IsContador
from rest_framework.views import APIView
from rest_framework.response import Response

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsClienteOrAdmin]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsVendedorOrBodeguero]

    def get_permissions(self):
        if self.request.method in ['GET', 'PATCH']:
            self.permission_classes = [IsAuthenticated, IsVendedorOrBodeguero]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role not in ['vendedor', 'bodeguero']:
            return Response({'detail': 'No permission to update this order.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.filter(metodo='transferencia')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsContador]

    def update(self, request, *args, **kwargs):
        if not request.user.role == 'contador':
            return Response({'detail': 'No permission to update this payment.'}, status=403)
        return super().update(request, *args, **kwargs)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
