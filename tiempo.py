#Version 25-septiembre-2016 6:29 am
from datetime import datetime
from decimal import Decimal,getcontext
getcontext().prec = 10
#-----------------------------------------------
def opciones_entrada():
	select = input("Las opciones de entrada son:\n(1) Tiempo actual\n(2) Tiempo manual\n(3) Leer a cabecera de un archivo proveniente de Spectrabyber\nEspecificar la opcion desde el teclado: ")
	return select

def tiempo_actual():
	##Variables del tiempo y fecha local
	local = datetime.now()	
	ahora = datetime.utcnow()
	d = ahora.day
	m = ahora.month
	y = ahora.year
	hr = ahora.hour
	mn = ahora.minute
	sg = ahora.second
	## representacion de fecha y hora local
	print ("Tiempo local	= %s\nTiempo UTC	= %s" %(local,ahora))
	return d,m,y,hr,mn,sg

def tiempo_manual():
	hr = input("Hora UTC	= ")
	mn = input("minutos		= ")
	sg = input("segundos	= ")
	d = input("dia		= ")
	m = input("mes		= ")
	y = input("anio		= ")
	print ("Tiempo UTC	= %s:%s:%s\nFecha		= %s/%s/%s" %(hr,mn,sg,d,m,y))
	return d,m,y,hr,mn,sg

def archivos():
	nombre_archivo = input("Archivo de entrada	= ")
	with open(nombre_archivo, 'r') as archivo:
		##Leer fecha, hora y ancho de paso de la cabecera
		archivo.seek(2)	
		m = int(archivo.read(2))

		if m > 10: p = 3 
		else: p = 2
		d = int(archivo.read(p))

		if d > 10: p = 3 
		else: p = 2
		y = int(archivo.read(5))
		hr = int(archivo.read(2))

		if hr > 10: p = 3 
		else: p = 2
		mn = int(archivo.read(p))
		
		if mn > 10: p = 3
		else: p = 2
		sg = int(archivo.read(p))
		h = float(archivo.read(8))
		print ("Inicio de la medicion\nFecha		= %s/%s/%s\nHora UTC	= %s:%s:%s" %(d,m,y,hr,mn,sg))
		archivo.seek(0)
		datos = archivo.readlines()
		n = len(datos)
	
	lugar = input("""Longitud del lugar: 
(1) Universum, Cd. de Mexico	= -99.1799
(2) Irya, Morelia, Michoacan	= -101.2284
(3) Otro
Especificar la opcion desde el teclado: """)		
	if lugar == 1:
		longitude = -99.1799
	elif lugar == 2:
		longitude = -101.2284
	elif lugar == 3:
		longitude = input("Longitude en decimales	= ")
	else:
		print ("Opcion no definida")

	return d,m,y,hr,mn,sg,n,h,datos,longitude
#-----------------------------------------------------------------------
def decimal_day(sg,mn,hr,d):
	## Convertir h/m/s -> decimal
	global fff,dd
	
	f = sg / 60.
	ff = (f + mn) / 60.
	fff = hr + ff	## hora expresada en decimales
	dec = fff / 24.	## fraccion del dia
	dd = d + dec 	## dia expresado en decimales
	return fff,dd

def julian_day(m,y,dd):
	## Convertir calendario gregoriano a dia juliano	
	global jd
	## condicion para enero y febrero
	if m <= 2:
		m = m + 12
		y = y - 1.

	a = int(y / 100.)
	b = 2. - a + int(a / 4.)
	jd = int(365.25 * (y + 4716.)) + int(30.6001 * (m + 1.)) + dd + b - 1524.5 ## Jean Meeus Astronomical algorithms
	return jd

def greenwich_sidereal(jd):
	##Convertir a tiempo sideral en Greenwich GST
	global theta,sgs,mgs,hgs

	t = (jd - 2451545.) / 36525.
	theta = 280.46061837 + (360.98564736629 * (jd - 2451545.)) + (0.0003987933 * t * t) - ((t * t * t) / 38710000.) ## for any instant

