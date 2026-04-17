import re
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal
import datetime
from datetime import timedelta
import random
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import transaction


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nombre = models.CharField("Nombre(s)", max_length=70)
    apellido_paterno = models.CharField("Apellido Paterno", max_length=50)
    apellido_materno = models.CharField("Apellido Materno", max_length=50, blank=True, null=True)
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[RegexValidator(regex=r'^\d{7,8}-[\dKk]$', message='Formato RUT inválido')],
        help_text="Ejemplo: 11527103-2"
    )
    telefono = models.CharField(max_length=15, blank=True, null=True)
    es_admin = models.BooleanField(default=False)

    temp_token = models.CharField(max_length=100, blank=True, null=True)
    token_expira = models.DateTimeField(blank=True, null=True)

    def nombre_completo(self):
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"
    nombre_completo.short_description = "Nombre Completo"

    def __str__(self):
        return self.nombre_completo()

    class Meta:
        verbose_name_plural = "Perfiles"


class UnidadMedida(models.TextChoices):
    KG = 'KG', 'Kilogramos'
    UN = 'UN', 'Unidad / Bolsa'
    CJ = 'CJ', 'Caja'

class Producto(models.Model):
    codigo_barras = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Se genera automáticamente si lo dejas vacío"
    )
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    
    unidad_medida = models.CharField(
        max_length=2, 
        choices=UnidadMedida.choices, 
        default=UnidadMedida.UN
    )
    
    # === CAMPOS NUEVOS PARA SOPORTE DE GRANEL ===
    es_granel = models.BooleanField(
        default=False,
        verbose_name="¿Es producto a granel (se vende por kilogramos)?"
    )
    
    # Precio: 
    # - Si es_granel = False → Precio por unidad
    # - Si es_granel = True  → Precio por kilogramo
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="Precio"
    )
    
    stock = models.DecimalField(
        max_digits=12, 
        decimal_places=3, 
        default=Decimal('0.000')
    )
    
    tamano_paquete = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        default=Decimal('1.000'), 
        help_text="Ej: 10 para caja de 10 unidades"
    )
    
    producto_hijo = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='productos_padre'
    )

    fecha_vencimiento = models.DateField(null=True, blank=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.es_granel:
            return f"{self.nombre} (GRANEL - ${self.precio}/kg)"
        return f"{self.nombre} [{self.codigo_barras or 'Sin código'}]"

    def get_precio_display(self):
        """Método útil para templates"""
        if self.es_granel:
            return f"${self.precio:,}".replace(',', '.') + " / kg"
        return f"${self.precio:,}".replace(',', '.')
        
    def save(self, *args, **kwargs):
            if not self.codigo_barras:
                # Guarda temporalmente para obtener ID
                super().save(*args, **kwargs)
                # Genera código basado en el ID
                id_str = str(self.id).zfill(9)
                self.codigo_barras = f"789{id_str}0"
                # Actualiza solo el campo código
                super().save(update_fields=['codigo_barras'])
            else:
                super().save(*args, **kwargs)

#Calcular gramos por valor ingresado para descontarlos del stock
    def calcular_cantidad_kg(self, monto_dinero):
        """Calcula kg de forma precisa a partir de un monto"""
        if not self.es_granel or self.precio <= 0:
            return Decimal('0.000')
        
        try:
            monto = Decimal(monto_dinero).quantize(Decimal('0.01'))
            cantidad = monto / self.precio
            return cantidad.quantize(Decimal('0.001'), rounding='ROUND_HALF_UP')
        except:
            return Decimal('0.000')

    def bajo_stock(self):
        return self.stock < Decimal('10.000')

    def agregar_stock(self, cantidad: Decimal):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")
        self.stock += cantidad
        self.save(update_fields=['stock'])
        if self.producto_hijo:
            self.producto_hijo.agregar_stock(cantidad * self.tamano_paquete)

    def restar_stock(self, cantidad: Decimal):
        if cantidad <= 0 or self.stock < cantidad:
            raise ValueError("Stock insuficiente")
        self.stock -= cantidad
        self.save(update_fields=['stock'])
        if self.producto_hijo:
            self.producto_hijo.restar_stock(cantidad * self.tamano_paquete)


class Carrito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    # Cantidad en kg o unidades (con 3 decimales para granel)
    cantidad = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=Decimal('1.000')
    )
    
    # NUEVOS CAMPOS PARA MANEJO DE PRODUCTOS GRANEL POR MONTO
    monto_pesos = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Monto en pesos ingresado por el cliente (solo para productos granel)"
    )
    es_personalizado = models.BooleanField(
        default=False,
        help_text="True si el ítem fue agregado por monto (ej: $5.000 de queso)"
    )
    
    class Meta:
        unique_together = ('carrito', 'producto')
    
    def __str__(self):
        if self.es_personalizado and self.monto_pesos:
            return f"${self.monto_pesos} - {self.producto.nombre} (personalizado)"
        if self.producto.es_granel:
            return f"{self.cantidad} kg × {self.producto.nombre}"
        return f"{int(self.cantidad)} × {self.producto.nombre}"


