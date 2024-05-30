import logging
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, Category, Order, OrderItem, Payment, User
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer, OrderItemSerializer, PaymentSerializer, UserSerializer, RegisterSerializer
from .permissions import IsClienteOrAdmin, IsVendedorOrBodeguero, IsContador
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

logger = logging.getLogger(__name__)

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
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['GET', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAuthenticated, IsVendedorOrBodeguero]
        elif self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsClienteOrAdmin]  # Solo clientes y admins pueden crear órdenes
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user)

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
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['GET', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAuthenticated, IsContador]
        elif self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsClienteOrAdmin]  # Solo clientes y admins pueden registrar pagos
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save()

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

@csrf_exempt
def save_transaction(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received data: {data}")
            
            # Verificar que los datos de PayPal están presentes
            username = data.get('username')
            if not username:
                return JsonResponse({'success': False, 'error': 'Username is required'}, status=400)
            
            cliente = User.objects.get(username=username)

            order_id = data.get('orderID')
            if not order_id:
                return JsonResponse({'success': False, 'error': 'Order ID is required'}, status=400)

            # Crear una nueva orden si no existe
            orden, created = Order.objects.get_or_create(
                cliente=cliente,
                estado='pendiente',
                defaults={
                    'direccion_envio': data.get('direccion_envio', ''),
                    'retiro_en_tienda': data.get('retiro_en_tienda', False)
                }
            )
            
            # Si la orden fue creada, agregar los items del carrito
            if created:
                for item in data['cartItems']:
                    producto = Product.objects.get(id_pro=item['id'])
                    OrderItem.objects.create(
                        orden=orden,
                        producto=producto,
                        cantidad=item['cantidad']
                    )
                orden.calculate_total()
                orden.save()

            # Obtener detalles del pago
            payment_details = data.get('paymentDetails', {})
            if 'purchase_units' not in payment_details or not payment_details['purchase_units']:
                return JsonResponse({'success': False, 'error': 'Payment details are incomplete'}, status=400)

            purchase_unit = payment_details['purchase_units'][0]
            amount_details = purchase_unit.get('amount', {})
            payment_method = amount_details.get('currency_code')
            payment_status = payment_details.get('status')
            payment_value = amount_details.get('value')

            detalles = f"Pago realizado con éxito. Monto: {payment_value} {payment_method}." if payment_status == 'COMPLETED' else 'Pago fallido.'

            Payment.objects.create(
                orden=orden,
                metodo=payment_method,
                monto=payment_value,
                confirmado='Confirmado' if payment_status == 'COMPLETED' else 'Por Pagar',
                detalles=detalles
            )

            return JsonResponse({'success': True})
        except User.DoesNotExist:
            logger.error(f"User does not exist: {username}")
            return JsonResponse({'success': False, 'error': 'User does not exist'}, status=404)
        except Product.DoesNotExist:
            logger.error(f"Product does not exist")
            return JsonResponse({'success': False, 'error': 'Product does not exist'}, status=404)
        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
