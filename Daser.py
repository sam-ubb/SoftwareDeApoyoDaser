import os
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import webbrowser

def cargar_datos_seleccionados(carpeta_seleccionada):
    try:
        # Leer los archivos .txt
        corr_file = os.path.join(carpeta_seleccionada, "Corr.txt")
        registro_laser_file = os.path.join(carpeta_seleccionada, "registro_laser.txt") #Reemplazar si se quiere leer otro archivo
        velocidad_file = os.path.join(carpeta_seleccionada, "Velocidad.txt")

        # Cargar archivos con delimitadores y manejo de errores
        corr_df = pd.read_csv(corr_file, sep=r'\s+', engine='python',on_bad_lines='skip')
        registro_laser_df = pd.read_csv(registro_laser_file, sep=r'\s+', engine='python',on_bad_lines='skip')
        velocidad_df = pd.read_csv(velocidad_file, sep=r'\s+', engine='python',on_bad_lines='skip')

        # Convertir columnas relevantes a valores numéricos
        for df , numeric_cols in zip([corr_df, registro_laser_df, velocidad_df], [["Corriente"], ["Temperatura(°C)","Distancia(mm)"], ["Milliseconds"]]):
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)  # Reemplazar NaN con 0

        # Combinar columnas de fecha y hora en cada archivo
        corr_df['datetime'] = pd.to_datetime(corr_df['Fecha'] + ' ' + corr_df['Hora'])
        registro_laser_df['datetime'] = pd.to_datetime(registro_laser_df['Fecha'] + ' ' + registro_laser_df['Hora'])
        velocidad_df['datetime'] = pd.to_datetime(velocidad_df['Date'] + ' ' + velocidad_df['Time'])

        # Renombrar columna "Pulse" de Velocidad.txt a "Velocidad del carro"
        velocidad_df.rename(columns={"Milliseconds": "Velocidad (ms)"}, inplace=True)

        # Eliminar duplicados en la columna datetime
        corr_df = corr_df.drop_duplicates(subset='datetime')
        registro_laser_df = registro_laser_df.drop_duplicates(subset='datetime')
        velocidad_df = velocidad_df.drop_duplicates(subset='datetime')

        # Unir los DataFrames en base a la columna 'datetime'
        merged_df = pd.merge(corr_df, registro_laser_df, on='datetime', how='outer')
        merged_df = pd.merge(merged_df, velocidad_df, on='datetime', how='outer')

        # Reemplazar valores faltantes con 0
        merged_df.fillna(0, inplace=True)

        # Filtrar filas donde todas las variables sean 0 (excepto datetime)
        columnas_a_verificar = ['Corriente', 'Temperatura(ºC)', 
                                'Distancia(mm)', 'Madera','Velocidad (ms)']
        merged_df = merged_df[~(merged_df[columnas_a_verificar] == 0).all(axis=1)]

        # Separar la columna datetime en fecha y hora
        merged_df['fecha'] = merged_df['datetime'].dt.date
        merged_df['hora'] = merged_df['datetime'].dt.time

        #ordenar los datos según la hora
        merged_df.sort_values(by='hora', inplace=True)

        # Reordenar columnas para mayor claridad
        columnas_ordenadas = ['fecha', 'hora', 'Corriente', 'Velocidad (ms)', 'Temperatura(ºC)', 
                              'Distancia(mm)', 'Madera']
        merged_df = merged_df[columnas_ordenadas]

        return merged_df
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")
        return pd.DataFrame()

