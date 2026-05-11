
from django.shortcuts import get_object_or_404, render, redirect
from .models import Tarea

def home(request):
    # Asegúrate de que el nombre sea 'tareas' para que coincida con tu HTML
    tareas = Tarea.objects.all() 
    return render(request, 'ventas/home.html', {'tareas': tareas}) 

def finalizar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    tarea.completada = True
    tarea.save()
    return redirect('home')