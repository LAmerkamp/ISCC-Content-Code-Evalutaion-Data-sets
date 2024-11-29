import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from os import listdir
from os.path import isfile, join
import re
import os


def fromMarkdownToDataFrame(path, unit):
    comparison_files = [f for f in listdir(path) if isfile(join(path, f))]
    data = []

    for comparison_file in comparison_files:
        comparison_path = join(path, comparison_file)
        
        # Datei einlesen
        if os.path.exists(comparison_path):
            with open(comparison_path, "r") as file:
                lines = file.readlines()
        else:
            print(f"Die Datei {comparison_path} existiert nicht.")

        # Daten extrahieren (wir überspringen die ersten beiden Zeilen, da sie Header und Trennzeichen sind)
        
        for line in lines[4:]:
            columns = line.split("|")
            if len(columns) < 6:  # Zeilen überspringen, die nicht genug Spalten haben
                continue
            
            filename = columns[1].strip()
            modificationType = filename.split("_")[1]
            content_code = columns[unit].strip() # 3 Für Semantic-Code; 4 für Content-Code
            content_sim = float(content_code.split("%")[0].strip())/100  # Wir nehmen nur den Prozentsatz
            data.append({"name": filename, "modificationType": modificationType, "contentSim": content_sim})

    # DataFrames für die verschiedenen Gruppen erstellen
    df = pd.DataFrame(data)
    return df
    

def ProzentToDouble(value):
    return float(value)/100

def updateAxes(fig):
    fig.update_yaxes(
        range=[0.2, 1.02], 
        tickformat=".0%", 
        dtick=0.1
    )
    fig.update_xaxes(
        categoryorder='array',
        #categoryarray=['_1', '_5', '_10'],  # Reihenfolge der Kategorien
        #tickangle=-45  # Optional: Labels schräg setzen, um Platz zu sparen
        tickangle=0
    )



def updateLayout(fig, title):
    fig.update_layout(
        title_text=title,
        width=500,
        height=500,
    )

def create_Bar_Diagram(df, yName):
    return px.bar(
        df, 
        x='name', 
        y='contentSim', 
        barmode ='group',
        labels={
            'name': 'Modification',
            'contentSim': f'{yName} - Similarity'
        }
        
    )

def create_Line_Diagram(df):
    return px.line(
        df, 
        x='name', 
        y='contentSim', 
        color='resource', 
        markers=True,
        labels={
            'name': 'Modification',
            'contentSim': 'Similarity',
            'resource': 'Data size:'
        }
    )

def createJPEG(fig, name, savePlace):
    fig.write_image(f'{savePlace}/_{name}.jpeg')


def extract_number(filename):
    # Prüfen, ob "same" im Dateinamen enthalten ist
    if "all" in filename:
        return float('inf')  # Gibt einen extrem hohen Wert zurück
    elif "increased" in filename: 
        return 100
    elif "decreased" in filename:
        return 101
    # Andernfalls versuchen, eine Zahl zu extrahieren
    match = re.search(r'(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def sortDataFrame(df):
    df['number'] = df['name'].apply(extract_number)
    df['number2'] = df['resource'].apply(extract_number)
    return df.sort_values(by=['number', 'number2'], ascending=[True, False]).drop(columns=['number', 'number2']) ##Sortiert noch nicht richtig 'number2'

def rename_name_column(name):
    #re.search(r'\d+%', name).group()+".jpg"
    return name.split('virtualViewing_change_playspeed_slower_')[1]

def buildDiagram(path):
    title = "virtualViewing_change_playspeed_slower"      #Ändern
    df_content = fromMarkdownToDataFrame(path, 3)
    df_content['name'] =  df_content['name'].apply(rename_name_column)

    fig_content = create_Bar_Diagram(df_content, "Content")
    updateAxes(fig_content)
    updateLayout(fig_content, title)
    createJPEG(fig_content, title.split("virtualViewing_")[1]+"_content-code", path)    #Ändern
    fig_content.show()

def main():
    path = "Desktop/bachelorarbeit/Testdaten/Ergebnisse/Video/test"
    buildDiagram(path)

if __name__ == "__main__":
    main()