# ==================== ORDEN ====================
class Orden(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente de Pago'),
        ('confirmacion', 'En Confirmación'),
        ('preparacion', 'En Preparación'),
        ('despacho', 'En Despacho / Listo para Retiro'),
        ('cancelado', 'Cancelado'),
        ('completado', 'Completado'),
    ]
    METODOS_PAGO = [
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Pago en Efectivo (Retiro)'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='transferencia')
    instrucciones_transferencia = models.TextField(default="Realice transferencia a Cuenta Corriente XXXX-XXXX y envíe comprobante por WhatsApp.")

    comprobante_b64 = models.TextField(blank=True, null=True, verbose_name="Comprobante (Base64)")
    nota_comprobante = models.TextField(blank=True, null=True)
    mensaje_cliente = models.TextField(blank=True, help_text="Mensaje opcional del cliente")

    def __str__(self):
        return f"Orden #{self.id} - {self.usuario.username}"

    def get_whatsapp_link(self):
        if hasattr(self.usuario, 'perfil') and self.usuario.perfil.telefono:
            telefono = re.sub(r'[^\d]', '', self.usuario.perfil.telefono)
            if telefono.startswith('56') and len(telefono) == 11:
                telefono = telefono[2:]
            elif len(telefono) == 9:
                telefono = '56' + telefono
            else:
                telefono = telefono.lstrip('0')
            return f"https://wa.me/{telefono}"
        return "https://wa.me/56949071013"

    def save(self, *args, **kwargs):
        # Solo actuamos si la orden ya existe (es una actualización)
        if self.pk is not None:
            old = Orden.objects.get(pk=self.pk)

            # =============================================================
            # CASO 1: Se cambia a "preparacion" → DESCONTAR stock (solo aquí)
            # =============================================================
            if old.estado != 'preparacion' and self.estado == 'preparacion':
                print(f"[STOCK] Orden #{self.pk} → PREPARACIÓN - Descontando stock")

                with transaction.atomic():
                    for item in self.itemorden_set.all():
                        # Protección contra descuentos duplicados
                        if getattr(item, 'stock_descontado', False):
                            print(f"  - {item.producto.nombre}: YA ESTABA DESCONTADO → omitiendo")
                            continue

                        if item.es_personalizado and item.monto_pesos:
                            # === Producto personalizado ===
                            kg_a_descontar = (item.monto_pesos / item.producto.precio).quantize(Decimal('0.001'))

                            if kg_a_descontar > item.producto.stock:
                                raise ValueError(f"Stock insuficiente para {item.producto.nombre}")

                            item.producto.stock -= kg_a_descontar
                            item.producto.save()

                            item.cantidad_real_entregada = kg_a_descontar
                            item.stock_descontado = True
                            item.save(update_fields=['cantidad_real_entregada', 'stock_descontado'])

                            print(f"  ✅ DESCONTADO (personalizado): {item.producto.nombre} → -{kg_a_descontar} kg")

                        elif not item.es_personalizado:
                            # === Producto unitario / por kg ===
                            if item.cantidad > item.producto.stock:
                                raise ValueError(f"Stock insuficiente para {item.producto.nombre}")

                            item.producto.stock -= item.cantidad
                            item.producto.save()

                            item.stock_descontado = True
                            item.save(update_fields=['stock_descontado'])

                            print(f"  ✅ DESCONTADO (unitario): {item.producto.nombre} → -{item.cantidad} unidades")

            # =============================================================
            # CASO 2: Se cambia a "cancelado" → DEVOLVER TODO el stock
            # =============================================================
            elif old.estado == 'preparacion' and self.estado == 'cancelado':
                print(f"[CANCELACIÓN] Orden #{self.pk} - Restaurando stock completo")

                with transaction.atomic():
                    for item in self.itemorden_set.all():
                        if getattr(item, 'stock_descontado', False):
                            if item.es_personalizado and item.cantidad_real_entregada:
                                item.producto.stock += item.cantidad_real_entregada
                                print(f"  ✅ RESTAURADO (personalizado): {item.producto.nombre} → +{item.cantidad_real_entregada} kg")
                            elif not item.es_personalizado:
                                item.producto.stock += item.cantidad
                                print(f"  ✅ RESTAURADO (unitario): {item.producto.nombre} → +{item.cantidad} unidades")

                            item.producto.save()
                            item.stock_descontado = False
                            item.save(update_fields=['stock_descontado'])
                        else:
                            print(f"  - {item.producto.nombre}: no tenía stock descontado")

        # Guardamos la orden normalmente
        super().save(*args, **kwargs)


class ItemOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='itemorden_set')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        default=Decimal('0.000'),
        help_text="Cantidad en kg (3 decimales para gramos)"
    )
    precio = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # NUEVOS CAMPOS PARA PERSONALIZADOS
    es_personalizado = models.BooleanField(default=False)
    monto_pesos = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    cantidad_real_entregada = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True,
        help_text="Cantidad real en kg (solo para pedidos personalizados)"
    )

    # ←←← ESTE CAMPO FALTABA
    stock_descontado = models.BooleanField(
        default=False,
        help_text="Indica si ya se descontó stock de este ítem"
    )

    def __str__(self):
        if self.es_personalizado and self.monto_pesos:
            return f"${self.monto_pesos} - {self.producto.nombre} (personalizado)"
        return f"{self.cantidad} kg x {self.producto.nombre}"

    class Meta:
        verbose_name = "Ítem de Orden"
        verbose_name_plural = "Ítems de Orden"


