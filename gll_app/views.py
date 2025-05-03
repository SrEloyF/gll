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
            return redirect('ver', nroPlaca=gallo.nroPlaca)
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
            placa_padre = request.POST.get('placaPadre') or None
            placa_madre = request.POST.get('placaMadre') or None

            if placa_padre and placa_padre == placa_madre:
                messages.error(request, "Padre y madre no pueden ser el mismo.")
            else:
                gallo = form.save(commit=False)
                gallo.placaPadre_id = placa_padre
                gallo.placaMadre_id = placa_madre
                gallo.save()
                return redirect('ver', nroPlaca=gallo.nroPlaca)
    else:
        form = GalloForm(instance=gallo)

    gallos = Gallo.objects.exclude(nroPlaca=gallo.nroPlaca)

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
    encuentro = get_object_or_404(Encuentro, pk=pk)
    dinero_final = 0
    
    
    resultado = encuentro.resultado

    pactada = float(max(encuentro.pactada, 0))  # este dato fijo será restado
    pago_juez = float(max(encuentro.pago_juez, 0))  # este dato fijo será restado

    apuesta_general = float(max(encuentro.apuesta_general, 0))
    apuesta_por_fuera = float(max(encuentro.apuesta_por_fuera, 0))

    premio_mayor = float(max(encuentro.premio_mayor, 0))
    porcentaje_premio_mayor = float(max(encuentro.porcentaje_premio_mayor, 0))
    dinero_del_premio_mayor = premio_mayor*(porcentaje_premio_mayor/100)

    todo_el_dinero_apostado = apuesta_general + apuesta_por_fuera

    dinero_luego_de_la_apuesta = 0

    if resultado == 'V':
        dinero_luego_de_la_apuesta = todo_el_dinero_apostado * 2
    elif resultado == 'T':
        dinero_luego_de_la_apuesta = 0
    elif resultado == 'D':
        dinero_luego_de_la_apuesta = 0 - todo_el_dinero_apostado
    else:
        raise Exception("Resultado no contemplado: " + resultado)
    
    dinero_luego_de_la_apuesta = dinero_luego_de_la_apuesta + dinero_del_premio_mayor

    pago_careador = 0 if dinero_luego_de_la_apuesta <= 0 else dinero_luego_de_la_apuesta * 0.15
    
    gastos = float(pago_careador) + float(pago_juez) + float(pactada)
    dinero_final = dinero_luego_de_la_apuesta - gastos

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
        form = EncuentroForm(request.POST, request.FILES, instance=encuentro)
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