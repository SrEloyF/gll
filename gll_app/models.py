from django.db import models
import time
import os

def imagen_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{int(time.time())}.{ext}"
    return os.path.join('gallos', filename)

def imagen_upload_path_encuentros(instance, filename):
    base, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    return f"media/videos/encuentros/{timestamp}_{base}{ext}"

class Gallo(models.Model):
    nroPlaca = models.IntegerField(primary_key=True, unique=True)
    fechaNac = models.DateField()
    color = models.CharField(max_length=100)
    sexo = models.CharField(max_length=1, choices=[('M', 'Macho'), ('H', 'Hembra')])
    tipoGallo = models.CharField(max_length=20, choices=[
        ('DP', 'Gallo De Pelea'),
        ('PADRE', 'Gallo Padre'),
        ('MADRE', 'Gallina madre')
    ])
    observaciones = models.TextField()
    nombre_img = models.ImageField(upload_to=imagen_upload_path)
    placaPadre = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='hijos_padre')
    placaMadre = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='hijos_madre')

    def __str__(self):
        return f"Gallo {self.nroPlaca}"

#migrar
#mostrar el 15% para el careador en el frontend

class Encuentro(models.Model):
    idEncuentro = models.AutoField(primary_key=True)
    fechaYHora = models.DateTimeField(null=False)
    galpon1 = models.CharField(max_length=100)
    galpon2 = models.CharField(max_length=100)
    ganador = models.ForeignKey(Gallo, on_delete=models.PROTECT, null=True)  # null si es empate
    video = models.FileField(upload_to=imagen_upload_path, null=True)

    # gastos fijos
    pactada = models.DecimalField(decimal_places=2, max_digits=10)
    pago_juez = models.DecimalField(decimal_places=2, max_digits=10)

    # ganancias
    apuesta_general = models.DecimalField(decimal_places=2, max_digits=10)
    premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=10)
    porcentaje_premio_mayor = models.DecimalField(decimal_places=2, default=0, max_digits=5)
    apuesta_por_fuera = models.DecimalField(decimal_places=3, default=0, max_digits=10)

class ParticipantesEnEncuentro(models.Model):
    idEncuentro = models.ForeignKey(Encuentro, on_delete=models.PROTECT)
    idParticipante = models.ForeignKey(Gallo, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('idEncuentro', 'idParticipante')
