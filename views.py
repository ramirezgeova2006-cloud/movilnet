"""
SISTEMA DE GESTIÓN DE ACTIVIDADES 
Descripción: Gestión de autenticación, registro con restricciones robustas y Dashboard.
"""

import re  # Módulo para Expresiones Regulares
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages 
from django.shortcuts import render, redirect, get_object_or_404
from .models import Proyecto, Task
from .forms import ProyectoForm, TaskForm, ManagerTaskForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q


# 1. VISTA DE LOGIN
def login_usuario(request):
    error = None
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('password')
        
        # El sistema aplica el algoritmo de cifrado y compara el hash
        user = authenticate(request, username=usuario, password=clave)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error = "Correo o contraseña incorrectos."

    return render(request, 'ventas/index.html', {'error': error})

# 2. VISTA DE REGISTRO CON RESTRICCIONES ACTUALIZADAS
def registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        correo_web = request.POST.get('correo') 
        clave_web = request.POST.get('pass1') 

        # --- RESTRICCIONES DE DOMINIO (VALIDACIONES) ---
        
        # 1. Restricción: Nombre (Solo letras y espacios)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            messages.error(request, 'El nombre solo puede contener letras.')
            return render(request, 'ventas/registro.html')

        # 2. Restricción: Apellido (Solo letras y espacios) - ¡CORREGIDO!
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', apellido):
            messages.error(request, 'El apellido solo puede contener letras.')
            return render(request, 'ventas/registro.html')

        # 3. Restricción: Estructura de correo válida
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', correo_web):
            messages.error(request, 'Formato de correo inválido.')
            return render(request, 'ventas/registro.html')

        # 4. Restricción: Contraseña Robusta - ¡ACTUALIZADO!
        # Requisitos: Mínimo 8 caracteres, letras, números y al menos un símbolo (punto, coma, @, etc.)
        regex_clave = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[.!@#$%^&*(),?":{}|<>]).{8,}$'
        if not re.match(regex_clave, clave_web):
            messages.error(request, 'La clave debe tener al menos 8 caracteres, letras, números y un símbolo (.,@#).')
            return render(request, 'ventas/registro.html')

        # --- PERSISTENCIA Y SEGURIDAD ---
        if correo_web and clave_web:
            # Verifica si el usuario ya existe
            if not User.objects.filter(username=correo_web).exists():
                
                # create_user genera automáticamente el HASH de seguridad
                nuevo_usuario = User.objects.create_user(
                    username=correo_web,
                    email=correo_web,
                    password=clave_web, 
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo_usuario.save() # Guarda en PostgreSQL
                
                messages.success(request, '🚀 ¡Cuenta creada con éxito! Ya puedes entrar.')
                return redirect('login_usuario') 
            else:
                messages.error(request, 'Este correo ya está registrado.')
    
    return render(request, 'ventas/registro.html')

# 3. VISTA DEL HOME
@login_required
def home(request):
    proyectos = []
    if request.user.is_authenticated:
        proyectos = Proyecto.objects.filter(activo=True)
        return render(request, 'ventas/home.html', {'proyectos': proyectos})
    else:
        return redirect('login_usuario')

# 4. VISTA DE LOGOUT
def cerrar_sesion(request):
    logout(request)
    return redirect('login_usuario')

@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            # --- Para que el sistema guarde el proyecto vinculado a la base de datos 
            proyecto = form.save()
            messages.success(request, '✅ Proyecto creado con éxito.')
            return redirect('home')
    else:
        form = ProyectoForm()
    return render(request, 'ventas/crear_proyecto.html', {'form': form})
    
def asignar_tarea(request, proyecto_id):
    proyecto =  get_object_or_404(Proyecto, id=proyecto_id)
    if request.method == 'POST':
        from_t = ManagerTaskForm(request.POST)
        if from_t.is_valid():
            tarea = from_t.save(commit=False)
            tarea.proyecto = proyecto
            tarea.created_by = request.user
            tarea.column ='POR_HACER'
            tarea.save()
            messages.success(request, f'✅ Tarea "{tarea.title}" asignada correctamente.')
            return redirect('home')
    else:
        from_t = ManagerTaskForm()

    return render(request, 'ventas/asignar_tareas.html', {
        'from_t': from_t,
        'proyecto': proyecto,
    })

@login_required
def lista_devs(request):
    usuarios = User.objects.annotate(
        total_tareas=Count('assigned_tasks'),
        tareas_pendientes=Count('assigned_tasks', filter=Q(assigned_tasks__column='POR_HACER')),
        tareas_en_proceso=Count('assigned_tasks', filter=Q(assigned_tasks__column='EN_PROCESO')),
        tareas_en_revision=Count('assigned_tasks', filter=Q(assigned_tasks__column='EN_REVISION')),
        tareas_finalizadas=Count('assigned_tasks', filter=Q(assigned_tasks__column='LISTO'))
    ).order_by('-total_tareas')
    
    return render(request, 'ventas/desarrolladores.html', {'usuarios': usuarios})

# 5. EDICIÓN DEL PROYECTO
def editar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if request.method == "POST":
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProyectoForm(instance=proyecto)
    return render(request, 'ventas/editar_proyecto.html', {'form': form, 'proyecto': proyecto})

# 6. INHABILITACION DEL PROYECTO
def inhabilitar_proyecto(request, pk):
    proyecto = get_object_or_404 (Proyecto, pk=pk)
    if request.method == "POST":
        proyecto.activo = False
        proyecto.save()
        return redirect('home')
        
def proyectos_inhabilitados(request):
    cancelados = Proyecto.objects.filter(activo=False)
    return render(request, 'ventas/cancelados.html',{'proyectos':cancelados})

def restaurar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if request.method == "POST":
        proyecto.activo = True
        proyecto.save()
        return redirect('proyectos_inhabilitados')
    
    return redirect('proyectos_inhabilitados') 

#Panel del desarollador
@login_required
def panel_desarrollador(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    # Si el desarrollador envía el formulario para crear una tarea
    if request.method == 'POST':
        form_tarea = TaskForm(request.POST)
        if form_tarea.is_valid():
            tarea = form_tarea.save(commit=False)
            tarea.proyecto = proyecto
            tarea.created_by = request.user
            tarea.save()
            messages.success(request, 'Tarea creada exitosamente.')
            return redirect('panel_desarrollador', proyecto_id=proyecto.id)
    else:
        form_tarea = TaskForm()
    
    # Obtener todas las tareas del proyecto
    tareas = Task.objects.filter(proyecto=proyecto)
    
    return render(request, 'ventas/desarrollador.html', {
        'proyecto': proyecto,
        'tareas': tareas,
        'form_tarea': form_tarea,
    })

# 7. ELIMINACIÓN DEL PROYECTO 
@login_required
def eliminar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if request.method == 'POST':
        nombre = proyecto.nombre
        proyecto.delete()
        messages.success(request, f'🗑️ Proyecto "{nombre}" eliminado correctamente.')
    return redirect('home')

@login_required
def eliminar_tarea(request, pk):
    tarea = get_object_or_404(Task, pk=pk)
    proyecto_id = tarea.proyecto.id
    if request.method == 'POST':
        # Un desarrollador solo puede borrar tareas que él mismo creó (y que no sean del gerente).
        # Un gerente (is_staff) puede borrar cualquier tarea.
        if request.user.is_staff or (tarea.created_by == request.user and not tarea.created_by.is_staff):
            tarea.delete()
            messages.success(request, '🗑️ Tarea eliminada correctamente.')
        else:
            messages.error(request, '⛔ No tienes permiso para eliminar esta tarea porque fue establecida por el gerente.')
    return redirect('panel_desarrollador', proyecto_id=proyecto_id)

@login_required
def finalizar_tarea(request, pk):
    tarea = get_object_or_404(Task, pk=pk)
    proyecto_id = tarea.proyecto.id
    if request.method == 'POST':
        tarea.column = 'EN_REVISION'
        tarea.save()
        messages.success(request, 'Tarea enviada a revisión.')
    return redirect('panel_desarrollador', proyecto_id=proyecto_id)

@login_required
def revision_tareas(request):
    # Obtener todas las tareas que están esperando revisión
    tareas_revision = Task.objects.filter(column='EN_REVISION').order_by('-id')
    return render(request, 'ventas/revision_tareas.html', {'tareas': tareas_revision})

@login_required
def aprobar_tarea(request, pk):
    tarea = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        tarea.column = 'LISTO'
        tarea.save()
        messages.success(request, f'✅ Tarea "{tarea.title}" aprobada y finalizada.')
    return redirect('revision_tareas')