# ==================== SEÑAL DE RESTAURACIÓN ====================
@receiver(post_delete, sender=ItemOrden)
def restaurar_stock_al_eliminar_item(sender, instance, **kwargs):
    """
    Restaura stock cuando se elimina manualmente un ítem (desde el admin).
    No se ejecuta al vaciar el carrito porque esos ítems no tienen orden asociada? 
    En realidad se ejecuta, pero como los ítems del carrito no tienen campos personalizados, 
    se maneja con la lógica de cantidad.
    """
    if not instance.producto:
        return

    # Caso 1: Ítem personalizado con cantidad_real_entregada (ya se descontó stock)
    if instance.es_personalizado and instance.cantidad_real_entregada:
        try:
            stock_a_restaurar = instance.cantidad_real_entregada.quantize(Decimal('0.001'))
            instance.producto.stock = (instance.producto.stock + stock_a_restaurar).quantize(Decimal('0.001'))
            instance.producto.save(update_fields=['stock'])
            print(f"[STOCK RESTAURADO] +{stock_a_restaurar} kg de {instance.producto.nombre} (personalizado)")
        except Exception as e:
            print(f"ERROR AL RESTAURAR STOCK (personalizado): {e}")

    # Caso 2: Ítem personalizado SIN cantidad_real_entregada → nunca se descontó stock, no hacer nada
    elif instance.es_personalizado and not instance.cantidad_real_entregada:
        print(f"[INFO] Ítem personalizado sin cantidad_real_entregada: {instance.producto.nombre} - no se restaura stock")

    # Caso 3: Ítem no personalizado (normal o granel por kg) → se descontó stock al crear la orden
    elif not instance.es_personalizado and instance.cantidad > 0:
        try:
            stock_a_restaurar = instance.cantidad.quantize(Decimal('0.001'))
            instance.producto.stock = (instance.producto.stock + stock_a_restaurar).quantize(Decimal('0.001'))
            instance.producto.save(update_fields=['stock'])
            print(f"[STOCK RESTAURADO] +{stock_a_restaurar} de {instance.producto.nombre}")
        except Exception as e:
            print(f"ERROR AL RESTAURAR STOCK: {e}")


class ConfiguracionHome(models.Model):
    fotos_carrusel = models.JSONField(default=list, blank=True, null=True)
    numero_contacto = models.CharField(max_length=15, default="56949071013")
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Configuración Home"


