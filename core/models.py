# models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Sum, F

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
        ('bodeguero', 'Bodeguero'),
        ('contador', 'Contador'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)

    objects = UserManager()

    def __str__(self):
        return self.username

class Category(models.Model):
    id_cat = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class Product(models.Model):
    id_pro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=100, null=True, blank=True)  # Añadir el campo marca
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    categories = models.ManyToManyField(Category, through='CategoryProduct')

    def __str__(self):
        return self.nombre

class CategoryProduct(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('category', 'product')

class Order(models.Model):
    id_ord = models.AutoField(primary_key=True)
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('preparado', 'Preparado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado')
    )

    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordenes')
    productos = models.ManyToManyField(Product, through='OrderItem')
    fecha_orden = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES)
    direccion_envio = models.CharField(max_length=255, null=True, blank=True)
    retiro_en_tienda = models.BooleanField(default=False)

    def calculate_total(self):
        total = self.items.aggregate(
            total=Sum(F('cantidad') * F('producto__precio'))
        )['total'] or 0
        self.total = total
        self.save()

    def __str__(self):
        return f'Orden {self.id_ord} - {self.cliente.username}'

class OrderItem(models.Model):
    orden = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.orden.calculate_total()

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre} en {self.orden}'

class Payment(models.Model):
    id_pay = models.AutoField(primary_key=True)
    orden = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='pago')
    metodo = models.CharField(max_length=50, choices=[('debito', 'Débito'), ('credito', 'Crédito'), ('transferencia', 'Transferencia')])
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    confirmado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.monto:
            self.monto = self.orden.total
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Pago de {self.orden.id_ord} - {self.metodo}'