##	theta = 6.697374558 + (2400.051336 * t) + (0.000025862 * (t ** 2)) + (fff * 1.0027379093) ## Peter Duffett-Smith Practical Astronomy with your Calculator or Spreadsheet

	if (theta // 360.) > 0:
		theta = theta - (360. * (theta // 360.))

	hgs = int(theta / 15)
	mgs = int(((theta / 15) - hgs) * 60.)
	sgs = int(((((theta / 15) - hgs) * 60.) - mgs) * 60.)
	return hgs,mgs,sgs,theta

def local_sidereal(thetad,longitude):
	global hls,mls,sls,phi
	phi = thetad + (longitude / 15.)
	if (phi // 24.) > 0:
		phi = phi - (24. * (phi // 24.))
	if phi < 0:
		phi = phi + 24.

	hls = int(phi)
	mls = int((phi - hls) * 60.)
	sls = int((((phi - hls) * 60.) - mls) * 60.)
	return hls,mls,sls,phi

def barrido_tiempo(d,m,y,hr,mn,sg,n,h,datos,longitude):

	nombre_archivo = input("Archivo de salida	= ")
	with open(nombre_archivo,'w') as ajuste:
		ajuste.write('# UTC		D.J.				LST decimal		LST		Voltaje\n')
		#dias en cada mes
		dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
		#condicion para anio bisiesto
		if y % 4 == 0: dias_mes[2] = 29
		
		##loop para barrer un determinado intervalo de tiempo	
		sg = sg - h
		for i in range(1,n): 
			if datos[i] == "0.000000\r\n":
				continue
			sg = sg + h
			if sg >= 60.: 
				mn = mn + 1
				sg = 0.
				if mn >= 60: 
					hr = hr + 1
					mn = 0
					if hr > 23:
						d = d + 1
						hr = 0
						if d > dias_mes[m - 1]:
							m = m + 1
							d = 1
							if m > 13:
								y = y + 1
								m = 1 			

			## escribir UTC en el fichero
			ajuste.write("%s:%s:%s    	" %(hr,mn,sg))
			fff,dd = decimal_day(sg,mn,hr,d)
			jd = julian_day(m,y,dd)
			hgs,mgs,sgs,theta = greenwich_sidereal(jd)
			thetad,dd = decimal_day(sgs,mgs,hgs,d)
			hls,mls,sls,phi = local_sidereal(thetad,longitude)
			##Escribir dia juliano en el fichero
			ajuste.write("%s        	"%jd)
			## escribir LST en el fichero
			ajuste.write("%s        	"%phi)
			ajuste.write("%s:%s:%s   	" %(hls,mls,sls))
			## escribir medicion en el fichero
			ajuste.write("%s" %datos[i])
#-----------------------------------------------------------------------------------
#Inicio
print ("Programa para hacer conversiones de tiempo")
select = int(opciones_entrada())

if 1<= select <= 2:

	if select == 1:
		d,m,y,hr,mn,sg = tiempo_actual()
	elif select == 2:
		d,m,y,hr,mn,sg = tiempo_manual()

	fff,dd = decimal_day(sg,mn,hr,d)
	jd = julian_day(m,y,dd)
	hgs,mgs,sgs,theta = greenwich_sidereal(jd)
	print ("Dia juliano 	= %s\n-----------------------------------------------------" %jd) 
	thetad,dd = decimal_day(sgs,mgs,hgs,d)
	longitud = [-79.838, -97.2928, -99.1799, -101.2284, -101.6816, -107.618,]
	lugar = ['GBT, Green Bank, West Virgina','GTM, Atzitzintla, Puebla', 'Universum, Cd. de Mexico', 'Irya, Morelia, Michoacan','MEXART, Coeneo, Michoacan', 'VLA, Socorro, Nvo. Mexico',]

	for i in range(0,len(longitud)):
		hls,mls,sls,phi = local_sidereal(thetad,longitud[i])
		print ("""%s	Longitude = %s
Tiempo (LST)	= %s:%s:%s
-----------------------------------------------------""" %(lugar[i],longitud[i],hls,mls,sls))
elif select == 3:
		d,m,y,hr,mn,sg,n,h,datos,longitude = archivos()
		barrido_tiempo(d,m,y,hr,mn,sg,n,h,datos,longitude)
else:
	print ("Opcion no definida")
