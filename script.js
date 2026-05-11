document.addEventListener('DOMContentLoaded', () => {
    const formularios = document.querySelectorAll('.form-finalizar');

    formularios.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Buscamos elementos dentro de la fila actual
            const fila = this.closest('tr');
            const boton = this.querySelector('.btn-finalizar');
            const celdaEstatus = fila.querySelector('.estatus-texto');
            const celdaEstado = fila.querySelector('.estado-dinamico');

            // Cambio visual inmediato
            boton.textContent = 'Finalizada';
            boton.classList.add('completado');
            boton.disabled = true;

            if (celdaEstatus) {
                celdaEstatus.textContent = 'Completada';
                celdaEstatus.classList.add('actualizado');
            }

            if (celdaEstado) {
                celdaEstado.textContent = 'En revisión';
                celdaEstado.classList.add('revision');
            }
            
            // El formulario se envía a Django normalmente después de esto
        });
    });
});