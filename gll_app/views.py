from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib import messages

def index(request):
    gallos = Gallo.objects.all()
    return render(request, 'index.html', {'gallos': gallos})

def ver(request, nroPlaca):
    gallo = get_object_or_404(Gallo, nroPlaca=nroPlaca)
    return render(request, 'ver.html', {'gallo': gallo})

def crear(request):
    if request.method == 'POST':
        form = GalloForm(request.POST, request.FILES)
        if form.is_valid():
            gallo = form.save(commit=False)
            placa_padre = request.POST.get('placaPadre') or None
            placa_madre = request.POST.get('placaMadre') or None

            if placa_padre:
                gallo.placaPadre_id = placa_padre  # si es FK
            if placa_madre:
                gallo.placaMadre_id = placa_madre

            gallo.save()
            return redirect('index')
        else:
            print(form.errors)

    else:
        form = GalloForm()
    return render(request, 'formulario.html', {'form': form, 'gallos': Gallo.objects.exclude(nroPlaca=form.instance.nroPlaca if form.instance else None)})

def editar(request, nroPlaca):
    gallo = get_object_or_404(Gallo, nroPlaca=nroPlaca)

    if request.method == 'POST':
        form = GalloForm(request.POST, request.FILES, instance=gallo)
        if form.is_valid():
            # recuperamos los valores de los hidden inputs
            placa_padre = request.POST.get('placaPadre') or None
            placa_madre = request.POST.get('placaMadre') or None

            # validación de no ser iguales (y no ambos None)
            if placa_padre and placa_padre == placa_madre:
                messages.error(request, "Padre y madre no pueden ser el mismo.")
            else:
                gallo = form.save(commit=False)
                # asignamos las FKs manualmente
                gallo.placaPadre_id = placa_padre
                gallo.placaMadre_id = placa_madre
                gallo.save()
                return redirect('index')
    else:
        form = GalloForm(instance=gallo)

    # lista de gallos para poblar los modales (excluimos al propio)
    gallos = Gallo.objects.exclude(nroPlaca=gallo.nroPlaca)

    # para mostrar los padres ya seleccionados al entrar en edición
    contexto = {
        'form': form,
        'gallos': gallos,
        'padre_sel': gallo.placaPadre_id,
        'madre_sel': gallo.placaMadre_id,
    }
    return render(request, 'formulario.html', contexto)

def eliminar(request, nroPlaca):
    gallo = get_object_or_404(Gallo, nroPlaca=nroPlaca)
    gallo.delete()
    return redirect('index')



def crear_encuentro(request):
    if request.method == 'POST':
        form = EncuentroForm(request.POST, request.FILES)
        participantes_ids = request.POST.getlist('participantes')
        ganador_id = request.POST.get('ganador')

        # Validamos que haya al menos 2 participantes
        if len(participantes_ids) < 2:
            form.add_error(None, "Debe seleccionar al menos 2 participantes.")
        else:
            if form.is_valid():
                encuentro = form.save(commit=False)

                # Si hay ganador, lo asignamos; usamos .nroPlaca o .pk, no .id
                if ganador_id:
                    try:
                        ganador = Gallo.objects.get(pk=ganador_id)
                        if str(ganador.nroPlaca) not in participantes_ids:
                            form.add_error(None, "El ganador debe estar entre los participantes.")
                        else:
                            encuentro.ganador = ganador
                    except Gallo.DoesNotExist:
                        form.add_error(None, "El ganador seleccionado no existe.")

                # Si no hay errores, guardamos todo
                if not form.errors:
                    encuentro.save()
                    for id_gallo in participantes_ids:
                        gallo = Gallo.objects.get(pk=id_gallo)
                        ParticipantesEnEncuentro.objects.create(
                            idEncuentro=encuentro,
                            idParticipante=gallo
                        )
                    # Aquí usamos el name='listar_encuentros' de urls.py
                    return redirect('listar_encuentros')

        print(form.errors)  # Para debug en consola

    else:
        form = EncuentroForm()

    gallos = Gallo.objects.all()
    return render(request, 'encuentros/crear_encuentro.html', {
        'form': form,
        'gallos': gallos
    })

def listar_encuentros(request):
    encuentros = Encuentro.objects.all().order_by('-fechaYHora')
    return render(request, 'encuentros/listar_encuentros.html', {'encuentros': encuentros})
