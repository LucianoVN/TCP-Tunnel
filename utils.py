import sys

# Árboles binarios para optimizar ordenamiento de mensajes

# Clase para los nodos internos del arbol
class NodoiABB:
    def __init__(self, izq, info, der):
        self.izq=izq
        self.info=info
        self.der=der
        
    def __str__(self):
        return "("+self.izq.__str__()+str(self.info)+self.der.__str__()+")"

    def inorden(self, lista):
        self.izq.inorden(lista)
        lista.append(self.info[1])
        self.der.inorden(lista)

# Clase para los nodos externos del arbol
class NodoeABB:
    def __init__(self):
        pass
    
    def __str__(self):
        return"☐"

    def inorden(self, lista):
        pass  

# Clase para el árbol de busqueda binaria
class ArbolABB:
    def __init__(self,raiz=NodoeABB()):
        self.raiz=raiz

    # Retorna una lista con los elementos en orden
    def inorden(self):
        lista_ordenada = []
        self.raiz.inorden(lista_ordenada)
        return lista_ordenada

    def insert(self,x):
        if isinstance(self.raiz, NodoeABB):
            self.raiz=NodoiABB(NodoeABB(),x,NodoeABB())
            return
        p=self.raiz
        while True:
            if x[0]==p.info[0]:
                return
            if x[0]<p.info[0]:
                if isinstance(p.izq, NodoeABB):
                    p.izq=NodoiABB(NodoeABB(),x,NodoeABB())
                    return
                p=p.izq
            else: # x>p.info
                if isinstance(p.der, NodoeABB):
                    p.der=NodoiABB(NodoeABB(),x,NodoeABB())
                    return
                p=p.der
                
    def __str__(self):        
        return self.raiz.__str__()

# Funcion que dado un ABB, entrega una lista con los elementos ordenados de menor a mayor
def ordena_ABB(a):
  arbolito = ArbolABB() # Crea el arbol ABB
  for i in range(0, len(a)): # Inserta todos los elementos
    arbolito.insert(a[i])
  msg = arbolito.inorden() 
  msg_reconstruido = b''
  for i in msg:
    msg_reconstruido = msg_reconstruido + i
  return msg_reconstruido

# Función que elimina la última línea impresa en el terminal (útil para desplegar la interfaz)
def delete_last_line():
    "Use this function to delete the last line in the STDOUT"

    #cursor up one line
    sys.stdout.write('\x1b[1A')

    #delete last line
    sys.stdout.write('\x1b[2K')