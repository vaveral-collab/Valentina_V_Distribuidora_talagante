# core/forms.py
from django import forms
from .models import Producto
from decimal import Decimal


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo_barras', 
            'nombre', 
            'categoria', 
            'descripcion',           # lo agregué por si lo usas en el futuro
            'precio', 
            'stock',
            'unidad_medida', 
            'tamano_paquete', 
            'producto_hijo',
            'fecha_vencimiento', 
            'imagen', 
            'activo',
            'es_granel'              # ← CAMPO AGREGADO AQUÍ
        ]
        
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'stock': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}), # Cambiado a 'any'
            'tamano_paquete': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}), # Cambiado a 'any'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuración para código de barras
        if not self.instance.pk:
            self.fields['codigo_barras'].required = False
            self.fields['codigo_barras'].help_text = "Se generará automáticamente (ej: MAN-00123)"
            self.fields['codigo_barras'].widget.attrs['placeholder'] = "Dejar vacío para autogenerar"
        else:
            self.fields['codigo_barras'].widget.attrs['readonly'] = True 

        # Forzar precio entero en edición
        if self.instance.pk and self.instance.precio:
            self.initial['precio'] = int(self.instance.precio)
        
        self.fields['precio'].widget.attrs.update({
            'step': '1',
            'min': '0',
            'class': 'form-control text-end',
            'placeholder': '15000'
        })

        # Configuración del campo es_granel (para que se vea bien)
        self.fields['es_granel'].label = "Es producto a granel (se vende por kilogramos)"
        self.fields['es_granel'].help_text = "Activa esto para queso, arroz, carne, harina, etc. (permite cantidades decimales)"

    # ==================== MÉTODOS CLEAN ====================
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None:
            try:
                precio_entero = int(float(precio))
                if precio_entero < 0:
                    raise forms.ValidationError("El precio no puede ser negativo.")
                return precio_entero
            except (ValueError, TypeError):
                raise forms.ValidationError("Ingresa un precio válido (solo números enteros).")
        return precio

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None:
            try:
                # Convertimos a Decimal pero sin forzar los .000
                stock_decimal = Decimal(str(stock))
                
                if stock_decimal < 0:
                    raise forms.ValidationError("El stock no puede ser negativo.")
                
                # Esto elimina ceros a la derecha innecesarios (9.000 -> 9)
                return stock_decimal.normalize() 
                
            except (ValueError, TypeError):
                raise forms.ValidationError("Ingresa un stock válido.")
        return stock

    def clean_tamano_paquete(self):
        tamano = self.cleaned_data.get('tamano_paquete')
        if tamano is not None:
            try:
                # CAMBIO: Usar normalize() en lugar de quantize
                tamano_decimal = Decimal(str(tamano)).normalize()
                if tamano_decimal <= 0:
                    raise forms.ValidationError("El tamaño del paquete debe ser mayor a 0.")
                return tamano_decimal
            except (ValueError, TypeError):
                raise forms.ValidationError("Ingresa un valor válido.")
        return tamano


# ==================== OTROS FORMULARIOS (sin cambios) ====================

class EscaneoEntradaForm(forms.Form):
    codigo_barras = forms.CharField(max_length=50, widget=forms.HiddenInput())
    cantidad = forms.DecimalField(
        label="Cantidad",
        min_value=Decimal('0.001'),
        decimal_places=3,
        initial=Decimal('1'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'step': 'any',
            'autofocus': True,
            'placeholder': 'Ej: 10, 12.5, 1',
            'style': 'font-size: 2rem; height: 80px;'
        })
    )


class ProductoRapidoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio', 'unidad_medida', 'fecha_vencimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '1', 'placeholder': 'Precio en pesos'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'precio': 'Precio (CLP)',
        }


class ConfigurarPaqueteForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['tamano_paquete', 'producto_hijo']
        widgets = {
            'tamano_paquete': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'producto_hijo': forms.Select(attrs={'class': 'form-select'}),
        }