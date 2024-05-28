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
    producto = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'producto', 'cantidad']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    cliente = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id_ord', 'cliente', 'items', 'fecha_orden', 'total', 'estado', 'direccion_envio', 'retiro_en_tienda']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(orden=order, **item_data)
        order.calculate_total()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        instance.estado = validated_data.get('estado', instance.estado)
        instance.direccion_envio = validated_data.get('direccion_envio', instance.direccion_envio)
        instance.retiro_en_tienda = validated_data.get('retiro_en_tienda', instance.retiro_en_tienda)
        instance.save()

        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(orden=instance, **item_data)

        instance.calculate_total()
        return instance

class PaymentSerializer(serializers.ModelSerializer):
    orden = OrderSerializer(read_only=True)  # Incluye los detalles de la orden

    class Meta:
        model = Payment
        fields = ['id_pay', 'orden', 'metodo', 'monto', 'confirmado', 'fecha_pago']
        read_only_fields = ['monto', 'metodo']  # Aseguramos que el monto y método sean de solo lectura

    def create(self, validated_data):
        validated_data['monto'] = validated_data['orden'].total
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'confirmado' in validated_data and self.context['request'].user.role == 'contador':
            instance.confirmado = validated_data['confirmado']
        instance.save()
        return instance

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
