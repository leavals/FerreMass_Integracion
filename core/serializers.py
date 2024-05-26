from rest_framework import serializers
from .models import User, Product, Order, OrderItem, Payment, Category

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id_cat', 'nombre', 'descripcion']

class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id_pro', 'nombre', 'descripcion', 'precio', 'stock', 'categories']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'producto', 'cantidad', 'precio']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    cliente = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id_ord', 'cliente', 'items', 'fecha_orden', 'total', 'estado', 'direccion_envio', 'retiro_en_tienda']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id_pay', 'orden', 'metodo', 'monto', 'confirmado', 'fecha_pago']

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        return user
