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
from .models import Order, OrderItem, Product, Payment, User

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

@csrf_exempt
def save_transaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            username = data.get('username')
            if not username:
                return JsonResponse({'success': False, 'error': 'Username is required'}, status=400)
            
            cliente = User.objects.get(username=username)

            order_id = data.get('orderID')
            if not order_id:
                return JsonResponse({'success': False, 'error': 'Order ID is required'}, status=400)

            if not Order.objects.filter(id_ord=order_id).exists():
                orden = Order.objects.create(
                    id_ord=order_id,
                    cliente=cliente,
                    estado='aprobado'
                )
                for item in data['cartItems']:
                    producto = Product.objects.get(id_pro=item['id'])
                    OrderItem.objects.create(
                        orden=orden,
                        producto=producto,
                        cantidad=item['cantidad']
                    )
                orden.calculate_total()
                orden.save()
            else:
                orden = Order.objects.get(id_ord=order_id)
                orden.estado = 'aprobado'
                orden.save()

            payment_method = 'crédito'
            payment_status = data.get('paymentDetails', {}).get('status', 'FAILED')
            detalles = f"Pago realizado con éxito. Monto: {data['paymentDetails']['purchase_units'][0]['amount']['value']} {data['paymentDetails']['purchase_units'][0]['amount']['currency_code']}." if payment_status == 'COMPLETED' else 'Pago fallido.'

            Payment.objects.create(
                orden=orden,
                metodo=payment_method,
                monto=data['paymentDetails']['purchase_units'][0]['amount']['value'],
                confirmado='Confirmado' if payment_status == 'COMPLETED' else 'Por Pagar',
                detalles=detalles
            )

            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User does not exist'}, status=404)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product does not exist'}, status=404)
        except Exception as e:
            print(f"Error saving transaction: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)