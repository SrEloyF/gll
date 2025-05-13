from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
import os
from django.conf import settings
import pymysql
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import datetime

def export_db(request):
    db_settings = settings.DATABASES['default']
    connection = pymysql.connect(
        host=db_settings['HOST'],
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        db=db_settings['NAME']
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            output_file = os.path.join(settings.BASE_DIR, 'exported_db.sql')

            with open(output_file, 'w') as f:
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SHOW CREATE TABLE {table_name}")
                    create_table_statement = cursor.fetchone()[1]
                    f.write(f"{create_table_statement};\n\n")
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()

                    for row in rows:
                        values = ', '.join([str(value) for value in row])
                        f.write(f"INSERT INTO {table_name} VALUES ({values});\n")

            print(f"Base de datos exportada exitosamente a {output_file}")
        with open(output_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/sql')
            response['Content-Disposition'] = 'attachment; filename=exported_db.sql'
            return response
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

    finally:
        connection.close()

"""
def index(request):
    gallos = Gallo.objects.all()
    return render(request, 'index.html', {'gallos': gallos})
"""

def index(request):
    gallos = Gallo.objects.all()
    paginator = Paginator(gallos, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'index.html', {'page_obj': page_obj})

def ver(request, idGallo):
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    edadGallo = now().date() - gallo.fechaNac
    edadGallo = edadGallo.days / 365
    edadGallo = round(edadGallo, 1)
    return render(request, 'ver.html', {'gallo': gallo, 'edadGallo': edadGallo})

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
            return redirect('ver', idGallo=gallo.idGallo)
        else:
            print(form.errors)

    else:
        form = GalloForm()
    return render(request, 'formulario.html', {'form': form, 'gallos': Gallo.objects.exclude(nroPlaca=form.instance.nroPlaca if form.instance else None)})

def editar(request, idGallo):
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    if request.method == 'POST':
        form = GalloForm(request.POST, request.FILES, instance=gallo)
        if form.is_valid():
            placa_padre = request.POST.get('placaPadre') or None
            placa_madre = request.POST.get('placaMadre') or None

            if placa_padre and placa_padre == placa_madre:
                messages.error(request, "Padre y madre no pueden ser el mismo.")
            else:
                gallo = form.save(commit=False)
                gallo.placaPadre_id = placa_padre
                gallo.placaMadre_id = placa_madre
                gallo.save()
                return redirect('ver', idGallo=gallo.idGallo)
    else:
        form = GalloForm(instance=gallo)

    gallos = Gallo.objects.exclude(idGallo=gallo.idGallo)

    contexto = {
        'form': form,
        'gallos': gallos,
        'padre_sel': gallo.placaPadre_id,
        'madre_sel': gallo.placaMadre_id,
    }
    return render(request, 'formulario.html', contexto)

def eliminar(request, idGallo):
    gallo = get_object_or_404(Gallo, idGallo=idGallo)
    gallo.delete()
    return redirect('index')


#encuentros
def crear_encuentro(request):
    if request.method == 'POST':
        form = EncuentroForm(request.POST, request.FILES)
        id_gallo = request.POST.get('gallo')

        if not id_gallo:
            form.add_error(None, "Debe seleccionar un gallo participante.")
        else:
            try:
                gallo = Gallo.objects.get(pk=id_gallo)
            except Gallo.DoesNotExist:
                form.add_error(None, "El gallo seleccionado no existe.")
                gallo = None

            if form.is_valid() and gallo:
                encuentro = form.save(commit=False)
                encuentro.gallo = gallo
                encuentro.save()
                return redirect('ver_encuentro', pk=encuentro.idEncuentro)
            else:
                print(form.errors)
                print("Gallo: ", gallo)

    else:
        form = EncuentroForm()

    gallos = Gallo.objects.all()
    return render(request, 'encuentros/form_encuentro.html', {
        'form': form,
        'gallos': gallos
    })

"""
def listar_encuentros(request):
    encuentros = Encuentro.objects.all().order_by('-fechaYHora')
    return render(request, 'encuentros/listar_encuentros.html', {'encuentros': encuentros})
"""

def listar_encuentros(request):
    encuentros = Encuentro.objects.all().order_by('-fechaYHora')
    paginator = Paginator(encuentros, 10)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'encuentros/listar_encuentros.html', {'page_obj': page_obj})


def ver_encuentro(request, pk):
    # Obtener el encuentro con el pk proporcionado
    encuentro = get_object_or_404(Encuentro, pk=pk)

    # Inicializar las variables
    dinero_final = 0
    resultado = encuentro.resultado

    # Obtener los valores que usaremos para los cálculos, asegurándonos de que no sean negativos
    pactada = float(max(encuentro.pactada, 0))  # Este dato fijo será restado
    pago_juez = float(max(encuentro.pago_juez, 0))  # Este dato fijo será restado
    apuesta_general = float(max(encuentro.apuesta_general, 0))
    apuesta_por_fuera = float(max(encuentro.apuesta_por_fuera, 0))
    premio_mayor = float(max(encuentro.premio_mayor, 0))
    porcentaje_premio_mayor = float(max(encuentro.porcentaje_premio_mayor, 0))

    # Calcular el dinero del premio mayor
    dinero_del_premio_mayor = premio_mayor * (porcentaje_premio_mayor / 100)

    # Calcular el total apostado
    todo_el_dinero_apostado = apuesta_general + apuesta_por_fuera

    # Inicializar el dinero después de la apuesta
    dinero_luego_de_la_apuesta = 0

    # Calcular el dinero luego de la apuesta según el resultado
    if resultado == 'V':  # Victoria
        dinero_luego_de_la_apuesta = todo_el_dinero_apostado + dinero_del_premio_mayor
    elif resultado == 'T':  # Tablas
        dinero_luego_de_la_apuesta = 0
    elif resultado == 'D':  # Derrota
        dinero_luego_de_la_apuesta = 0 - todo_el_dinero_apostado
    else:
        raise Exception("Resultado no contemplado: " + resultado)

    # Calcular el pago al careador (15% si el dinero luego de la apuesta es positivo)
    pago_careador = 0 if apuesta_general <= 0 else apuesta_general * 0.15
    pago_careador = pago_careador + (0 if dinero_del_premio_mayor <= 0 else dinero_del_premio_mayor * 0.15)

    # Calcular los gastos totales
    gastos = pago_careador + pago_juez + pactada
    print(pago_careador)
    
    # Calcular el dinero final después de restar los gastos
    dinero_final = dinero_luego_de_la_apuesta - gastos

    # Pasar todos los datos al template
    return render(
        request, 'encuentros/ver_encuentro.html', 
        {
            'encuentro': encuentro,
            'todo_el_dinero_apostado': todo_el_dinero_apostado,
            'pago_careador': pago_careador,
            'dinero_del_premio_mayor': dinero_del_premio_mayor,
            'dinero_luego_de_la_apuesta': dinero_luego_de_la_apuesta,
            'gastos': gastos,
            'dinero_final': dinero_final,
            'pactada': pactada,
            'pago_juez': pago_juez,
            'apuesta_general': apuesta_general,
            'apuesta_por_fuera': apuesta_por_fuera,
            'premio_mayor': premio_mayor,
            'porcentaje_premio_mayor': porcentaje_premio_mayor,
            'resultado': resultado,
        }
    )

def encuentro_form(request, pk=None):
    if pk:
        encuentro = get_object_or_404(Encuentro, pk=pk)
        titulo = "Editar Encuentro #" + str(encuentro.pk)
    else:
        encuentro = None
        titulo = "Nuevo Encuentro"

    if request.method == 'POST':
        print("FILES recibidos:", request.FILES)   
        form = EncuentroForm(request.POST, request.FILES, instance=encuentro)
        id_gallo = request.POST.get('gallo')
        print("ID Gallo:", id_gallo)

        if not form.is_valid():
            print("Errores en el form:", form.errors.as_json()) 
        else:
            print("Form válido")

        if not id_gallo:
            form.add_error(None, "Debe seleccionar un gallo participante.")
        else:
            try:
                gallo = Gallo.objects.get(pk=id_gallo)
            except Gallo.DoesNotExist:
                form.add_error(None, "El gallo seleccionado no existe.")
                gallo = None

            if form.is_valid() and gallo:
                encuentro = form.save(commit=False)
                encuentro.gallo = gallo
                print("Antes de save():", encuentro.video, encuentro.imagen_evento)
                encuentro.save()
                print("Después de save():", encuentro.video, encuentro.imagen_evento)
                return redirect('ver_encuentro', pk=encuentro.idEncuentro)
            else:
                print("Errores en el form:", form.errors.as_json()) 
                print("Gallo: ", gallo)
    else:
        form = EncuentroForm(instance=encuentro)

    gallos = Gallo.objects.all()
    return render(request, 'encuentros/form_encuentro.html', {
        'form': form,
        'gallos': gallos,
        'titulo': titulo,
        'encuentro': encuentro
    })

@require_POST
def eliminar_encuentro(request, pk):
    encuentro = get_object_or_404(Encuentro, pk=pk)
    encuentro.delete()
    return redirect('listar_encuentros')

#colores
def color_list(request):
    # Si es una solicitud POST, se elimina el color
    if request.method == 'POST' and 'delete_color' in request.POST:
        color_id = request.POST.get('delete_color')
        color = get_object_or_404(Color, pk=color_id)
        color.delete()
        return redirect('color_list')

    colores = Color.objects.all()
    return render(request, 'colores/listar_colores.html', {'colores': colores})

# Vista para crear un color
def color_create(request):
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('color_list')
    else:
        form = ColorForm()
    return render(request, 'colores/form_color.html', {'form': form})

# Vista para editar un color
def color_edit(request, pk):
    color = get_object_or_404(Color, pk=pk)
    if request.method == 'POST':
        form = ColorForm(request.POST, instance=color)
        if form.is_valid():
            form.save()
            return redirect('color_list')
    else:
        form = ColorForm(instance=color)
    return render(request, 'colores/form_color.html', {'form': form})

#estados
def estado_list(request):
    # Si es una solicitud POST, se elimina el estado
    if request.method == 'POST' and 'delete_estado' in request.POST:
        estado_id = request.POST.get('delete_estado')
        estado = get_object_or_404(Estado, pk=estado_id)
        estado.delete()
        return redirect('estado_list')

    estados = Estado.objects.all()
    return render(request, 'estados/listar_estados.html', {'estados': estados})

# Vista para crear un estado
def estado_create(request):
    if request.method == 'POST':
        form = EstadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('estado_list')
    else:
        form = EstadoForm()
    return render(request, 'estados/form_estado.html', {'form': form})

# Vista para editar un estado
def estado_edit(request, pk):
    estado = get_object_or_404(Estado, pk=pk)
    if request.method == 'POST':
        form = EstadoForm(request.POST, instance=estado)
        if form.is_valid():
            form.save()
            return redirect('estado_list')
    else:
        form = EstadoForm(instance=estado)
    return render(request, 'estados/form_estado.html', {'form': form})


# Vista para listar galpones
def galpon_list(request):
    # Si es una solicitud POST, se elimina el galpón
    if request.method == 'POST' and 'delete_galpon' in request.POST:
        galpon_id = request.POST.get('delete_galpon')
        galpon = get_object_or_404(Galpon, pk=galpon_id)
        galpon.delete()
        return redirect('galpon_list')

    galpones = Galpon.objects.all()
    return render(request, 'galpones/listar_galpones.html', {'galpones': galpones})

# Vista para crear un galpón
def galpon_create(request):
    if request.method == 'POST':
        form = GalponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('galpon_list')
    else:
        form = GalponForm()
    return render(request, 'galpones/form_galpon.html', {'form': form})

# Vista para editar un galpón
def galpon_edit(request, pk):
    galpon = get_object_or_404(Galpon, pk=pk)
    if request.method == 'POST':
        form = GalponForm(request.POST, instance=galpon)
        if form.is_valid():
            form.save()
            return redirect('galpon_list')
    else:
        form = GalponForm(instance=galpon)
    return render(request, 'galpones/form_galpon.html', {'form': form})

# dueños
# Vista para listar los dueños
def dueno_list(request):
    if request.method == 'POST' and 'delete_dueno' in request.POST:
        dueno_id = request.POST.get('delete_dueno')
        dueno = get_object_or_404(Dueno, pk=dueno_id)
        dueno.delete()
        return redirect('dueno_list')

    duenos = Dueno.objects.all()
    return render(request, 'duenos_eventos/listar_duenos.html', {'duenos': duenos})

# Vista para crear un dueño
def dueno_create(request):
    if request.method == 'POST':
        form = DuenoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dueno_list')
    else:
        form = DuenoForm()
    return render(request, 'duenos_eventos/form_dueno.html', {'form': form})

# Vista para editar un dueño
def dueno_edit(request, pk):
    dueno = get_object_or_404(Dueno, pk=pk)
    if request.method == 'POST':
        form = DuenoForm(request.POST, instance=dueno)
        if form.is_valid():
            form.save()
            return redirect('dueno_list')
    else:
        form = DuenoForm(instance=dueno)
    return render(request, 'duenos_eventos/form_dueno.html', {'form': form})