def crear_interfaz():
    ventana = ctk.CTk()
    ventana.title("Selector de Carpetas y Visualización de Datos")
    ventana.geometry("1200x800")

    tabview = ctk.CTkTabview(ventana, width=1200, height=800)
    tabview.pack(expand=True, fill="both")

    seleccionar_tab = tabview.add("Seleccionar Carpeta")
    visualizar_tab = tabview.add("Visualizar Datos")
    graficos_tab = tabview.add("Visualizar Gráficos")
    parametros_tab = tabview.add("Visualizar parámetros por tabla")

    def cargar_carpetas():
        ruta_base = ruta_base_var.get()
        if not os.path.isdir(ruta_base):
            messagebox.showerror("Error", "La ruta base ingresada no es válida.")
            return
        try:
            carpetas = sorted([f for f in os.listdir(ruta_base) if os.path.isdir(os.path.join(ruta_base, f))],
                              key=lambda x: os.path.getmtime(os.path.join(ruta_base, x)),
                              reverse=True)[:7]
            selectdown.configure(values=carpetas)
            messagebox.showinfo("Éxito", "Carpetas cargadas correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las carpetas: {e}")



    # Agregar widgets en la pestaña "Seleccionar Carpeta"
    etiqueta_ruta = ctk.CTkLabel(seleccionar_tab, text="1.- Ingrese la ruta base para cargar los datos:", font=("Arial", 18))
    etiqueta_ruta.pack(pady=10)

    ruta_base_var = ctk.StringVar(value="")
    ruta_base_entry = ctk.CTkEntry(seleccionar_tab, textvariable=ruta_base_var, width=250)
    ruta_base_entry.pack(pady=10)

    cargar_carpetas_button = ctk.CTkButton(seleccionar_tab, text="Cargar Carpetas", command=cargar_carpetas)
    cargar_carpetas_button.pack(pady=10)

    etiqueta_seleccionar_carpeta = ctk.CTkLabel(seleccionar_tab, text="2.- Seleccione una carpeta o busquela por su nombre", font=("Arial", 18))
    etiqueta_seleccionar_carpeta.pack(pady=10)

    carpeta_seleccionada_var = ctk.StringVar(value="Seleccionar carpeta")
    selectdown = ctk.CTkOptionMenu(seleccionar_tab, variable=carpeta_seleccionada_var)
    selectdown.pack(pady=10)

    buscar_var = ctk.StringVar()
    buscar_entry = ctk.CTkEntry(seleccionar_tab, textvariable=buscar_var, placeholder_text="Buscar carpeta por nombre")
    buscar_entry.pack(pady=10)


    def cargar_datos():
        ruta_base = ruta_base_var.get()
        if not os.path.isdir(ruta_base):
            messagebox.showerror("Error", "La ruta base ingresada no es válida.")
            return
        carpeta_seleccionada = os.path.join(ruta_base, carpeta_seleccionada_var.get())
        if not os.path.isdir(carpeta_seleccionada):
            messagebox.showwarning("Advertencia", "Por favor selecciona una carpeta válida.")
            return
        datos = cargar_datos_seleccionados(carpeta_seleccionada)
        if not datos.empty:
            guardar_txt(datos, ruta_base)  # Guardar el archivo txt en la ruta base
            mostrar_datos(datos)
            tabview.set("Visualizar Datos")

    def guardar_txt(datos, ruta_base):
        archivo_txt = os.path.join(ruta_base, "datos_exportados.txt")
        try:
            datos.to_csv(archivo_txt, index=False, sep='\t')
            messagebox.showinfo("Éxito", f"Datos guardados en {archivo_txt}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los datos: {e}")

    etiqueta_cargar_datos = ctk.CTkLabel(seleccionar_tab, text="3.- Presione el botón para cargar los datos:", font=("Arial", 18))
    etiqueta_cargar_datos.pack(pady=10)

    cargar_button = ctk.CTkButton(seleccionar_tab, text="Cargar Datos", command=cargar_datos)
    cargar_button.pack(pady=20)

    # Mostrar datos en la pestaña "Visualizar Datos"
    def mostrar_datos(datos):
        global datos_filtrados_global
        datos_filtrados_global = datos
        for widget in visualizar_tab.winfo_children():
            widget.destroy()

        # Frame horizontal para filtros
        filtro_frame = ctk.CTkFrame(visualizar_tab)
        filtro_frame.pack(pady=10, fill="x")

        #Filtro por jornada y hora
        jornada_var = ctk.StringVar(value="Todas")
        jornada_menu = ctk.CTkOptionMenu(filtro_frame, values=["Todas", "Mañana", "Tarde", "Noche"], variable=jornada_var)
        jornada_menu.pack(side="left", padx=5)

        hora_inicio_var = ctk.StringVar()
        hora_fin_var = ctk.StringVar()

        hora_inicio_entry = ctk.CTkEntry(filtro_frame, textvariable=hora_inicio_var, placeholder_text="Hora Inicio (HH:MM:SS)")
        hora_inicio_entry.pack(side="left", padx=5)

        hora_fin_entry = ctk.CTkEntry(filtro_frame, textvariable=hora_fin_var, placeholder_text="Hora Fin (HH:MM:SS)")
        hora_fin_entry.pack(side="left", padx=5)

        #Filtro Madera
        madera_var = ctk.StringVar(value="Seleccionar")
        madera_menu = ctk.CTkOptionMenu(filtro_frame, values=["Madera 1", "Madera 0"], variable=madera_var)
        madera_menu.pack(side="left", padx=5)


        aplicar_filtro_button = ctk.CTkButton(filtro_frame, text="Aplicar Filtro", command=lambda: aplicar_filtros(datos))
        aplicar_filtro_button.pack(side="left", padx=5)

        #Botón de reiniciar filtros
        reiniciar_filtro_button = ctk.CTkButton(filtro_frame, text="Reiniciar Filtros", command=lambda: reiniciar_filtros(datos))
        reiniciar_filtro_button.pack(side="left", padx=5)

        frame = ttk.Frame(visualizar_tab)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=list(datos.columns), show="headings")
        for col in datos.columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")
        for _, row in datos.iterrows():
            tree.insert("", "end", values=list(row))

        scrollbar_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar_y.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        tree.configure(xscrollcommand=scrollbar_x.set)

        tree.pack(expand=True, fill="both")

        def aplicar_filtros(datos_filtrados):
            global datos_filtrados_global

            if jornada_var.get() != "Todas":
                if jornada_var.get() == "Mañana":
                    datos_filtrados = datos_filtrados[datos_filtrados['hora'].between(pd.Timestamp("06:00:00").time(), pd.Timestamp("12:00:00").time())]
                elif jornada_var.get() == "Tarde":
                    datos_filtrados = datos_filtrados[datos_filtrados['hora'].between(pd.Timestamp("12:00:00").time(), pd.Timestamp("18:00:00").time())]
                elif jornada_var.get() == "Noche":
                    datos_filtrados = datos_filtrados[(datos_filtrados['hora'] >= pd.Timestamp("18:00:00").time()) | (datos_filtrados['hora'] < pd.Timestamp("06:00:00").time())]

            if hora_inicio_var.get() and hora_fin_var.get():
                try:
                    hora_inicio = pd.to_datetime(hora_inicio_var.get(), format='%H:%M:%S').time()
                    hora_fin = pd.to_datetime(hora_fin_var.get(), format='%H:%M:%S').time()
                    datos_filtrados = datos_filtrados[
                        (datos_filtrados['hora'] >= hora_inicio) &
                        (datos_filtrados['hora'] <= hora_fin)
                    ]
                except ValueError:
                    messagebox.showerror("Error", "Formato de hora inválido. Use HH:MM:SS.")

            if madera_var.get() != "Seleccionar":
                try:
                    madera_valor = 1 if madera_var.get() == "Madera 1" else 0
                    datos_filtrados = datos_filtrados[datos_filtrados['Madera'] == madera_valor]
                except ValueError:
                    messagebox.showerror("Error", "Valor no válido para filtrar.")

            actualizar_tabla(datos_filtrados)
            datos_filtrados_global = datos_filtrados.copy()

        def reiniciar_filtros(datos_originales):
            jornada_var.set("Todas")
            hora_inicio_var.set("")
            hora_fin_var.set("")
            madera_var.set("Seleccionar")

            #Restaurar la tabla con los datos originales
            actualizar_tabla(datos_originales)
            datos_filtrados_global = datos_originales.copy()

        def actualizar_tabla(datos_actualizados):
            for row in tree.get_children():
                tree.delete(row)
            for _, row in datos_actualizados.iterrows():
                tree.insert("", "end", values=list(row))

        def exportar_datos_filtrados():
            global datos_filtrados_global
            if datos_filtrados_global.empty:
                messagebox.showerror("Error", "No hay datos para exportar.")
                return
            try:
                ruta_base = ruta_base_var.get()
                archivo_txt = os.path.join(ruta_base, "datos_filtrados.txt")
                datos_filtrados_global.to_csv(archivo_txt, index=False, sep='\t')
                messagebox.showinfo("Éxito", f"Datos exportados en {archivo_txt}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron exportar los datos: {e}")

        exportar_button = ctk.CTkButton(visualizar_tab, text="Exportar Datos Filtrados", command=exportar_datos_filtrados)
        exportar_button.pack(pady=10)


        def filtrar_madera(datos,valor):
            if valor not in ['0','1']:
                messagebox.showerror("Error", "Valor no válido para filtrar.")
                return
            try:
                valor = int(valor)
                datos_filtrados = datos[datos['Madera'] == valor]
                actualizar_tabla(datos_filtrados)
                datos_filtrados_global = datos_filtrados.copy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo filtrar: {e}")

        def mostrar_graficos():
        # Limpia la pestaña
            for widget in graficos_tab.winfo_children():
                widget.destroy()

    # Sección 1: Dataset completo
    ctk.CTkLabel(graficos_tab, text="Visualizar graficos del Dataset completo:", font=("Arial", 16)).pack(pady=10)
    
    # Variables para dataset completo
    dataset_completo_var = ctk.StringVar()
    opciones_completo = []

    def cargar_variables_completo():
        ruta_base = ruta_base_var.get()
        archivo_txt = os.path.join(ruta_base, "datos_exportados.txt")
        if not os.path.isfile(archivo_txt):
            messagebox.showerror("Error", "No se ha cargado el dataset completo.")
            return
        try:
            datos_completos = pd.read_csv(archivo_txt, sep='\t')
            opciones = [col for col in datos_completos.columns[2:] if col != "Madera"]   # Excluye 'fecha' y 'hora'
            dataset_completo_var.set("")
            completo_menu.configure(values=opciones)
            completo_menu.pack(pady=5)
            messagebox.showinfo("Éxito", "Variables cargadas correctamente.")
            return datos_completos
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las variables del dataset completo: {e}")
            return None

    def graficar_completo():
        ruta_base = ruta_base_var.get()
        archivo_txt = os.path.join(ruta_base, "datos_exportados.txt")
        if not os.path.isfile(archivo_txt):
            messagebox.showerror("Error", "No se ha cargado el dataset completo.")
            return
        try:
            datos_completos = pd.read_csv(archivo_txt, sep='\t')
            variable = dataset_completo_var.get()
            if variable not in datos_completos.columns:
                messagebox.showerror("Error", "Variable no válida para graficar.")
                return
            fig = px.line(datos_completos, x='hora', y=variable, title=f"Gráfico de {variable} (Dataset completo)")
            fig.update_layout(xaxis_title="Hora", yaxis_title=variable)
            temp_html = "temp_plot_completo.html"
            pio.write_html(fig, file=temp_html, auto_open=False)
            webbrowser.open(temp_html)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo graficar: {e}")

    cargar_completo_button = ctk.CTkButton(graficos_tab, text="Cargar Variables", command=cargar_variables_completo)
    cargar_completo_button.pack(pady=5)

    completo_menu = ctk.CTkOptionMenu(graficos_tab, variable=dataset_completo_var, values=opciones_completo)
    completo_menu.pack(pady=5)

    graficar_completo_button = ctk.CTkButton(graficos_tab, text="Seleccionar y Graficar", command=graficar_completo)
    graficar_completo_button.pack(pady=10)

    # Sección 2: Dataset filtrado
    ctk.CTkLabel(graficos_tab, text="Visualizar graficos del Dataset filtrado:", font=("Arial", 16)).pack(pady=10)
    
    # Variables para dataset filtrado
    dataset_filtrado_var = ctk.StringVar()
    opciones_filtrado = []

    def cargar_variables_filtrado():
        global datos_filtrados_global
        if 'datos_filtrados_global' not in globals() or datos_filtrados_global.empty:
            messagebox.showerror("Error", "No se ha cargado el dataset filtrado.")
            return
        try:
            opciones = [col for col in datos_filtrados_global.columns[2:] if col != "Madera"]  # Excluye 'fecha' y 'hora'
            dataset_filtrado_var.set("")
            filtrado_menu.configure(values=opciones)
            filtrado_menu.pack(pady=5)
            messagebox.showinfo("Éxito", "Variables cargadas correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las variables del dataset filtrado: {e}")

    def graficar_filtrado():
        global datos_filtrados_global
        if 'datos_filtrados_global' not in globals() or datos_filtrados_global.empty:
            messagebox.showerror("Error", "No se ha cargado el dataset filtrado.")
            return
        try:
            variable = dataset_filtrado_var.get()
            if variable not in datos_filtrados_global.columns:
                messagebox.showerror("Error", "Variable no válida para graficar.")
                return
            fig = px.line(datos_filtrados_global, x='hora', y=variable, title=f"Gráfico de {variable}")
            fig.update_layout(xaxis_title="Hora", yaxis_title=variable)
            temp_html = "temp_plot_filtrado.html"
            pio.write_html(fig, file=temp_html, auto_open=False)
            webbrowser.open(temp_html)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo graficar: {e}")

    cargar_filtrado_button = ctk.CTkButton(graficos_tab, text="Cargar Variables", command=cargar_variables_filtrado)
    cargar_filtrado_button.pack(pady=5)

    filtrado_menu = ctk.CTkOptionMenu(graficos_tab, variable=dataset_filtrado_var, values=opciones_filtrado)
    filtrado_menu.pack(pady=5)

    graficar_filtrado_button = ctk.CTkButton(graficos_tab, text="Seleccionar y Graficar", command=graficar_filtrado)
    graficar_filtrado_button.pack(pady=10)

    def detectar_tablas(datos):
        tablas = []
        en_tabla = False
        tabla_actual = {}
        for i, row in datos.iterrows():
            if row["Madera"] == 1:
                if not en_tabla:
                    en_tabla = True
                    tabla_actual = {"inicio": row["hora"], "fin": row["hora"], "Corriente_Total": row["Corriente"],
                                    "Corriente_Max": row["Corriente"], "Corriente_Min": row["Corriente"],"Temperatura_Max": row["Temperatura(ºC)"],
                                    "Temperatura_Min": row["Temperatura(ºC)"],"Registro": 1
                }
                else:
                    tabla_actual["fin"] = row["hora"]
                    tabla_actual["Corriente_Total"] += row["Corriente"]
                    tabla_actual["Corriente_Max"] = max(tabla_actual["Corriente_Max"], row["Corriente"])
                    tabla_actual["Corriente_Min"] = min(tabla_actual["Corriente_Min"], row["Corriente"])
                    tabla_actual["Temperatura_Max"] = max(tabla_actual["Temperatura_Max"], row["Temperatura(ºC)"])
                    tabla_actual["Temperatura_Min"] = min(tabla_actual["Temperatura_Min"], row["Temperatura(ºC)"])
                    tabla_actual["Registro"] += 1
            else:
                if en_tabla:
                    en_tabla = False
                    tablas.append(tabla_actual)
        return tablas
    

    def mostrar_tablas(parametros_tab, ruta_base):
        archivo_exportado = os.path.join(ruta_base, "datos_exportados.txt")
        if not os.path.isfile(archivo_exportado):
            messagebox.showerror("Error", "No se ha cargado el dataset completo.")
            return
        try:
            datos = pd.read_csv(archivo_exportado, sep='\t')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")
            return
        
        if datos.empty:
            messagebox.showerror("Error", "No se han cargado los datos.")
            return
        

        #Detectar tablas basadas en Madera
        tablas = detectar_tablas(datos)

        #Limpiar la pestaña antes de mostrar nuevas tablas
        for widget in parametros_tab.winfo_children():
                widget.destroy()

        if not tablas:
            messagebox.showinfo("Información", "No se detectaron tablas.")
            return
        #Mostrar tablas detectadas
        ctk.CTkLabel(parametros_tab, text="Tablas detectadas:", font=("Arial", 18)).pack(pady=10)
        tabla_var = ctk.StringVar(value="Seleccione una tabla")
        opciones_tablas = [f"Tabla {i+1}" for i in range(len(tablas))]
        tabla_menu = ctk.CTkOptionMenu(parametros_tab, variable=tabla_var, values=opciones_tablas)
        tabla_menu.pack(pady=10)

        # Crear un frame persistente para los detalles
        detalle_frame = ctk.CTkFrame(parametros_tab, width=600, height=400, corner_radius=15, fg_color="#FFFFFF",border_color="#000000", border_width=2)
        detalle_frame.pack(pady=20)
        

        def mostrar_detalles():
            seleccion = tabla_var.get()
            if seleccion == "Seleccione una tabla":
                messagebox.showerror("Error", "Por favor seleccione una tabla.")
                return
            
            for widget in parametros_tab.winfo_children():
                    widget.destroy()


            indice = int(seleccion.split(" ")[1]) - 1
            tabla = tablas[indice]

            #Calcular duración de corte
            hora_inicio = pd.Timestamp(tabla["inicio"])
            hora_fin = pd.Timestamp(tabla["fin"])
            duracion_corte = (hora_fin - hora_inicio).total_seconds() #Duración en segundos

            #Calcular velocidad (en m/s)
            distancia_mm = datos["Distancia(mm)"].sum() #Suma distancia total
            distancia_m = distancia_mm / 1000 #Convertir a metros
            velocidad = distancia_m / duracion_corte if duracion_corte > 0 else 0

            #marco de detalles
            detalle_frame = ctk.CTkFrame(parametros_tab, width=800, height=400, corner_radius=15, fg_color="#FFFFFF",border_color="#000000", border_width=2)
            detalle_frame.pack(pady=30)
            detalle_frame.pack_propagate(False)

            ctk.CTkLabel(detalle_frame, text=f"Detalles de {seleccion}:", font=("Arial", 16,"bold"),text_color="black").pack(pady=10)
            
            detalles = [
                f"Hora de inicio: {tabla['inicio']}",
                f"Hora de fin: {tabla['fin']}",
                f"Duración de corte: {duracion_corte:.2f} segundos",
                f"Corriente total: {tabla['Corriente_Total']:.2f} A",
                f"Corriente máxima: {tabla['Corriente_Max']:.2f} A",
                f"Corriente mínima: {tabla['Corriente_Min']:.2f} A",
                f"Temperatura máxima: {tabla['Temperatura_Max']:.2f} °C",
                f"Temperatura mínima: {tabla['Temperatura_Min']:.2f} °C",
                f"Velocidad: {velocidad:.2f} m/s"
            ]

            for detalle in detalles:
                ctk.CTkLabel(detalle_frame, text=detalle, font=("Arial", 14),text_color="black",anchor="w").pack(anchor="w", padx=10,pady=5)
            
            datos_frame = ctk.CTkFrame(detalle_frame, width=580, height=240, fg_color="#FFFFFF")
            datos_frame.pack(pady=10, padx=10, fill="both", expand=True)
            datos_frame.pack_propagate(True) 
            

            def visualizar_graficas():
                variables = ["Corriente", "Velocidad (ms)", "Temperatura(ºC)", "Distancia(mm)"]
                hora_inicio = pd.Timestamp(tabla["inicio"]).time()
                hora_fin = pd.Timestamp(tabla["fin"]).time()

                ruta_base = ruta_base_var.get()
                archivo_txt = os.path.join(ruta_base, "datos_exportados.txt")
                if not os.path.isfile(archivo_txt):
                    messagebox.showerror("Error", "No se ha cargado el dataset completo.")
                    return
                try:
                    datos_completos = pd.read_csv(archivo_txt, sep='\t')
                    datos_filtrados = datos_completos[
                        (pd.to_datetime(datos_completos['hora'], format='%H:%M:%S').dt.time >= hora_inicio) &
                        (pd.to_datetime(datos_completos['hora'], format='%H:%M:%S').dt.time <= hora_fin)
                    ]
                    if datos_filtrados.empty:
                        messagebox.showerror("Error", "No hay datos para graficar.")
                        return

                    #Crear subplots
                    fig = make_subplots(rows= len(variables), cols=1,shared_xaxes= True, vertical_spacing= 0.02, subplot_titles=[f"Gráfico de {var}" for var in variables])

                    for i, variable in enumerate(variables, start=1):
                        if variable in datos_filtrados.columns:
                            fig.add_trace(
                                go.Scatter(
                                    x=datos_filtrados['hora'],
                                    y=datos_filtrados[variable],
                                    mode='lines',
                                    name=variable
                                ),
                                row=i, col=1
                            )
                            fig.update_yaxes(title_text=variable,row=i, col=1)

                    fig.update_layout(
                        height=300 * len(variables),
                        title_text= f"Gráficas de Variables desde {tabla['inicio']} hasta {tabla['fin']}",
                        showlegend=False,
                    )

                    temp_html = "temp_plot_all_variables.html"
                    pio.write_html(fig, temp_html, auto_open=False)
                    webbrowser.open(temp_html)
                except Exception as e:
                    messagebox.showerror("Error",f"No se pudo graficar: {e}") 


            ctk.CTkButton(parametros_tab,text="Visualizar gráficas",command=visualizar_graficas,width=200,corner_radius=10).pack(pady=10)

            # Botón para volver atrás
            def volver_atras():
            # Limpiar el frame actual
                for widget in parametros_tab.winfo_children():
                    widget.destroy()
            # Volver a mostrar la lista de tablas
                    mostrar_tablas(parametros_tab, ruta_base)

            ctk.CTkButton(parametros_tab, text="Volver atrás", command=volver_atras,width=200, corner_radius=10).pack(pady=10)


        
        # Botón para cargar datos en la pestaña "Visualizar parámetros por tabla"
        ctk.CTkButton(parametros_tab, text="Mostrar detalles", command=mostrar_detalles).pack(pady=20)

    def cargar_parametros_inicial(parametros_tab, ruta_base):
        mostrar_tablas(parametros_tab, ruta_base)
        for widget in parametros_tab.winfo_children():
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Cargar parámetros de tablas":
                widget.destroy()

    # boton
    ctk.CTkButton(parametros_tab, text="Cargar parámetros de tablas", 
    command=lambda: cargar_parametros_inicial(parametros_tab, ruta_base_var.get())).pack(pady=20)

    ventana.mainloop()

if __name__ == "__main__":
    crear_interfaz()