class CodigoVerificacion(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    expirado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)

    def es_valido(self):
        return not self.expirado and timezone.now() < self.creado_en + timedelta(minutes=10)
    



  # TODAS LAS COMUNAS RM (52)
COMUNAS_RM = [
    ('Alhué', 'Alhué'), ('Buin', 'Buin'), ('Calera de Tango', 'Calera de Tango'),
    ('Cerrillos', 'Cerrillos'), ('Cerro Navia', 'Cerro Navia'), ('Colina', 'Colina'),
    ('Conchalí', 'Conchalí'), ('Curacaví', 'Curacaví'), ('El Bosque', 'El Bosque'),
    ('El Monte', 'El Monte'), ('Estación Central', 'Estación Central'),
    ('Huechuraba', 'Huechuraba'), ('Independencia', 'Independencia'),
    ('Isla de Maipo', 'Isla de Maipo'), ('La Cisterna', 'La Cisterna'),
    ('La Florida', 'La Florida'), ('La Granja', 'La Granja'), ('La Pintana', 'La Pintana'),
    ('La Reina', 'La Reina'), ('Las Condes', 'Las Condes'), ('Lo Barnechea', 'Lo Barnechea'),
    ('Lo Espejo', 'Lo Espejo'), ('Lo Prado', 'Lo Prado'), ('Macul', 'Macul'),
    ('Maipú', 'Maipú'), ('María Pinto', 'María Pinto'), ('Melipilla', 'Melipilla'),
    ('Ñuñoa', 'Ñuñoa'), ('Padre Hurtado', 'Padre Hurtado'), ('Paine', 'Paine'),
    ('Pedro Aguirre Cerda', 'Pedro Aguirre Cerda'), ('Peñaflor', 'Peñaflor'),
    ('Peñalolén', 'Peñalolén'), ('Pirque', 'Pirque'), ('Providencia', 'Providencia'),
    ('Pudahuel', 'Pudahuel'), ('Puente Alto', 'Puente Alto'), ('Quilicura', 'Quilicura'),
    ('Quinta Normal', 'Quinta Normal'), ('Recoleta', 'Recoleta'), ('Renca', 'Renca'),
    ('San Bernardo', 'San Bernardo'), ('San Joaquín', 'San Joaquín'),
    ('San José de Maipo', 'San José de Maipo'), ('San Miguel', 'San Miguel'),
    ('San Pedro', 'San Pedro'), ('San Ramón', 'San Ramón'), ('Santiago', 'Santiago'),
    ('Talagante', 'Talagante'), ('Til Til', 'Til Til'), ('Vitacura', 'Vitacura'),
]

# 1. DIRECCIONES GUARDADAS DEL CLIENTE (para usar después)
class DireccionGuardada(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direcciones')
    nombre = models.CharField("Ej: Casa, Trabajo, Mamá", max_length=100)
    calle = models.CharField("Calle", max_length=200)
    numero = models.CharField("Número / Depto", max_length=50, blank=True, null=True)
    comuna = models.CharField(max_length=100, choices=COMUNAS_RM)
    notas = models.TextField("Indicaciones", blank=True, null=True)
    predeterminada = models.BooleanField("Predeterminada", default=False)

    def save(self, *args, **kwargs):
        if self.predeterminada:
            DireccionGuardada.objects.filter(usuario=self.usuario).update(predeterminada=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.comuna}"

# 2. DIRECCIÓN DEL PEDIDO (una por orden)
class DireccionEnvio(models.Model):
    orden = models.OneToOneField('Orden', on_delete=models.CASCADE, related_name='direccion_envio')    
    METODO_CHOICES = [
        ('retiro', 'Retiro en local'),
        ('domicilio', 'Envío a domicilio'),
    ]
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES, default='retiro')
    
    calle = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=50, blank=True, null=True)
    comuna = models.CharField(max_length=100, choices=COMUNAS_RM, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.metodo == 'retiro':
            return "Retiro en local"
        return f"{self.calle} {self.numero}, {self.get_comuna_display()}"

 # MODELO PARA EL CARRUSEL (BANNER) ---
class Banner(models.Model):
    titulo = models.CharField(max_length=100, help_text="Texto alternativo para la imagen")
    imagen = models.ImageField(upload_to='banners/') 
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0, help_text="0 aparece primero, 1 segundo, etc.")

    def __str__(self):
        return self.titulo
