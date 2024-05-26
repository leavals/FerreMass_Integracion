import os
import django
import random
from datetime import datetime

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ferremassltv.settings')
django.setup()

# Importar modelos
from core.models import Category, Product, CategoryProduct

def crear_categorias_y_productos():
    # Estructura de datos con categorías y productos
    categorias = {
        'Herramientas': {
            'Herramientas Manuales': ['Martillos', 'Destornilladores', 'Llaves'],
            'Herramientas Eléctricas': ['Taladros', 'Sierras', 'Lijadoras']
        },
        'Materiales de Construcción': {
            'Materiales Básicos': ['Cemento', 'Arena', 'Ladrillos'],
            'Acabados': ['Pinturas', 'Barnices', 'Cerámicos']
        },
        'Equipos de Seguridad': ['Casos', 'Guantes', 'Lentes de Seguridad'],
        'Accesorios Varios': ['Tornillos y Anclajes', 'Fijaciones y Adhesivos', 'Equipos de Medición']
    }

    marcas = ['Bosch', 'Makita', 'Stanley', '3M', 'Samsung']

    for categoria_principal, subcategorias in categorias.items():
        if isinstance(subcategorias, dict):
            for subcategoria, productos in subcategorias.items():
                cat_obj, _ = Category.objects.get_or_create(nombre=subcategoria)
                crear_productos(cat_obj, productos, marcas)
        else:
            cat_obj, _ = Category.objects.get_or_create(nombre=categoria_principal)
            crear_productos(cat_obj, subcategorias, marcas)

def crear_productos(categoria, productos, marcas):
    for producto in productos:
        for _ in range(3):
            codigo_producto = f'{producto[:3].upper()}-{random.randint(100, 999)}'
            prod_obj = Product.objects.create(
                nombre=producto,
                descripcion=f'Descripción de {producto}',
                precio=random.randint(5000, 500000),
                stock=random.randint(1, 100)
            )
            # Añadir relación con categoría
            CategoryProduct.objects.create(category=categoria, product=prod_obj)

if __name__ == '__main__':
    crear_categorias_y_productos()
