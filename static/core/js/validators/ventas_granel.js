function aplicarCalculo() {
    const montoTexto = document.getElementById('input-monto-dinero').value.trim();
    const monto = parseFloat(montoTexto);

    if (!productoIdActual || isNaN(monto) || monto <= 0) {
        alert("Por favor ingresa un monto válido mayor a 0");
        return;
    }

    // Función para obtener CSRF token de la cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const formData = new FormData();
    formData.append('monto', monto);  // Enviamos el monto en pesos

    fetch(`/add_to_carrito/${productoIdActual}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok || response.redirected) {
            // Si la respuesta es exitosa o hay redirección, vamos al carrito
            window.location.href = '/carrito/';
        } else {
            alert("Error al agregar al carrito. Código: " + response.status);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error de conexión");
    });
}