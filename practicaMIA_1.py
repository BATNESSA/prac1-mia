#!/usr/bin/env python
# coding: utf-8

# In[1]:

import re
import unidecode
import os, os.path
import nltk
nltk.download('cess_esp')
from langdetect import detect
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.corpus import cess_esp
from nltk import tokenize
from nltk import punkt
from nltk import corpus
from nltk import tag
from whoosh import index
from whoosh import fields
from whoosh import scoring
from whoosh.fields import Schema, TEXT
from whoosh.index import create_in
from whoosh import qparser
from whoosh.qparser import QueryParser
from whoosh.qparser import *

#Funcion en para introducir un número por teclado
def elegirNumeroMenu():
    correcto=False
    num=0
    while(not correcto):
        try:
            num = int(input("Introduce un numero que sea una opción del menú: "))
            correcto=True
        except ValueError:
            print('Error, introduce un numero entero o no es un nº del 1 al 4')
     
    return num

def procesarTokens(t):
    t = t.strip()
    t = t.lower()
    t = unidecode.unidecode(t)
    resul=""
               
    tokensT = list(tokenize.word_tokenize(t))
    tsinsw = [w for w in tokensT if not w in stopwords]
    listaToken = list(algoritmo_unigram_tagger.tag(tsinsw))
    listaSustantivos = []

    for tlt in listaToken:
        if (tlt[1] == None) or (re.search("^nc", tlt[1])):
            #listaSustantivos.append(tlt)
            resul=resul+tlt[0]+" "

    return resul


#-----------      PRIMER PUNTO       ------------
# Definimos el esquema 
esquema = Schema(titulo=TEXT(stored=True), 
                noticia=TEXT(stored=True),
                resumen=TEXT(stored=True),
                )

# Lectura de ficheros de texto plano del directorio 'noticias' donde se encuentran
# los archivos 
path = 'noticias' 
ficheros = os.listdir(path)
documentos = []

#crear un carpeta para guardar el índice
if not os.path.exists("contenido"):
    os.mkdir("contenido")
    
#crear el índice (si existe, lo sobrescribe) con el esquema definido
index.create_in("contenido", esquema) 
#abrir el índice
indice = index.open_dir("contenido")
#crear un objeto escritor para escribir

stopwords = set(stopwords.words("spanish"))

for nombrefichero in ficheros:    
        if os.path.isfile(os.path.join(path, nombrefichero)): #si es un fichero y no es un directorio
            fich = open(os.path.join(path, nombrefichero), "r", encoding='utf-8')
            text = fich.read()
            detect(text)
           
            # quitamos '.', ',' y ';'
            text = text.replace(",","")
            text = text.replace(".","")
            text = text.replace(";","")
            # separamos las secciones con un salto de línea entre párrafos
            # '\n\n' es el indicativo en nuestro programa de separador de secciones
            textAux = text.split('\n\n')

            train_sents = cess_esp.tagged_sents()
            algoritmo_unigram_tagger = tag.UnigramTagger(train_sents)

            #en cada seccion del archivo: ponemos en minuscula, 
            #quitamos acentos y stopwords con el metodo procesarTokens(t)
            
            titAux=procesarTokens(textAux[0])
            notAux=procesarTokens(textAux[1])
            resAux=procesarTokens(textAux[2])
                
            writer = indice.writer()
            writer.add_document(
                titulo = "".join(titAux),
                noticia = "".join(notAux), 
                resumen = "".join(resAux) 
            )
            writer.commit()

#se muestra el menú por el que el usuario debe configurar su búsqueda
print ("Elija una de las siguientes opciones de búsqueda")

salir = False
opcion = 0
 
while not salir:
    busqueda = ""
 
    print ("1. Título.")
    print ("2. Noticia.")
    print ("3. Resumen.")
    print ("4. Salir")
     
    opcion = elegirNumeroMenu()
    
    if opcion == 1:
        busqueda = "titulo"
    elif opcion == 2:
        busqueda = "noticia"
    elif opcion == 3:
        busqueda = "resumen"
    elif opcion == 4:
        salir = True
    else:
        print ("El numero elegido no está entre el 1 y 4")

    #Definir un parser para un campo concreto
    parserTitulo=QueryParser(busqueda, schema=esquema)

    if busqueda != "":
        textoBuscar = input("Introduzca el texto que desea buscar: ")
        #Parsear la cadena para convertirla a un objeto consulta (query) ; otros operadores AND NOT ()
        consulta=parserTitulo.parse(textoBuscar)
        print (consulta)

        # Abre el objeto buscador y luego lo cierra con el bloque "with"
        with indice.searcher(weighting=scoring.TF_IDF()) as buscador:
    
            #Busca en el índice los documentos más parecidos devolviendo un máximo de documentos (limit)
            documentos_recuperados = buscador.search(consulta, limit=50, terms = True) #terms = True guarda los términos que hicieron match entre la consulta y el documento
            print (documentos_recuperados)
            #imprimir resultados
            for i in range(len(documentos_recuperados)):
                print(documentos_recuperados[i]['titulo'], 
                    str(documentos_recuperados[i].score), documentos_recuperados[i]['noticia'])
